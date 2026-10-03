"""Protocol-level MCP tests with isolated API fixture, no TTS charges."""
import asyncio
from contextlib import asynccontextmanager
import json
import os
from pathlib import Path
import socket
import subprocess
import sys
import threading
import time
import unittest
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from uuid import uuid4

import httpx
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from mcp.client.streamable_http import streamable_http_client

ROOT = Path(__file__).resolve().parents[2]
SAMPLE = json.loads((ROOT / "scripts/rainy-inn.json").read_text())


class FixtureHandler(BaseHTTPRequestHandler):
    calls = []
    records = {}
    revoked = set()

    def log_message(self, *args):
        pass

    def do_GET(self): self.handle_api()
    def do_POST(self): self.handle_api()
    def do_PUT(self): self.handle_api()
    def do_PATCH(self): self.handle_api()
    def do_DELETE(self): self.handle_api()

    def handle_api(self):
        owner = self.headers.get("Authorization", "").removeprefix("Bearer ")
        if owner not in {"fixture-user-a", "fixture-user-b"} or owner in self.revoked:
            return self.respond({"detail": "unauthorized"}, 401)
        payload = json.loads(self.rfile.read(int(self.headers.get("Content-Length", 0))) or b"null")
        path = self.path.removeprefix("/podcast/api")
        self.calls.append((owner, self.command, path, payload))
        if path == "/auth/me": return self.respond({"id": owner})
        if path == "/catalog":
            return self.respond({"voices": [{"id": "Serena"}, {"id": "Ethan"}], "scenes": [{"id": "rainy-inn"}], "script_schema": {"type": "object"}, "preferences_schema": {"type": "object"}, "defaults": {"voice": "Serena"}, "sample_script": SAMPLE})
        if path == "/preferences":
            return self.respond(payload or {"voice": "Serena", "scene": "rainy-inn", "ambience_dbfs": -38, "sleep_timer_minutes": 30})
        if path == "/scripts/validate":
            if payload["script"].get("version") != 1: return self.respond({"detail": "version must be 1"}, 422)
            return self.respond({"valid": True, "script": payload["script"], "characters": 42, "segments": 10})
        if path == "/podcasts":
            if self.command == "GET": return self.respond({"items": [v for v in self.records.values() if v["owner"] == owner]})
            item = {"id": str(uuid4()), "owner": owner, "status": "draft", "stage": "草稿", "progress": 0, "title": payload["script"]["title"], **payload}
            self.records[item["id"]] = item
            return self.respond(item)
        parts = path.strip("/").split("/")
        if len(parts) >= 2 and parts[0] == "podcasts":
            item = self.records.get(parts[1])
            if not item or item["owner"] != owner: return self.respond({"detail": "not found"}, 404)
            if len(parts) == 2:
                if self.command == "DELETE":
                    del self.records[item["id"]]
                    return self.respond({"ok": True})
                if self.command == "PATCH": item.update(payload)
                return self.respond(item)
            action = parts[2]
            if action in {"generate", "retry"}:
                item.update(status="queued", stage="排队中")
                return self.respond(item)
            if action == "cancel":
                item.update(status="cancelled", stage="已取消")
                return self.respond(item)
            if action == "events": return self.respond({"items": [{"status": item["status"], "stage": item["stage"]}]})
            if action == "progress": return self.respond({"ok": True})
        return self.respond({"detail": "unknown route"}, 404)

    def respond(self, data, code=200):
        raw = json.dumps(data).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(raw)))
        self.end_headers()
        self.wfile.write(raw)


def result_json(result):
    if result.isError:
        raise AssertionError(result.content)
    return json.loads(result.content[0].text)


class MCPTransportTests(unittest.IsolatedAsyncioTestCase):
    @classmethod
    def setUpClass(cls):
        cls.api = ThreadingHTTPServer(("127.0.0.1", 0), FixtureHandler)
        cls.thread = threading.Thread(target=cls.api.serve_forever, daemon=True)
        cls.thread.start()
        cls.env = {**os.environ, "AIPODCAST_API_URL": f"http://127.0.0.1:{cls.api.server_port}/podcast/api", "AIPODCAST_TOKEN": "fixture-user-a"}

    @classmethod
    def tearDownClass(cls):
        cls.api.shutdown()
        cls.api.server_close()
        cls.thread.join()

    @asynccontextmanager
    async def stdio(self):
        params = StdioServerParameters(command=sys.executable, args=[str(ROOT / "mcp/server.py")], env=self.env)
        async with stdio_client(params) as streams:
            async with ClientSession(*streams) as session:
                await session.initialize()
                yield session

    async def test_stdio_complete_lifecycle_and_machine_guidance(self):
        async with self.stdio() as session:
            tools = (await session.list_tools()).tools
            self.assertEqual(len(tools), 16)
            self.assertTrue(next(t for t in tools if t.name == "delete_podcast").annotations.destructiveHint)
            data = result_json(await session.call_tool("catalog"))
            self.assertIn("script_schema", data)
            resources = (await session.list_resources()).resources
            self.assertEqual(len(resources), 4)
            schema = await session.read_resource("nightharbor://script-schema")
            self.assertIn("object", schema.contents[0].text)
            guide = await session.get_prompt("prepare_sleep_podcast", {"idea": "雨夜的小房间", "mode": "generate"})
            self.assertIn("request_id", guide.messages[0].content.text)
            self.assertTrue(result_json(await session.call_tool("validate_script", {"script": SAMPLE}))["valid"])
            draft = result_json(await session.call_tool("create_draft", {"script": SAMPLE}))
            pid = draft["id"]
            self.assertEqual(draft["status"], "draft")
            self.assertFalse(any(c[2] == f"/podcasts/{pid}/generate" for c in FixtureHandler.calls))
            result_json(await session.call_tool("update_draft", {"podcast_id": pid, "script": SAMPLE}))
            rid = result_json(await session.call_tool("new_request_id"))["request_id"]
            for _ in range(2):
                queued = result_json(await session.call_tool("generate_podcast", {"podcast_id": pid, "request_id": rid}))
                self.assertEqual(queued["status"], "queued")
            paid = [c for c in FixtureHandler.calls if c[2] == f"/podcasts/{pid}/generate"]
            self.assertEqual([c[3]["request_id"] for c in paid], [rid, rid])
            self.assertFalse(result_json(await session.call_tool("get_audio_link", {"podcast_id": pid}))["ready"])
            result_json(await session.call_tool("get_lifecycle", {"podcast_id": pid}))
            result_json(await session.call_tool("cancel_podcast", {"podcast_id": pid}))
            result_json(await session.call_tool("retry_podcast", {"podcast_id": pid, "request_id": str(uuid4())}))
            FixtureHandler.records[pid].update(status="ready", stage="完成", progress=100, duration_seconds=42, audio_url=f"https://example.test/podcast/api/podcasts/{pid}/audio", narration_url=f"https://example.test/podcast/api/podcasts/{pid}/audio?variant=narration")
            link = result_json(await session.call_tool("get_audio_link", {"podcast_id": pid}))
            self.assertTrue(link["ready"])
            self.assertEqual(link["web_url"], "https://example.test/podcast/")
            self.assertTrue(link["audio_url"].startswith("https://example.test/"))
            self.assertNotIn("fixture-user-a", json.dumps(link))
            result_json(await session.call_tool("save_playback_progress", {"podcast_id": pid, "position_seconds": 12}))
            result_json(await session.call_tool("delete_podcast", {"podcast_id": pid}))
            self.assertNotIn(pid, FixtureHandler.records)

    async def test_validation_and_path_injection_fail_before_mutation(self):
        async with self.stdio() as session:
            bad = await session.call_tool("create_draft", {"script": {"version": 99}})
            self.assertTrue(bad.isError)
            before = len(FixtureHandler.calls)
            bad_id = await session.call_tool("get_podcast", {"podcast_id": "../../auth/me"})
            self.assertTrue(bad_id.isError)
            self.assertEqual(before, len(FixtureHandler.calls))

    async def test_http_auth_two_concurrent_accounts_and_revocation(self):
        with socket.socket() as sock:
            sock.bind(("127.0.0.1", 0))
            port = sock.getsockname()[1]
        env = {**self.env, "AIPODCAST_MCP_PORT": str(port)}
        process = subprocess.Popen([sys.executable, str(ROOT / "mcp/server.py"), "--transport", "streamable-http"], env=env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        url = f"http://127.0.0.1:{port}/podcast/mcp"
        try:
            async with httpx.AsyncClient(trust_env=False) as client:
                for attempt in range(60):
                    try:
                        response = await client.post(url)
                        break
                    except httpx.ConnectError:
                        await asyncio.sleep(.05)
                else: self.fail("HTTP MCP failed to start")
                self.assertEqual(response.status_code, 401)
                invalid = await client.post(url, headers={"Authorization": "Bearer invalid"})
                self.assertEqual(invalid.status_code, 401)
            async def as_user(user):
                async with httpx.AsyncClient(headers={"Authorization": f"Bearer {user}"}, trust_env=False) as http_client:
                    async with streamable_http_client(url, http_client=http_client) as (read, write, _):
                        async with ClientSession(read, write) as session:
                            await session.initialize()
                            draft = result_json(await session.call_tool("create_draft", {"script": SAMPLE}))
                            own = result_json(await session.call_tool("list_podcasts"))
                            self.assertTrue(all(x["owner"] == user for x in own["items"]))
                            return draft
            a, b = await asyncio.gather(as_user("fixture-user-a"), as_user("fixture-user-b"))
            self.assertNotEqual(a["id"], b["id"])
            self.assertEqual(a["owner"], "fixture-user-a")
            self.assertEqual(b["owner"], "fixture-user-b")
            async with httpx.AsyncClient(headers={"Authorization": "Bearer fixture-user-a"}, trust_env=False) as http_client:
                async with streamable_http_client(url, http_client=http_client) as (read, write, _):
                    async with ClientSession(read, write) as session:
                        await session.initialize()
                        denied = await session.call_tool("get_podcast", {"podcast_id": b["id"]})
                        self.assertTrue(denied.isError)
            FixtureHandler.revoked.add("fixture-user-a")
            async with httpx.AsyncClient(trust_env=False) as client:
                revoked = await client.post(url, headers={"Authorization": "Bearer fixture-user-a"})
                self.assertEqual(revoked.status_code, 401)
        finally:
            FixtureHandler.revoked.clear()
            process.terminate()
            process.wait(timeout=5)


if __name__ == "__main__":
    unittest.main()

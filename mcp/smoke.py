#!/usr/bin/env python3
"""Live MCP acceptance. Reads token only from environment; never prints it.

Read-only by default. --create-draft persists a tiny script; --generate explicitly
starts provider synthesis and waits up to --timeout seconds for a terminal state.
"""
from __future__ import annotations
import argparse
import asyncio
from contextlib import asynccontextmanager
import json
import os
from pathlib import Path
import sys
import time
from uuid import uuid4

import httpx
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from mcp.client.streamable_http import streamable_http_client

ROOT = Path(__file__).resolve().parents[1]


def unpack(result):
    if result.isError:
        raise RuntimeError(result.content[0].text)
    return json.loads(result.content[0].text)


@asynccontextmanager
async def connection(args):
    if args.remote:
        async with httpx.AsyncClient(headers={"Authorization": "Bearer " + os.environ["AIPODCAST_TOKEN"]}, trust_env=False, timeout=45) as client:
            async with streamable_http_client(args.remote, http_client=client) as (read, write, _):
                async with ClientSession(read, write) as session:
                    await session.initialize()
                    yield session
    else:
        params = StdioServerParameters(command=sys.executable, args=[str(ROOT / "mcp/server.py")], env=dict(os.environ))
        async with stdio_client(params) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                yield session


async def run(args):
    evidence = {"transport": "http" if args.remote else "stdio"}
    async with connection(args) as session:
        evidence["tools"] = len((await session.list_tools()).tools)
        evidence["resources"] = len((await session.list_resources()).resources)
        evidence["prompts"] = len((await session.list_prompts()).prompts)
        catalog = unpack(await session.call_tool("catalog"))
        evidence["voices"] = [v["id"] for v in catalog["voices"]]
        evidence["preferences"] = unpack(await session.call_tool("get_preferences"))
        library = unpack(await session.call_tool("list_podcasts"))["items"]
        evidence["library_items"] = [{"id": item["id"], "status": item["status"]} for item in library]
        await session.read_resource("nightharbor://script-schema")
        await session.read_resource("nightharbor://authoring-guide")
        pid = args.podcast_id
        if args.create_draft or args.generate:
            script = catalog["sample_script"]
            script["id"] = "mcp-acceptance-" + uuid4().hex[:12]
            script["title"] = "MCP 验收 · 窗边雨声"
            script["segments"] = [{"id": "quiet", "label": "窗边", "text": "窗外是细细的雨。灯光很淡，被子温暖。这个安静的房间，陪你慢慢休息。", "pause_after_seconds": 2}]
            script["mix"].update(intro_seconds=2, tail_seconds=8, fade_out_seconds=5)
            validation = unpack(await session.call_tool("validate_script", {"script": script}))
            evidence["validation"] = {"valid": validation["valid"], "characters": validation["characters"]}
            item = unpack(await session.call_tool("create_draft", {"script": script, "scene": "rainy-inn"}))
            pid = item["id"]
            evidence["created_status"] = item["status"]
        if pid:
            evidence["podcast_id"] = pid
            if args.generate:
                rid = unpack(await session.call_tool("new_request_id"))["request_id"]
                queued = unpack(await session.call_tool("generate_podcast", {"podcast_id": pid, "request_id": rid}))
                repeated = unpack(await session.call_tool("generate_podcast", {"podcast_id": pid, "request_id": rid}))
                assert queued["id"] == repeated["id"] == pid
                evidence["duplicate_request_same_podcast"] = True
                deadline = time.monotonic() + args.timeout
                while time.monotonic() < deadline:
                    item = unpack(await session.call_tool("get_podcast", {"podcast_id": pid}))
                    if item["status"] in ("ready", "failed", "cancelled"):
                        break
                    await asyncio.sleep(3)
                else:
                    evidence["wait_timed_out"] = True
            item = unpack(await session.call_tool("get_podcast", {"podcast_id": pid}))
            evidence["final_status"] = item["status"]
            evidence["progress"] = item["progress"]
            evidence["events"] = unpack(await session.call_tool("get_lifecycle", {"podcast_id": pid}))["items"]
            evidence["audio_link"] = unpack(await session.call_tool("get_audio_link", {"podcast_id": pid}))
            if item["status"] == "ready":
                async with httpx.AsyncClient(trust_env=False, timeout=45) as client:
                    response = await client.get(evidence["audio_link"]["audio_url"], headers={"Authorization": "Bearer " + os.environ["AIPODCAST_TOKEN"], "Range": "bytes=0-1023"})
                    evidence["audio_range"] = {"status": response.status_code, "bytes": len(response.content), "type": response.headers.get("content-type")}
                    assert response.status_code == 206 and len(response.content) == 1024
            if args.delete_after:
                evidence["deleted"] = unpack(await session.call_tool("delete_podcast", {"podcast_id": pid}))["ok"]
    print(json.dumps(evidence, ensure_ascii=False, indent=2))
    if args.generate and evidence.get("final_status") != "ready":
        raise SystemExit(2)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--remote", help="Streamable HTTP MCP URL; default launches local stdio")
    parser.add_argument("--podcast-id", help="Inspect existing podcast, avoiding a new paid job")
    parser.add_argument("--create-draft", action="store_true")
    parser.add_argument("--generate", action="store_true")
    parser.add_argument("--delete-after", action="store_true")
    parser.add_argument("--timeout", type=int, default=300)
    args = parser.parse_args()
    if not os.environ.get("AIPODCAST_TOKEN"):
        parser.error("AIPODCAST_TOKEN must be configured privately in environment")
    asyncio.run(run(args))


if __name__ == "__main__":
    main()

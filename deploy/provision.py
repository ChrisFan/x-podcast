"""Provision isolated AIPodcast resources. Secrets travel over SSH stdin only."""
import json
import os
from pathlib import Path
import secrets
import subprocess
from urllib.parse import quote

ROOT = Path(__file__).resolve().parents[1]
PRIVATE = ROOT / ".local"
SSH = ["ssh", "-i", str(Path.home()/".ssh/alu-designer-deploy"), "-o", "IdentitiesOnly=yes",
       "-o", "BatchMode=yes", "-o", "StrictHostKeyChecking=yes", "deploy@120.55.99.193"]


def remote(command, data=None):
    result = subprocess.run(SSH + [command], input=data, capture_output=True)
    if result.returncode:
        # Provisioning SQL/env may contain secrets; never print raw failure output.
        raise RuntimeError("Remote operation failed (output withheld to protect credentials): " + command.split()[0])
    return result.stdout.decode()


def private_write(name, data):
    path = PRIVATE / name
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    with os.fdopen(fd, "w") as file:
        file.write(data)


def main():
    PRIVATE.mkdir(mode=0o700, exist_ok=True)
    secrets_path = PRIVATE / "deployment-secrets.json"
    if secrets_path.exists():
        config = json.loads(secrets_path.read_text())
    else:
        config = {key: secrets.token_urlsafe(32) for key in ["owner_password", "runtime_password", "invite_code", "acceptance_password"]}
        private_write(secrets_path.name, json.dumps(config))
    remote("sudo -n install -d -m 700 /etc/aipodcast")
    remote("id aipodcast >/dev/null 2>&1 || sudo -n useradd --system --home-dir /var/lib/aipodcast --shell /sbin/nologin aipodcast")
    remote("sudo -n install -d -o aipodcast -g aipodcast -m 750 /var/lib/aipodcast; sudo -n install -d -m 755 /opt/aipodcast/releases /opt/aipodcast/runtime; sudo -n install -d -m 700 /var/backups/aipodcast")
    query = "SELECT datname FROM pg_database WHERE datname='aipodcast';"
    exists = remote("sudo -n docker exec -i aluminum-cloud-test-db psql -X -U aluminum_owner -d postgres -At", query.encode()).strip()
    if not exists:
        sql = fr"""\set ON_ERROR_STOP on
CREATE ROLE aipodcast_owner LOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE NOREPLICATION PASSWORD '{config['owner_password']}';
CREATE ROLE aipodcast_runtime LOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE NOREPLICATION PASSWORD '{config['runtime_password']}';
CREATE DATABASE aipodcast OWNER aipodcast_owner;
REVOKE ALL ON DATABASE aipodcast FROM PUBLIC;
GRANT CONNECT ON DATABASE aipodcast TO aipodcast_runtime;
\connect aipodcast
REVOKE ALL ON SCHEMA public FROM PUBLIC;
ALTER SCHEMA public OWNER TO aipodcast_owner;
GRANT USAGE ON SCHEMA public TO aipodcast_runtime;
ALTER DEFAULT PRIVILEGES FOR ROLE aipodcast_owner IN SCHEMA public GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO aipodcast_runtime;
ALTER DEFAULT PRIVILEGES FOR ROLE aipodcast_owner IN SCHEMA public GRANT USAGE, SELECT ON SEQUENCES TO aipodcast_runtime;
"""
        remote("sudo -n docker exec -i aluminum-cloud-test-db psql -X -q -U aluminum_owner -d postgres", sql.encode())
    def url(role, password, port):
        return f"postgresql://{role}:{quote(password, safe='')}@127.0.0.1:{port}/aipodcast"
    local_runtime = url("aipodcast_runtime",config["runtime_password"],55440)
    local_owner = url("aipodcast_owner",config["owner_password"],55440)
    api_key = ""
    for line in (ROOT/".env").read_text().splitlines():
        if line.startswith("DASHSCOPE_API_KEY="):
            api_key = line.partition("=")[2]
    if not api_key:
        raise RuntimeError("Local TTS API key missing")
    env = {
        "DATABASE_URL": url("aipodcast_runtime",config["runtime_password"],55439),
        "PODCAST_DATA_DIR": "/var/lib/aipodcast",
        "PODCAST_PUBLIC_BASE_URL": "https://alu-designer.pawlpixel.com/podcast/api",
        "PODCAST_INVITE_CODE": config["invite_code"],
        "DASHSCOPE_API_KEY": api_key,
        "DASHSCOPE_REGION": "beijing",
        "AIPODCAST_API_URL": "http://127.0.0.1:3211/podcast/api",
    }
    remote("sudo -n sh -c 'umask 077; cat > /etc/aipodcast/api.env'", "\n".join(f"{k}={v}" for k,v in env.items()).encode()+b"\n")
    private_write("server.env", "DATABASE_URL="+local_runtime+"\nPODCAST_DATA_DIR="+str(PRIVATE/"data")+"\nPODCAST_INVITE_CODE="+config["invite_code"]+"\n")
    private_write("owner.env", "DATABASE_URL="+local_owner+"\n")
    private_write("ACCESS.md", "# 夜航 MVP 私密访问资料\n\n网页：https://alu-designer.pawlpixel.com/podcast/\n\n注册邀请码："+config["invite_code"]+"\n\n联调账号：mvp-owner@example.invalid\n\n联调密码："+config["acceptance_password"]+"\n\n账号由验收流程创建；请在验收完成后使用，或自行注册个人账号。不要提交或公开本文件。\n")
    print("Isolated DB/users/config prepared. Credentials saved under .local (not printed).")


if __name__ == "__main__":
    main()

"""Package only source files and deploy without touching shared databases/services."""
import argparse
from datetime import datetime
from pathlib import Path
import subprocess
import tarfile
from zoneinfo import ZoneInfo
from provision import ROOT, SSH, remote


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--publish',action='store_true',help='Install HTTPS route and start services after packaging')
    args=parser.parse_args()
    release=datetime.now(ZoneInfo('Asia/Shanghai')).strftime('%Y%m%d-%H%M%S')
    archive=ROOT/'.local/release.tar.gz'
    with tarfile.open(archive,'w:gz') as out:
        for name in ['podcast.py','requirements.txt','server','web','mcp','skills','scripts','deploy','docs','README.md']:
            path=ROOT/name
            if not path.exists():
                continue
            candidates=[path] if path.is_file() else path.rglob('*')
            for file in candidates:
                rel=file.relative_to(ROOT)
                if file.is_file() and not any(p in ('__pycache__','node_modules','.venv','artifacts','.pytest_cache') for p in rel.parts) and file.suffix!='.pyc':
                    out.add(file,arcname=str(rel))
    subprocess.run(['scp','-q',*SSH[1:-1],str(archive),SSH[-1]+':/tmp/aipodcast-release.tar.gz'],check=True)
    dest='/opt/aipodcast/releases/'+release
    remote('sudo -n mkdir -p '+dest+'; sudo -n tar -xzf /tmp/aipodcast-release.tar.gz -C '+dest)
    remote("sudo -n sh -c 'readlink -f /opt/aipodcast/current > /etc/aipodcast/previous-release.txt || true'")
    remote('sudo -n ln -sfn '+dest+' /opt/aipodcast/current')
    remote('sudo -n install -m 644 '+dest+'/deploy/aipodcast.service '+dest+'/deploy/aipodcast-mcp.service '+dest+'/deploy/aipodcast-backup.service '+dest+'/deploy/aipodcast-backup.timer /etc/systemd/system/')
    remote('sudo -n chmod +x '+dest+'/deploy/backup.sh; sudo -n systemctl daemon-reload')
    if args.publish:
        remote('sudo -n systemctl enable --now aipodcast.service aipodcast-mcp.service')
        remote('sudo -n systemctl restart aipodcast.service aipodcast-mcp.service')
        # Check local health before changing public routing.
        remote("for i in $(seq 1 30); do curl -fsS http://127.0.0.1:3211/podcast/api/health && exit 0; sleep 1; done; exit 1")
        remote('sudo -n install -m 644 '+dest+'/deploy/aipodcast.nginx.conf /etc/nginx/snippets/aipodcast.conf')
        patch=r'''
from pathlib import Path
import shutil,time,subprocess
p=Path('/etc/nginx/conf.d/pawlpixel.conf')
text=p.read_text()
include='    include /etc/nginx/snippets/aipodcast.conf;\n'
anchor='    root /var/www/alu-designer;\n'
if include not in text:
    if text.count(anchor)!=1: raise RuntimeError('Expected exactly one existing app server')
    backup=Path('/etc/nginx/aipodcast-backups')
    backup.mkdir(exist_ok=True)
    saved=backup/('pawlpixel-'+str(int(time.time()))+'.conf')
    shutil.copy2(p,saved)
    p.write_text(text.replace(anchor,anchor+include))
    checked=subprocess.run(['nginx','-t'],capture_output=True)
    if checked.returncode:
        shutil.copy2(saved,p)
        raise RuntimeError('Nginx check failed, previous configuration restored')
subprocess.run(['nginx','-t'],check=True)
subprocess.run(['systemctl','reload','nginx'],check=True)
'''
        remote('sudo -n /opt/aipodcast/venv/bin/python -',patch.encode())
        remote('sudo -n systemctl enable --now aipodcast-backup.timer')
    print('Deployed release '+dest+(' and published HTTPS route' if args.publish else ' (not started)'))


if __name__=='__main__':
    main()

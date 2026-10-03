"""Verify only AIPodcast's latest backup in a uniquely named temporary database."""
import json
from datetime import datetime,timezone
from pathlib import Path
from provision import remote, ROOT


def main():
    backup=remote("sudo -n sh -c 'ls -dt /var/backups/aipodcast/snapshot-* | head -n 1'").strip()
    if not backup.startswith('/var/backups/aipodcast/snapshot-') or any(x in backup for x in ('\n',"'",' ')):
        raise RuntimeError('Unexpected backup location')
    temp='aipodcast_restore_'+datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')
    remote("sudo -n sh -c 'cd "+backup+" && sha256sum -c SHA256SUMS'")
    remote('sudo -n docker exec aluminum-cloud-test-db createdb -U aluminum_owner -O aipodcast_owner '+temp)
    try:
        remote("sudo -n sh -c 'docker exec -i aluminum-cloud-test-db pg_restore -U aluminum_owner -d "+temp+" < "+backup+"/database.dump'")
        permissions=json.loads(remote('sudo -n docker exec -i aluminum-cloud-test-db psql -X -U aluminum_owner -d '+temp+' -At',b"SELECT json_build_object('tables_owned_by_migration_role', NOT EXISTS (SELECT FROM pg_tables WHERE schemaname='public' AND tableowner<>'aipodcast_owner'),'runtime_can_read',has_table_privilege('aipodcast_runtime','podcasts','SELECT'),'runtime_cannot_create',NOT has_schema_privilege('aipodcast_runtime','public','CREATE'));"))
        if not all(permissions.values()): raise RuntimeError('Restored owner/ACL mismatch')
        query="SELECT json_build_object('accounts',(SELECT count(*) FROM accounts),'podcasts',(SELECT count(*) FROM podcasts),'jobs',(SELECT count(*) FROM jobs),'events',(SELECT count(*) FROM events),'ready',(SELECT count(*) FROM podcasts WHERE status='ready'),'main_script_md5',(SELECT md5(script::text) FROM podcasts WHERE id='49df1434-5da8-41f2-b050-3ee0bc4a0aeb'));"
        restored=json.loads(remote('sudo -n docker exec -i aluminum-cloud-test-db psql -X -U aluminum_owner -d '+temp+' -At',query.encode()))
        live_hash=remote('sudo -n docker exec -i aluminum-cloud-test-db psql -X -U aluminum_owner -d aipodcast -At',"SELECT md5(script::text) FROM podcasts WHERE id='49df1434-5da8-41f2-b050-3ee0bc4a0aeb';".encode()).strip()
        if restored['main_script_md5']!=live_hash or restored['ready']<2:
            raise RuntimeError('Restored ready podcasts/script mismatch')
        # Extract privately and validate that ready audio is present and content-identical.
        extract='/var/backups/aipodcast/'+temp
        remote('sudo -n install -d -m 700 '+extract)
        try:
            remote('sudo -n tar -xzf '+backup+'/assets.tar.gz -C '+extract)
            script="""import hashlib,json,pathlib,sys
base=pathlib.Path(sys.argv[1]); source=pathlib.Path('/var/lib/aipodcast'); checked=0
for p in base.rglob('*.mp3'):
    current=source/p.relative_to(base)
    if not current.exists() or hashlib.sha256(current.read_bytes()).digest()!=hashlib.sha256(p.read_bytes()).digest(): raise SystemExit('Audio hash mismatch')
    checked+=1
assert checked>=4
print(json.dumps({'mp3_files_verified':checked}))
"""
            asset=json.loads(remote('sudo -n /opt/aipodcast/venv/bin/python - '+extract,script.encode()))
        finally:
            remote('sudo -n rm -rf -- '+extract)
        result={'backup':backup,'temporary_database':temp,'restored':restored,'permissions':permissions,'audio':asset,'passed':True}
        (ROOT/'acceptance/restore-results.json').write_text(json.dumps(result,indent=2))
        print(json.dumps(result,indent=2))
    finally:
        remote('sudo -n docker exec aluminum-cloud-test-db dropdb -U aluminum_owner '+temp)


if __name__=='__main__': main()

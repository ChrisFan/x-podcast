#!/bin/bash
set -euo pipefail
umask 077
base=/var/backups/aipodcast
stamp=$(date -u +%Y%m%dT%H%M%SZ)
stage="$base/.partial-$stamp"
target="$base/snapshot-$stamp"
mkdir -p "$stage"
trap 'rm -rf -- "$stage"' EXIT
docker exec aluminum-cloud-test-db pg_dump -U aluminum_owner -d aipodcast -Fc > "$stage/database.dump"
test -s "$stage/database.dump"
# Only this app's assets and configuration. Shared DB/container is never stopped.
tar -czf "$stage/assets.tar.gz" -C /var/lib/aipodcast .
tar -czf "$stage/config.tar.gz" -C /etc/aipodcast .
cat > "$stage/roles.sql" <<'SQL'
-- Restore only into a new/rebuilt instance after checking role existence.
CREATE ROLE aipodcast_owner LOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE NOREPLICATION;
CREATE ROLE aipodcast_runtime LOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE NOREPLICATION;
-- Set runtime password privately from config.tar.gz api.env; set a new migration-owner password.
SQL
readlink -f /opt/aipodcast/current > "$stage/release.txt"
(cd "$stage" && sha256sum database.dump assets.tar.gz config.tar.gz roles.sql > SHA256SUMS)
mv "$stage" "$target"
find "$base" -maxdepth 1 -type d -name 'snapshot-*' -mtime +7 -exec rm -rf -- {} +
printf 'AIPodcast backup completed: %s\n' "$target"

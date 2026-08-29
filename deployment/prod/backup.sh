#!/bin/bash
# Nightly backup: both databases, the GNS3 project volume, then an off-host copy.
# Installed at /usr/local/bin/onlinetlabs-backup, driven by onlinetlabs-backup.timer.
set -euo pipefail

DEST=/root/backups
RETENTION_DAYS=14
ENV_FILE=/etc/onlinetlabs-backup.env
ts=$(date +%F_%H%M%S)
umask 077

# BACKUP_REMOTE  rclone destination, e.g. "b2:onlinetlabs-backups"
# BACKUP_PASSPHRASE  symmetric key for the archive that leaves the machine
# shellcheck source=/dev/null
[ -f "$ENV_FILE" ] && . "$ENV_FILE"

made=()

dump_one() {
  local container="$1" user="$2" db="$3" name="$4"
  local out="$DEST/${name}-${ts}.dump"
  if ! docker exec "$container" pg_dump -U "$user" -Fc "$db" > "$out"; then
    rm -f "$out"; echo "FAILED: $name"; return 1
  fi
  if ! docker exec -i "$container" pg_restore -l < "$out" > /dev/null 2>&1; then
    rm -f "$out"; echo "CORRUPT: $name"; return 1
  fi
  echo "ok: $out ($(stat -c%s "$out") bytes)"
  made+=("$out")
}

dump_one prod-db-1 onlinetlabs onlinetlabs onlinetlabs
dump_one gns3-postgres-1 "$(docker exec gns3-postgres-1 printenv POSTGRES_USER)" "$(docker exec gns3-postgres-1 printenv POSTGRES_DB)" gns3

# GNS3 project data: the lab template projects live here, not in postgres.
# images/ is excluded: large and rebuildable from the deploy.
tar_out="$DEST/gns3-runtime-${ts}.tar.gz"
if tar -czf "$tar_out" -C /opt/onlinetlabs/gns3 runtime 2>/dev/null; then
  if tar -tzf "$tar_out" > /dev/null 2>&1; then
    echo "ok: $tar_out ($(stat -c%s "$tar_out") bytes)"
    made+=("$tar_out")
  else
    rm -f "$tar_out"; echo "CORRUPT: gns3-runtime"
  fi
else
  rm -f "$tar_out"; echo "FAILED: gns3-runtime"
fi

find "$DEST" \( -name '*.dump' -o -name '*.tar.gz' \) -mtime +$RETENTION_DAYS -delete

# Off-host copy is optional and currently not configured by choice.
# Set BACKUP_REMOTE and BACKUP_PASSPHRASE in $ENV_FILE to enable it.
if [ -z "${BACKUP_REMOTE:-}" ] || [ -z "${BACKUP_PASSPHRASE:-}" ]; then
  echo "note: off-host copy disabled, every copy is on the disk it backs up"
  exit 0
fi

command -v rclone > /dev/null || { echo "FAILED: rclone is not installed"; exit 1; }

for path in "${made[@]}"; do
  enc="${path}.enc"
  if ! openssl enc -aes-256-cbc -salt -pbkdf2 -in "$path" -out "$enc" \
        -pass "pass:${BACKUP_PASSPHRASE}"; then
    rm -f "$enc"; echo "FAILED: encrypt $path"; exit 1
  fi
  if ! rclone copy --no-traverse "$enc" "$BACKUP_REMOTE/"; then
    rm -f "$enc"; echo "FAILED: upload $enc"; exit 1
  fi
  echo "off-host: $(basename "$enc")"
  rm -f "$enc"
done

rclone delete --min-age "${RETENTION_DAYS}d" "$BACKUP_REMOTE/" || true

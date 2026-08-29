# Backup units

Install on the prod host:

```
install -m 700 deployment/prod/backup.sh /usr/local/bin/onlinetlabs-backup
install -m 644 deployment/prod/systemd/onlinetlabs-backup.* /etc/systemd/system/
systemctl daemon-reload && systemctl enable --now onlinetlabs-backup.timer
```

Off-host copy needs `/etc/onlinetlabs-backup.env` (mode 600):

```
BACKUP_REMOTE=<rclone remote>:<bucket>
BACKUP_PASSPHRASE=<symmetric key>
```

Without it the run reports failure rather than silently keeping every copy on
the disk it backs up. `rclone` must be installed and its remote configured.

Restore drill, on a clean host:

```
rclone copy "$BACKUP_REMOTE/onlinetlabs-<ts>.dump.enc" .
openssl enc -aes-256-cbc -d -salt -pbkdf2 -in onlinetlabs-<ts>.dump.enc \
  -out onlinetlabs.dump -pass "pass:$BACKUP_PASSPHRASE"
pg_restore -d onlinetlabs onlinetlabs.dump
```

#!/bin/sh
# Boot gns3server. Templates and IOS images are provisioned externally:
#   - images: bind-mounted from host at /data/images
#   - templates: registered by gns3-service on its startup
set -eu

CONFIG=${CONFIG:-/data/config.ini}
[ -f "$CONFIG" ] || cp /config.ini "$CONFIG"

# Подставляем админ-креды из env (prod) в конфиг — иначе остаётся dev-fallback admin/admin.
# Применяется при создании админа на первом старте (пустой controller-DB).
[ -n "${GNS3_DEFAULT_ADMIN_USER:-}" ] && \
  sed -i "s|^default_admin_username = .*|default_admin_username = ${GNS3_DEFAULT_ADMIN_USER}|" "$CONFIG"
[ -n "${GNS3_DEFAULT_ADMIN_PASSWORD:-}" ] && \
  sed -i "s|^default_admin_password = .*|default_admin_password = ${GNS3_DEFAULT_ADMIN_PASSWORD}|" "$CONFIG"

cd /data
exec gns3server -A --config "$CONFIG"

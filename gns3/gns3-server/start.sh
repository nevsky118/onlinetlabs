#!/bin/sh
# Boot gns3server. Templates and IOS images are provisioned externally:
#   - images: bind-mounted from host at /data/images
#   - templates: registered by gns3-service on its startup
set -eu

CONFIG=${CONFIG:-/data/config.ini}
[ -f "$CONFIG" ] || cp /config.ini "$CONFIG"

cd /data
exec gns3server -A --config "$CONFIG"

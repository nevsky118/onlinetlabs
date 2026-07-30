#!/bin/sh
# PE-3: the trap goes before set -eu, otherwise an early failure kills the process without cleanup (zombie daemons).
shutdown() {
    echo "Received signal — stopping FRR daemons..."
    if [ -n "${TAIL_PID:-}" ]; then
        kill -TERM "$TAIL_PID" 2>/dev/null || true
    fi
    /usr/lib/frr/frrinit.sh stop || true
    exit 0
}
trap shutdown TERM INT

set -eu

ROLE="${FRR_ROLE:-}"

# Setup VLAN sub-interfaces if eth0/eth1 are present (GNS3 ubridge attaches them)
# Retry: ubridge may attach interfaces slightly after container start.
ETH0_TIMEOUT="${FRR_IFACE_TIMEOUT:-10}"
ETH0_READY=0
i=0
while [ "$i" -lt "$ETH0_TIMEOUT" ]; do
    if ip link show eth0 >/dev/null 2>&1; then
        ETH0_READY=1
        break
    fi
    i=$((i + 1))
    echo "Waiting for eth0 ($i/$ETH0_TIMEOUT)..."
    sleep 1
done

if [ "$ETH0_READY" -eq 0 ]; then
    echo "ERROR: eth0 not present after ${ETH0_TIMEOUT}s — ubridge attach failed; refusing to continue" >&2
    exit 1
fi

# eth0/eth1 are flat interfaces, the role's FRR config assigns the IPs.
ip link set eth0 up || true

if ip link show eth1 >/dev/null 2>&1; then
    ip link set eth1 up || true
fi

# Start FRR daemons — fail loud if it doesn't come up.
/usr/lib/frr/frrinit.sh start

# Wait for vtysh ready
VTYSH_TIMEOUT="${FRR_VTYSH_TIMEOUT:-12}"
VTYSH_READY=0
i=0
while [ "$i" -lt "$VTYSH_TIMEOUT" ]; do
    if vtysh -c "show version" >/dev/null 2>&1; then
        VTYSH_READY=1
        break
    fi
    i=$((i + 1))
    sleep 1
done

if [ "$VTYSH_READY" -eq 0 ]; then
    echo "ERROR: vtysh not ready after ${VTYSH_TIMEOUT}s — FRR daemons failed to come up" >&2
    exit 1
fi

# PE-1: rendering of the role (env+tmpl). There is no static fallback, no env means we fail explicitly.
ROLE_CONFIGS_DIR=/etc/frr/role-configs
RENDERED_CONFIG=/etc/frr/role-configs/rendered.cfg
CONFIG_PATH=""

if [ -n "$ROLE" ]; then
    ENV_FILE="$ROLE_CONFIGS_DIR/$ROLE.env"

    # The template and the set of required variables depend on the role.
    # GW is a flat gateway for two /24 subnets without OSPF; the rest are OSPF site+backbone.
    if [ "$ROLE" = "GW" ]; then
        TMPL_FILE="$ROLE_CONFIGS_DIR/gw.cfg.tmpl"
        REQUIRED_VARS="FRR_HOSTNAME FRR_ETH0_IP FRR_ETH1_IP"
    else
        TMPL_FILE="$ROLE_CONFIGS_DIR/frr.cfg.tmpl"
        REQUIRED_VARS="FRR_HOSTNAME FRR_SITE_IP FRR_SITE_NET FRR_BACKBONE_IP FRR_BACKBONE_NET FRR_ROUTER_ID"
    fi

    if [ ! -f "$ENV_FILE" ] || [ ! -f "$TMPL_FILE" ]; then
        echo "ERROR: FRR_ROLE=$ROLE has no $ENV_FILE or $TMPL_FILE" >&2
        exit 1
    fi

    # shellcheck disable=SC1090
    set -a
    . "$ENV_FILE"
    set +a

    # Validation of the required variables, otherwise envsubst substitutes empty values and the config comes out broken.
    for _v in $REQUIRED_VARS; do
        eval "_val=\${$_v:-}"
        if [ -z "$_val" ]; then
            echo "ERROR: $_v is not set in $ENV_FILE" >&2
            exit 1
        fi
    done

    echo "Rendering $(basename "$TMPL_FILE") from $ENV_FILE (role=$ROLE)"
    envsubst < "$TMPL_FILE" > "$RENDERED_CONFIG"
    echo "=== rendered config ==="
    cat "$RENDERED_CONFIG"
    echo "======================="
    CONFIG_PATH="$RENDERED_CONFIG"
fi

if [ -n "$CONFIG_PATH" ] && [ -f "$CONFIG_PATH" ]; then
    echo "Applying $CONFIG_PATH (role=$ROLE)"
    vtysh -f "$CONFIG_PATH" || echo "vtysh -f returned non-zero (transient — link may still be coming up)"
else
    echo "FRR_ROLE not set; booting bare FRR"
fi

# Keep container alive — PID-1 signal proxying: forward SIGTERM/INT to FRR
# before exiting so daemons shut down cleanly (no orphaned processes).
echo "FRR ready (role=${ROLE:-bare})"

if [ -f /var/log/frr/zebra.log ]; then
    tail -F /var/log/frr/zebra.log &
    TAIL_PID=$!
    wait "$TAIL_PID"
else
    sleep infinity &
    TAIL_PID=$!
    wait "$TAIL_PID"
fi

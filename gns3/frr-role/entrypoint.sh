#!/bin/sh
# PE-3: trap регистрируется ДО set -eu — иначе ранний сбой (frrinit.sh start)
# завершит процесс без cleanup, оставив зомби-демонов.
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
ETH0_READY=0
for i in 1 2 3 4 5 6 7 8 9 10; do
    if ip link show eth0 >/dev/null 2>&1; then
        ETH0_READY=1
        break
    fi
    echo "Waiting for eth0 (attempt $i)..."
    sleep 1
done

if [ "$ETH0_READY" -eq 0 ]; then
    echo "ERROR: eth0 not present after 10 attempts — ubridge attach failed; refusing to continue" >&2
    exit 1
fi

# eth0 — плоский site-интерфейс (IP вешает FRR-конфиг). VLAN-сабинтерфейсы
# больше не нужны: топология упрощена до PC1—R1═R2—PC3 без свитчей.
ip link set eth0 up || true

if ip link show eth1 >/dev/null 2>&1; then
    ip link set eth1 up || true
fi

# Start FRR daemons — fail loud if it doesn't come up.
/usr/lib/frr/frrinit.sh start

# Wait for vtysh ready
VTYSH_READY=0
for i in 1 2 3 4 5 6 7 8 9 10 11 12; do
    if vtysh -c "show version" >/dev/null 2>&1; then
        VTYSH_READY=1
        break
    fi
    sleep 1
done

if [ "$VTYSH_READY" -eq 0 ]; then
    echo "ERROR: vtysh not ready after 12 attempts — FRR daemons failed to come up" >&2
    exit 1
fi

# PE-1: рендер конфига роли.
# Приоритет: env-файл + шаблон envsubst → fallback на статический .cfg (backward compat).
ROLE_CONFIGS_DIR=/etc/frr/role-configs
RENDERED_CONFIG=/etc/frr/role-configs/rendered.cfg
CONFIG_PATH=""

if [ -n "$ROLE" ]; then
    ENV_FILE="$ROLE_CONFIGS_DIR/$ROLE.env"
    TMPL_FILE="$ROLE_CONFIGS_DIR/frr.cfg.tmpl"
    STATIC_CFG="$ROLE_CONFIGS_DIR/$ROLE.cfg"

    if [ -f "$ENV_FILE" ] && [ -f "$TMPL_FILE" ]; then
        echo "Rendering frr.cfg.tmpl с $ENV_FILE (role=$ROLE)"
        # shellcheck disable=SC1090
        set -a
        . "$ENV_FILE"
        set +a
        envsubst < "$TMPL_FILE" > "$RENDERED_CONFIG"
        CONFIG_PATH="$RENDERED_CONFIG"
    elif [ -f "$STATIC_CFG" ]; then
        echo "WARN: $ENV_FILE отсутствует — fallback на статический $STATIC_CFG"
        CONFIG_PATH="$STATIC_CFG"
    fi
fi

if [ -n "$CONFIG_PATH" ] && [ -f "$CONFIG_PATH" ]; then
    echo "Applying $CONFIG_PATH (role=$ROLE)"
    vtysh -f "$CONFIG_PATH" || echo "vtysh -f returned non-zero (transient — link may still be coming up)"
else
    echo "FRR_ROLE not set ($ROLE); booting bare FRR"
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

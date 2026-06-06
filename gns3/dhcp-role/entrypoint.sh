#!/bin/sh
# trap регистрируется ДО set -eu — иначе ранний сбой завершит процесс без cleanup.
shutdown() {
    echo "Received signal — stopping dnsmasq..."
    [ -n "${TAIL_PID:-}" ] && kill -TERM "$TAIL_PID" 2>/dev/null || true
    [ -n "${DNSMASQ_PID:-}" ] && kill -TERM "$DNSMASQ_PID" 2>/dev/null || true
    exit 0
}
trap shutdown TERM INT

set -eu

# GNS3 ubridge подключает eth0 чуть позже старта контейнера.
ETH0_TIMEOUT="${DHCP_IFACE_TIMEOUT:-10}"
ETH0_READY=0
i=0
while [ "$i" -lt "$ETH0_TIMEOUT" ]; do
    if ip link show eth0 >/dev/null 2>&1; then ETH0_READY=1; break; fi
    i=$((i + 1)); echo "Waiting for eth0 ($i/$ETH0_TIMEOUT)..."; sleep 1
done
if [ "$ETH0_READY" -eq 0 ]; then
    echo "ERROR: eth0 not present after ${ETH0_TIMEOUT}s — ubridge attach failed" >&2
    exit 1
fi

# Валидация обязательных переменных — иначе рендер даст битый dnsmasq.conf.
for _v in DHCP_SUBNET DHCP_RANGE DHCP_GATEWAY; do
    eval "_val=\${$_v:-}"
    if [ -z "$_val" ]; then echo "ERROR: $_v не задана" >&2; exit 1; fi
done

# Префикс из DHCP_SUBNET (192.168.10.0/24 -> 24): нужен для ip addr add.
DHCP_PREFIX="${DHCP_SUBNET##*/}"
if [ "$DHCP_PREFIX" = "$DHCP_SUBNET" ] || [ -z "$DHCP_PREFIX" ]; then
    echo "ERROR: DHCP_SUBNET=$DHCP_SUBNET без /prefix" >&2; exit 1
fi
DHCP_LEASE_TIME="${DHCP_LEASE_TIME:-24h}"

# eth0 — плоский site-интерфейс. GNS3 IP не вешает, адрес шлюза вешаем сами.
ip addr add "$DHCP_GATEWAY/$DHCP_PREFIX" dev eth0
ip link set eth0 up

export DHCP_SUBNET DHCP_RANGE DHCP_GATEWAY DHCP_LEASE_TIME
TMPL_FILE=/etc/dnsmasq/role-configs/dnsmasq.conf.tmpl
RENDERED_CONFIG=/etc/dnsmasq/role-configs/dnsmasq.conf
if [ ! -f "$TMPL_FILE" ]; then echo "ERROR: нет шаблона $TMPL_FILE" >&2; exit 1; fi

echo "Rendering dnsmasq.conf.tmpl (subnet=$DHCP_SUBNET range=$DHCP_RANGE gw=$DHCP_GATEWAY lease=$DHCP_LEASE_TIME)"
envsubst < "$TMPL_FILE" > "$RENDERED_CONFIG"
echo "=== rendered config ==="; cat "$RENDERED_CONFIG"; echo "======================="

dnsmasq -k --conf-file="$RENDERED_CONFIG" &
DNSMASQ_PID=$!
echo "dnsmasq ready (subnet=$DHCP_SUBNET)"

# PID-1 проксирует сигналы дочернему процессу.
if [ -f /var/log/dnsmasq.log ]; then
    tail -F /var/log/dnsmasq.log & TAIL_PID=$!; wait "$TAIL_PID"
else
    sleep infinity & TAIL_PID=$!; wait "$TAIL_PID"
fi

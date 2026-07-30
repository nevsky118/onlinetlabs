#!/bin/sh
# The trap is registered BEFORE set -eu, otherwise an early failure ends the process without cleanup.
shutdown() {
    echo "Received signal — stopping dnsmasq..."
    [ -n "${TAIL_PID:-}" ] && kill -TERM "$TAIL_PID" 2>/dev/null || true
    [ -n "${DNSMASQ_PID:-}" ] && kill -TERM "$DNSMASQ_PID" 2>/dev/null || true
    exit 0
}
trap shutdown TERM INT

set -eu

# GNS3 ubridge attaches eth0 slightly after the container starts.
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

# Validation of the required variables, otherwise rendering produces a broken dnsmasq.conf.
for _v in DHCP_SUBNET DHCP_RANGE DHCP_GATEWAY; do
    eval "_val=\${$_v:-}"
    if [ -z "$_val" ]; then echo "ERROR: $_v is not set" >&2; exit 1; fi
done

# Prefix taken from DHCP_SUBNET (192.168.10.0/24 -> 24), needed for ip addr add.
DHCP_PREFIX="${DHCP_SUBNET##*/}"
if [ "$DHCP_PREFIX" = "$DHCP_SUBNET" ] || [ -z "$DHCP_PREFIX" ]; then
    echo "ERROR: DHCP_SUBNET=$DHCP_SUBNET has no /prefix" >&2; exit 1
fi
DHCP_LEASE_TIME="${DHCP_LEASE_TIME:-24h}"

# eth0 is a flat site interface. GNS3 does not assign an IP, we assign the gateway address ourselves.
ip addr add "$DHCP_GATEWAY/$DHCP_PREFIX" dev eth0
ip link set eth0 up

export DHCP_SUBNET DHCP_RANGE DHCP_GATEWAY DHCP_LEASE_TIME
TMPL_FILE=/etc/dnsmasq/role-configs/dnsmasq.conf.tmpl
RENDERED_CONFIG=/etc/dnsmasq/role-configs/dnsmasq.conf
if [ ! -f "$TMPL_FILE" ]; then echo "ERROR: template $TMPL_FILE is missing" >&2; exit 1; fi

echo "Rendering dnsmasq.conf.tmpl (subnet=$DHCP_SUBNET range=$DHCP_RANGE gw=$DHCP_GATEWAY lease=$DHCP_LEASE_TIME)"
envsubst < "$TMPL_FILE" > "$RENDERED_CONFIG"
echo "=== rendered config ==="; cat "$RENDERED_CONFIG"; echo "======================="

dnsmasq -k --conf-file="$RENDERED_CONFIG" &
DNSMASQ_PID=$!
echo "dnsmasq ready (subnet=$DHCP_SUBNET)"

# PID 1 proxies signals to the child process.
if [ -f /var/log/dnsmasq.log ]; then
    tail -F /var/log/dnsmasq.log & TAIL_PID=$!; wait "$TAIL_PID"
else
    sleep infinity & TAIL_PID=$!; wait "$TAIL_PID"
fi

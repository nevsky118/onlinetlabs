FROM quay.io/frrouting/frr:9.1.0

USER root
# iproute2 for ip link / VLAN sub-interfaces
# gettext gives envsubst, needed to render frr.cfg.tmpl from the role's env file
RUN apk add --no-cache iproute2 gettext

COPY configs/daemons /etc/frr/daemons
# Template plus role env files (new path, PE-1).
COPY configs/frr.cfg.tmpl /etc/frr/role-configs/frr.cfg.tmpl
COPY configs/R1.env /etc/frr/role-configs/R1.env
COPY configs/R2.env /etc/frr/role-configs/R2.env
COPY configs/gw.cfg.tmpl /etc/frr/role-configs/gw.cfg.tmpl
COPY configs/GW.env /etc/frr/role-configs/GW.env
COPY entrypoint.sh /usr/local/bin/onlinetlabs-entrypoint

RUN chmod +x /usr/local/bin/onlinetlabs-entrypoint && \
    mkdir -p /etc/frr/role-configs

ENTRYPOINT ["/usr/local/bin/onlinetlabs-entrypoint"]

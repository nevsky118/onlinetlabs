FROM quay.io/frrouting/frr:9.1.0

USER root
# iproute2 — для ip link / VLAN sub-interfaces
# gettext — даёт envsubst, нужен для рендера frr.cfg.tmpl по env-файлу роли
RUN apk add --no-cache iproute2 gettext

COPY configs/daemons /etc/frr/daemons
# Шаблон + env-файлы ролей (новый путь — PE-1).
COPY configs/frr.cfg.tmpl /etc/frr/role-configs/frr.cfg.tmpl
COPY configs/R1.env /etc/frr/role-configs/R1.env
COPY configs/R2.env /etc/frr/role-configs/R2.env
COPY entrypoint.sh /usr/local/bin/onlinetlabs-entrypoint

RUN chmod +x /usr/local/bin/onlinetlabs-entrypoint && \
    mkdir -p /etc/frr/role-configs

ENTRYPOINT ["/usr/local/bin/onlinetlabs-entrypoint"]

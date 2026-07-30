FROM alpine:3.21

USER root
# iproute2, we bring eth0 up ourselves because GNS3 does not assign an address. gettext gives envsubst for rendering the config.
RUN apk add --no-cache dnsmasq iproute2 gettext

COPY configs/dnsmasq.conf.tmpl /etc/dnsmasq/role-configs/dnsmasq.conf.tmpl
COPY entrypoint.sh /usr/local/bin/onlinetlabs-entrypoint

RUN chmod +x /usr/local/bin/onlinetlabs-entrypoint && \
    mkdir -p /etc/dnsmasq/role-configs

ENTRYPOINT ["/usr/local/bin/onlinetlabs-entrypoint"]

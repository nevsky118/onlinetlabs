# gns3-server: alpine + dynamips + ubridge + vpcs + gns3server.
# Image is intentionally minimal: no IOS images baked in (mounted from host),
# no template registration (handled by gns3-service on startup).
# qemu is NOT installed, because the active labs (lan-static-ip / dhcp-basics /
# inter-subnet-routing) use only VPCS, the built-in ethernet_switch (ubridge) and docker nodes.

FROM alpine:3.21

RUN apk add --no-cache --virtual=build-deps gcc python3-dev musl-dev linux-headers \
 && apk add --no-cache \
      bash python3 curl py3-pip \
      util-linux libcap cpulimit iptables \
      busybox-static \
 && echo "https://dl-cdn.alpinelinux.org/alpine/edge/community" >> /etc/apk/repositories \
 && apk add --no-cache \
      dynamips ubridge vpcs docker-cli \
 && pip install --break-system-packages gns3-server==3.0.6 \
 && apk del --purge build-deps

# Without the switching binaries the image is silently broken (409 "Could not find ..." on seed).
# docker-cli is required too: gns3server shells out to `docker exec` in _fix_permissions()
# before stopping a docker node, and without it every stop fails and is swallowed as 204.
# We catch that at build time, not at runtime.
RUN for bin in dynamips ubridge vpcs docker; do \
      command -v "$bin" >/dev/null || { echo "FATAL: $bin is missing from the image"; exit 1; }; \
    done

# Modern Docker daemons (29+) require API client >= 1.40. Upstream gns3server
# 3.0.2 hardcodes /v1.24/ on the /version probe and DOCKER_MINIMUM_API_VERSION
# 1.25 elsewhere, which is rejected with "client version 1.24 is too old".
# Patch both to 1.40.
RUN sed -i 's|http://docker/v1.24/|http://docker/v1.40/|g; s|DOCKER_MINIMUM_API_VERSION = "1.25"|DOCKER_MINIMUM_API_VERSION = "1.40"|g; s|DOCKER_PREFERRED_API_VERSION = "1.30"|DOCKER_PREFERRED_API_VERSION = "1.40"|g' \
  /usr/lib/python3.12/site-packages/gns3server/compute/docker/__init__.py

COPY start.sh /start.sh
COPY config.ini /config.ini
COPY patch_bind.py /patch_bind.py

# The web-ui bundle (gns3-server 3.0.6) does not contain auth-relay.html, so a
# deep link to a student's project leads to the login form, which requires typing
# the temporary credentials by hand. We put our own relay page next to index.html,
# it fills the login/password into the login form and takes the student straight
# to the project returnUrl.
COPY auth-relay.html /usr/lib/python3.12/site-packages/gns3server/static/web-ui/auth-relay.html

# gns3server passes container-local paths in HostConfig.Mounts.Source. The host
# Docker daemon only understands host paths, so we translate via env-driven
# prefix rewrite (see GNS3_BIND_PATH_TRANSLATION in docker-compose).
RUN python3 /patch_bind.py

RUN chmod +x /start.sh

WORKDIR /data
VOLUME ["/data"]
EXPOSE 3080
CMD ["/start.sh"]

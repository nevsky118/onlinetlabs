# gns3-server: alpine + dynamips + ubridge + vpcs + gns3server.
# Image is intentionally minimal: no IOS images baked in (mounted from host),
# no template registration (handled by gns3-service on startup).
# qemu НЕ ставим: активные лабы (lan-static-ip / dhcp-basics / inter-subnet-routing)
# используют только VPCS, встроенный ethernet_switch (ubridge) и docker-узлы.

FROM alpine:3.21

RUN apk add --no-cache --virtual=build-deps gcc python3-dev musl-dev linux-headers \
 && apk add --no-cache \
      bash python3 curl py3-pip \
      util-linux libcap cpulimit iptables \
      busybox-static \
 && echo "https://dl-cdn.alpinelinux.org/alpine/edge/community" >> /etc/apk/repositories \
 && apk add --no-cache \
      dynamips ubridge vpcs \
 && pip install --break-system-packages gns3-server==3.0.6 \
 && apk del --purge build-deps

# Без бинарей коммутации образ молча-битый (409 "Could not find ..." на seed).
# Ловим на сборке, а не в рантайме.
RUN for bin in dynamips ubridge vpcs; do \
      command -v "$bin" >/dev/null || { echo "FATAL: $bin отсутствует в образе"; exit 1; }; \
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

# Бандл web-ui (gns3-server 3.0.6) не содержит auth-relay.html: deep-link на
# проект студента ведёт на форму логина, требующую ручного ввода временных
# доступов. Кладём свою страницу-релей рядом с index.html — она подставляет
# логин/пароль в форму логина и ведёт студента сразу к returnUrl проекта.
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

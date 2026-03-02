FROM python:3.14-slim AS vpcs-builder

RUN apt-get update && apt-get install -y --no-install-recommends \
    git gcc make libc6-dev \
    && git clone --depth 1 https://github.com/GNS3/vpcs.git /tmp/vpcs \
    && cd /tmp/vpcs/src && ./mk.sh

FROM python:3.14-slim

RUN pip install --no-cache-dir gns3-server==3.0.6

RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

COPY --from=vpcs-builder /tmp/vpcs/src/vpcs /usr/local/bin/vpcs

EXPOSE 3080

CMD ["gns3server", "--host", "0.0.0.0", "--port", "3080"]

"""Patch gns3server docker_vm.py to translate container bind sources to host paths."""
import os
import sys

PATH = "/usr/lib/python3.12/site-packages/gns3server/compute/docker/docker_vm.py"
with open(PATH) as f:
    src = f.read()

HELPER = '''
import os as _os
def _gns3_translate_bind_source(p):
    """Translate a container-side bind source to a host path.

    gns3-server constructs HostConfig.Mounts.Source from its own filesystem
    view, then asks the host Docker daemon to bind that path. The daemon
    only sees host paths. Env var GNS3_BIND_PATH_TRANSLATION lists pairs
    as 'container_prefix=host_prefix;container_prefix=host_prefix'.
    """
    raw = _os.environ.get("GNS3_BIND_PATH_TRANSLATION", "")
    if not raw:
        return p
    for pair in raw.split(";"):
        if not pair.strip() or "=" not in pair:
            continue
        c, h = pair.split("=", 1)
        c = c.rstrip("/")
        h = h.rstrip("/")
        if p == c or p.startswith(c + "/"):
            return h + p[len(c):]
    return p
'''

if "_gns3_translate_bind_source" not in src:
    src = HELPER + "\n" + src

src = src.replace(
    '"Source": resources_path,',
    '"Source": _gns3_translate_bind_source(resources_path),',
    1,
)
old_inner = (
    '"Source": source,\n'
    '                "Target": "/gns3volumes{}".format(volume)'
)
new_inner = (
    '"Source": _gns3_translate_bind_source(source),\n'
    '                "Target": "/gns3volumes{}".format(volume)'
)
if old_inner in src:
    src = src.replace(old_inner, new_inner, 1)
else:
    print("WARN: inner block not found")

with open(PATH, "w") as f:
    f.write(src)
print("patched OK")

"""Convert a GNS3 .gns3a appliance file → template dict for bootstrap.

Usage:
    python import_appliance.py PATH [--image-filename FILE]

Outputs a Python dict literal (as JSON) to stdout. Pipe or paste into
LAB_TEMPLATES in `gns3-service/src/templates_bootstrap.py`.

Only QEMU appliances are supported (the ones in GNS3 marketplace that we care
about: Cisco IOSv, Cisco IOSvL2, etc.). Dynamips and other types are out of
scope; for them, just write the template dict by hand.
"""

import argparse
import json
import sys
from pathlib import Path


def appliance_to_template(appliance: dict, image_filename: str | None) -> dict:
    """Map a `.gns3a` appliance JSON to a GNS3 v3 template dict."""
    if "qemu" not in appliance:
        raise SystemExit(
            f"Appliance {appliance.get('name')!r} is not a QEMU appliance; "
            "this importer only handles QEMU."
        )

    qemu = appliance["qemu"]
    images = appliance.get("images", [])

    chosen_image: dict | None = None
    if image_filename:
        for img in images:
            if img["filename"] == image_filename:
                chosen_image = img
                break
        if chosen_image is None:
            raise SystemExit(
                f"image {image_filename!r} not found in appliance "
                f"(available: {[i['filename'] for i in images]})"
            )
    elif images:
        chosen_image = images[0]

    template: dict = {
        "name": appliance["name"],
        "template_type": "qemu",
        "compute_id": "local",
        "category": appliance.get("category", "router"),
        "default_name_format": "R{0}",  # caller should override per role
        "port_name_format": appliance.get("port_name_format", "Ethernet{0}"),
        "qemu_path": "/usr/bin/qemu-system-x86_64",
        "adapter_type": qemu.get("adapter_type", "e1000"),
        "adapters": qemu.get("adapters", 4),
        "ram": qemu.get("ram", 512),
        "console_type": qemu.get("console_type", "telnet"),
        "kvm": qemu.get("kvm", "require"),
        "hda_disk_interface": qemu.get("hda_disk_interface", "virtio"),
    }
    if "port_segment_size" in appliance:
        template["port_segment_size"] = appliance["port_segment_size"]
    if chosen_image:
        template["hda_disk_image"] = chosen_image["filename"]

    return template


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("path", type=Path, help="Path to .gns3a file")
    parser.add_argument(
        "--image-filename",
        default=None,
        help="Exact image filename to pick from appliance.images[]",
    )
    args = parser.parse_args()

    appliance = json.loads(args.path.read_text())
    template = appliance_to_template(appliance, args.image_filename)
    json.dump(template, sys.stdout, indent=4)
    print()


if __name__ == "__main__":
    main()

# QEMU images for GNS3

Place Cisco IOSv / IOSvL2 .qcow2 files here. They are bind-mounted into
the gns3-server container at `/data/images/QEMU/`.

GNS3 auto-populates this folder with default disk templates (`empty*.qcow2`,
`OVMF*.fd`). Those are normal — leave them. Only add the Cisco images listed
below.

## Required files for OSPF+VLAN CCNA lab (`ospf-vlan-lab-ccna`)

| File | Source | Size |
|-|-|-|
| `vios-adventerprisek9-m.spa.159-3.m10.qcow2` | Cisco Learning Account | ~57 MB |
| `vios_l2-adventerprisek9-m.ssa.high_iron_20200929.qcow2` | Cisco Learning Account | ~90 MB |

Older versions also accepted — see corresponding `.gns3a` appliance file in
`gns3/appliances/` (or upstream GNS3 marketplace) for the `images[]` array.

## How to obtain

Cisco distributes these for **non-commercial educational use** through:

1. Register a free Cisco Learning Account at
   <https://u.cisco.com/my-learning/my-account>
2. Navigate to Modeling Labs section
3. Download the latest **IOSv** and **IOSvL2** qcow2 images
4. Place the `.qcow2` files directly in this folder (no subdir)

This platform's usage is non-commercial and for education — fits Cisco's
distribution terms. No CML (Cisco Modeling Labs) paid license required.

## Architecture

These images are x86_64. They run only on x86_64 hosts with `/dev/kvm`
accessible to the gns3-server container. On Apple Silicon (ARM64) or other
non-x86 hardware they will not be registered as GNS3 templates — the
bootstrap code in `gns3-service/src/templates_bootstrap.py` checks
image presence via `GET /v3/images?image_type=qemu` and skips the
template registration gracefully.

For production deployment on x86_64 Linux see `docs/deployment/x86-production.md`.

## Git

This folder is `.gitignore`d. Do not commit the qcow2 files (large, and
licensed only for download by the user — not for redistribution).

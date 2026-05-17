# GNS3 Images

Host-side directory bind-mounted into `gns3-server` at `/data/images` (read-only).

Populate with IOS / qemu / vpcs images by hand or via a download script. **Never commit binaries** — `.gitignore` excludes everything except this README.

For Cisco c3745 dynamips templates the file must be named `IOS/c3745-adventerprisek9-mz.124-25d.image` (no `.zip`). Template registration is handled at startup by `gns3-service` (`src/templates_bootstrap.py`).

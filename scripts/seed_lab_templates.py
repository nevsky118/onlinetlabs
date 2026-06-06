"""Заполнение labs.gns3_template_project_id из скриптов сборки шаблонов GNS3.

Идемпотентно. Запуск: python -m scripts.seed_lab_templates
"""

import asyncio
import re
import subprocess
import sys
from pathlib import Path

from sqlalchemy import select

from db.session import async_session
from models.lab import Lab


REPO_ROOT = Path(__file__).resolve().parent.parent
BUILD_SCRIPTS_DIR = REPO_ROOT / "gns3" / "gns3-service" / "scripts"

SEED_PLAN = {
    "lan-static-ip": ("build_lan_static_ip_template.py", "LAN_STATIC_IP_TEMPLATE_PROJECT_ID"),
    "dhcp-basics": ("build_dhcp_template.py", "DHCP_TEMPLATE_PROJECT_ID"),
    "inter-subnet-routing": ("build_inter_subnet_routing_template.py", "INTER_SUBNET_ROUTING_TEMPLATE_PROJECT_ID"),
}


def _run_build_script(script_name: str, env_var: str) -> str:
    script_path = BUILD_SCRIPTS_DIR / script_name
    if not script_path.exists():
        raise FileNotFoundError(f"build script not found: {script_path}")
    result = subprocess.run([sys.executable, str(script_path)], capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"{script_name} exited {result.returncode}: {result.stderr.strip()}")
    match = re.search(rf"^{re.escape(env_var)}=(\S+)\s*$", result.stdout, re.MULTILINE)
    if not match:
        raise RuntimeError(f"{script_name} did not emit {env_var}=<uuid>; stdout:\n{result.stdout}")
    return match.group(1)


async def seed() -> int:
    updated = 0
    async with async_session() as db:
        for slug, (script_name, env_var) in SEED_PLAN.items():
            project_id = _run_build_script(script_name, env_var)
            result = await db.execute(select(Lab).where(Lab.slug == slug))
            lab = result.scalar_one_or_none()
            if lab is None:
                print(f"skip {slug}: no labs row (run sync-content first)")
                continue
            if lab.gns3_template_project_id == project_id:
                print(f"ok   {slug}: already {project_id}")
                continue
            lab.gns3_template_project_id = project_id
            print(f"set  {slug}: gns3_template_project_id={project_id}")
            updated += 1
        await db.commit()
    return updated


async def main() -> None:
    updated = await seed()
    print(f"Seeded {updated} lab template ids")


if __name__ == "__main__":
    asyncio.run(main())

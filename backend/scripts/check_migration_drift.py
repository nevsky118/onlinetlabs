"""Fails when the ORM models and the migration chain disagree."""

import sys
from pathlib import Path

from alembic import command
from alembic.config import Config

_MARKER = "drift-check"


def main() -> int:
    """Autogenerates a revision, reports any operation in it, then removes it."""
    root = Path(__file__).resolve().parent.parent
    versions = root / "migrations" / "versions"
    config = Config(str(root / "alembic.ini"))
    config.set_main_option("script_location", str(root / "migrations"))

    before = set(versions.glob("*.py"))
    try:
        command.revision(config, message=_MARKER, autogenerate=True)
    finally:
        generated = sorted(set(versions.glob("*.py")) - before)

    body = "\n".join(path.read_text() for path in generated)
    for path in generated:
        path.unlink()

    operations = [line.strip() for line in body.splitlines() if line.strip().startswith("op.")]
    if operations:
        print("migration drift detected:")
        for line in operations:
            print("  " + line)
        return 1
    print("no migration drift")
    return 0


if __name__ == "__main__":
    sys.exit(main())

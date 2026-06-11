"""Загрузка YAML-спецификации задания лабы и извлечение ожидаемых значений."""

from pathlib import Path

import yaml


def load_lab_spec(lab_slug: str) -> dict | None:
    """Загружает YAML-спецификацию задания лабы (шаги и ожидаемые значения)."""
    yaml_path = Path(__file__).parent.parent / "validation" / "labs" / f"{lab_slug}.yaml"
    if not yaml_path.exists():
        return None
    return yaml.safe_load(yaml_path.read_text(encoding="utf-8"))


def expected_vpcs_config(spec: dict | None) -> dict[str, dict]:
    """Извлекает из спецификации ожидаемый IP/gateway по узлам VPCS: node_name -> {ip, gateway}."""
    result: dict[str, dict] = {}
    if not spec:
        return result
    for step in spec.get("steps", []):
        for check in step.get("checks", []):
            if check.get("kind") == "vpcs.show_ip":
                node = check.get("node")
                if node:
                    expect = check.get("expect", {})
                    result[node] = {"ip": expect.get("ip"), "gateway": expect.get("gateway")}
    return result

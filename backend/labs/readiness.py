"""Single definition of whether a lab can actually be launched.

Launch, the admin surface and the startup audit all resolve readiness here, so
they cannot drift apart.
"""

from dataclasses import dataclass

from models.catalog import Lab

NO_TEMPLATE_IOSVL2 = "error.lab.iosvl2_missing"
NO_TEMPLATE_FRR = "error.lab.no_template"
NO_TEMPLATE_DEFAULT = "error.lab.no_template_project"

_GNS3 = "gns3"


def template_column_for(lab: Lab) -> tuple[str, str]:
    """Return the template column a lab launches from, and the code raised when it is empty."""
    if lab.slug.endswith("-ccna"):
        return "gns3_template_project_id_iosvl2", NO_TEMPLATE_IOSVL2
    if lab.slug.endswith("-frr"):
        return "gns3_template_project_id_frr", NO_TEMPLATE_FRR
    return "gns3_template_project_id", NO_TEMPLATE_DEFAULT


def resolve_template_id(lab: Lab) -> tuple[str | None, str | None]:
    """Return (template_project_id, blocker_code). Exactly one of them is set."""
    column, code = template_column_for(lab)
    template_id = getattr(lab, column, None)
    if not template_id:
        return None, code
    return template_id, None


def launch_blocker(lab: Lab) -> str | None:
    """i18n code explaining why the lab cannot launch, or None when it can."""
    if lab.environment_type != _GNS3:
        return None
    _, code = resolve_template_id(lab)
    return code


def is_launchable(lab: Lab) -> bool:
    """True when a launch request for this lab would get past template resolution."""
    return launch_blocker(lab) is None


@dataclass(frozen=True)
class LabProblem:
    """One misconfiguration found by the audit."""

    slug: str
    kind: str
    detail: str


def audit_labs(labs: list[Lab], spec_slugs: set[str]) -> list[LabProblem]:
    """Report every lab whose declarations do not add up.

    `spec_slugs` are the validation specs present on disk.
    """
    problems: list[LabProblem] = []
    lab_slugs = {lab.slug for lab in labs}

    for lab in labs:
        blocker = launch_blocker(lab)
        if blocker and lab.enabled:
            column, _ = template_column_for(lab)
            problems.append(LabProblem(lab.slug, "enabled_but_unlaunchable", f"{column} is empty"))
        elif blocker:
            column, _ = template_column_for(lab)
            problems.append(LabProblem(lab.slug, "no_template", f"{column} is empty"))

        if lab.environment_type == _GNS3 and lab.slug not in spec_slugs:
            problems.append(LabProblem(lab.slug, "spec_missing", "no validation spec on disk"))

    for slug in sorted(spec_slugs - lab_slugs):
        problems.append(LabProblem(slug, "spec_orphan", "validation spec has no lab row"))

    return problems

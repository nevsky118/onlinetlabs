# Test data generators for labs.

from models.lab import Lab


class LabData:
    """Generates a Lab row carrying only the fields readiness looks at."""

    def __init__(self, slug: str, **overrides):
        defaults = {
            "environment_type": "gns3",
            "enabled": True,
            "title_i18n": {"en": slug},
        }
        self.slug = slug
        self.fields = defaults | overrides
        self.lab = Lab(slug=slug, **self.fields)


class LabSetData:
    """Generates a set of labs plus the spec slugs on disk, for audit_labs."""

    def __init__(self):
        self.broken = LabData("dhcp-basics").lab
        self.healthy = LabData("lan-static-ip", gns3_template_project_id="tpl-1").lab
        self.orphan_spec_slug = "ghost-lab"
        self.labs = [self.broken, self.healthy]
        self.spec_slugs = {self.healthy.slug, self.broken.slug, self.orphan_spec_slug}

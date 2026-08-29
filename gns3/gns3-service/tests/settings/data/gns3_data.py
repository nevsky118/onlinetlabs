"""Test data generators for the GNS3 REST payloads the service proxies."""


class Gns3NodeData:
    """Generates the JSON structure of a GNS3 API node."""

    def __init__(self, **overrides):
        defaults = {
            "node_id": "node-1",
            "project_id": "project-1",
            "name": "R1",
            "node_type": "docker",
            "status": "started",
            "console": 5000,
            "console_type": "telnet",
            "console_host": "127.0.0.1",
            "compute_id": "local",
            "properties": {"container_id": "container-xyz"},
            "ports": [{"name": "eth0", "port_number": 0, "adapter_number": 0}],
        }
        self.data = defaults | overrides


class Gns3LinkData:
    """Generates the JSON structure of a GNS3 API link."""

    def __init__(self, **overrides):
        defaults = {
            "link_id": "link-1",
            "project_id": "project-1",
            "nodes": [
                {"node_id": "node-1", "adapter_number": 0, "port_number": 0},
                {"node_id": "node-2", "adapter_number": 0, "port_number": 0},
            ],
            "link_type": "ethernet",
            "capturing": False,
            "filters": {},
        }
        self.data = defaults | overrides


class Gns3ProjectData:
    """Generates the JSON structure of a GNS3 API project."""

    def __init__(self, **overrides):
        defaults = {
            "project_id": "project-1",
            "name": "test-project",
            "status": "opened",
            "path": "/tmp/projects/project-1",
            "auto_close": False,
            "auto_open": False,
            "auto_start": False,
        }
        self.data = defaults | overrides


class Gns3UserData:
    """Generates the JSON structure of a GNS3 API user."""

    def __init__(self, **overrides):
        defaults = {
            "user_id": "user-1",
            "username": "student-1",
            "email": "student-1@example.com",
            "full_name": "Student One",
            "is_active": True,
            "is_superadmin": False,
        }
        self.data = defaults | overrides

"""Environment seeding for the gns3-service unit tests.

Test data lives in tests/settings/data.
"""

import os

# Seed env before any import of src.config. Settings are lazy, but as soon as
# the router tests reach settings.security.internal_api_token, the full model
# gets loaded. The defaults must not conflict with real .env variables.
os.environ.setdefault("GNS3_URL", "http://gns3:3080")
os.environ.setdefault("GNS3_ADMIN_USER", "admin")
os.environ.setdefault("GNS3_ADMIN_PASSWORD", "admin")
os.environ.setdefault("DB_USER", "test")
os.environ.setdefault("DB_PASSWORD", "test")
os.environ.setdefault("DB_HOST", "localhost")
os.environ.setdefault("DB_PORT", "5432")
os.environ.setdefault("DB_NAME", "test")
os.environ.setdefault("REDIS_URL", "redis://localhost:6379/0")
os.environ.setdefault("INTERNAL_API_TOKEN", "test-internal-token")

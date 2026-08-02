"""Shared observability: structured logging, request-id middleware, Sentry.

Service-specific metrics stay in each service: the metric sets are different
domains and nothing is gained by merging them.
"""

from mcp_sdk.observability.logging import configure_logging
from mcp_sdk.observability.request_id import RequestIDMiddleware
from mcp_sdk.observability.sentry import configure_sentry

__all__ = ["RequestIDMiddleware", "configure_logging", "configure_sentry"]

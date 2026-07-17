"""Sentry initialization for FastAPI. Sample rate 10 percent in prod, 100 in dev."""

import os

import sentry_sdk
from sentry_sdk.integrations.fastapi import FastApiIntegration
from sentry_sdk.integrations.starlette import StarletteIntegration


def configure_sentry(service: str, environment: str = "dev") -> None:
    """Initializes Sentry if SENTRY_DSN is set. Silently exits without a DSN."""
    dsn = os.getenv("SENTRY_DSN")
    if not dsn:
        return
    sample = 1.0 if environment == "dev" else 0.1
    sentry_sdk.init(
        dsn=dsn,
        environment=environment,
        traces_sample_rate=sample,
        send_default_pii=False,
        integrations=[FastApiIntegration(), StarletteIntegration()],
        release=os.getenv("RELEASE_SHA", "dev"),
    )
    sentry_sdk.set_tag("service", service)

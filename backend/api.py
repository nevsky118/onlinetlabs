"""The only place a router is mounted. Each router carries its own prefix and tags.

Include order is the match order: Starlette resolves paths in registration
order, so a literal route must be included before a router that could swallow
it with a path parameter.
"""

from fastapi import FastAPI

from admin.router import router as admin_router
from auth.router import router as auth_router
from chat.router import router as chat_router
from consent.router import router as consent_router
from courses import router as courses_router
from experiment.router import router as experiment_router
from instructor.router import router as instructor_router
from labs.router import internal_router as labs_internal_router
from labs.router import router as labs_router
from observability.router import router as health_router
from progress.router import router as progress_router
from sessions.router import router as sessions_router
from sessions.router import ws_router
from sessions.routers.escalation import router as escalation_router
from sessions.routers.queries import agent_activity_router
from sessions.routers.ticket import router as gns3_ticket_router
from telemetry import router as analytics_router
from users.router import router as users_router
from validation.router import router as validation_router
from validation.runs_router import router as validation_runs_router


def register(app: FastAPI) -> None:
    """Mounts every router on the application."""
    for router in (
        health_router,
        admin_router,
        analytics_router,
        auth_router,
        consent_router,
        users_router,
        courses_router,
        labs_router,
        labs_internal_router,
        progress_router,
        instructor_router,
        sessions_router,
        ws_router,
        escalation_router,
        experiment_router,
        gns3_ticket_router,
        validation_router,
        validation_runs_router,
        agent_activity_router,
        chat_router,
    ):
        app.include_router(router)

from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from auth.router import router as auth_router
from config import settings
from courses.router import router as courses_router
from db.session import get_db
from experiment.router import router as experiment_router
from labs.router import router as labs_router
from progress.router import router as progress_router
from sessions.router import router as sessions_router

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.api.frontend_url],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router, prefix="/auth", tags=["auth"])
app.include_router(courses_router, prefix="/courses", tags=["courses"])
app.include_router(labs_router, prefix="/labs", tags=["labs"])
app.include_router(progress_router, prefix="/users/me/progress", tags=["progress"])
app.include_router(sessions_router, prefix="/users/me/sessions", tags=["sessions"])
app.include_router(experiment_router, prefix="/experiment", tags=["experiment"])


@app.get("/")
def root():
    return {"message": "Hello World"}


@app.get("/health")
async def health(db: AsyncSession = Depends(get_db)):
    await db.execute(text("SELECT 1"))
    return {"status": "ok", "db": "connected"}

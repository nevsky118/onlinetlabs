# REST-эндпоинты для CRUD GNS3-проектов (прокси к admin-клиенту).

from fastapi import APIRouter, Depends

from src.models import ProjectCreate, ProjectResponse

from ._deps import get_admin_client

router = APIRouter()


@router.post(
    "/projects",
    status_code=201,
    response_model=ProjectResponse,
    tags=["projects"],
    summary="Создать проект в GNS3",
)
async def create_project(body: ProjectCreate, admin_client=Depends(get_admin_client)):
    result = await admin_client.create_project(body.name)
    return ProjectResponse(project_id=result["project_id"], name=result["name"])


@router.get(
    "/projects",
    response_model=list[ProjectResponse],
    tags=["projects"],
    summary="Список проектов GNS3",
)
async def list_projects(admin_client=Depends(get_admin_client)):
    projects = await admin_client.list_projects()
    return [ProjectResponse(project_id=p["project_id"], name=p["name"]) for p in projects]


@router.delete(
    "/projects/{project_id}",
    status_code=204,
    tags=["projects"],
    summary="Удалить проект GNS3",
)
async def delete_project(project_id: str, admin_client=Depends(get_admin_client)):
    await admin_client.delete_project(project_id)

from fastapi import APIRouter, HTTPException
from sqlalchemy import select

from ..database import async_session
from ..models import Project, Workspace
from ..schemas.project import ProjectCreate, ProjectResponse

router = APIRouter(tags=["projects"])


async def _ensure_default_workspace() -> Workspace:
    async with async_session() as session:
        result = await session.execute(select(Workspace).limit(1))
        ws = result.scalar_one_or_none()
        if ws:
            return ws
        ws = Workspace(name="default")
        session.add(ws)
        await session.commit()
        await session.refresh(ws)
        return ws


async def get_or_create_project(name: str) -> Project:
    async with async_session() as session:
        result = await session.execute(select(Project).where(Project.name == name))
        project = result.scalar_one_or_none()
        if project:
            return project
        ws = await _ensure_default_workspace()
        project = Project(name=name, workspace_id=ws.id)
        session.add(project)
        await session.commit()
        await session.refresh(project)
        return project


@router.get("/projects", response_model=list[ProjectResponse])
async def list_projects():
    async with async_session() as session:
        result = await session.execute(select(Project).order_by(Project.created_at.desc()))
        return result.scalars().all()


@router.post("/projects", response_model=ProjectResponse, status_code=201)
async def create_project(data: ProjectCreate):
    ws = await _ensure_default_workspace()
    async with async_session() as session:
        project = Project(name=data.name, description=data.description, workspace_id=ws.id)
        session.add(project)
        await session.commit()
        await session.refresh(project)
        return project

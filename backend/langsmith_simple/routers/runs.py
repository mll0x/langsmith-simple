from datetime import datetime, timezone
from uuid import UUID

from typing import Annotated

from fastapi import APIRouter, HTTPException, Query
from sqlalchemy import select, func as sa_func

from ..database import async_session
from ..models import Run, Project
from ..redis_client import publish_run_event
from ..schemas.run import RunCreate, RunUpdate, RunResponse, RunBatch, RunListResponse
from ..routers.projects import get_or_create_project

router = APIRouter(tags=["runs"])


@router.post("/runs", status_code=201)
async def create_run(data: RunCreate):
    project = await get_or_create_project(data.project_name)
    async with async_session() as session:
        run = Run(
            id=data.id,
            name=data.name,
            run_type=data.run_type,
            parent_run_id=data.parent_run_id,
            project_id=project.id,
            status=data.status,
            inputs=data.inputs,
            outputs=data.outputs,
            error=data.error,
            serialized=data.serialized,
            events=data.events,
            extra=data.extra,
            start_time=data.start_time or datetime.now(timezone.utc),
            end_time=data.end_time,
            prompt_tokens=data.prompt_tokens,
            completion_tokens=data.completion_tokens,
            total_tokens=data.total_tokens,
        )
        session.add(run)
        await session.commit()

    await publish_run_event(
        project.name,
        {"type": "run_created", "run_id": str(data.id), "status": data.status},
    )
    return {"id": str(data.id)}


@router.patch("/runs/{run_id}")
async def update_run(run_id: UUID, data: RunUpdate):
    async with async_session() as session:
        result = await session.execute(select(Run).where(Run.id == run_id))
        run = result.scalar_one_or_none()
        if not run:
            raise HTTPException(404, "Run not found")

        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(run, field, value)

        if data.status and data.status != "running":
            run.end_time = data.end_time or datetime.now(timezone.utc)

        run.modified_at = datetime.now(timezone.utc)
        await session.commit()
        project_name = run.project.name if run.project else "default"

    await publish_run_event(
        project_name,
        {"type": "run_updated", "run_id": str(run_id), "status": data.status or run.status},
    )
    return {"id": str(run_id)}


@router.post("/runs/batch")
async def batch_runs(data: RunBatch):
    created_ids: list[str] = []
    async with async_session() as session:
        for run_data in data.post:
            project = await get_or_create_project(run_data.project_name)
            run = Run(
                id=run_data.id,
                name=run_data.name,
                run_type=run_data.run_type,
                parent_run_id=run_data.parent_run_id,
                project_id=project.id,
                status=run_data.status,
                inputs=run_data.inputs,
                outputs=run_data.outputs,
                error=run_data.error,
                start_time=run_data.start_time or datetime.now(timezone.utc),
                end_time=run_data.end_time,
                prompt_tokens=run_data.prompt_tokens,
                completion_tokens=run_data.completion_tokens,
                total_tokens=run_data.total_tokens,
            )
            session.add(run)
            created_ids.append(str(run_data.id))

        for patch_data in data.patch:
            run_id = patch_data.pop("id", None)
            if not run_id:
                continue
            result = await session.execute(select(Run).where(Run.id == run_id))
            run = result.scalar_one_or_none()
            if run:
                for field, value in patch_data.items():
                    setattr(run, field, value)
                run.modified_at = datetime.now(timezone.utc)

        await session.commit()

    # Publish simple events for batch (project name not easily available here without extra queries)
    for rid in created_ids:
        await publish_run_event("default", {"type": "run_created", "run_id": rid})
    return {"ok": True}


@router.get("/runs", response_model=RunListResponse)
async def list_runs(
    project_name: str | None = None,
    status: str | None = None,
    run_type: str | None = None,
    name_contains: str | None = None,
    min_total_tokens: int | None = None,
    max_total_tokens: int | None = None,
    limit: Annotated[int, Query(le=1000)] = 100,
    offset: int = 0,
):
    async with async_session() as session:
        query = select(Run).where(Run.parent_run_id.is_(None))
        count_query = select(sa_func.count()).select_from(Run).where(Run.parent_run_id.is_(None))

        if project_name:
            sub = select(Project.id).where(Project.name == project_name)
            query = query.where(Run.project_id.in_(sub))
            count_query = count_query.where(Run.project_id.in_(sub))
        if status:
            query = query.where(Run.status == status)
            count_query = count_query.where(Run.status == status)
        if run_type:
            query = query.where(Run.run_type == run_type)
            count_query = count_query.where(Run.run_type == run_type)
        if name_contains:
            query = query.where(Run.name.ilike(f"%{name_contains}%"))
            count_query = count_query.where(Run.name.ilike(f"%{name_contains}%"))
        if min_total_tokens is not None:
            query = query.where(Run.total_tokens >= min_total_tokens)
            count_query = count_query.where(Run.total_tokens >= min_total_tokens)
        if max_total_tokens is not None:
            query = query.where(Run.total_tokens <= max_total_tokens)
            count_query = count_query.where(Run.total_tokens <= max_total_tokens)

        total_result = await session.execute(count_query)
        total = total_result.scalar() or 0

        query = query.order_by(Run.start_time.desc()).limit(limit).offset(offset)
        result = await session.execute(query)
        runs = result.scalars().all()

        return RunListResponse(runs=runs, total=total)


@router.get("/runs/{run_id}", response_model=RunResponse)
async def get_run(run_id: UUID):
    async with async_session() as session:
        result = await session.execute(select(Run).where(Run.id == run_id))
        run = result.scalar_one_or_none()
        if not run:
            raise HTTPException(404, "Run not found")

        children_result = await session.execute(
            select(Run).where(Run.parent_run_id == run_id).order_by(Run.start_time)
        )
        child_runs = children_result.scalars().all()

        run_dict = {
            "id": run.id,
            "name": run.name,
            "run_type": run.run_type,
            "parent_run_id": run.parent_run_id,
            "project_id": run.project_id,
            "status": run.status,
            "inputs": run.inputs,
            "outputs": run.outputs,
            "error": run.error,
            "extra": run.extra,
            "prompt_tokens": run.prompt_tokens,
            "completion_tokens": run.completion_tokens,
            "total_tokens": run.total_tokens,
            "prompt_cost": run.prompt_cost,
            "completion_cost": run.completion_cost,
            "first_token_at": run.first_token_at,
            "start_time": run.start_time,
            "end_time": run.end_time,
            "child_runs": [
                {
                    "id": c.id, "name": c.name, "run_type": c.run_type,
                    "parent_run_id": c.parent_run_id, "project_id": c.project_id,
                    "status": c.status, "inputs": c.inputs, "outputs": c.outputs,
                    "error": c.error, "extra": c.extra,
                    "prompt_tokens": c.prompt_tokens, "completion_tokens": c.completion_tokens,
                    "total_tokens": c.total_tokens,
                    "prompt_cost": c.prompt_cost, "completion_cost": c.completion_cost,
                    "first_token_at": c.first_token_at,
                    "start_time": c.start_time, "end_time": c.end_time,
                    "child_runs": [],
                }
                for c in child_runs
            ],
        }
        return RunResponse.model_validate(run_dict)


@router.delete("/runs/{run_id}", status_code=204)
async def delete_run(run_id: UUID):
    async with async_session() as session:
        result = await session.execute(select(Run).where(Run.id == run_id))
        run = result.scalar_one_or_none()
        if not run:
            raise HTTPException(404, "Run not found")
        await session.delete(run)
        await session.commit()

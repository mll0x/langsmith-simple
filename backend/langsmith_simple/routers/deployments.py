from uuid import UUID

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import StreamingResponse

from ..schemas.deployment import DeploymentCreate, DeploymentResponse, DeploymentUpdate
from ..services.deployment_service import (
    list_deployments,
    get_deployment,
    create_deployment,
    update_deployment,
    delete_deployment,
    start_deployment,
    stop_deployment,
    get_deployment_logs,
    stream_deployment_logs,
)

router = APIRouter(tags=["deployments"])


@router.get("/deployments", response_model=list[DeploymentResponse])
async def read_deployments():
    return await list_deployments()


@router.post("/deployments", response_model=DeploymentResponse, status_code=201)
async def create(data: DeploymentCreate):
    return await create_deployment(data)


@router.get("/deployments/{deployment_id}", response_model=DeploymentResponse)
async def read(deployment_id: UUID):
    deployment = await get_deployment(deployment_id)
    if not deployment:
        raise HTTPException(404, "Deployment not found")
    return deployment


@router.patch("/deployments/{deployment_id}", response_model=DeploymentResponse)
async def update(deployment_id: UUID, data: DeploymentUpdate):
    deployment = await update_deployment(deployment_id, data)
    if not deployment:
        raise HTTPException(404, "Deployment not found")
    return deployment


@router.delete("/deployments/{deployment_id}", status_code=204)
async def delete(deployment_id: UUID):
    ok = await delete_deployment(deployment_id)
    if not ok:
        raise HTTPException(404, "Deployment not found")


@router.post("/deployments/{deployment_id}/start", response_model=DeploymentResponse)
async def start(deployment_id: UUID):
    deployment = await start_deployment(deployment_id)
    if not deployment:
        raise HTTPException(404, "Deployment not found")
    return deployment


@router.post("/deployments/{deployment_id}/stop", response_model=DeploymentResponse)
async def stop(deployment_id: UUID):
    deployment = await stop_deployment(deployment_id)
    if not deployment:
        raise HTTPException(404, "Deployment not found")
    return deployment


@router.get("/deployments/{deployment_id}/logs")
async def logs(deployment_id: UUID, tail: int = Query(default=100, ge=1)):
    text = get_deployment_logs(deployment_id)
    lines = text.splitlines()
    return {"lines": lines[-tail:]}


@router.get("/deployments/{deployment_id}/logs/stream")
async def stream_logs(deployment_id: UUID):
    async def event_generator():
        async for chunk in stream_deployment_logs(deployment_id):
            yield chunk

    return StreamingResponse(event_generator(), media_type="text/event-stream")

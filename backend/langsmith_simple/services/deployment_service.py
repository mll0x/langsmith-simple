import asyncio
from uuid import UUID

from sqlalchemy import select

from ..database import async_session
from ..deployment.local_manager import LocalDeploymentManager
from ..models.deployment import Deployment
from ..schemas.deployment import DeploymentCreate, DeploymentUpdate

_manager = LocalDeploymentManager()


async def list_deployments() -> list[Deployment]:
    async with async_session() as session:
        result = await session.execute(select(Deployment).order_by(Deployment.created_at.desc()))
        return result.scalars().all()


async def get_deployment(deployment_id: UUID) -> Deployment | None:
    async with async_session() as session:
        result = await session.execute(select(Deployment).where(Deployment.id == deployment_id))
        return result.scalar_one_or_none()


async def create_deployment(data: DeploymentCreate) -> Deployment:
    async with async_session() as session:
        deployment = Deployment(
            name=data.name,
            config_path=data.config_path,
            source_type=data.source_type,
            env_vars=data.env_vars or {},
            status="created",
            command=data.command,
        )
        session.add(deployment)
        await session.commit()
        await session.refresh(deployment)
        return deployment


async def update_deployment(deployment_id: UUID, data: DeploymentUpdate) -> Deployment | None:
    async with async_session() as session:
        result = await session.execute(select(Deployment).where(Deployment.id == deployment_id))
        deployment = result.scalar_one_or_none()
        if not deployment:
            return None
        if data.env_vars is not None:
            deployment.env_vars = data.env_vars
        if data.status is not None:
            deployment.status = data.status
        await session.commit()
        await session.refresh(deployment)
        return deployment


async def delete_deployment(deployment_id: UUID) -> bool:
    async with async_session() as session:
        result = await session.execute(select(Deployment).where(Deployment.id == deployment_id))
        deployment = result.scalar_one_or_none()
        if not deployment:
            return False
        if deployment.status == "running" and deployment.pid:
            _manager.stop(deployment)
        await session.delete(deployment)
        await session.commit()
        return True


async def start_deployment(deployment_id: UUID) -> Deployment | None:
    async with async_session() as session:
        result = await session.execute(select(Deployment).where(Deployment.id == deployment_id))
        deployment = result.scalar_one_or_none()
        if not deployment:
            return None
        if deployment.status == "running":
            return deployment
        _manager.start(deployment)
        await session.commit()
        await session.refresh(deployment)
        return deployment


async def stop_deployment(deployment_id: UUID) -> Deployment | None:
    async with async_session() as session:
        result = await session.execute(select(Deployment).where(Deployment.id == deployment_id))
        deployment = result.scalar_one_or_none()
        if not deployment:
            return None
        _manager.stop(deployment)
        await session.commit()
        await session.refresh(deployment)
        return deployment


def get_deployment_logs(deployment_id: UUID) -> str:
    return _manager.get_logs(deployment_id)


async def stream_deployment_logs(deployment_id: UUID):
    from ..deployment.local_manager import _logs_dir

    log_file = _logs_dir() / f"{deployment_id}.log"
    if not log_file.exists():
        yield f"data: {''}\n\n"
        return

    with open(log_file, "r") as f:
        f.seek(0, 2)
        pos = f.tell()

        while True:
            f.seek(pos)
            line = f.readline()
            if line:
                yield f"data: {line}\n\n"
                pos = f.tell()
            else:
                await asyncio.sleep(1)

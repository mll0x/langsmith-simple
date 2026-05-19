from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class DeploymentCreate(BaseModel):
    name: str
    config_path: str
    source_type: str = "local"
    env_vars: dict | None = None
    command: str | None = None


class DeploymentUpdate(BaseModel):
    env_vars: dict | None = None
    status: str | None = None


class DeploymentResponse(BaseModel):
    id: UUID
    name: str
    config_path: str
    source_type: str
    env_vars: dict | None = None
    status: str
    container_url: str | None = None
    port: int | None = None
    pid: int | None = None
    command: str | None = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}

from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, Field


class RunCreate(BaseModel):
    id: UUID
    name: str
    run_type: str
    parent_run_id: UUID | None = None
    project_name: str = "default"
    inputs: dict | None = None
    outputs: dict | None = None
    error: str | None = None
    serialized: dict | None = None
    events: list | None = None
    extra: dict | None = None
    start_time: datetime | None = None
    end_time: datetime | None = None
    status: str = "running"
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0


class RunUpdate(BaseModel):
    outputs: dict | None = None
    error: str | None = None
    status: str | None = None
    end_time: datetime | None = None
    prompt_tokens: int | None = None
    completion_tokens: int | None = None
    total_tokens: int | None = None


class RunResponse(BaseModel):
    id: UUID
    name: str
    run_type: str
    parent_run_id: UUID | None = None
    project_id: UUID
    status: str
    inputs: dict | None = None
    outputs: dict | None = None
    error: str | None = None
    extra: dict | None = None
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0
    prompt_cost: Decimal = Decimal("0")
    completion_cost: Decimal = Decimal("0")
    first_token_at: datetime | None = None
    start_time: datetime
    end_time: datetime | None = None
    child_runs: list["RunResponse"] = Field(default_factory=list)

    model_config = {"from_attributes": True}


class RunBatch(BaseModel):
    post: list[RunCreate] = Field(default_factory=list)
    patch: list[dict] = Field(default_factory=list)


class RunListItem(BaseModel):
    id: UUID
    name: str
    run_type: str
    parent_run_id: UUID | None = None
    project_id: UUID
    status: str
    inputs: dict | None = None
    outputs: dict | None = None
    error: str | None = None
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0
    prompt_cost: Decimal = Decimal("0")
    completion_cost: Decimal = Decimal("0")
    start_time: datetime
    end_time: datetime | None = None

    model_config = {"from_attributes": True}


class RunListResponse(BaseModel):
    runs: list[RunListItem]
    total: int

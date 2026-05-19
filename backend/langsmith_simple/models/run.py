import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import ForeignKey, Integer, Numeric, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB, TIMESTAMP
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..database import Base


class Run(Base):
    __tablename__ = "runs"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(255))
    run_type: Mapped[str] = mapped_column(String(50))
    parent_run_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("runs.id", ondelete="CASCADE"), index=True)
    project_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("projects.id", ondelete="CASCADE"), index=True)
    status: Mapped[str] = mapped_column(String(20), default="running", index=True)

    inputs: Mapped[dict | None] = mapped_column(JSONB)
    outputs: Mapped[dict | None] = mapped_column(JSONB)
    error: Mapped[str | None] = mapped_column(Text)
    serialized: Mapped[dict | None] = mapped_column(JSONB)
    events: Mapped[list | None] = mapped_column(JSONB)
    extra: Mapped[dict | None] = mapped_column(JSONB)

    prompt_tokens: Mapped[int] = mapped_column(Integer, default=0)
    completion_tokens: Mapped[int] = mapped_column(Integer, default=0)
    total_tokens: Mapped[int] = mapped_column(Integer, default=0)
    prompt_cost: Mapped[Decimal] = mapped_column(Numeric(10, 6), default=Decimal("0"))
    completion_cost: Mapped[Decimal] = mapped_column(Numeric(10, 6), default=Decimal("0"))

    first_token_at: Mapped[datetime | None] = mapped_column(TIMESTAMP(timezone=True))
    start_time: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), server_default=func.now())
    end_time: Mapped[datetime | None] = mapped_column(TIMESTAMP(timezone=True))
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), server_default=func.now())
    modified_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now())

    project: Mapped["Project"] = relationship(back_populates="runs")
    parent_run: Mapped["Run | None"] = relationship(remote_side=[id], foreign_keys=[parent_run_id])
    child_runs: Mapped[list["Run"]] = relationship(
        back_populates="parent_run",
        foreign_keys=[parent_run_id],
        order_by="Run.start_time",
    )
    feedbacks: Mapped[list["Feedback"]] = relationship(back_populates="run", order_by="Feedback.created_at.desc()")

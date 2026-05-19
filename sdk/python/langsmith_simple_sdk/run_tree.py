import uuid
from datetime import datetime, timezone
from typing import Any

from .client import Client


class RunTree:
    def __init__(
        self,
        name: str,
        run_type: str = "chain",
        inputs: dict | None = None,
        parent: "RunTree | None" = None,
        project_name: str = "default",
        client: Client | None = None,
        id: uuid.UUID | str | None = None,
        **extra: Any,
    ):
        self.id = str(id or uuid.uuid4())
        self.name = name
        self.run_type = run_type
        self.inputs = inputs or {}
        self.outputs: dict | None = None
        self.error: str | None = None
        self.status = "running"
        self.parent = parent
        self.parent_run_id = parent.id if parent else None
        self.project_name = project_name
        self.children: list[RunTree] = []
        self.start_time = datetime.now(timezone.utc)
        self.end_time: datetime | None = None
        self.prompt_tokens = 0
        self.completion_tokens = 0
        self.total_tokens = 0

        self._client = client or Client()

    def create_child(
        self,
        name: str,
        run_type: str = "llm",
        inputs: dict | None = None,
    ) -> "RunTree":
        child = RunTree(
            name=name,
            run_type=run_type,
            inputs=inputs,
            parent=self,
            project_name=self.project_name,
            client=self._client,
        )
        self.children.append(child)
        child._post_create()
        return child

    def _post_create(self):
        self._client.create_run(
            id=self.id,
            name=self.name,
            run_type=self.run_type,
            inputs=self.inputs,
            parent_run_id=self.parent_run_id,
            project_name=self.project_name,
            status=self.status,
        )

    def end(
        self,
        outputs: dict | None = None,
        error: str | None = None,
        prompt_tokens: int = 0,
        completion_tokens: int = 0,
        total_tokens: int = 0,
    ):
        self.outputs = outputs
        self.error = error
        self.status = "error" if error else "success"
        self.end_time = datetime.now(timezone.utc)
        self.prompt_tokens = prompt_tokens
        self.completion_tokens = completion_tokens
        self.total_tokens = total_tokens

        self._client.update_run(
            run_id=self.id,
            outputs=outputs,
            error=error,
            status=self.status,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total_tokens=total_tokens,
            end_time=self.end_time.isoformat(),
        )

    def __enter__(self):
        self._post_create()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type:
            self.end(error=str(exc_val))
        elif self.status == "running":
            self.end()
        return False

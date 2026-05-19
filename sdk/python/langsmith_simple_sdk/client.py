import os
import uuid
from datetime import datetime, timezone
from typing import Any

import httpx


def _env(key: str, default: str = "") -> str:
    return os.environ.get(key, default)


class Client:
    def __init__(
        self,
        api_url: str | None = None,
        api_key: str | None = None,
    ):
        self.api_url = (api_url or _env("LANGSMITH_ENDPOINT", "http://localhost:8000/api/v1")).rstrip("/")
        self.api_key = api_key or _env("LANGSMITH_API_KEY", "")
        self._http = httpx.Client(
            base_url=self.api_url,
            headers={"X-API-Key": self.api_key} if self.api_key else {},
            timeout=30.0,
        )

    def create_run(
        self,
        name: str,
        run_type: str = "chain",
        inputs: dict | None = None,
        outputs: dict | None = None,
        error: str | None = None,
        parent_run_id: uuid.UUID | str | None = None,
        project_name: str = "default",
        id: uuid.UUID | str | None = None,
        status: str = "running",
        **extra: Any,
    ) -> dict:
        run_id = str(id or uuid.uuid4())
        payload: dict[str, Any] = {
            "id": run_id,
            "name": name,
            "run_type": run_type,
            "parent_run_id": str(parent_run_id) if parent_run_id else None,
            "project_name": project_name,
            "inputs": inputs,
            "outputs": outputs,
            "error": error,
            "status": status,
            "start_time": datetime.now(timezone.utc).isoformat(),
        }
        resp = self._http.post("/runs", json=payload)
        resp.raise_for_status()
        return resp.json()

    def update_run(
        self,
        run_id: uuid.UUID | str,
        outputs: dict | None = None,
        error: str | None = None,
        status: str | None = None,
        prompt_tokens: int | None = None,
        completion_tokens: int | None = None,
        total_tokens: int | None = None,
        end_time: str | None = None,
    ) -> dict:
        payload: dict[str, Any] = {}
        if outputs is not None:
            payload["outputs"] = outputs
        if error is not None:
            payload["error"] = error
        if status is not None:
            payload["status"] = status
        if prompt_tokens is not None:
            payload["prompt_tokens"] = prompt_tokens
        if completion_tokens is not None:
            payload["completion_tokens"] = completion_tokens
        if total_tokens is not None:
            payload["total_tokens"] = total_tokens
        if end_time is not None:
            payload["end_time"] = end_time

        resp = self._http.patch(f"/runs/{run_id}", json=payload)
        resp.raise_for_status()
        return resp.json()

    def batch_runs(
        self,
        post: list[dict] | None = None,
        patch: list[dict] | None = None,
    ) -> dict:
        payload: dict[str, Any] = {}
        if post:
            payload["post"] = post
        if patch:
            payload["patch"] = patch
        resp = self._http.post("/runs/batch", json=payload)
        resp.raise_for_status()
        return resp.json()

    def list_runs(
        self,
        project_name: str | None = None,
        status: str | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> dict:
        params: dict[str, Any] = {"limit": limit, "offset": offset}
        if project_name:
            params["project_name"] = project_name
        if status:
            params["status"] = status
        resp = self._http.get("/runs", params=params)
        resp.raise_for_status()
        return resp.json()

    def get_run(self, run_id: uuid.UUID | str) -> dict:
        resp = self._http.get(f"/runs/{run_id}")
        resp.raise_for_status()
        return resp.json()

    def close(self):
        self._http.close()

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()

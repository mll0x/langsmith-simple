import functools
import json
from typing import Any, Callable

from .run_tree import RunTree


def _safe_serialize(obj: Any) -> Any:
    try:
        return json.loads(json.dumps(obj, default=str))
    except (TypeError, ValueError):
        return str(obj)


def traceable(
    name: str | None = None,
    run_type: str = "chain",
    project_name: str = "default",
):
    def decorator(func: Callable) -> Callable:
        run_name = name or func.__name__

        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            with RunTree(
                name=run_name,
                run_type=run_type,
                inputs={"args": _safe_serialize(args), "kwargs": _safe_serialize(kwargs)},
                project_name=project_name,
            ) as run:
                result = func(*args, **kwargs)
                run.end(outputs={"result": _safe_serialize(result)})
                return result

        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            with RunTree(
                name=run_name,
                run_type=run_type,
                inputs={"args": _safe_serialize(args), "kwargs": _safe_serialize(kwargs)},
                project_name=project_name,
            ) as run:
                result = await func(*args, **kwargs)
                run.end(outputs={"result": _safe_serialize(result)})
                return result

        import asyncio
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        return wrapper

    return decorator

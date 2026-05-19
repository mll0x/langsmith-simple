import uuid
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest


def _make_mock_session():
    session = AsyncMock()
    session.commit = AsyncMock()
    session.add = MagicMock()
    session.delete = AsyncMock()
    session.refresh = AsyncMock()
    return session


@pytest.fixture
def mock_session():
    return _make_mock_session()


@pytest.mark.anyio
async def test_create_run(mock_session):
    from langsmith_simple.routers.runs import create_run
    from langsmith_simple.schemas.run import RunCreate

    run_id = uuid.uuid4()
    data = RunCreate(
        id=run_id,
        name="test-run",
        run_type="chain",
        project_name="default",
    )

    with patch("langsmith_simple.routers.runs.async_session") as mock_factory, \
         patch("langsmith_simple.routers.runs.get_or_create_project") as mock_project, \
         patch("langsmith_simple.routers.runs.publish_run_event") as mock_pub:
        mock_factory.return_value.__aenter__ = AsyncMock(return_value=mock_session)
        mock_factory.return_value.__aexit__ = AsyncMock(return_value=False)
        mock_project.return_value = MagicMock(id=uuid.uuid4(), name="default")

        result = await create_run(data)
        assert result["id"] == str(run_id)
        mock_session.add.assert_called_once()
        mock_session.commit.assert_awaited_once()
        mock_pub.assert_awaited_once()


@pytest.mark.anyio
async def test_update_run(mock_session):
    from langsmith_simple.routers.runs import update_run
    from langsmith_simple.schemas.run import RunUpdate

    run_id = uuid.uuid4()
    data = RunUpdate(status="success", outputs={"answer": 42})

    mock_run = MagicMock()
    mock_run.status = "running"
    mock_run.project = MagicMock(name="default")
    mock_run.modified_at = None

    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = mock_run
    mock_session.execute = AsyncMock(return_value=mock_result)

    with patch("langsmith_simple.routers.runs.async_session") as mock_factory, \
         patch("langsmith_simple.routers.runs.publish_run_event") as mock_pub:
        mock_factory.return_value.__aenter__ = AsyncMock(return_value=mock_session)
        mock_factory.return_value.__aexit__ = AsyncMock(return_value=False)

        result = await update_run(run_id, data)
        assert result["id"] == str(run_id)
        assert mock_run.status == "success"
        mock_session.commit.assert_awaited_once()
        mock_pub.assert_awaited_once()


@pytest.mark.anyio
async def test_list_runs(mock_session):
    from datetime import datetime, timezone
    from decimal import Decimal
    from types import SimpleNamespace
    from langsmith_simple.routers.runs import list_runs

    run_id = uuid.uuid4()
    mock_run = SimpleNamespace(
        id=run_id,
        name="test-run",
        run_type="chain",
        parent_run_id=None,
        project_id=uuid.uuid4(),
        status="success",
        inputs=None,
        outputs=None,
        error=None,
        prompt_tokens=0,
        completion_tokens=0,
        total_tokens=0,
        prompt_cost=Decimal("0"),
        completion_cost=Decimal("0"),
        start_time=datetime.now(timezone.utc),
        end_time=None,
    )

    mock_result1 = MagicMock()
    mock_result1.scalar.return_value = 5

    mock_result2 = MagicMock()
    mock_result2.scalars.return_value.all.return_value = [mock_run]

    mock_session.execute = AsyncMock(side_effect=[mock_result1, mock_result2])

    with patch("langsmith_simple.routers.runs.async_session") as mock_factory:
        mock_factory.return_value.__aenter__ = AsyncMock(return_value=mock_session)
        mock_factory.return_value.__aexit__ = AsyncMock(return_value=False)

        result = await list_runs(project_name="default", status="success")
        assert result.total == 5
        assert len(result.runs) == 1
        assert result.runs[0].id == run_id


@pytest.mark.anyio
async def test_get_run_not_found(mock_session):
    from langsmith_simple.routers.runs import get_run
    from fastapi import HTTPException

    run_id = uuid.uuid4()
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = None
    mock_session.execute = AsyncMock(return_value=mock_result)

    with patch("langsmith_simple.routers.runs.async_session") as mock_factory:
        mock_factory.return_value.__aenter__ = AsyncMock(return_value=mock_session)
        mock_factory.return_value.__aexit__ = AsyncMock(return_value=False)

        with pytest.raises(HTTPException) as exc_info:
            await get_run(run_id)
        assert exc_info.value.status_code == 404

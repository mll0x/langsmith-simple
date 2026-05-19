import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest


@pytest.fixture
def mock_session():
    session = AsyncMock()
    session.commit = AsyncMock()
    session.add = MagicMock()
    session.refresh = AsyncMock()
    return session


@pytest.mark.anyio
async def test_create_deployment():
    from langsmith_simple.routers.deployments import create
    from langsmith_simple.schemas.deployment import DeploymentCreate

    data = DeploymentCreate(name="my-agent", config_path="/tmp/agent")
    mock_dep = MagicMock()
    mock_dep.name = "my-agent"
    mock_dep.config_path = "/tmp/agent"

    with patch(
        "langsmith_simple.routers.deployments.create_deployment",
        return_value=mock_dep,
    ) as mock_svc:
        result = await create(data)
        assert result.name == "my-agent"
        mock_svc.assert_awaited_once_with(data)


@pytest.mark.anyio
async def test_list_deployments():
    from langsmith_simple.routers.deployments import read_deployments

    mock_dep = MagicMock()

    with patch(
        "langsmith_simple.routers.deployments.list_deployments",
        return_value=[mock_dep],
    ) as mock_svc:
        result = await read_deployments()
        assert len(result) == 1
        mock_svc.assert_awaited_once()


@pytest.mark.anyio
async def test_start_deployment():
    from langsmith_simple.routers.deployments import start

    dep_id = uuid.uuid4()
    mock_dep = MagicMock()
    mock_dep.status = "running"
    mock_dep.pid = 12345
    mock_dep.port = 8081

    with patch(
        "langsmith_simple.routers.deployments.start_deployment",
        return_value=mock_dep,
    ) as mock_svc:
        result = await start(dep_id)
        assert result.status == "running"
        assert result.pid == 12345
        mock_svc.assert_awaited_once_with(dep_id)


@pytest.mark.anyio
async def test_stop_deployment():
    from langsmith_simple.routers.deployments import stop

    dep_id = uuid.uuid4()
    mock_dep = MagicMock()
    mock_dep.status = "stopped"
    mock_dep.pid = None

    with patch(
        "langsmith_simple.routers.deployments.stop_deployment",
        return_value=mock_dep,
    ) as mock_svc:
        result = await stop(dep_id)
        assert result.status == "stopped"
        assert result.pid is None
        mock_svc.assert_awaited_once_with(dep_id)


@pytest.mark.anyio
async def test_delete_deployment():
    from langsmith_simple.routers.deployments import delete

    dep_id = uuid.uuid4()

    with patch(
        "langsmith_simple.routers.deployments.delete_deployment",
        return_value=True,
    ) as mock_svc:
        await delete(dep_id)
        mock_svc.assert_awaited_once_with(dep_id)


def test_get_deployment_logs():
    from langsmith_simple.services.deployment_service import get_deployment_logs

    with patch(
        "langsmith_simple.services.deployment_service._manager.get_logs",
        return_value="line1\nline2\nline3",
    ) as mock_logs:
        result = get_deployment_logs(uuid.uuid4())
        assert result == "line1\nline2\nline3"
        mock_logs.assert_called_once()

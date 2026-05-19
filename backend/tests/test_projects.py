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
async def test_list_projects(mock_session):
    from langsmith_simple.routers.projects import list_projects

    mock_project = MagicMock()
    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = [mock_project]
    mock_session.execute = AsyncMock(return_value=mock_result)

    with patch("langsmith_simple.routers.projects.async_session") as mock_factory:
        mock_factory.return_value.__aenter__ = AsyncMock(return_value=mock_session)
        mock_factory.return_value.__aexit__ = AsyncMock(return_value=False)

        result = await list_projects()
        assert len(result) == 1


@pytest.mark.anyio
async def test_create_project(mock_session):
    from langsmith_simple.routers.projects import create_project
    from langsmith_simple.schemas.project import ProjectCreate

    data = ProjectCreate(name="test-project", description="desc")
    mock_ws = MagicMock(id=uuid.uuid4())

    with patch("langsmith_simple.routers.projects.async_session") as mock_factory, \
         patch("langsmith_simple.routers.projects._ensure_default_workspace") as mock_ws_fn:
        mock_factory.return_value.__aenter__ = AsyncMock(return_value=mock_session)
        mock_factory.return_value.__aexit__ = AsyncMock(return_value=False)
        mock_ws_fn.return_value = mock_ws

        result = await create_project(data)
        assert result.name == "test-project"
        mock_session.add.assert_called_once()
        mock_session.commit.assert_awaited_once()

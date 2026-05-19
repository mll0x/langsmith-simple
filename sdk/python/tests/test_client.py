import uuid
from unittest.mock import MagicMock, patch

import pytest

from langsmith_simple_sdk.client import Client


@pytest.fixture
def client():
    return Client(api_url="http://test/api/v1", api_key="test-key")


def test_client_env_vars():
    with patch.dict("os.environ", {"LANGSMITH_ENDPOINT": "http://env/api", "LANGSMITH_API_KEY": "env-key"}):
        c = Client()
        assert c.api_url == "http://env/api"
        assert c.api_key == "env-key"


def test_create_run(client):
    mock_response = MagicMock()
    mock_response.json.return_value = {"id": "run-123"}
    mock_response.raise_for_status = MagicMock()

    with patch.object(client._http, "post", return_value=mock_response) as mock_post:
        result = client.create_run(name="test", run_type="chain")
        assert result["id"] == "run-123"
        mock_post.assert_called_once()
        args, kwargs = mock_post.call_args
        assert args[0] == "/runs"
        assert kwargs["json"]["name"] == "test"


def test_update_run(client):
    mock_response = MagicMock()
    mock_response.json.return_value = {"id": "run-123"}
    mock_response.raise_for_status = MagicMock()

    with patch.object(client._http, "patch", return_value=mock_response) as mock_patch:
        result = client.update_run("run-123", status="success")
        assert result["id"] == "run-123"
        mock_patch.assert_called_once()


def test_batch_runs(client):
    mock_response = MagicMock()
    mock_response.json.return_value = {"ok": True}
    mock_response.raise_for_status = MagicMock()

    with patch.object(client._http, "post", return_value=mock_response) as mock_post:
        result = client.batch_runs(post=[{"id": str(uuid.uuid4()), "name": "r1"}])
        assert result["ok"] is True
        mock_post.assert_called_once()


def test_list_runs(client):
    mock_response = MagicMock()
    mock_response.json.return_value = {"runs": [], "total": 0}
    mock_response.raise_for_status = MagicMock()

    with patch.object(client._http, "get", return_value=mock_response) as mock_get:
        result = client.list_runs(project_name="default")
        assert result["total"] == 0
        mock_get.assert_called_once()


def test_context_manager():
    with patch.object(Client, "close") as mock_close:
        with Client() as c:
            pass
        mock_close.assert_called_once()

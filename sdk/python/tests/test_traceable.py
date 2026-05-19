import asyncio
from unittest.mock import MagicMock, patch

import pytest

from langsmith_simple_sdk.traceable import traceable, _safe_serialize


def test_safe_serialize_dict():
    assert _safe_serialize({"a": 1}) == {"a": 1}


def test_safe_serialize_unserializable():
    class Foo:
        pass
    result = _safe_serialize(Foo())
    assert isinstance(result, str)


def test_traceable_sync():
    mock_run = MagicMock()
    mock_run.end = MagicMock()

    with patch("langsmith_simple_sdk.traceable.RunTree", return_value=mock_run):
        mock_run.__enter__ = MagicMock(return_value=mock_run)
        mock_run.__exit__ = MagicMock(return_value=False)

        @traceable(name="test_fn")
        def my_func(x):
            return x * 2

        result = my_func(3)
        assert result == 6
        mock_run.__enter__.assert_called_once()
        mock_run.end.assert_called_once()


@pytest.mark.anyio
async def test_traceable_async():
    mock_run = MagicMock()
    mock_run.end = MagicMock()

    with patch("langsmith_simple_sdk.traceable.RunTree", return_value=mock_run):
        mock_run.__enter__ = MagicMock(return_value=mock_run)
        mock_run.__exit__ = MagicMock(return_value=False)

        @traceable(name="test_async")
        async def my_async(x):
            return x + 1

        result = await my_async(5)
        assert result == 6
        mock_run.end.assert_called_once()

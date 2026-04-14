"""共享 fixture — 元数据提取器单元测试（Mock HTTP 响应，不依赖真实网络）"""

from typing import Any
from unittest.mock import MagicMock

import pytest


def _make_response(content: bytes, status_code: int, content_type: str) -> MagicMock:
    mock = MagicMock()
    mock.status_code = status_code
    mock.content = content
    mock.text = content.decode("utf-8", errors="replace")
    mock.headers = {"Content-Type": content_type}
    mock.raise_for_status = MagicMock()
    return mock


@pytest.fixture
def mock_html_response():
    """返回一个工厂函数，用于生成 Mock HTML 响应对象。

    用法::

        def test_xxx(mock_html_response):
            resp = mock_html_response("<html>...</html>")
    """

    def factory(html_content: str, status_code: int = 200) -> MagicMock:
        return _make_response(
            html_content.encode("utf-8"),
            status_code,
            "text/html; charset=utf-8",
        )

    return factory


@pytest.fixture
def mock_json_response():
    """返回一个工厂函数，用于生成 Mock JSON 响应对象。

    用法::

        def test_xxx(mock_json_response):
            resp = mock_json_response({"key": "value"})
    """
    import json

    def factory(data: Any, status_code: int = 200) -> MagicMock:
        body = json.dumps(data, ensure_ascii=False).encode("utf-8")
        mock = _make_response(body, status_code, "application/json; charset=utf-8")
        mock.json = MagicMock(return_value=data)
        return mock

    return factory

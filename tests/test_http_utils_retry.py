"""HttpUtils.fetch 重试与 should_retry 短路行为单测。"""

from unittest.mock import MagicMock, patch

import pytest
import requests

from pavone.config.configs import DownloadConfig, ProxyConfig
from pavone.utils.http_utils import HttpUtils, skip_retry_on_4xx


def _make_resp(status: int) -> requests.Response:
    resp = requests.Response()
    resp.status_code = status
    resp.url = "https://example.com/x"
    return resp


def _download_cfg() -> DownloadConfig:
    cfg = DownloadConfig()
    cfg.retry_times = 3
    cfg.retry_interval = 1  # ms，避免单测真等
    return cfg


@patch("pavone.utils.http_utils.requests.get")
def test_fetch_4xx_retries_by_default(mock_get: MagicMock) -> None:
    """没传 should_retry 时，4xx 仍按 max_retry 重试（保持向后兼容）。"""
    resp = _make_resp(404)
    err = requests.HTTPError("404 Client Error", response=resp)
    mock_get.return_value = MagicMock(raise_for_status=MagicMock(side_effect=err))

    with pytest.raises(requests.RequestException):
        HttpUtils.fetch(_download_cfg(), ProxyConfig(), "https://example.com/x", max_retry=3)

    assert mock_get.call_count == 3


@patch("pavone.utils.http_utils.requests.get")
def test_fetch_4xx_with_skip_callback_does_not_retry(mock_get: MagicMock) -> None:
    """传入 skip_retry_on_4xx 时，4xx 应立即放弃，不再重试。"""
    resp = _make_resp(404)
    err = requests.HTTPError("404 Client Error", response=resp)
    mock_get.return_value = MagicMock(raise_for_status=MagicMock(side_effect=err))

    with pytest.raises(requests.RequestException):
        HttpUtils.fetch(
            _download_cfg(),
            ProxyConfig(),
            "https://example.com/x",
            max_retry=3,
            should_retry=skip_retry_on_4xx,
        )

    assert mock_get.call_count == 1, "4xx + skip_retry_on_4xx 应只请求一次"


@patch("pavone.utils.http_utils.requests.get")
def test_fetch_5xx_with_skip_callback_still_retries(mock_get: MagicMock) -> None:
    """skip_retry_on_4xx 只对 4xx 生效，5xx 仍重试。"""
    resp = _make_resp(503)
    err = requests.HTTPError("503", response=resp)
    mock_get.return_value = MagicMock(raise_for_status=MagicMock(side_effect=err))

    with pytest.raises(requests.RequestException):
        HttpUtils.fetch(
            _download_cfg(),
            ProxyConfig(),
            "https://example.com/x",
            max_retry=3,
            should_retry=skip_retry_on_4xx,
        )

    assert mock_get.call_count == 3


@patch("pavone.utils.http_utils.requests.get")
def test_fetch_connection_error_with_skip_callback_still_retries(mock_get: MagicMock) -> None:
    """无 status_code 的网络错误（如 ConnectionError）走默认 True 分支，依然重试。"""
    mock_get.side_effect = requests.ConnectionError("boom")

    with pytest.raises(requests.RequestException):
        HttpUtils.fetch(
            _download_cfg(),
            ProxyConfig(),
            "https://example.com/x",
            max_retry=3,
            should_retry=skip_retry_on_4xx,
        )

    assert mock_get.call_count == 3


@patch("pavone.utils.http_utils.requests.get")
def test_fetch_4xx_skip_with_no_exceptions_returns_response(mock_get: MagicMock) -> None:
    """no_exceptions=True + skip_retry_on_4xx 时 4xx 应返回最后一次响应而非抛错，且仍只请求一次。"""
    resp = _make_resp(404)
    err = requests.HTTPError("404", response=resp)
    mock_resp = MagicMock(spec=requests.Response)
    mock_resp.status_code = 404
    mock_resp.raise_for_status = MagicMock(side_effect=err)
    mock_get.return_value = mock_resp

    out = HttpUtils.fetch(
        _download_cfg(),
        ProxyConfig(),
        "https://example.com/x",
        max_retry=3,
        no_exceptions=True,
        should_retry=skip_retry_on_4xx,
    )

    assert mock_get.call_count == 1
    assert out is mock_resp


@patch("pavone.utils.http_utils.requests.get")
def test_custom_should_retry_callback(mock_get: MagicMock) -> None:
    """用户可以传任意自定义判定函数，比如对 503 也立即放弃。"""
    resp = _make_resp(503)
    err = requests.HTTPError("503", response=resp)
    mock_get.return_value = MagicMock(raise_for_status=MagicMock(side_effect=err))

    def no_retry_on_503(exc: requests.RequestException) -> bool:
        code = getattr(getattr(exc, "response", None), "status_code", None)
        return code != 503

    with pytest.raises(requests.RequestException):
        HttpUtils.fetch(
            _download_cfg(),
            ProxyConfig(),
            "https://example.com/x",
            max_retry=3,
            should_retry=no_retry_on_503,
        )

    assert mock_get.call_count == 1

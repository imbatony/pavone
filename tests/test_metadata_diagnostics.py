from types import SimpleNamespace
from typing import Optional, Tuple
from unittest.mock import patch

import pytest
import requests
from bs4 import BeautifulSoup

from pavone.models import BaseMetadata
from pavone.plugins.metadata.avbase_metadata import AvBaseMetadata
from pavone.plugins.metadata.base import ApiMetadataPlugin, HtmlMetadataPlugin, MetadataPlugin
from pavone.plugins.metadata.fanza_metadata import FanzaMetadata
from pavone.plugins.metadata.supfc2_metadata import SupFC2Metadata
from scripts import test_metadata_plugins
from scripts.test_metadata_plugins import (
    QUALITY_GATES,
    _has_meaningful_title,
    apply_previous_results,
    classify_failure,
    generate_markdown,
    run_tests,
    select_test_cases,
)


class _DiagnosticPlugin(HtmlMetadataPlugin):
    def can_extract(self, identifier: str) -> bool:
        return True

    def _resolve(self, identifier: str) -> Tuple[Optional[str], Optional[str]]:
        return "movie-id", "https://example.com/movie-id"

    def _parse(self, soup: BeautifulSoup, movie_id: str, page_url: str) -> Optional[BaseMetadata]:
        return None


class _ApiDiagnosticPlugin(ApiMetadataPlugin):
    def can_extract(self, identifier: str) -> bool:
        return True

    def _resolve(self, identifier: str) -> Tuple[Optional[str], Optional[str]]:
        return "movie-id", "https://example.com/movie-id"

    def _build_api_url(self, movie_id: str) -> str:
        return "https://example.com/api/movie-id"

    def _parse(self, data: dict[str, object], movie_id: str, page_url: str) -> Optional[BaseMetadata]:
        return None


def _response(status: int = 200) -> requests.Response:
    response = requests.Response()
    response.status_code = status
    response.url = "https://example.com/final"
    response._content = b"<html></html>"
    response.encoding = "utf-8"
    return response


def test_html_plugin_records_parse_diagnostic() -> None:
    plugin = _DiagnosticPlugin()
    with patch.object(plugin, "_fetch_page", return_value=_response()):
        assert plugin.extract_metadata("movie-id") is None

    diagnostic = plugin.get_last_diagnostic()
    assert diagnostic["stage"] == "parse"
    assert diagnostic["error"] == "解析器返回空结果"
    assert diagnostic["http_status"] == 200
    assert diagnostic["final_url"] == "https://example.com/final"


def test_html_plugin_records_http_failure() -> None:
    plugin = _DiagnosticPlugin()
    response = _response(403)
    error = requests.HTTPError("403 Client Error", response=response)
    with patch.object(plugin, "_fetch_page", side_effect=error):
        assert plugin.extract_metadata("movie-id") is None

    diagnostic = plugin.get_last_diagnostic()
    assert diagnostic["stage"] == "fetch"
    assert diagnostic["exception_type"] == "HTTPError"
    assert diagnostic["http_status"] == 403
    assert classify_failure(diagnostic) == "BLOCKED"


def test_api_json_decode_failure_is_parse_diagnostic() -> None:
    plugin = _ApiDiagnosticPlugin()
    response = _response()
    with (
        patch.object(plugin, "_fetch_api", return_value=response),
        patch.object(response, "json", side_effect=ValueError("invalid json")),
    ):
        assert plugin.extract_metadata("movie-id") is None

    diagnostic = plugin.get_last_diagnostic()
    assert diagnostic["stage"] == "parse"
    assert diagnostic["exception_type"] == "ValueError"
    assert classify_failure(diagnostic) == "PARSE"


@pytest.mark.parametrize("plugin_class", [AvBaseMetadata, FanzaMetadata, SupFC2Metadata])
def test_overridden_extractors_record_resolve_diagnostic(plugin_class: type[MetadataPlugin]) -> None:
    plugin = plugin_class()
    assert plugin.extract_metadata("https://example.com/invalid") is None
    diagnostic = plugin.get_last_diagnostic()
    assert diagnostic["stage"] == "resolve"
    assert diagnostic["error"]


@pytest.mark.parametrize(
    ("diagnostic", "expected"),
    [
        ({"stage": "resolve", "error": "bad id"}, "STALE_CASE"),
        ({"stage": "fetch", "error": "404 Client Error"}, "STALE_CASE"),
        ({"stage": "fetch", "error": "connection timed out"}, "NETWORK"),
        ({"stage": "fetch", "error": "403 forbidden", "http_status": 403}, "BLOCKED"),
        ({"stage": "parse", "error": "selector missing", "http_status": 200}, "PARSE"),
        ({"stage": "unknown", "error": "no details"}, "EMPTY_RESULT"),
    ],
)
def test_classify_failure(diagnostic: dict[str, object], expected: str) -> None:
    assert classify_failure(diagnostic) == expected


def test_select_test_cases_rejects_unknown_plugin() -> None:
    with pytest.raises(ValueError, match="未知插件"):
        select_test_cases({"MissingMetadata"})


def test_run_tests_retries_selected_plugin(monkeypatch: pytest.MonkeyPatch) -> None:
    class FakePlugin:
        def __init__(self) -> None:
            self.calls = 0

        def can_extract(self, identifier: str) -> bool:
            return True

        def extract_metadata(self, identifier: str) -> object | None:
            self.calls += 1
            if self.calls == 1:
                return None
            return SimpleNamespace(title="Recovered")

        def get_last_diagnostic(self) -> dict[str, object]:
            return {"stage": "fetch", "error": "connection timed out"}

    plugin = FakePlugin()
    manager = SimpleNamespace(load_plugins=lambda: None, metadata_plugins=[plugin])
    monkeypatch.setattr(test_metadata_plugins, "TEST_CASES", [("FakePlugin", "Html", "id")])
    with patch("pavone.manager.plugin_manager.PluginManager", return_value=manager):
        results = run_tests({"FakePlugin"}, retries=1)

    assert results[0]["status"] == "OK"
    assert results[0]["attempts"] == 2
    assert plugin.calls == 2


def test_quality_gate_marks_returned_metadata_as_degraded(monkeypatch: pytest.MonkeyPatch) -> None:
    class FakeTokyoHotPlugin:
        def can_extract(self, identifier: str) -> bool:
            return True

        def extract_metadata(self, identifier: str) -> object:
            return SimpleNamespace(title="n0697", code="n0697", cover="cover.jpg", premiered=None, studio="TOKYO-HOT")

    manager = SimpleNamespace(load_plugins=lambda: None, metadata_plugins=[FakeTokyoHotPlugin()])
    monkeypatch.setattr(
        test_metadata_plugins,
        "TEST_CASES",
        [("FakeTokyoHotPlugin", "Html", "https://my.tokyo-hot.com/product/n0697/?lang=ja")],
    )
    monkeypatch.setitem(QUALITY_GATES, "FakeTokyoHotPlugin", QUALITY_GATES["TokyoHotMetadata"])
    with patch("pavone.manager.plugin_manager.PluginManager", return_value=manager):
        results = run_tests({"FakeTokyoHotPlugin"})

    assert results[0]["status"] == "DEGRADED"
    assert results[0]["failure_type"] == "QUALITY_GATE"
    assert results[0]["quality_gate"]["missing_fields"] == ["premiered", "title"]
    assert results[0]["quality_gate"]["min_score"] == 70


def test_title_with_code_and_descriptive_text_is_meaningful() -> None:
    metadata = SimpleNamespace(code="FC2-2941579", title="FC2-2941579 あどけない顔をした美少女")

    assert _has_meaningful_title(metadata)


def test_title_with_only_repeated_code_is_not_meaningful() -> None:
    metadata = SimpleNamespace(code="n0697", title="n0697 n0697")

    assert not _has_meaningful_title(metadata)


@pytest.mark.parametrize(
    ("plugin_name", "min_score", "required_fields"),
    [
        ("TokyoHotMetadata", 70, {"title", "cover", "premiered", "studio"}),
        ("PcolleMetadata", 50, {"title", "cover", "premiered", "studio", "plot"}),
        ("MyWifeMetadata", 45, {"title", "cover", "studio"}),
        ("PPVDataBankMetadata", 30, {"title", "cover", "premiered", "studio"}),
        ("JavfreeMetadata", 25, {"title", "cover", "premiered", "director"}),
    ],
)
def test_quality_gate_definitions(plugin_name: str, min_score: int, required_fields: set[str]) -> None:
    assert QUALITY_GATES[plugin_name]["min_score"] == min_score
    assert set(QUALITY_GATES[plugin_name]["required_fields"]) == required_fields


def test_apply_previous_results_records_trends() -> None:
    results = [
        {"plugin": "Regressed", "status": "DEGRADED", "score": 55},
        {"plugin": "Worsened", "status": "FAIL", "score": 0},
        {"plugin": "Recovered", "status": "OK", "score": 60},
        {"plugin": "NewPlugin", "status": "OK", "score": 50},
    ]
    previous = {
        "results": [
            {"plugin": "Regressed", "status": "OK", "score": 80},
            {"plugin": "Worsened", "status": "DEGRADED", "score": 40},
            {"plugin": "Recovered", "status": "FAIL", "score": 0},
        ]
    }

    apply_previous_results(results, previous)

    assert results[0]["previous_status"] == "OK"
    assert results[0]["previous_score"] == 80
    assert results[0]["status_change"] == "REGRESSED"
    assert results[0]["score_change"] == -25
    assert results[1]["status_change"] == "REGRESSED"
    assert results[2]["status_change"] == "RECOVERED"
    assert results[2]["score_change"] == 60
    assert results[3]["status_change"] == "NEW"
    assert results[3]["score_change"] is None


@pytest.mark.parametrize("current_status", ["DEGRADED", "SKIP", "NOT_FOUND"])
def test_non_ok_improvement_is_not_reported_as_recovered(current_status: str) -> None:
    results = [{"plugin": "StillUnhealthy", "status": current_status, "score": 20}]
    previous = {"results": [{"plugin": "StillUnhealthy", "status": "FAIL", "score": 0}]}

    apply_previous_results(results, previous)

    assert results[0]["status_change"] == "CHANGED"


def test_markdown_without_previous_results_remains_compatible() -> None:
    markdown = generate_markdown(
        {
            "version": "1.0.0",
            "timestamp": "2026-07-24",
            "total_time_s": 1,
            "results": [],
        }
    )

    assert "## 趋势" not in markdown
    assert "质量降级 | 0" in markdown
    assert "[#126](https://github.com/imbatony/pavone/issues/126)" in markdown


def test_markdown_highlights_trends() -> None:
    results = [
        {
            "plugin": "Regressed",
            "base_class": "Html",
            "status": "DEGRADED",
            "score": 55,
            "time_ms": 100,
            "fields": {},
            "error": "评分过低",
            "failure_type": "QUALITY_GATE",
            "failure_stage": "quality",
        },
        {
            "plugin": "Recovered",
            "base_class": "Html",
            "status": "OK",
            "score": 60,
            "time_ms": 100,
            "fields": {},
            "error": None,
            "title": "Recovered title",
        },
    ]
    apply_previous_results(
        results,
        {
            "results": [
                {"plugin": "Regressed", "status": "OK", "score": 80},
                {"plugin": "Recovered", "status": "FAIL", "score": 0},
            ]
        },
    )

    markdown = generate_markdown(
        {
            "version": "1.0.0",
            "timestamp": "2026-07-24",
            "total_time_s": 1,
            "results": results,
        }
    )

    assert "**新增失败/降级**: Regressed (OK → DEGRADED)" in markdown
    assert "**恢复**: Recovered (FAIL → OK)" in markdown
    assert "**显著降分**: Regressed (80 → 55, -25)" in markdown


def test_markdown_includes_failure_diagnostics() -> None:
    markdown = generate_markdown(
        {
            "version": "1.0.0",
            "timestamp": "2026-07-24",
            "total_time_s": 1,
            "results": [
                {
                    "plugin": "BlockedMetadata",
                    "base_class": "Html",
                    "status": "FAIL",
                    "score": 0,
                    "time_ms": 100,
                    "fields": {},
                    "error": "403 Client Error",
                    "failure_type": "BLOCKED",
                    "failure_stage": "fetch",
                    "http_status": 403,
                    "final_url": "https://example.com/final",
                }
            ],
        }
    )

    assert "BLOCKED/fetch" in markdown
    assert "HTTP 403" in markdown
    assert "https://example.com/final" in markdown

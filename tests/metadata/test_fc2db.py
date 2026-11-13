"""FC2DB 提取器测试，夹具保留实测页面结构并使用示例标题和演员。"""

from pathlib import Path
from unittest.mock import patch

import pytest
import requests
from bs4 import BeautifulSoup

from pavone.manager.plugin_manager import PluginManager
from pavone.models import MovieMetadata
from pavone.plugins.metadata import FC2DBMetadata
from pavone.plugins.metadata import fc2db_metadata as module

PAGE_URL = "https://fc2db.net/work/5002880/"


@pytest.fixture
def extractor() -> FC2DBMetadata:
    return FC2DBMetadata()


@pytest.fixture
def html() -> str:
    return (Path(__file__).parents[1] / "sites" / "fc2db.html").read_text(encoding="utf-8")


def response_for(html: str, status: int = 200) -> requests.Response:
    response = requests.Response()
    response.status_code = status
    response.url = PAGE_URL
    response.encoding = "utf-8"
    response._content = html.encode("utf-8")
    return response


@pytest.mark.parametrize(
    "identifier",
    [
        PAGE_URL,
        "http://www.fc2db.net/work/5002880",
        PAGE_URL + "?source=test#details",
        "5002880",
        "FC2-5002880",
        "FC2-PPV-5002880",
        " fc2_ppv_5002880 ",
    ],
)
def test_identifiers(extractor: FC2DBMetadata, identifier: str) -> None:
    assert extractor.can_extract(identifier)
    assert extractor._resolve(identifier) == ("5002880", PAGE_URL)


@pytest.mark.parametrize(
    "identifier",
    [
        "",
        "ABC-123",
        "https://fc2db.net/works/",
        "https://fc2db.net/work/not-a-number/",
        "https://fc2db.net/work/5002880/extra/",
        "https://fc2db.net/actress/5002880/",
        "https://example.com/work/5002880/",
        "https://fc2db.net.example.com/work/5002880/",
        "ftp://fc2db.net/work/5002880/",
    ],
)
def test_invalid_identifiers(extractor: FC2DBMetadata, identifier: str) -> None:
    assert not extractor.can_extract(identifier)
    with patch.object(extractor, "_fetch_page") as fetch:
        assert extractor.extract_metadata(identifier) is None
    fetch.assert_not_called()


def test_extract_metadata(extractor: FC2DBMetadata, html: str) -> None:
    with patch.object(extractor, "_fetch_page", return_value=response_for(html)):
        metadata = extractor.extract_metadata("FC2-PPV-5002880")
    assert isinstance(metadata, MovieMetadata)
    assert metadata.site == "FC2DB"
    assert metadata.url == PAGE_URL
    assert metadata.code == "FC2-5002880"
    assert metadata.title == "FC2-5002880 Sample work title"
    assert metadata.original_title == "Sample work title"
    assert metadata.actors == ["Sample actor"]
    assert metadata.studio == "KING POWER D"
    assert metadata.premiered == "2026-11-03"
    assert metadata.year == 2026
    assert metadata.runtime == 84
    assert metadata.tags == ["スレンダー", "色白"]
    assert metadata.cover == "https://fc2db.net/wp-content/uploads/2026/11/1793689832.99.jpg?v=1793696478"
    assert metadata.poster == metadata.thumbnail == metadata.cover
    assert not metadata.backdrops
    assert not metadata.plot
    assert metadata.rating is None
    assert metadata.official_rating == "JP-18+"
    assert extractor.get_last_diagnostic()["stage"] == "complete"


def test_optional_fields_and_cover_fallback(extractor: FC2DBMetadata, html: str) -> None:
    soup = BeautifulSoup(html, "lxml")
    for tag in soup.select("meta[property='og:image'], dl dt, dl dd, a[href*='/actress/'], a[href*='/work-tags/']"):
        tag.decompose()
    description = soup.select_one(".prose")
    assert description is not None
    description.append(BeautifulSoup("<p>First line</p><p>Second line</p>", "html.parser"))
    with patch.object(extractor, "_fetch_page", return_value=response_for(str(soup))):
        metadata = extractor.extract_metadata(PAGE_URL)
    assert isinstance(metadata, MovieMetadata)
    assert not metadata.actors
    assert not metadata.tags
    assert metadata.studio is None
    assert metadata.premiered is None
    assert metadata.runtime is None
    assert metadata.plot == "First line\nSecond line"
    assert metadata.cover == "https://fc2db.net/wp-content/uploads/cover-1024x1024.jpg"


@pytest.mark.parametrize(
    "html",
    [
        '<h1>年齢確認</h1><form action="/__verify_age__"></form>',
        "<main><h1>Page not found</h1></main>",
        "<main><h1>[FC2-PPV-1234567] Wrong work</h1></main>",
        "<main><h1>[FC2-PPV-5002880]</h1></main>",
        "<main><h1>[FC2-PPV-5002880] Title</h1><dl><dt>商品ID</dt><dd>1234567</dd></dl></main>",
    ],
)
def test_rejects_non_work_pages(extractor: FC2DBMetadata, html: str) -> None:
    with patch.object(extractor, "_fetch_page", return_value=response_for(html)):
        assert extractor.extract_metadata(PAGE_URL) is None
    assert extractor.get_last_diagnostic()["stage"] == "parse"
    assert extractor.get_last_diagnostic()["error"]


def test_browser_fetch(extractor: FC2DBMetadata, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(extractor.config.download, "cache_dir", str(tmp_path))
    response = response_for("details")
    with patch.object(module.HttpUtils, "fetch_with_browser", return_value=response) as fetch:
        assert extractor._fetch_page(PAGE_URL) is response
    kwargs = fetch.call_args.kwargs
    assert kwargs["url"] == PAGE_URL
    assert kwargs["wait_for_content"] == ["[FC2-PPV-5002880]"]
    assert kwargs["reject_content"] == ['action="/__verify_age__"']
    assert kwargs["browser_user_data_path"] == str(tmp_path / "browser" / "fc2db-profile")
    assert kwargs["browser_load_mode"] == "normal"
    assert kwargs["max_wait"] == 300


def test_browser_failure_is_diagnostic(extractor: FC2DBMetadata) -> None:
    with patch.object(module.HttpUtils, "fetch_with_browser", return_value=response_for("", 503)):
        assert extractor.extract_metadata(PAGE_URL) is None
    diagnostic = extractor.get_last_diagnostic()
    assert diagnostic["stage"] == "fetch"
    assert diagnostic["http_status"] == 503
    assert diagnostic["exception_type"] == "HTTPError"


def test_plugin_discovery() -> None:
    manager = PluginManager()
    assert manager._discover_plugins_in_module(module) == 1
    assert isinstance(manager.plugins["FC2DBMetadata"], FC2DBMetadata)

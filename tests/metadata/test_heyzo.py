"""
HEYZO 元数据提取器测试

使用真实 HTML (tests/sites/heyzo.html)
参考: metatube-sdk-go/provider/heyzo/heyzo_test.go
测试 ID: 3456
"""

from unittest.mock import MagicMock, patch

from pavone.plugins.metadata.heyzo_metadata import HeyzoMetadata


class TestHeyzoMetadata:
    def setup_method(self):
        self.extractor = HeyzoMetadata()

    def test_can_extract_url(self):
        assert self.extractor.can_extract("https://www.heyzo.com/moviepages/3456/index.html")

    def test_can_extract_movie_id(self):
        assert self.extractor.can_extract("3456")
        assert self.extractor.can_extract("HEYZO-3456")

    def test_cannot_extract_invalid(self):
        assert not self.extractor.can_extract("https://example.com/moviepages/3456/index.html")
        assert not self.extractor.can_extract("")
        assert not self.extractor.can_extract("12")

    def _mock_html_response(self):
        with open("tests/sites/heyzo.html", "r", encoding="utf-8") as f:
            html = f.read()
        mock = MagicMock()
        mock.status_code = 200
        mock.content = html.encode("utf-8")
        mock.text = html
        mock.raise_for_status = MagicMock()
        return mock

    def test_extract_metadata_with_mock(self):
        resp = self._mock_html_response()
        url = "https://www.heyzo.com/moviepages/3456/index.html"
        with patch.object(self.extractor, "fetch", return_value=resp):
            metadata = self.extractor.extract_metadata(url)

        assert metadata is not None
        assert "HEYZO-3456" in metadata.code
        assert "テスト動画" in metadata.title
        assert metadata.premiered == "2023-06-20"
        assert "テスト美咲" in metadata.actors
        assert metadata.studio == "HEYZO"
        assert metadata.runtime == 90
        assert metadata.rating == 4.5
        assert metadata.cover is not None
        assert metadata.official_rating == "JP-18+"

    def test_extract_genres(self):
        resp = self._mock_html_response()
        url = "https://www.heyzo.com/moviepages/3456/index.html"
        with patch.object(self.extractor, "fetch", return_value=resp):
            metadata = self.extractor.extract_metadata(url)

        assert metadata is not None
        assert metadata.tags is not None
        assert "美乳" in metadata.tags

    def test_extract_series(self):
        resp = self._mock_html_response()
        url = "https://www.heyzo.com/moviepages/3456/index.html"
        with patch.object(self.extractor, "fetch", return_value=resp):
            metadata = self.extractor.extract_metadata(url)

        assert metadata is not None
        assert metadata.serial == "テストシリーズ"

    def test_extract_metadata_from_bare_id(self):
        resp = self._mock_html_response()
        with patch.object(self.extractor, "fetch", return_value=resp):
            metadata = self.extractor.extract_metadata("3456")
        assert metadata is not None

    def test_extract_metadata_invalid_url(self):
        assert self.extractor.extract_metadata("https://example.com/") is None

    def test_extract_metadata_network_error(self):
        import requests

        with patch.object(self.extractor, "fetch", side_effect=requests.ConnectionError("timeout")):
            result = self.extractor.extract_metadata("https://www.heyzo.com/moviepages/3456/index.html")
        assert result is None

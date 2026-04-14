"""
Pcolle 元数据提取器测试

使用真实 HTML (tests/sites/pcolle.html)
参考: metatube-sdk-go/provider/pcolle/pcolle_test.go
测试 ID: abc123def45
"""

from unittest.mock import MagicMock, patch

from pavone.plugins.metadata.pcolle_metadata import PcolleMetadata


class TestPcolleMetadata:
    def setup_method(self):
        self.extractor = PcolleMetadata()

    def test_can_extract_url(self):
        assert self.extractor.can_extract("https://www.pcolle.com/product/detail/?product_id=abc123def45")

    def test_can_extract_movie_id(self):
        assert self.extractor.can_extract("abc123def45")
        assert self.extractor.can_extract("PCOLLE-abc123def45")

    def test_cannot_extract_invalid(self):
        assert not self.extractor.can_extract("https://example.com/product/detail/?product_id=abc123def45")
        assert not self.extractor.can_extract("")
        assert not self.extractor.can_extract("short")

    def _mock_html_response(self):
        with open("tests/sites/pcolle.html", "r", encoding="utf-8") as f:
            html = f.read()
        mock = MagicMock()
        mock.status_code = 200
        mock.content = html.encode("utf-8")
        mock.text = html
        mock.raise_for_status = MagicMock()
        return mock

    def test_extract_metadata_with_mock(self):
        resp = self._mock_html_response()
        url = "https://www.pcolle.com/product/detail/?product_id=abc123def45"
        with patch.object(self.extractor, "fetch", return_value=resp):
            metadata = self.extractor.extract_metadata(url)

        assert metadata is not None
        assert "PCOLLE" in metadata.code
        assert "テスト商品タイトル" in metadata.title
        assert metadata.studio == "テスト販売者"
        assert metadata.premiered == "2023-12-01"
        assert metadata.cover is not None
        assert metadata.official_rating == "JP-18+"

    def test_extract_genres(self):
        resp = self._mock_html_response()
        url = "https://www.pcolle.com/product/detail/?product_id=abc123def45"
        with patch.object(self.extractor, "fetch", return_value=resp):
            metadata = self.extractor.extract_metadata(url)

        assert metadata is not None
        assert metadata.tags is not None
        assert "盗撮" in metadata.tags

    def test_extract_summary(self):
        resp = self._mock_html_response()
        url = "https://www.pcolle.com/product/detail/?product_id=abc123def45"
        with patch.object(self.extractor, "fetch", return_value=resp):
            metadata = self.extractor.extract_metadata(url)

        assert metadata is not None
        assert "テスト商品の説明" in (metadata.plot or "")

    def test_extract_metadata_from_bare_id(self):
        resp = self._mock_html_response()
        with patch.object(self.extractor, "fetch", return_value=resp):
            metadata = self.extractor.extract_metadata("abc123def45")
        assert metadata is not None

    def test_extract_metadata_invalid_url(self):
        assert self.extractor.extract_metadata("https://example.com/") is None

    def test_extract_metadata_network_error(self):
        import requests

        with patch.object(self.extractor, "fetch", side_effect=requests.ConnectionError("timeout")):
            result = self.extractor.extract_metadata("https://www.pcolle.com/product/detail/?product_id=abc123def45")
        assert result is None

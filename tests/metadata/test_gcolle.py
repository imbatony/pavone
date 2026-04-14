"""
Gcolle 元数据提取器测试

使用真实 HTML (tests/sites/gcolle.html)
参考: metatube-sdk-go/provider/gcolle/gcolle_test.go
测试 ID: 847256
"""

from unittest.mock import MagicMock, patch

from pavone.plugins.metadata.gcolle_metadata import GcolleMetadata


class TestGcolleMetadata:
    def setup_method(self):
        self.extractor = GcolleMetadata()

    def test_can_extract_url(self):
        assert self.extractor.can_extract("https://gcolle.net/product_info.php/products_id/847256")

    def test_can_extract_movie_id(self):
        assert self.extractor.can_extract("847256")
        assert self.extractor.can_extract("GCOLLE-847256")

    def test_cannot_extract_invalid(self):
        assert not self.extractor.can_extract("https://example.com/products/847256")
        assert not self.extractor.can_extract("abc")
        assert not self.extractor.can_extract("")

    def _mock_html_response(self):
        with open("tests/sites/gcolle.html", "r", encoding="utf-8") as f:
            html = f.read()
        mock = MagicMock()
        mock.status_code = 200
        mock.content = html.encode("utf-8")
        mock.text = html
        mock.raise_for_status = MagicMock()
        return mock

    def test_extract_metadata_with_mock(self):
        resp = self._mock_html_response()
        url = "https://gcolle.net/product_info.php/products_id/847256"
        with patch.object(self.extractor, "fetch", return_value=resp):
            metadata = self.extractor.extract_metadata(url)

        assert metadata is not None
        assert "GCOLLE-847256" in metadata.code
        assert metadata.official_rating == "JP-18+"

    def test_extract_metadata_from_id(self):
        resp = self._mock_html_response()
        with patch.object(self.extractor, "fetch", return_value=resp):
            metadata = self.extractor.extract_metadata("847256")
        assert metadata is not None

    def test_extract_metadata_invalid(self):
        assert self.extractor.extract_metadata("https://example.com/") is None

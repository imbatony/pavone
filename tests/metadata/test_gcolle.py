"""
Gcolle 元数据提取器测试

使用真实 HTML (tests/sites/gcolle.html)
参考: metatube-sdk-go/provider/gcolle/gcolle_test.go
测试 ID: 847256
"""

from unittest.mock import MagicMock, patch

import requests

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
        with open("tests/sites/gcolle_product.html", "r", encoding="utf-8") as f:
            html = f.read()
        mock = MagicMock()
        mock.status_code = 200
        mock.url = "https://gcolle.net/product_info.php/products_id/847256"
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
        assert "電車XX #22" in metadata.title
        assert metadata.plot is not None and "商品説明" in metadata.plot
        assert metadata.studio == "4号車"
        assert metadata.premiered == "2022-06-03"
        assert metadata.tags is not None and "個人撮影" in metadata.tags
        assert metadata.cover == "https://img.gcolle.net/uploader/original/21651/cover.jpg"
        assert metadata.backdrops == ["https://img.gcolle.net/uploader/sample/21651/sample01.jpg"]
        assert metadata.official_rating == "JP-18+"

    def test_extract_metadata_from_id(self):
        resp = self._mock_html_response()
        with patch.object(self.extractor, "fetch", return_value=resp):
            metadata = self.extractor.extract_metadata("847256")
        assert metadata is not None

    def test_extract_metadata_invalid(self):
        assert self.extractor.extract_metadata("https://example.com/") is None

    def test_age_check_page_is_not_metadata(self):
        with open("tests/sites/gcolle.html", "r", encoding="utf-8") as f:
            html = f.read()
        response = MagicMock()
        response.status_code = 200
        response.url = "https://gcolle.net/age_check.php/continue/token"
        response.text = html

        with patch.object(self.extractor, "_fetch_page", return_value=response):
            assert self.extractor.extract_metadata("847256") is None

    def test_fetch_page_follows_age_confirmation_with_redirect_cookie(self):
        with open("tests/sites/gcolle.html", "r", encoding="utf-8") as f:
            age_html = f.read()

        redirect = requests.Response()
        redirect.status_code = 302
        redirect.cookies.set("osCsid", "session-token")

        age_response = requests.Response()
        age_response.status_code = 200
        age_response.url = "https://gcolle.net/age_check.php/continue/token"
        age_response.encoding = "utf-8"
        age_response._content = age_html.encode("utf-8")
        age_response.history = [redirect]

        product_response = self._mock_html_response()
        with patch.object(self.extractor, "fetch", side_effect=[age_response, product_response]) as fetch:
            result = self.extractor._fetch_page("https://gcolle.net/product_info.php/products_id/847256")

        assert result is product_response
        assert fetch.call_count == 2
        follow_up = fetch.call_args_list[1]
        assert "age_check" in follow_up.args[0]
        assert follow_up.kwargs["cookies"] == {"osCsid": "session-token"}
        assert follow_up.kwargs["headers"]["Referer"] == age_response.url

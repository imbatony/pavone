"""
JAVFREE 元数据提取器测试

使用真实 HTML (tests/sites/javfree.html)
参考: metatube-sdk-go/provider/javfree/javfree_test.go
测试 ID: 12345-1234567
"""

from unittest.mock import MagicMock, patch

from pavone.plugins.metadata.javfree_metadata import JavfreeMetadata


class TestJavfreeMetadata:
    def setup_method(self):
        self.extractor = JavfreeMetadata()

    def test_can_extract_url(self):
        assert self.extractor.can_extract("https://javfree.me/12345/fc2-ppv-1234567")

    def test_can_extract_movie_id(self):
        assert self.extractor.can_extract("12345-1234567")

    def test_cannot_extract_invalid(self):
        assert not self.extractor.can_extract("https://example.com/12345/fc2-ppv-1234567")
        assert not self.extractor.can_extract("")
        assert not self.extractor.can_extract("not-valid")

    def _mock_html_response(self):
        with open("tests/sites/javfree.html", "r", encoding="utf-8") as f:
            html = f.read()
        mock = MagicMock()
        mock.status_code = 200
        mock.content = html.encode("utf-8")
        mock.text = html
        mock.raise_for_status = MagicMock()
        return mock

    def test_extract_metadata_with_mock(self):
        resp = self._mock_html_response()
        url = "https://javfree.me/12345/fc2-ppv-1234567"
        with patch.object(self.extractor, "fetch", return_value=resp):
            metadata = self.extractor.extract_metadata(url)

        assert metadata is not None
        assert "FC2-1234567" in metadata.code
        assert "テスト動画タイトル" in metadata.title
        assert metadata.director == "テスト出品者"
        assert metadata.premiered == "2023-09-01"
        assert metadata.cover is not None
        assert metadata.official_rating == "JP-18+"

    def test_extract_preview_images(self):
        resp = self._mock_html_response()
        url = "https://javfree.me/12345/fc2-ppv-1234567"
        with patch.object(self.extractor, "fetch", return_value=resp):
            metadata = self.extractor.extract_metadata(url)

        assert metadata is not None
        # First image becomes cover, rest become backdrops
        assert metadata.backdrops is not None
        assert len(metadata.backdrops) == 2

    def test_extract_metadata_from_bare_id(self):
        resp = self._mock_html_response()
        with patch.object(self.extractor, "fetch", return_value=resp):
            metadata = self.extractor.extract_metadata("12345-1234567")
        assert metadata is not None

    def test_extract_metadata_invalid_url(self):
        assert self.extractor.extract_metadata("https://example.com/") is None

    def test_extract_metadata_network_error(self):
        import requests

        with patch.object(self.extractor, "fetch", side_effect=requests.ConnectionError("timeout")):
            result = self.extractor.extract_metadata("https://javfree.me/12345/fc2-ppv-1234567")
        assert result is None

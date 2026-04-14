"""
MadouQu 元数据提取器测试

使用真实 HTML (tests/sites/madouqu.html)
参考: metatube-sdk-go/provider/madouqu/madouqu_test.go
测试 ID: mdx-0236
"""

from unittest.mock import MagicMock, patch

from pavone.plugins.metadata.madouqu_metadata import MadouquMetadata


class TestMadouquMetadata:
    def setup_method(self):
        self.extractor = MadouquMetadata()

    def test_can_extract_url(self):
        assert self.extractor.can_extract("https://madouqu.com/mdx-0236/")

    def test_can_extract_movie_id(self):
        assert self.extractor.can_extract("mdx-0236")

    def test_cannot_extract_invalid(self):
        assert not self.extractor.can_extract("https://example.com/mdx-0236/")
        assert not self.extractor.can_extract("")
        assert not self.extractor.can_extract("12345")

    def _mock_html_response(self):
        with open("tests/sites/madouqu.html", "r", encoding="utf-8") as f:
            html = f.read()
        mock = MagicMock()
        mock.status_code = 200
        mock.content = html.encode("utf-8")
        mock.text = html
        mock.raise_for_status = MagicMock()
        return mock

    def test_extract_metadata_with_mock(self):
        resp = self._mock_html_response()
        url = "https://madouqu.com/mdx-0236/"
        with patch.object(self.extractor, "fetch", return_value=resp):
            metadata = self.extractor.extract_metadata(url)

        assert metadata is not None
        assert metadata.code == "MDX-0236"
        assert "测试麻豆视频标题" in metadata.title
        assert "小明" in metadata.actors
        assert "小红" in metadata.actors
        assert metadata.studio == "麻豆传媒"
        assert metadata.cover is not None
        assert metadata.official_rating == "JP-18+"

    def test_extract_metadata_from_bare_id(self):
        resp = self._mock_html_response()
        with patch.object(self.extractor, "fetch", return_value=resp):
            metadata = self.extractor.extract_metadata("mdx-0236")
        assert metadata is not None

    def test_extract_metadata_invalid_url(self):
        assert self.extractor.extract_metadata("https://example.com/") is None

    def test_extract_metadata_network_error(self):
        import requests

        with patch.object(self.extractor, "fetch", side_effect=requests.ConnectionError("timeout")):
            result = self.extractor.extract_metadata("https://madouqu.com/mdx-0236/")
        assert result is None

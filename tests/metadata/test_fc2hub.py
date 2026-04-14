"""
FC2HUB 元数据提取器测试

使用真实 HTML (tests/sites/fc2hub.html)
参考: metatube-sdk-go/provider/fc2hub/fc2hub_test.go
测试 ID: 1152468-2725031
"""

from unittest.mock import MagicMock, patch

from pavone.plugins.metadata.fc2hub_metadata import Fc2HubMetadata


class TestFc2HubMetadata:
    def setup_method(self):
        self.extractor = Fc2HubMetadata()

    def test_can_extract_url(self):
        assert self.extractor.can_extract("https://javten.com/video/1152468/id2725031/")

    def test_can_extract_movie_id(self):
        assert self.extractor.can_extract("1152468-2725031")

    def test_cannot_extract_invalid(self):
        assert not self.extractor.can_extract("https://example.com/video/123/id456/")
        assert not self.extractor.can_extract("")
        assert not self.extractor.can_extract("not-a-valid-id")

    def _mock_html_response(self):
        with open("tests/sites/fc2hub.html", "r", encoding="utf-8") as f:
            html = f.read()
        mock = MagicMock()
        mock.status_code = 200
        mock.content = html.encode("utf-8")
        mock.text = html
        mock.raise_for_status = MagicMock()
        return mock

    def test_extract_metadata_with_mock(self):
        resp = self._mock_html_response()
        url = "https://javten.com/video/1152468/id2725031/"
        with patch.object(self.extractor, "fetch", return_value=resp):
            metadata = self.extractor.extract_metadata(url)

        assert metadata is not None
        assert "FC2" in metadata.code
        assert "2725031" in metadata.code
        assert "個人撮影" in metadata.title or "みさき" in metadata.title
        assert metadata.cover is not None
        assert metadata.official_rating == "JP-18+"

    def test_extract_metadata_from_id(self):
        resp = self._mock_html_response()
        with patch.object(self.extractor, "fetch", return_value=resp):
            metadata = self.extractor.extract_metadata("1152468-2725031")
        assert metadata is not None

    def test_extract_metadata_invalid(self):
        assert self.extractor.extract_metadata("https://example.com/") is None

"""
JAV321 元数据提取器测试

使用真实 HTML (tests/sites/jav321.html)
参考: metatube-sdk-go/provider/jav321/jav321_test.go
测试 ID: ABP-123
"""

from unittest.mock import MagicMock, patch

from pavone.plugins.metadata.jav321_metadata import Jav321Metadata


class TestJav321Metadata:
    def setup_method(self):
        self.extractor = Jav321Metadata()

    def test_can_extract_url(self):
        assert self.extractor.can_extract("https://www.jav321.com/video/ABP-123")

    def test_can_extract_movie_id(self):
        assert self.extractor.can_extract("ABP-123")

    def test_cannot_extract_invalid(self):
        assert not self.extractor.can_extract("https://example.com/video/ABP-123")
        assert not self.extractor.can_extract("")
        assert not self.extractor.can_extract("12345")

    def _mock_html_response(self):
        with open("tests/sites/jav321.html", "r", encoding="utf-8") as f:
            html = f.read()
        mock = MagicMock()
        mock.status_code = 200
        mock.content = html.encode("utf-8")
        mock.text = html
        mock.raise_for_status = MagicMock()
        return mock

    def test_extract_metadata_with_mock(self):
        resp = self._mock_html_response()
        url = "https://www.jav321.com/video/ABP-123"
        with patch.object(self.extractor, "fetch", return_value=resp):
            metadata = self.extractor.extract_metadata(url)

        assert metadata is not None
        assert metadata.code == "ABP-123"
        assert "テスト動画タイトル" in metadata.title
        assert metadata.premiered == "2023-07-10"
        assert metadata.runtime == 120
        assert "テスト花子" in metadata.actors
        assert metadata.studio == "テストメーカー"
        assert metadata.serial == "テストシリーズ"
        assert metadata.cover is not None
        assert metadata.official_rating == "JP-18+"

    def test_extract_genres(self):
        resp = self._mock_html_response()
        url = "https://www.jav321.com/video/ABP-123"
        with patch.object(self.extractor, "fetch", return_value=resp):
            metadata = self.extractor.extract_metadata(url)

        assert metadata is not None
        assert metadata.tags is not None
        assert "巨乳" in metadata.tags

    def test_extract_rating(self):
        resp = self._mock_html_response()
        url = "https://www.jav321.com/video/ABP-123"
        with patch.object(self.extractor, "fetch", return_value=resp):
            metadata = self.extractor.extract_metadata(url)

        assert metadata is not None
        assert metadata.rating == 3.5

    def test_extract_metadata_from_bare_id(self):
        resp = self._mock_html_response()
        with patch.object(self.extractor, "fetch", return_value=resp):
            metadata = self.extractor.extract_metadata("ABP-123")
        assert metadata is not None

    def test_extract_metadata_invalid_url(self):
        assert self.extractor.extract_metadata("https://example.com/") is None

    def test_extract_metadata_network_error(self):
        import requests

        with patch.object(self.extractor, "fetch", side_effect=requests.ConnectionError("timeout")):
            result = self.extractor.extract_metadata("https://www.jav321.com/video/ABP-123")
        assert result is None

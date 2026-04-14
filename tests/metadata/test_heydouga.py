"""
HeyDouga 元数据提取器测试

使用真实 HTML (tests/sites/heydouga.html)
参考: metatube-sdk-go/provider/heydouga/heydouga_test.go
测试 ID: 4037-175
"""

from unittest.mock import MagicMock, patch

from pavone.plugins.metadata.heydouga_metadata import HeydougaMetadata


class TestHeydougaMetadata:
    def setup_method(self):
        self.extractor = HeydougaMetadata()

    def test_can_extract_url(self):
        assert self.extractor.can_extract("https://www.heydouga.com/moviepages/4037/175/index.html")

    def test_can_extract_movie_id(self):
        assert self.extractor.can_extract("4037-175")
        assert self.extractor.can_extract("HEYDOUGA-4037-175")

    def test_cannot_extract_invalid(self):
        assert not self.extractor.can_extract("https://example.com/moviepages/4037/175/index.html")
        assert not self.extractor.can_extract("")
        assert not self.extractor.can_extract("invalid")

    def _mock_html_response(self):
        with open("tests/sites/heydouga.html", "r", encoding="utf-8") as f:
            html = f.read()
        mock = MagicMock()
        mock.status_code = 200
        mock.content = html.encode("utf-8")
        mock.text = html
        mock.raise_for_status = MagicMock()
        return mock

    def test_extract_metadata_with_mock(self):
        resp = self._mock_html_response()
        url = "https://www.heydouga.com/moviepages/4037/175/index.html"
        with patch.object(self.extractor, "fetch", return_value=resp):
            metadata = self.extractor.extract_metadata(url)

        assert metadata is not None
        assert "HEYDOUGA-4037-175" in metadata.code
        assert "テスト動画タイトル" in metadata.title
        assert metadata.premiered == "2023-05-15"
        assert "テスト花子" in metadata.actors
        assert metadata.studio == "テストスタジオ"
        assert metadata.runtime == 45
        assert metadata.cover is not None
        assert metadata.official_rating == "JP-18+"

    def test_extract_backdrops(self):
        resp = self._mock_html_response()
        url = "https://www.heydouga.com/moviepages/4037/175/index.html"
        with patch.object(self.extractor, "fetch", return_value=resp):
            metadata = self.extractor.extract_metadata(url)

        assert metadata is not None
        assert metadata.backdrops is not None
        assert len(metadata.backdrops) == 2

    def test_extract_metadata_from_bare_id(self):
        resp = self._mock_html_response()
        with patch.object(self.extractor, "fetch", return_value=resp):
            metadata = self.extractor.extract_metadata("4037-175")
        assert metadata is not None
        assert "HEYDOUGA" in metadata.code

    def test_extract_metadata_invalid_url(self):
        assert self.extractor.extract_metadata("https://example.com/") is None

    def test_extract_metadata_network_error(self):
        import requests

        with patch.object(self.extractor, "fetch", side_effect=requests.ConnectionError("timeout")):
            result = self.extractor.extract_metadata("https://www.heydouga.com/moviepages/4037/175/index.html")
        assert result is None

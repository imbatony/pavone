"""
JavBus 元数据提取器测试

使用真实 HTML (tests/sites/javbus.html)
参考: metatube-sdk-go/provider/javbus/javbus_test.go
测试 ID: ABC-123
"""

from unittest.mock import MagicMock, patch

from pavone.plugins.metadata.javbus_metadata import JavbusMetadata


class TestJavbusMetadata:
    def setup_method(self):
        self.extractor = JavbusMetadata()

    def test_can_extract_url(self):
        assert self.extractor.can_extract("https://www.javbus.com/ja/ABC-123")

    def test_can_extract_movie_id(self):
        assert self.extractor.can_extract("ABC-123")

    def test_cannot_extract_invalid(self):
        assert not self.extractor.can_extract("https://example.com/ja/ABC-123")
        assert not self.extractor.can_extract("")
        assert not self.extractor.can_extract("12345")

    def _mock_html_response(self):
        with open("tests/sites/javbus.html", "r", encoding="utf-8") as f:
            html = f.read()
        mock = MagicMock()
        mock.status_code = 200
        mock.content = html.encode("utf-8")
        mock.text = html
        mock.raise_for_status = MagicMock()
        return mock

    def test_extract_metadata_with_mock(self):
        resp = self._mock_html_response()
        url = "https://www.javbus.com/ja/ABC-123"
        with patch.object(self.extractor, "fetch", return_value=resp):
            metadata = self.extractor.extract_metadata(url)

        assert metadata is not None
        assert metadata.code == "ABC-123"
        assert "テスト動画タイトル" in metadata.title
        assert metadata.premiered == "2023-08-15"
        assert metadata.runtime == 90
        assert "テスト花子" in metadata.actors
        assert metadata.studio == "テストメーカー"
        assert metadata.serial == "テストシリーズ"
        assert metadata.director == "テスト監督"
        assert metadata.cover is not None
        assert metadata.official_rating == "JP-18+"

    def test_extract_genres(self):
        resp = self._mock_html_response()
        url = "https://www.javbus.com/ja/ABC-123"
        with patch.object(self.extractor, "fetch", return_value=resp):
            metadata = self.extractor.extract_metadata(url)

        assert metadata is not None
        assert metadata.tags is not None
        assert "巨乳" in metadata.tags
        assert "中出し" in metadata.tags

    def test_extract_backdrops(self):
        resp = self._mock_html_response()
        url = "https://www.javbus.com/ja/ABC-123"
        with patch.object(self.extractor, "fetch", return_value=resp):
            metadata = self.extractor.extract_metadata(url)

        assert metadata is not None
        assert metadata.backdrops is not None
        assert len(metadata.backdrops) == 2

    def test_extract_label(self):
        resp = self._mock_html_response()
        url = "https://www.javbus.com/ja/ABC-123"
        with patch.object(self.extractor, "fetch", return_value=resp):
            metadata = self.extractor.extract_metadata(url)

        assert metadata is not None
        assert metadata.tagline == "テストレーベル"

    def test_extract_metadata_from_bare_id(self):
        resp = self._mock_html_response()
        with patch.object(self.extractor, "fetch", return_value=resp):
            metadata = self.extractor.extract_metadata("ABC-123")
        assert metadata is not None

    def test_extract_metadata_invalid_url(self):
        assert self.extractor.extract_metadata("https://example.com/") is None

    def test_extract_metadata_network_error(self):
        import requests

        with patch.object(self.extractor, "fetch", side_effect=requests.ConnectionError("timeout")):
            result = self.extractor.extract_metadata("https://www.javbus.com/ja/ABC-123")
        assert result is None

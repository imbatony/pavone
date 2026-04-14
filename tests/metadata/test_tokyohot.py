"""
Tokyo-Hot 元数据提取器测试

使用真实 HTML (tests/sites/tokyohot.html)
参考: metatube-sdk-go/provider/tokyo-hot/tokyo-hot_test.go
测试 ID: n1234
"""

from unittest.mock import MagicMock, patch

from pavone.plugins.metadata.tokyohot_metadata import TokyoHotMetadata


class TestTokyoHotMetadata:
    def setup_method(self):
        self.extractor = TokyoHotMetadata()

    def test_can_extract_url(self):
        assert self.extractor.can_extract("https://my.tokyo-hot.com/product/n1234/?lang=ja")

    def test_can_extract_movie_id(self):
        assert self.extractor.can_extract("n1234")
        assert self.extractor.can_extract("k5678")

    def test_cannot_extract_invalid(self):
        assert not self.extractor.can_extract("https://example.com/product/n1234/")
        assert not self.extractor.can_extract("")

    def _mock_html_response(self):
        with open("tests/sites/tokyohot.html", "r", encoding="utf-8") as f:
            html = f.read()
        mock = MagicMock()
        mock.status_code = 200
        mock.content = html.encode("utf-8")
        mock.text = html
        mock.raise_for_status = MagicMock()
        return mock

    def test_extract_metadata_with_mock(self):
        resp = self._mock_html_response()
        url = "https://my.tokyo-hot.com/product/n1234/?lang=ja"
        with patch.object(self.extractor, "fetch", return_value=resp):
            metadata = self.extractor.extract_metadata(url)

        assert metadata is not None
        assert metadata.code == "n1234"
        assert "テスト動画タイトル" in metadata.title
        assert metadata.premiered == "2024-01-10"
        assert metadata.runtime == 90
        assert "テスト花子" in metadata.actors
        assert metadata.studio == "TOKYO-HOT"
        assert metadata.serial == "テストシリーズ"
        assert metadata.cover is not None
        assert metadata.official_rating == "JP-18+"

    def test_extract_genres(self):
        resp = self._mock_html_response()
        url = "https://my.tokyo-hot.com/product/n1234/?lang=ja"
        with patch.object(self.extractor, "fetch", return_value=resp):
            metadata = self.extractor.extract_metadata(url)

        assert metadata is not None
        assert metadata.tags is not None
        assert "中出し" in metadata.tags

    def test_extract_label(self):
        resp = self._mock_html_response()
        url = "https://my.tokyo-hot.com/product/n1234/?lang=ja"
        with patch.object(self.extractor, "fetch", return_value=resp):
            metadata = self.extractor.extract_metadata(url)

        assert metadata is not None
        assert metadata.tagline == "テストレーベル"

    def test_extract_backdrops(self):
        resp = self._mock_html_response()
        url = "https://my.tokyo-hot.com/product/n1234/?lang=ja"
        with patch.object(self.extractor, "fetch", return_value=resp):
            metadata = self.extractor.extract_metadata(url)

        assert metadata is not None
        assert metadata.backdrops is not None
        assert len(metadata.backdrops) == 2

    def test_extract_metadata_from_bare_id(self):
        resp = self._mock_html_response()
        with patch.object(self.extractor, "fetch", return_value=resp):
            metadata = self.extractor.extract_metadata("n1234")
        assert metadata is not None

    def test_extract_metadata_invalid_url(self):
        assert self.extractor.extract_metadata("https://example.com/") is None

    def test_extract_metadata_network_error(self):
        import requests

        with patch.object(self.extractor, "fetch", side_effect=requests.ConnectionError("timeout")):
            result = self.extractor.extract_metadata("https://my.tokyo-hot.com/product/n1234/?lang=ja")
        assert result is None

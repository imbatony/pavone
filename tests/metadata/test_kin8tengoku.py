"""
KIN8TENGOKU 元数据提取器测试

使用真实 HTML (tests/sites/kin8tengoku.html)
参考: metatube-sdk-go/provider/kin8tengoku/kin8tengoku_test.go
测试 ID: 3891
"""

from unittest.mock import MagicMock, patch

from pavone.plugins.metadata.kin8tengoku_metadata import Kin8tengokuMetadata


class TestKin8tengokuMetadata:
    def setup_method(self):
        self.extractor = Kin8tengokuMetadata()

    def test_can_extract_url(self):
        assert self.extractor.can_extract("https://www.kin8tengoku.com/moviepages/3891/index.html")

    def test_can_extract_movie_id(self):
        assert self.extractor.can_extract("3891")
        assert self.extractor.can_extract("KIN8-3891")

    def test_cannot_extract_invalid(self):
        assert not self.extractor.can_extract("https://example.com/moviepages/3891/index.html")
        assert not self.extractor.can_extract("")
        assert not self.extractor.can_extract("12")

    def _mock_html_response(self):
        with open("tests/sites/kin8tengoku.html", "r", encoding="utf-8") as f:
            html = f.read()
        mock = MagicMock()
        mock.status_code = 200
        mock.content = html.encode("utf-8")
        mock.text = html
        mock.raise_for_status = MagicMock()
        return mock

    def test_extract_metadata_with_mock(self):
        resp = self._mock_html_response()
        url = "https://www.kin8tengoku.com/moviepages/3891/index.html"
        with patch.object(self.extractor, "fetch", return_value=resp):
            metadata = self.extractor.extract_metadata(url)

        assert metadata is not None
        assert "KIN8-3891" in metadata.code
        assert "テスト金髪動画タイトル" in metadata.title
        assert metadata.premiered == "2023-10-05"
        assert metadata.runtime == 60
        assert "テストモデル" in metadata.actors
        assert metadata.studio == "金髪天國"
        assert metadata.cover is not None
        assert metadata.official_rating == "JP-18+"

    def test_extract_genres(self):
        resp = self._mock_html_response()
        url = "https://www.kin8tengoku.com/moviepages/3891/index.html"
        with patch.object(self.extractor, "fetch", return_value=resp):
            metadata = self.extractor.extract_metadata(url)

        assert metadata is not None
        assert metadata.tags is not None
        assert "金髪" in metadata.tags

    def test_extract_summary(self):
        resp = self._mock_html_response()
        url = "https://www.kin8tengoku.com/moviepages/3891/index.html"
        with patch.object(self.extractor, "fetch", return_value=resp):
            metadata = self.extractor.extract_metadata(url)

        assert metadata is not None
        assert "テスト動画の説明" in (metadata.plot or "")

    def test_extract_backdrops(self):
        resp = self._mock_html_response()
        url = "https://www.kin8tengoku.com/moviepages/3891/index.html"
        with patch.object(self.extractor, "fetch", return_value=resp):
            metadata = self.extractor.extract_metadata(url)

        assert metadata is not None
        assert metadata.backdrops is not None
        assert len(metadata.backdrops) == 2

    def test_extract_metadata_from_bare_id(self):
        resp = self._mock_html_response()
        with patch.object(self.extractor, "fetch", return_value=resp):
            metadata = self.extractor.extract_metadata("3891")
        assert metadata is not None

    def test_extract_metadata_invalid_url(self):
        assert self.extractor.extract_metadata("https://example.com/") is None

    def test_extract_metadata_network_error(self):
        import requests

        with patch.object(self.extractor, "fetch", side_effect=requests.ConnectionError("timeout")):
            result = self.extractor.extract_metadata("https://www.kin8tengoku.com/moviepages/3891/index.html")
        assert result is None

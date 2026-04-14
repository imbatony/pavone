"""
FC2PPVDB 元数据提取器测试

使用模拟 HTML (tests/sites/fc2ppvdb.html)
参考: metatube-sdk-go/provider/fc2ppvdb/fc2ppvdb_test.go
测试 ID: 4669533
"""

from unittest.mock import MagicMock, patch

from pavone.plugins.metadata.fc2ppvdb_metadata import Fc2PpvdbMetadata


class TestFc2PpvdbMetadata:
    def setup_method(self):
        self.extractor = Fc2PpvdbMetadata()

    def test_can_extract_url(self):
        assert self.extractor.can_extract("https://fc2ppvdb.com/articles/4669533")

    def test_can_extract_movie_id(self):
        assert self.extractor.can_extract("4669533")
        assert self.extractor.can_extract("2812904")

    def test_cannot_extract_invalid(self):
        assert not self.extractor.can_extract("https://example.com/articles/123")
        assert not self.extractor.can_extract("abc")
        assert not self.extractor.can_extract("")

    def _mock_html_response(self):
        with open("tests/sites/fc2ppvdb.html", "r", encoding="utf-8") as f:
            html = f.read()
        mock = MagicMock()
        mock.status_code = 200
        mock.content = html.encode("utf-8")
        mock.text = html
        mock.raise_for_status = MagicMock()
        return mock

    def test_extract_metadata_with_mock(self):
        resp = self._mock_html_response()
        url = "https://fc2ppvdb.com/articles/4669533"
        with patch.object(self.extractor, "fetch", return_value=resp):
            metadata = self.extractor.extract_metadata(url)

        assert metadata is not None
        assert "FC2-4669533" in metadata.code
        assert "ハメ撮り" in metadata.title or "美形" in metadata.title
        assert metadata.studio == "ハメ撮り倶楽部"
        assert metadata.runtime == 65
        assert metadata.premiered == "2024-01-15"
        assert "美咲りん" in metadata.actors
        assert metadata.cover is not None
        assert metadata.official_rating == "JP-18+"

    def test_extract_metadata_invalid(self):
        assert self.extractor.extract_metadata("https://example.com/") is None

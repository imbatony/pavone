"""
Getchu 元数据提取器测试

使用真实 HTML (tests/sites/getchu.html)
参考: metatube-sdk-go/provider/getchu/getchu_test.go
测试 ID: 4018339
"""

from unittest.mock import MagicMock, patch

from pavone.plugins.metadata.getchu_metadata import GetchuMetadata


class TestGetchuMetadata:
    def setup_method(self):
        self.extractor = GetchuMetadata()

    def test_can_extract_url(self):
        assert self.extractor.can_extract("https://dl.getchu.com/i/item4018339")

    def test_can_extract_movie_id(self):
        assert self.extractor.can_extract("4018339")
        assert self.extractor.can_extract("GETCHU-4018339")

    def test_cannot_extract_invalid(self):
        assert not self.extractor.can_extract("https://example.com/item4018339")
        assert not self.extractor.can_extract("abc")
        assert not self.extractor.can_extract("")

    def _mock_html_response(self):
        with open("tests/sites/getchu.html", "r", encoding="utf-8") as f:
            html = f.read()
        mock = MagicMock()
        mock.status_code = 200
        mock.content = html.encode("utf-8")
        mock.text = html
        mock.raise_for_status = MagicMock()
        return mock

    def test_extract_metadata_with_mock(self):
        resp = self._mock_html_response()
        url = "https://dl.getchu.com/i/item4018339"
        with patch.object(self.extractor, "fetch", return_value=resp):
            metadata = self.extractor.extract_metadata(url)

        assert metadata is not None
        assert "GETCHU-4018339" in metadata.code
        assert "猫耳コス" in metadata.title or "S級美少女" in metadata.title
        assert metadata.studio == "NAGOYAか円光"
        assert metadata.premiered == "2019-06-03"
        assert metadata.cover is not None
        assert "getchu.com" in metadata.cover
        assert metadata.official_rating == "JP-18+"

    def test_extract_tags(self):
        resp = self._mock_html_response()
        url = "https://dl.getchu.com/i/item4018339"
        with patch.object(self.extractor, "fetch", return_value=resp):
            metadata = self.extractor.extract_metadata(url)
        assert metadata is not None
        assert metadata.tags is not None
        assert len(metadata.tags) > 0

    def test_extract_metadata_from_id(self):
        resp = self._mock_html_response()
        with patch.object(self.extractor, "fetch", return_value=resp):
            metadata = self.extractor.extract_metadata("4018339")
        assert metadata is not None

    def test_extract_metadata_invalid(self):
        assert self.extractor.extract_metadata("https://example.com/") is None

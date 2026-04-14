"""
H4610 元数据提取器测试

使用真实 HTML (tests/sites/h4610.html)
参考: metatube-sdk-go/provider/h4610/h4610_test.go
测试 ID: tk0047
"""

from unittest.mock import MagicMock, patch

from pavone.plugins.metadata.h4610_metadata import H4610Metadata


class TestH4610Metadata:
    def setup_method(self):
        self.extractor = H4610Metadata()

    def test_can_extract_url(self):
        assert self.extractor.can_extract("https://www.h4610.com/moviepages/tk0047/index.html")

    def test_can_extract_movie_id(self):
        assert self.extractor.can_extract("tk0047")
        assert self.extractor.can_extract("h4610-tk0047")

    def test_cannot_extract_invalid(self):
        assert not self.extractor.can_extract("https://example.com/moviepages/tk0047/index.html")
        assert not self.extractor.can_extract("")
        assert not self.extractor.can_extract("SDMT-415")

    def _mock_html_response(self):
        with open("tests/sites/h4610.html", "r", encoding="utf-8") as f:
            html = f.read()
        mock = MagicMock()
        mock.status_code = 200
        mock.content = html.encode("utf-8")
        mock.text = html
        mock.raise_for_status = MagicMock()
        return mock

    def test_extract_metadata_with_mock(self):
        resp = self._mock_html_response()
        url = "https://www.h4610.com/moviepages/tk0047/index.html"
        with patch.object(self.extractor, "fetch", return_value=resp):
            metadata = self.extractor.extract_metadata(url)

        assert metadata is not None
        assert "tk0047" in metadata.code
        assert "菊名 美羅" in metadata.title or "菊名" in metadata.title
        assert metadata.runtime == 63  # PT01H03M29S
        assert metadata.premiered == "2021-11-20"
        assert metadata.studio == "エッチな4610"
        assert metadata.cover is not None
        assert "h4610.com" in metadata.cover
        assert metadata.official_rating == "JP-18+"

    def test_extract_actors(self):
        resp = self._mock_html_response()
        url = "https://www.h4610.com/moviepages/tk0047/index.html"
        with patch.object(self.extractor, "fetch", return_value=resp):
            metadata = self.extractor.extract_metadata(url)
        assert metadata is not None
        assert metadata.actors is not None
        assert "菊名 美羅" in metadata.actors

    def test_extract_metadata_from_id(self):
        resp = self._mock_html_response()
        with patch.object(self.extractor, "fetch", return_value=resp):
            metadata = self.extractor.extract_metadata("tk0047")
        assert metadata is not None
        assert "tk0047" in metadata.code

    def test_extract_metadata_invalid(self):
        assert self.extractor.extract_metadata("https://example.com/") is None

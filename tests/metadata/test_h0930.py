"""
H0930 元数据提取器测试

使用真实 HTML (tests/sites/h0930.html)
参考: metatube-sdk-go/provider/h0930/h0930_test.go
测试 ID: ori1643
"""

from unittest.mock import MagicMock, patch

from pavone.plugins.metadata.h0930_metadata import H0930Metadata


class TestH0930Metadata:
    def setup_method(self):
        self.extractor = H0930Metadata()

    def test_can_extract_url(self):
        assert self.extractor.can_extract("https://www.h0930.com/moviepages/ori1643/index.html")

    def test_can_extract_movie_id(self):
        assert self.extractor.can_extract("ori1643")
        assert self.extractor.can_extract("h0930-ori1643")

    def test_cannot_extract_invalid(self):
        assert not self.extractor.can_extract("https://example.com/moviepages/ori1643/index.html")
        assert not self.extractor.can_extract("")
        assert not self.extractor.can_extract("SDMT-415")

    def _mock_html_response(self):
        with open("tests/sites/h0930.html", "r", encoding="utf-8") as f:
            html = f.read()
        mock = MagicMock()
        mock.status_code = 200
        mock.content = html.encode("utf-8")
        mock.text = html
        mock.raise_for_status = MagicMock()
        return mock

    def test_extract_metadata_with_mock(self):
        resp = self._mock_html_response()
        url = "https://www.h0930.com/moviepages/ori1643/index.html"
        with patch.object(self.extractor, "fetch", return_value=resp):
            metadata = self.extractor.extract_metadata(url)

        assert metadata is not None
        assert "ori1643" in metadata.code
        assert "片嶋 藍香" in metadata.title or "片嶋" in metadata.title
        assert metadata.runtime == 57  # PT00H57M26S
        assert metadata.premiered == "2022-09-17"
        assert metadata.studio == "エッチな0930"
        assert metadata.cover is not None
        assert "h0930.com" in metadata.cover
        assert metadata.official_rating == "JP-18+"

    def test_extract_actors(self):
        resp = self._mock_html_response()
        url = "https://www.h0930.com/moviepages/ori1643/index.html"
        with patch.object(self.extractor, "fetch", return_value=resp):
            metadata = self.extractor.extract_metadata(url)
        assert metadata is not None
        assert metadata.actors is not None
        assert "片嶋 藍香" in metadata.actors

    def test_extract_metadata_from_id(self):
        resp = self._mock_html_response()
        with patch.object(self.extractor, "fetch", return_value=resp):
            metadata = self.extractor.extract_metadata("ori1643")
        assert metadata is not None
        assert "ori1643" in metadata.code

    def test_extract_metadata_invalid(self):
        assert self.extractor.extract_metadata("https://example.com/") is None

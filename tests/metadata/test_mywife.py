"""
MyWife 元数据提取器测试

使用真实 HTML (tests/sites/mywife.html)
参考: metatube-sdk-go/provider/mywife/mywife_test.go
测试 ID: 1234
"""

from unittest.mock import MagicMock, patch

from pavone.plugins.metadata.mywife_metadata import MyWifeMetadata


class TestMyWifeMetadata:
    def setup_method(self):
        self.extractor = MyWifeMetadata()

    def test_can_extract_url(self):
        assert self.extractor.can_extract("https://mywife.cc/teigaku/model/no/1234")

    def test_can_extract_movie_id(self):
        assert self.extractor.can_extract("1234")
        assert self.extractor.can_extract("MYWIFE-1234")

    def test_cannot_extract_invalid(self):
        assert not self.extractor.can_extract("https://example.com/teigaku/model/no/1234")
        assert not self.extractor.can_extract("")
        assert not self.extractor.can_extract("ABC-123")

    def _mock_html_response(self):
        with open("tests/sites/mywife.html", "r", encoding="utf-8") as f:
            html = f.read()
        mock = MagicMock()
        mock.status_code = 200
        mock.content = html.encode("utf-8")
        mock.text = html
        mock.raise_for_status = MagicMock()
        return mock

    def test_extract_metadata_with_mock(self):
        resp = self._mock_html_response()
        url = "https://mywife.cc/teigaku/model/no/1234"
        with patch.object(self.extractor, "fetch", return_value=resp):
            metadata = self.extractor.extract_metadata(url)

        assert metadata is not None
        assert "MYWIFE-1234" in metadata.code
        assert metadata.studio == "舞ワイフ"
        assert metadata.cover is not None
        assert "topview.jpg" in metadata.cover
        assert metadata.official_rating == "JP-18+"

    def test_extract_backdrops(self):
        resp = self._mock_html_response()
        url = "https://mywife.cc/teigaku/model/no/1234"
        with patch.object(self.extractor, "fetch", return_value=resp):
            metadata = self.extractor.extract_metadata(url)

        assert metadata is not None
        assert metadata.backdrops is not None
        assert len(metadata.backdrops) == 2

    def test_extract_metadata_from_bare_id(self):
        resp = self._mock_html_response()
        with patch.object(self.extractor, "fetch", return_value=resp):
            metadata = self.extractor.extract_metadata("1234")
        assert metadata is not None

    def test_extract_metadata_invalid_url(self):
        assert self.extractor.extract_metadata("https://example.com/") is None

    def test_extract_metadata_network_error(self):
        import requests

        with patch.object(self.extractor, "fetch", side_effect=requests.ConnectionError("timeout")):
            result = self.extractor.extract_metadata("https://mywife.cc/teigaku/model/no/1234")
        assert result is None

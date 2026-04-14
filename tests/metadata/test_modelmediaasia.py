"""
ModelMediaAsia 元数据提取器测试

使用 Mock JSON API 响应
参考: metatube-sdk-go/provider/modelmediaasia/modelmediaasia_test.go
测试 ID: mdx-0236
"""

from unittest.mock import MagicMock, patch

from pavone.plugins.metadata.modelmediaasia_metadata import ModelMediaAsiaMetadata


class TestModelMediaAsiaMetadata:
    def setup_method(self):
        self.extractor = ModelMediaAsiaMetadata()

    def test_can_extract_url(self):
        assert self.extractor.can_extract("https://modelmediaasia.com/zh-CN/videos/mdx-0236")

    def test_can_extract_movie_id(self):
        assert self.extractor.can_extract("mdx-0236")

    def test_cannot_extract_invalid(self):
        assert not self.extractor.can_extract("https://example.com/videos/mdx-0236")
        assert not self.extractor.can_extract("")

    def _mock_json_response(self):
        mock = MagicMock()
        mock.status_code = 200
        mock.json.return_value = {
            "data": {
                "serial_number": "MDX-0236",
                "title_cn": "测试视频标题",
                "description_cn": "测试视频描述",
                "cover": "https://modelmediaasia.com/images/cover.jpg",
                "published_at": 1672531200000,
                "tags": [{"name_cn": "剧情"}, {"name_cn": "制服"}],
                "models": [{"name_cn": "测试演员"}],
            }
        }
        mock.raise_for_status = MagicMock()
        return mock

    def test_extract_metadata_with_mock(self):
        resp = self._mock_json_response()
        with patch.object(self.extractor, "fetch", return_value=resp):
            metadata = self.extractor.extract_metadata("https://modelmediaasia.com/zh-CN/videos/mdx-0236")

        assert metadata is not None
        assert metadata.code == "MDX-0236"
        assert "测试视频标题" in metadata.title
        assert "测试演员" in metadata.actors
        assert metadata.studio == "麻豆傳媒映畫"
        assert metadata.cover is not None
        assert metadata.official_rating == "JP-18+"

    def test_extract_metadata_from_bare_id(self):
        resp = self._mock_json_response()
        with patch.object(self.extractor, "fetch", return_value=resp):
            metadata = self.extractor.extract_metadata("mdx-0236")
        assert metadata is not None

    def test_extract_metadata_invalid_url(self):
        assert self.extractor.extract_metadata("https://example.com/") is None

    def test_extract_metadata_network_error(self):
        import requests

        with patch.object(self.extractor, "fetch", side_effect=requests.ConnectionError("timeout")):
            result = self.extractor.extract_metadata("https://modelmediaasia.com/zh-CN/videos/mdx-0236")
        assert result is None

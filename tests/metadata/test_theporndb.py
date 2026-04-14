"""
ThePornDB 元数据提取器测试

使用 Mock JSON API 响应
参考: metatube-sdk-go/provider/theporndb/theporndb_test.go
测试 slug: test-scene-slug
"""

from unittest.mock import MagicMock, patch

from pavone.plugins.metadata.theporndb_metadata import ThePorndbMetadata


class TestThePorndbMetadata:
    def setup_method(self):
        self.extractor = ThePorndbMetadata()
        self.extractor._access_token = "test-api-token-123"

    def test_can_extract_url(self):
        assert self.extractor.can_extract("https://theporndb.net/scenes/test-scene-slug")

    def test_can_extract_movie_id(self):
        assert self.extractor.can_extract("test-scene-slug")

    def test_cannot_extract_invalid(self):
        assert not self.extractor.can_extract("https://example.com/scenes/test-scene-slug")
        assert not self.extractor.can_extract("")

    def _mock_json_response(self):
        mock = MagicMock()
        mock.status_code = 200
        mock.json.return_value = {
            "data": {
                "slug": "test-scene-slug",
                "title": "Test Scene Title",
                "description": "This is a test scene description.",
                "image": "https://theporndb.net/images/cover.jpg",
                "poster": "https://theporndb.net/images/poster.jpg",
                "rating": 8.5,
                "date": "2024-01-15",
                "duration": 45,
                "site": {"name": "Test Studio"},
                "tags": [{"name": "Anal"}, {"name": "Threesome"}],
                "performers": [{"name": "Test Actor 1"}, {"name": "Test Actor 2"}],
                "directors": [{"name": "Test Director"}],
                "trailer": "https://theporndb.net/videos/trailer.mp4",
            }
        }
        mock.raise_for_status = MagicMock()
        return mock

    def test_extract_metadata_with_mock(self):
        resp = self._mock_json_response()
        with patch.object(self.extractor, "fetch", return_value=resp):
            metadata = self.extractor.extract_metadata("https://theporndb.net/scenes/test-scene-slug")

        assert metadata is not None
        assert "test-scene-slug" in metadata.code
        assert "Test Scene Title" in metadata.title
        assert "Test Actor 1" in metadata.actors
        assert metadata.studio == "Test Studio"
        assert metadata.director == "Test Director"
        assert metadata.rating == 8.5
        assert metadata.runtime == 45
        assert metadata.premiered == "2024-01-15"
        assert metadata.trailer == "https://theporndb.net/videos/trailer.mp4"

    def test_extract_genres(self):
        resp = self._mock_json_response()
        with patch.object(self.extractor, "fetch", return_value=resp):
            metadata = self.extractor.extract_metadata("test-scene-slug")

        assert metadata is not None
        assert "Anal" in metadata.tags

    def test_no_token_returns_none(self):
        extractor_no_token = ThePorndbMetadata()
        extractor_no_token._access_token = None
        result = extractor_no_token.extract_metadata("test-scene-slug")
        assert result is None

    def test_extract_metadata_invalid_url(self):
        assert self.extractor.extract_metadata("https://example.com/") is None

    def test_extract_metadata_network_error(self):
        import requests

        with patch.object(self.extractor, "fetch", side_effect=requests.ConnectionError("timeout")):
            result = self.extractor.extract_metadata("https://theporndb.net/scenes/test-scene-slug")
        assert result is None

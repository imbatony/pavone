"""
MuraMura 元数据提取器测试

使用 Mock JSON API 响应
参考: metatube-sdk-go/provider/muramura/muramura_test.go
测试 ID: 011215_178
"""

from unittest.mock import MagicMock, patch

from pavone.plugins.metadata.muramura_metadata import MuramuraMetadata


class TestMuramuraMetadata:
    def setup_method(self):
        self.extractor = MuramuraMetadata()

    def test_can_extract_url(self):
        assert self.extractor.can_extract("https://www.muramura.tv/movies/011215_178/")

    def test_can_extract_movie_id(self):
        assert self.extractor.can_extract("011215_178")

    def test_cannot_extract_invalid(self):
        assert not self.extractor.can_extract("https://example.com/movies/011215_178/")
        assert not self.extractor.can_extract("")
        assert not self.extractor.can_extract("ABC-123")

    def _mock_json_response(self):
        mock = MagicMock()
        mock.status_code = 200
        mock.json.return_value = {
            "Title": "テスト動画タイトル",
            "ActressesJa": ["テスト花子"],
            "UCNAME": ["素人", "フェラ"],
            "Desc": "テスト動画の説明です。",
            "Release": "2015-01-12",
            "Duration": 3600,
            "AvgRating": 4.0,
            "ThumbUltra": "https://www.muramura.tv/images/thumb_ultra.jpg",
            "MovieThumb": "https://www.muramura.tv/images/movie_thumb.jpg",
        }
        mock.raise_for_status = MagicMock()
        return mock

    def test_extract_metadata_with_mock(self):
        resp = self._mock_json_response()
        with patch.object(self.extractor, "fetch", return_value=resp):
            metadata = self.extractor.extract_metadata("https://www.muramura.tv/movies/011215_178/")

        assert metadata is not None
        assert "011215_178" in metadata.code
        assert "テスト動画タイトル" in metadata.title
        assert "テスト花子" in metadata.actors
        assert metadata.studio == "ムラムラってくる素人"
        assert metadata.runtime == 60
        assert metadata.rating == 8.0
        assert metadata.cover is not None
        assert metadata.official_rating == "JP-18+"

    def test_extract_metadata_from_bare_id(self):
        resp = self._mock_json_response()
        with patch.object(self.extractor, "fetch", return_value=resp):
            metadata = self.extractor.extract_metadata("011215_178")
        assert metadata is not None

    def test_extract_metadata_invalid_url(self):
        assert self.extractor.extract_metadata("https://example.com/") is None

    def test_extract_metadata_network_error(self):
        import requests

        with patch.object(self.extractor, "fetch", side_effect=requests.ConnectionError("timeout")):
            result = self.extractor.extract_metadata("https://www.muramura.tv/movies/011215_178/")
        assert result is None

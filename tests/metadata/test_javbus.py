"""
JavBus 元数据提取器测试

使用真实 HTML (tests/sites/javbus.html)
参考: metatube-sdk-go/provider/javbus/javbus_test.go
测试 ID: ABC-123
"""

from unittest.mock import MagicMock, patch

from pavone.plugins.metadata.javbus_metadata import JavbusMetadata


class TestJavbusMetadata:
    def setup_method(self):
        self.extractor = JavbusMetadata()

    def test_can_extract_url(self):
        assert self.extractor.can_extract("https://www.javbus.com/ja/ABC-123")

    def test_can_extract_movie_id(self):
        assert self.extractor.can_extract("ABC-123")

    def test_can_extract_movie_id_no_hyphen(self):
        """无连字符的品番码也应匹配 (如 N0970, HEYZO0993)"""
        assert self.extractor.can_extract("N0970")
        assert self.extractor.can_extract("n0970")
        assert self.extractor.can_extract("HEYZO0993")
        assert self.extractor.can_extract("GACHI918")

    def test_cannot_extract_invalid(self):
        assert not self.extractor.can_extract("https://example.com/ja/ABC-123")
        assert not self.extractor.can_extract("")
        assert not self.extractor.can_extract("12345")

    def _mock_html_response(self):
        with open("tests/sites/javbus.html", "r", encoding="utf-8") as f:
            html = f.read()
        mock = MagicMock()
        mock.status_code = 200
        mock.content = html.encode("utf-8")
        mock.text = html
        mock.raise_for_status = MagicMock()
        return mock

    def test_extract_metadata_with_mock(self):
        resp = self._mock_html_response()
        url = "https://www.javbus.com/ja/ABC-123"
        with patch.object(self.extractor, "fetch", return_value=resp):
            metadata = self.extractor.extract_metadata(url)

        assert metadata is not None
        assert metadata.code == "ABC-123"
        assert "テスト動画タイトル" in metadata.title
        # 标题不应包含 "JavBus" 后缀
        assert "JavBus" not in metadata.title
        assert metadata.premiered == "2023-08-15"
        assert metadata.runtime == 90
        assert "テスト花子" in metadata.actors
        assert metadata.studio == "テストメーカー"
        assert metadata.serial == "テストシリーズ"
        assert metadata.director == "テスト監督"
        assert metadata.cover is not None
        assert metadata.official_rating == "JP-18+"

    def test_extract_genres(self):
        resp = self._mock_html_response()
        url = "https://www.javbus.com/ja/ABC-123"
        with patch.object(self.extractor, "fetch", return_value=resp):
            metadata = self.extractor.extract_metadata(url)

        assert metadata is not None
        # tags 和 genres 都应包含相同数据
        assert metadata.tags is not None
        assert "巨乳" in metadata.tags
        assert "中出し" in metadata.tags
        assert metadata.genres is not None
        assert "巨乳" in metadata.genres
        assert "中出し" in metadata.genres

    def test_extract_backdrops(self):
        resp = self._mock_html_response()
        url = "https://www.javbus.com/ja/ABC-123"
        with patch.object(self.extractor, "fetch", return_value=resp):
            metadata = self.extractor.extract_metadata(url)

        assert metadata is not None
        assert metadata.backdrops is not None
        assert len(metadata.backdrops) == 2
        # 第一张预览图应作为主 backdrop
        assert metadata.backdrop == metadata.backdrops[0]

    def test_extract_label(self):
        resp = self._mock_html_response()
        url = "https://www.javbus.com/ja/ABC-123"
        with patch.object(self.extractor, "fetch", return_value=resp):
            metadata = self.extractor.extract_metadata(url)

        assert metadata is not None
        assert metadata.tagline == "テストレーベル"

    def test_extract_thumbnail_from_cover(self):
        """缩略图应从封面 URL 推导 (/cover/xxx_b.jpg → /thumbs/xxx.jpg)"""
        resp = self._mock_html_response()
        url = "https://www.javbus.com/ja/ABC-123"
        with patch.object(self.extractor, "fetch", return_value=resp):
            metadata = self.extractor.extract_metadata(url)

        assert metadata is not None
        assert metadata.thumbnail is not None
        assert "/thumbs/" in metadata.thumbnail
        assert metadata.thumbnail == "https://www.javbus.com/pics/thumbs/475i.jpg"

    def test_extract_poster(self):
        """poster 应设为推导后的缩略图 URL"""
        resp = self._mock_html_response()
        url = "https://www.javbus.com/ja/ABC-123"
        with patch.object(self.extractor, "fetch", return_value=resp):
            metadata = self.extractor.extract_metadata(url)

        assert metadata is not None
        assert metadata.poster is not None
        assert "/thumbs/" in metadata.poster

    def test_derive_thumb_url(self):
        """封面 URL → 缩略图 URL 的转换"""
        assert (
            JavbusMetadata._derive_thumb_url("https://www.javbus.com/pics/cover/475i_b.jpg")
            == "https://www.javbus.com/pics/thumbs/475i.jpg"
        )
        assert (
            JavbusMetadata._derive_thumb_url("https://www.javbus.com/imgs/cover/cnw_b.jpg")
            == "https://www.javbus.com/imgs/thumbs/cnw.jpg"
        )
        assert (
            JavbusMetadata._derive_thumb_url("https://www.javbus.com/pics/cover/475i.png")
            == "https://www.javbus.com/pics/thumbs/475i.png"
        )
        assert JavbusMetadata._derive_thumb_url("https://example.com/other/path.jpg") is None

    def test_extract_metadata_from_bare_id(self):
        resp = self._mock_html_response()
        with patch.object(self.extractor, "fetch", return_value=resp):
            metadata = self.extractor.extract_metadata("ABC-123")
        assert metadata is not None

    def test_extract_metadata_from_bare_id_no_hyphen(self):
        """无连字符品番也能正常提取"""
        resp = self._mock_html_response()
        with patch.object(self.extractor, "fetch", return_value=resp):
            metadata = self.extractor.extract_metadata("N0970")
        assert metadata is not None

    def test_extract_metadata_invalid_url(self):
        assert self.extractor.extract_metadata("https://example.com/") is None

    def test_extract_metadata_network_error(self):
        import requests

        with patch.object(self.extractor, "fetch", side_effect=requests.ConnectionError("timeout")):
            result = self.extractor.extract_metadata("https://www.javbus.com/ja/ABC-123")
        assert result is None

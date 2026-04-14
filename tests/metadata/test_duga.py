"""
DUGA 元数据提取器测试

使用真实 HTML (tests/sites/duga.html)
参考: metatube-sdk-go/provider/duga/duga_test.go
测试 ID: waap-1294
"""

from unittest.mock import MagicMock, patch

from pavone.plugins.metadata.duga_metadata import DugaMetadata


class TestDugaMetadata:
    """测试 DugaMetadata 提取器"""

    def setup_method(self):
        self.extractor = DugaMetadata()

    # ===================== can_extract 测试 =====================

    def test_can_extract_url(self):
        assert self.extractor.can_extract("https://duga.jp/ppv/waap-1294/")
        assert self.extractor.can_extract("https://duga.jp/ppv/glory-4262/")

    def test_can_extract_movie_id(self):
        assert self.extractor.can_extract("waap-1294")
        assert self.extractor.can_extract("glory-4262")

    def test_cannot_extract_invalid(self):
        assert not self.extractor.can_extract("https://example.com/ppv/waap-1294/")
        assert not self.extractor.can_extract("")

    # ===================== extract_metadata mock 测试 =====================

    def _mock_html_response(self):
        with open("tests/sites/duga.html", "r", encoding="utf-8") as f:
            html = f.read()
        mock = MagicMock()
        mock.status_code = 200
        mock.content = html.encode("utf-8")
        mock.text = html
        mock.raise_for_status = MagicMock()
        return mock

    def test_extract_metadata_with_mock(self):
        """测试 extract_metadata（使用mock模拟网络请求，真实HTML数据）"""
        resp = self._mock_html_response()
        url = "https://duga.jp/ppv/waap-1294/"
        with patch.object(self.extractor, "fetch", return_value=resp):
            metadata = self.extractor.extract_metadata(url)

        assert metadata is not None
        assert "AIリマスター" in metadata.title
        assert metadata.studio == "ワープエンタテインメント"
        assert metadata.runtime == 125  # "125分29秒" → 125
        assert metadata.premiered == "2022-04-22"
        assert metadata.serial == "AIリマスター"
        assert "希内あんな" in metadata.actors
        assert metadata.cover is not None
        assert "duga.jp" in metadata.cover or "pic.duga.jp" in metadata.cover
        assert metadata.official_rating == "JP-18+"

    def test_extract_director(self):
        """测试监督提取"""
        resp = self._mock_html_response()
        url = "https://duga.jp/ppv/waap-1294/"
        with patch.object(self.extractor, "fetch", return_value=resp):
            metadata = self.extractor.extract_metadata(url)

        assert metadata is not None
        assert metadata.director == "金田一小五郎"

    def test_extract_genres(self):
        """测试类别提取"""
        resp = self._mock_html_response()
        url = "https://duga.jp/ppv/waap-1294/"
        with patch.object(self.extractor, "fetch", return_value=resp):
            metadata = self.extractor.extract_metadata(url)

        assert metadata is not None
        assert metadata.tags is not None
        assert "アナル" in metadata.tags

    def test_extract_backdrops(self):
        """测试预览图提取"""
        resp = self._mock_html_response()
        url = "https://duga.jp/ppv/waap-1294/"
        with patch.object(self.extractor, "fetch", return_value=resp):
            metadata = self.extractor.extract_metadata(url)

        assert metadata is not None
        assert metadata.backdrops is not None
        assert len(metadata.backdrops) == 10

    def test_extract_code(self):
        """测试品番码提取"""
        resp = self._mock_html_response()
        url = "https://duga.jp/ppv/waap-1294/"
        with patch.object(self.extractor, "fetch", return_value=resp):
            metadata = self.extractor.extract_metadata(url)

        assert metadata is not None
        # code 应该是 RECEN-012（メーカー品番）或 waap-1294（作品ID）
        assert metadata.code in ("RECEN-012", "waap-1294")

    def test_extract_metadata_from_bare_id(self):
        """测试从裸 ID 提取"""
        resp = self._mock_html_response()
        with patch.object(self.extractor, "fetch", return_value=resp):
            metadata = self.extractor.extract_metadata("waap-1294")

        assert metadata is not None
        assert "AIリマスター" in metadata.title

    def test_extract_metadata_invalid_url(self):
        """无效URL返回None"""
        assert self.extractor.extract_metadata("https://example.com/") is None

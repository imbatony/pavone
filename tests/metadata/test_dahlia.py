"""
DAHLIA 元数据提取器测试

使用真实 HTML (tests/sites/dahlia.html)
参考: metatube-sdk-go/provider/dahlia/dahlia_test.go
测试 ID: dldss339
"""

from unittest.mock import MagicMock, patch

from pavone.plugins.metadata.dahlia_metadata import DahliaMetadata


class TestDahliaMetadata:
    """测试 DahliaMetadata 提取器"""

    def setup_method(self):
        self.extractor = DahliaMetadata()

    # ===================== can_extract 测试 =====================

    def test_can_extract_url(self):
        assert self.extractor.can_extract("https://dahlia-av.jp/works/dldss339/")
        assert self.extractor.can_extract("https://dahlia-av.jp/works/DLDSS327/")

    def test_cannot_extract_bare_id(self):
        """DAHLIA 只支持 URL，不支持裸 ID"""
        assert not self.extractor.can_extract("dldss339")

    def test_cannot_extract_invalid(self):
        assert not self.extractor.can_extract("https://example.com/works/dldss339/")
        assert not self.extractor.can_extract("")

    # ===================== extract_metadata mock 测试 =====================

    def _mock_html_response(self):
        with open("tests/sites/dahlia.html", "r", encoding="utf-8") as f:
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
        url = "https://dahlia-av.jp/works/dldss339/"
        with patch.object(self.extractor, "fetch", return_value=resp):
            metadata = self.extractor.extract_metadata(url)

        assert metadata is not None
        assert "dldss339" in metadata.code
        assert "峰玲子" in metadata.title or "DLDSS-339" in metadata.title
        assert metadata.runtime == 120
        assert metadata.premiered == "2024-07-27"
        assert "峰玲子" in metadata.actors
        assert metadata.studio == "DAHLIA"
        assert metadata.cover is not None
        assert "faleno.net" in metadata.cover or "dahlia" in metadata.cover
        assert metadata.official_rating == "JP-18+"

    def test_extract_backdrops(self):
        """测试预览图提取"""
        resp = self._mock_html_response()
        url = "https://dahlia-av.jp/works/dldss339/"
        with patch.object(self.extractor, "fetch", return_value=resp):
            metadata = self.extractor.extract_metadata(url)

        assert metadata is not None
        assert metadata.backdrops is not None
        assert len(metadata.backdrops) == 10

    def test_extract_plot(self):
        """测试简介提取"""
        resp = self._mock_html_response()
        url = "https://dahlia-av.jp/works/dldss339/"
        with patch.object(self.extractor, "fetch", return_value=resp):
            metadata = self.extractor.extract_metadata(url)

        assert metadata is not None
        assert metadata.plot is not None
        assert len(metadata.plot) > 20

    def test_extract_metadata_invalid_url(self):
        """无效URL返回None"""
        assert self.extractor.extract_metadata("https://example.com/") is None

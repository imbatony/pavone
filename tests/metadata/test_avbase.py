"""
AVBASE 元数据提取器测试

使用模拟 __NEXT_DATA__ 页面 (tests/sites/avbase.html)
参考: metatube-sdk-go/provider/avbase/avbase_test.go
测试 ID: SSIS-354
"""

from unittest.mock import MagicMock, patch

from pavone.plugins.metadata.avbase_metadata import AvBaseMetadata


class TestAvBaseMetadata:
    """测试 AvBaseMetadata 提取器"""

    def setup_method(self):
        self.extractor = AvBaseMetadata()

    # ===================== can_extract 测试 =====================

    def test_can_extract_url(self):
        assert self.extractor.can_extract("https://www.avbase.net/works/SSIS-354")
        assert self.extractor.can_extract("https://avbase.net/works/prestige:ABP-588")

    def test_can_extract_movie_id(self):
        assert self.extractor.can_extract("SSIS-354")
        assert self.extractor.can_extract("prestige:ABP-588")
        assert self.extractor.can_extract("tameike:MEYD-856")

    def test_cannot_extract_invalid(self):
        assert not self.extractor.can_extract("https://example.com/works/SSIS-354")
        assert not self.extractor.can_extract("")

    # ===================== extract_metadata mock 测试 =====================

    def _mock_html_response(self, filepath):
        with open(filepath, "r", encoding="utf-8") as f:
            html = f.read()
        mock = MagicMock()
        mock.status_code = 200
        mock.content = html.encode("utf-8")
        mock.text = html
        mock.raise_for_status = MagicMock()
        return mock

    def _mock_json_from_html(self, filepath):
        """从 HTML 中提取 __NEXT_DATA__ 并返回 JSON mock response"""
        import json

        from bs4 import BeautifulSoup

        with open(filepath, "r", encoding="utf-8") as f:
            html = f.read()
        soup = BeautifulSoup(html, "lxml")
        script = soup.find("script", id="__NEXT_DATA__")
        data = json.loads(script.string)
        page_props = data.get("props", {}).get("pageProps", {})

        mock = MagicMock()
        mock.status_code = 200
        mock.json = MagicMock(return_value=page_props)
        mock.raise_for_status = MagicMock()
        return mock

    def test_extract_metadata_via_html_fallback(self):
        """测试当 buildId 获取失败时，通过 HTML __NEXT_DATA__ 回退提取元数据"""
        self.extractor._build_id = None

        page_resp = self._mock_html_response("tests/sites/avbase.html")

        def side_effect(url, **kwargs):
            if "avbase.net/" == url.rstrip("/").split("//")[-1]:
                # 首页请求失败 → _get_build_id 返回 None → 走 fallback
                raise Exception("Simulated homepage fetch failure")
            return page_resp

        with patch.object(self.extractor, "fetch", side_effect=side_effect):
            metadata = self.extractor.extract_metadata("https://www.avbase.net/works/SSIS-354")

        assert metadata is not None
        assert "星宮一花" in metadata.title or "SSIS-354" in metadata.title
        assert metadata.studio == "S1 NO.1 STYLE"
        assert metadata.runtime == 150
        assert metadata.premiered == "2021-12-07"
        assert "星宮一花" in metadata.actors
        assert "巨乳" in metadata.tags
        assert metadata.cover is not None
        assert metadata.official_rating == "JP-18+"

    def test_extract_metadata_via_api(self):
        """测试通过 Next.js API 提取元数据"""
        self.extractor._build_id = "test-build-id"

        import json

        from bs4 import BeautifulSoup

        with open("tests/sites/avbase.html", "r", encoding="utf-8") as f:
            html = f.read()
        soup = BeautifulSoup(html, "lxml")
        script = soup.find("script", id="__NEXT_DATA__")
        data = json.loads(script.string)
        page_props = data.get("props", {}).get("pageProps", {})

        api_resp = MagicMock()
        api_resp.status_code = 200
        api_resp.json = MagicMock(return_value={"pageProps": page_props})
        api_resp.raise_for_status = MagicMock()

        with patch.object(self.extractor, "fetch", return_value=api_resp):
            metadata = self.extractor.extract_metadata("https://www.avbase.net/works/SSIS-354")

        assert metadata is not None
        assert metadata.code == "SSIS-354"
        assert "星宮一花" in metadata.actors
        assert len(metadata.backdrops) == 2

    def test_extract_metadata_invalid_url(self):
        """无效URL返回None"""
        metadata = self.extractor.extract_metadata("https://example.com/works/X")
        assert metadata is None

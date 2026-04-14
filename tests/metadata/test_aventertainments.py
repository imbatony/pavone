"""
AVEntertainments 元数据提取器测试

使用真实 HTML (tests/sites/aventertainments.html)
参考: metatube-sdk-go/provider/aventertainments/aventertainments_test.go
测试 ID: 142802 (product_id)
"""

from unittest.mock import MagicMock, patch

from pavone.plugins.metadata.aventertainments_metadata import AvEntertainmentsMetadata


class TestAvEntertainmentsMetadata:
    """测试 AvEntertainmentsMetadata 提取器"""

    def setup_method(self):
        self.extractor = AvEntertainmentsMetadata()

    # ===================== can_extract 测试 =====================

    def test_can_extract_url(self):
        assert self.extractor.can_extract(
            "https://www.aventertainments.com/product_lists.aspx?product_id=142802&languageID=2&dept_id=29"
        )
        assert self.extractor.can_extract("https://www.aventertainments.com/dvd/detail?pro=4319&lang=2&culture=ja-JP&cat=29")

    def test_cannot_extract_invalid(self):
        assert not self.extractor.can_extract("https://example.com/product?pro=123")
        assert not self.extractor.can_extract("")
        assert not self.extractor.can_extract("invalid")

    # ===================== extract_metadata mock 测试 =====================

    def _mock_html_response(self):
        with open("tests/sites/aventertainments.html", "r", encoding="utf-8") as f:
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
        url = "https://www.aventertainments.com/product_lists.aspx?product_id=142802&languageID=2&dept_id=29"
        with patch.object(self.extractor, "fetch", return_value=resp):
            metadata = self.extractor.extract_metadata(url)

        assert metadata is not None
        assert "CATCHEYE" in metadata.title
        assert "上原ゆあ" in metadata.actors
        assert metadata.runtime == 122  # "Apx. 122 Min."
        assert metadata.premiered == "2022-09-15"  # "09/15/2022"
        assert metadata.studio == "CATCHEYE"
        assert metadata.code == "DRC-217"
        assert metadata.cover is not None
        assert metadata.official_rating == "JP-18+"

    def test_extract_metadata_tags(self):
        """测试标签提取"""
        resp = self._mock_html_response()
        url = "https://www.aventertainments.com/product_lists.aspx?product_id=142802&languageID=2&dept_id=29"
        with patch.object(self.extractor, "fetch", return_value=resp):
            metadata = self.extractor.extract_metadata(url)

        assert metadata is not None
        assert metadata.tags is not None
        assert len(metadata.tags) > 0

    def test_extract_metadata_invalid_url(self):
        """无效URL返回None"""
        assert self.extractor.extract_metadata("https://example.com/nope") is None

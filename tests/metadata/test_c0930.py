"""
C0930 元数据提取器测试

使用真实 HTML (tests/sites/c0930.html)
参考: metatube-sdk-go/provider/c0930/c0930_test.go
测试 ID: ki220913
"""

from unittest.mock import MagicMock, patch

import pytest

from pavone.plugins.metadata.c0930_metadata import C0930Metadata


class TestC0930Metadata:
    """测试 C0930Metadata 提取器"""

    def setup_method(self):
        self.extractor = C0930Metadata()

    # ===================== can_extract 测试 =====================

    def test_can_extract_url(self):
        assert self.extractor.can_extract("https://www.c0930.com/moviepages/ki220913/index.html")
        assert self.extractor.can_extract("https://c0930.com/moviepages/hitozuma1391/index.html")

    def test_cannot_extract_invalid(self):
        assert not self.extractor.can_extract("https://example.com/moviepages/ki220913/index.html")
        assert not self.extractor.can_extract("")
        assert not self.extractor.can_extract("SDMT-415")

    # ===================== extract_metadata mock 测试 =====================

    def _mock_html_response(self):
        with open("tests/sites/c0930.html", "r", encoding="utf-8") as f:
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
        url = "https://www.c0930.com/moviepages/ki220913/index.html"
        with patch.object(self.extractor, "fetch", return_value=resp):
            metadata = self.extractor.extract_metadata(url)

        assert metadata is not None
        assert "ki220913" in metadata.code
        assert "森山 志野" in metadata.title or "森山" in metadata.title
        assert metadata.runtime == 51  # PT00H51M53S → 51 min
        assert metadata.premiered == "2022-09-13"
        assert metadata.studio == "人妻斬り"
        assert metadata.cover is not None
        assert "c0930.com" in metadata.cover
        assert metadata.plot is not None
        assert metadata.official_rating == "JP-18+"

    def test_extract_actors(self):
        """测试演员提取"""
        resp = self._mock_html_response()
        url = "https://www.c0930.com/moviepages/ki220913/index.html"
        with patch.object(self.extractor, "fetch", return_value=resp):
            metadata = self.extractor.extract_metadata(url)

        assert metadata is not None
        assert metadata.actors is not None
        assert len(metadata.actors) > 0
        assert "森山 志野" in metadata.actors

    def test_extract_rating(self):
        """测试评分提取"""
        resp = self._mock_html_response()
        url = "https://www.c0930.com/moviepages/ki220913/index.html"
        with patch.object(self.extractor, "fetch", return_value=resp):
            metadata = self.extractor.extract_metadata(url)

        assert metadata is not None
        assert metadata.rating == pytest.approx(3.0, abs=0.5)

    def test_extract_metadata_invalid_url(self):
        """无效URL返回None"""
        assert self.extractor.extract_metadata("https://example.com/") is None

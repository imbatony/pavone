"""
Caribbeancom元数据提取器测试
"""

from unittest.mock import MagicMock, patch

import pytest

from pavone.plugins.metadata.caribbeancom_metadata import CaribbeancomMetadata


class TestCaribbeancomMetadata:
    """测试CaribbeancomMetadata提取器"""

    def setup_method(self):
        self.extractor = CaribbeancomMetadata()

    # ===================== can_extract 测试 =====================

    def test_can_extract_url(self):
        """测试是否能识别caribbeancom URL"""
        assert self.extractor.can_extract("https://www.caribbeancom.com/moviepages/033026-001/index.html")
        assert self.extractor.can_extract("https://caribbeancom.com/moviepages/033026-001/index.html")
        assert self.extractor.can_extract("http://www.caribbeancom.com/moviepages/033026-001/index.html")
        assert self.extractor.can_extract("https://en.caribbeancom.com/moviepages/033026-001/index.html")

    def test_can_extract_movie_id(self):
        """测试是否能识别番号"""
        assert self.extractor.can_extract("033026-001")
        assert self.extractor.can_extract("112018-001")
        assert self.extractor.can_extract("020820-971")

    def test_cannot_extract_invalid(self):
        """测试无效的identifier"""
        assert not self.extractor.can_extract("ftp://example.com")
        assert not self.extractor.can_extract("https://example.com/video")
        assert not self.extractor.can_extract("invalid string")
        assert not self.extractor.can_extract("SDMT-415")
        assert not self.extractor.can_extract("")
        assert not self.extractor.can_extract("12345")

    def test_can_extract_premium_url(self):
        """测试caribbeancompr URL"""
        assert self.extractor.can_extract("https://www.caribbeancompr.com/moviepages/050815_203/index.html")

    def test_can_extract_premium_code(self):
        """测试caribbeancompr番号（underscore格式）"""
        assert self.extractor.can_extract("050815_203")

    # ===================== _extract_movie_id 测试 =====================

    def test_extract_movie_id_from_url(self):
        """测试从URL提取番号"""
        assert (
            self.extractor._extract_movie_id_from_url(
                "https://www.caribbeancom.com/moviepages/033026-001/index.html"
            )
            == "033026-001"
        )
        assert (
            self.extractor._extract_movie_id_from_url(
                "https://en.caribbeancom.com/moviepages/112018-001/index.html"
            )
            == "112018-001"
        )
        assert self.extractor._extract_movie_id_from_url("https://www.caribbeancom.com/ranking/") is None

    def test_extract_movie_id_from_code(self):
        """测试从番号字符串提取"""
        assert self.extractor._extract_movie_id("033026-001") == "033026-001"
        assert (
            self.extractor._extract_movie_id("https://www.caribbeancom.com/moviepages/033026-001/index.html")
            == "033026-001"
        )
        assert self.extractor._extract_movie_id("invalid") is None

    # ===================== HTML 解析测试 =====================

    def test_extract_title(self):
        """测试从HTML提取标题"""
        with open("tests/sites/caribbeancom.html", "r", encoding="utf-8") as f:
            html = f.read()
        assert self.extractor._extract_title(html) == "絶倫上司とセックス残業 後藤あや"

    def test_extract_actors(self):
        """测试从HTML提取演员"""
        with open("tests/sites/caribbeancom.html", "r", encoding="utf-8") as f:
            html = f.read()
        actors = self.extractor._extract_actors(html)
        assert actors == ["後藤あや"]

    def test_extract_release_date(self):
        """测试从HTML提取配信日"""
        with open("tests/sites/caribbeancom.html", "r", encoding="utf-8") as f:
            html = f.read()
        assert self.extractor._extract_release_date(html) == "2026-03-30"

    def test_extract_duration(self):
        """测试从HTML提取时长"""
        with open("tests/sites/caribbeancom.html", "r", encoding="utf-8") as f:
            html = f.read()
        assert self.extractor._extract_duration(html) == 52  # 00:51:31 = 52 min (31s >= 30 rounds up)

    def test_extract_tags(self):
        """测试从HTML提取标签"""
        with open("tests/sites/caribbeancom.html", "r", encoding="utf-8") as f:
            html = f.read()
        tags = self.extractor._extract_tags(html)
        assert "美乳" in tags
        assert "中出し" in tags
        assert "OL" in tags
        assert len(tags) == 7

    def test_extract_rating(self):
        """测试从HTML提取评分"""
        with open("tests/sites/caribbeancom.html", "r", encoding="utf-8") as f:
            html = f.read()
        assert self.extractor._extract_rating(html) == 10.0  # 5 stars → 10.0

    def test_extract_description(self):
        """测试从HTML提取描述"""
        with open("tests/sites/caribbeancom.html", "r", encoding="utf-8") as f:
            html = f.read()
        desc = self.extractor._extract_description(html)
        assert desc is not None
        assert "後藤あや" in desc

    # ===================== _build_metadata_from_html 完整测试 =====================

    def test_build_metadata_from_html(self):
        """测试从HTML构建完整元数据"""
        with open("tests/sites/caribbeancom.html", "r", encoding="utf-8") as f:
            html = f.read()

        metadata = self.extractor._build_metadata_from_html(html, "033026-001")

        assert metadata is not None
        assert metadata.code == "033026-001"
        assert "絶倫上司とセックス残業" in metadata.title
        assert metadata.url == "https://www.caribbeancom.com/moviepages/033026-001/index.html"
        assert metadata.site == "Caribbeancom"
        assert metadata.actors == ["後藤あや"]
        assert metadata.runtime == 52
        assert metadata.premiered == "2026-03-30"
        assert metadata.year == 2026
        assert "美乳" in metadata.tags
        assert metadata.rating == 10.0
        assert metadata.plot is not None
        assert metadata.cover is None  # 离线测试无法请求图片
        assert metadata.poster == "https://www.caribbeancom.com/moviepages/033026-001/images/l_l.jpg"
        assert metadata.thumbnail is None
        assert metadata.backdrops is None  # 测试 HTML 中无画像ギャラリー区域
        assert metadata.studio == "カリビアンコム"
        assert metadata.official_rating == "JP-18+"

    # ===================== extract_metadata mock 测试 =====================

    def test_extract_metadata_with_mock(self):
        """测试extract_metadata方法（使用mock模拟网络请求）"""
        with open("tests/sites/caribbeancom.html", "r", encoding="utf-8") as f:
            html_content = f.read()

        mock_response = MagicMock()
        mock_response.text = html_content

        with patch.object(self.extractor, "fetch", return_value=mock_response):
            metadata = self.extractor.extract_metadata("033026-001")

        assert metadata is not None
        assert metadata.code == "033026-001"
        assert metadata.actors == ["後藤あや"]
        assert metadata.studio == "カリビアンコム"

    def test_extract_metadata_from_url_with_mock(self):
        """测试从URL提取元数据（使用mock）"""
        with open("tests/sites/caribbeancom.html", "r", encoding="utf-8") as f:
            html_content = f.read()

        mock_response = MagicMock()
        mock_response.text = html_content

        with patch.object(self.extractor, "fetch", return_value=mock_response):
            metadata = self.extractor.extract_metadata(
                "https://www.caribbeancom.com/moviepages/033026-001/index.html"
            )

        assert metadata is not None
        assert metadata.code == "033026-001"

    def test_extract_metadata_invalid_identifier(self):
        """测试无效identifier返回None"""
        metadata = self.extractor.extract_metadata("invalid_id")
        assert metadata is None

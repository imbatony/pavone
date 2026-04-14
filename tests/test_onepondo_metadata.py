"""
1Pondo元数据提取器测试
"""

import json
from unittest.mock import MagicMock, patch

import pytest

from pavone.plugins.metadata.onepondo_metadata import OnePondoMetadata


class TestOnePondoMetadata:
    """测试OnePondoMetadata提取器"""

    def setup_method(self):
        self.extractor = OnePondoMetadata()

    # ===================== can_extract 测试 =====================

    def test_can_extract_url(self):
        """测试是否能识别1pondo URL"""
        assert self.extractor.can_extract("https://www.1pondo.tv/movies/032417_504/")
        assert self.extractor.can_extract("https://1pondo.tv/movies/032417_504/")
        assert self.extractor.can_extract("http://www.1pondo.tv/movies/032417_504/")
        assert self.extractor.can_extract("https://en.1pondo.tv/movies/032417_504/")

    def test_can_extract_movie_id(self):
        """测试是否能识别番号"""
        assert self.extractor.can_extract("032417_504")
        assert self.extractor.can_extract("112018_001")
        assert self.extractor.can_extract("020820_971")

    def test_cannot_extract_invalid(self):
        """测试无效的identifier"""
        assert not self.extractor.can_extract("ftp://example.com")
        assert not self.extractor.can_extract("https://example.com/video")
        assert not self.extractor.can_extract("invalid string")
        assert not self.extractor.can_extract("SDMT-415")
        assert not self.extractor.can_extract("")
        assert not self.extractor.can_extract("12345")
        assert not self.extractor.can_extract("FC2-1234567")

    # ===================== _extract_movie_id 测试 =====================

    def test_extract_movie_id_from_url(self):
        """测试从URL提取番号"""
        assert self.extractor._extract_movie_id_from_url("https://www.1pondo.tv/movies/032417_504/") == "032417_504"
        assert self.extractor._extract_movie_id_from_url("https://en.1pondo.tv/movies/112018_001/") == "112018_001"
        assert self.extractor._extract_movie_id_from_url("https://www.1pondo.tv/ranking/") is None

    def test_extract_movie_id_from_code(self):
        """测试从番号字符串提取"""
        assert self.extractor._extract_movie_id("032417_504") == "032417_504"
        assert self.extractor._extract_movie_id("https://www.1pondo.tv/movies/032417_504/") == "032417_504"
        assert self.extractor._extract_movie_id("invalid") is None

    # ===================== _build_metadata 测试 =====================

    def test_build_metadata_from_json(self):
        """测试从JSON数据构建元数据"""
        with open("tests/sites/onepondo.json", "r", encoding="utf-8") as f:
            data = json.load(f)

        page_url = "https://www.1pondo.tv/movies/032417_504/"
        metadata = self.extractor._parse(data, "032417_504", page_url)

        assert metadata is not None
        assert metadata.code == "032417_504"
        assert "モデルコレクション 碧木凛" in metadata.title
        assert metadata.url == "https://www.1pondo.tv/movies/032417_504/"
        assert metadata.site == "1Pondo"
        assert metadata.actors == ["碧木凛"]
        assert metadata.runtime == 62  # 3746 sec ≈ 62 min
        assert metadata.premiered == "2017-03-30"
        assert metadata.year == 2017
        assert metadata.serial == "モデルコレクション"
        assert "制服" in metadata.tags
        assert metadata.rating == pytest.approx(8.8, abs=0.1)  # 4.39 * 2 ≈ 8.8
        assert metadata.plot is not None
        assert "碧木凛" in metadata.plot
        assert metadata.cover is not None
        assert metadata.backdrop is None
        assert metadata.backdrops == [
            "https://www.1pondo.tv/assets/sample/032417_504/popu/1.jpg",
            "https://www.1pondo.tv/assets/sample/032417_504/popu/2.jpg",
            "https://www.1pondo.tv/assets/sample/032417_504/popu/3.jpg",
        ]
        assert metadata.poster == "https://www.1pondo.tv/assets/sample/032417_504/str.jpg"
        assert metadata.official_rating == "JP-18+"

    def test_build_metadata_missing_fields(self):
        """测试缺少可选字段时仍能构建"""
        data = {
            "Title": "Test Title",
            "MovieID": "010120_001",
            "Release": "2020-01-01",
            "Duration": None,
            "ActressesJa": [],
            "AvgRating": None,
            "Desc": None,
            "Series": None,
            "UCNAME": [],
            "MovieThumb": None,
            "ThumbHigh": None,
        }

        metadata = self.extractor._parse(data, "010120_001", "https://www.1pondo.tv/movies/010120_001/")
        assert metadata is not None
        assert metadata.code == "010120_001"
        assert "Test Title" in metadata.title

    # ===================== extract_metadata mock 测试 =====================

    def test_extract_metadata_with_mock(self):
        """测试extract_metadata方法（使用mock模拟网络请求）"""
        with open("tests/sites/onepondo.json", "r", encoding="utf-8") as f:
            json_data = json.load(f)

        mock_response = MagicMock()
        mock_response.json.return_value = json_data

        with patch.object(self.extractor, "fetch", return_value=mock_response):
            metadata = self.extractor.extract_metadata("032417_504")

        assert metadata is not None
        assert metadata.code == "032417_504"
        assert metadata.actors == ["碧木凛"]

    def test_extract_metadata_from_url_with_mock(self):
        """测试从URL提取元数据（使用mock）"""
        with open("tests/sites/onepondo.json", "r", encoding="utf-8") as f:
            json_data = json.load(f)

        mock_response = MagicMock()
        mock_response.json.return_value = json_data

        with patch.object(self.extractor, "fetch", return_value=mock_response):
            metadata = self.extractor.extract_metadata("https://www.1pondo.tv/movies/032417_504/")

        assert metadata is not None
        assert metadata.code == "032417_504"

    def test_extract_metadata_invalid_identifier(self):
        """测试无效identifier返回None"""
        metadata = self.extractor.extract_metadata("invalid_id")
        assert metadata is None

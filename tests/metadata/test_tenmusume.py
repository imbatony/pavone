"""
10musume 元数据提取器测试

使用真实 API 响应数据 (tests/sites/tenmusume.json)
参考: metatube-sdk-go/provider/10musume/10musume_test.go
测试 ID: 042922_01
"""

from unittest.mock import MagicMock, patch

import pytest

from pavone.plugins.metadata.tenmusume_metadata import TenMusumeMetadata


class TestTenMusumeMetadata:
    """测试 TenMusumeMetadata 提取器"""

    def setup_method(self):
        self.extractor = TenMusumeMetadata()

    # ===================== can_extract 测试 =====================

    def test_can_extract_url(self):
        assert self.extractor.can_extract("https://www.10musume.com/movies/042922_01/")
        assert self.extractor.can_extract("https://10musume.com/movies/010906_04/")

    def test_can_extract_movie_id(self):
        assert self.extractor.can_extract("042922_01")
        assert self.extractor.can_extract("041607_01")
        assert self.extractor.can_extract("010906_04")

    def test_cannot_extract_invalid(self):
        assert not self.extractor.can_extract("https://example.com/movies/042922_01/")
        assert not self.extractor.can_extract("SDMT-415")
        assert not self.extractor.can_extract("")
        assert not self.extractor.can_extract("invalid")

    # ===================== extract_metadata mock 测试 =====================

    def _load_json(self):
        import json

        with open("tests/sites/tenmusume.json", "r", encoding="utf-8") as f:
            return json.load(f)

    def _mock_json_response(self, data):
        mock = MagicMock()
        mock.status_code = 200
        mock.json = MagicMock(return_value=data)
        mock.raise_for_status = MagicMock()
        return mock

    def test_extract_metadata_with_mock(self):
        """测试 extract_metadata（使用mock模拟网络请求，真实JSON数据）"""
        data = self._load_json()
        resp = self._mock_json_response(data)
        with patch.object(self.extractor, "fetch", return_value=resp):
            metadata = self.extractor.extract_metadata("042922_01")

        assert metadata is not None
        assert metadata.code == "042922_01"
        assert "パツパツのナースコスプレ" in metadata.title
        assert metadata.actors == ["井出ふみか"]
        assert metadata.runtime == 61  # 3636s / 60 = 60.6 → round = 61
        assert metadata.premiered == "2022-04-29"
        assert metadata.studio == "天然むすめ"
        assert "中出し" in metadata.tags
        assert "フェラ" in metadata.tags
        assert metadata.rating == pytest.approx(6.0, abs=0.1)  # 3.0 * 2 = 6.0
        assert metadata.cover is not None
        assert metadata.plot is not None
        assert metadata.official_rating == "JP-18+"

    def test_extract_metadata_from_url_with_mock(self):
        """测试从URL提取元数据"""
        data = self._load_json()
        resp = self._mock_json_response(data)
        with patch.object(self.extractor, "fetch", return_value=resp):
            metadata = self.extractor.extract_metadata("https://www.10musume.com/movies/042922_01/")

        assert metadata is not None
        assert metadata.code == "042922_01"
        assert "井出ふみか" in metadata.actors

    def test_extract_metadata_empty_response(self):
        """空JSON返回None"""
        resp = self._mock_json_response({})
        with patch.object(self.extractor, "fetch", return_value=resp):
            metadata = self.extractor.extract_metadata("042922_01")
        assert metadata is None

    def test_extract_metadata_invalid_identifier(self):
        """无效identifier返回None"""
        metadata = self.extractor.extract_metadata("INVALID-ID")
        assert metadata is None

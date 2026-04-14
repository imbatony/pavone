"""
FANZA 元数据提取器测试

使用模拟 __NEXT_DATA__ 页面 (tests/sites/fanza.html)
参考: metatube-sdk-go/provider/fanza/fanza_test.go
测试 ID: midv00047
"""

from unittest.mock import MagicMock, patch

import pytest

from pavone.plugins.metadata.fanza_metadata import FanzaMetadata


class TestFanzaMetadata:
    def setup_method(self):
        self.extractor = FanzaMetadata()

    def test_can_extract_url(self):
        assert self.extractor.can_extract("https://www.dmm.co.jp/digital/videoa/-/detail/=/cid=midv00047/")
        assert self.extractor.can_extract("https://www.dmm.co.jp/mono/dvd/-/detail/=/cid=midv00047/")
        assert self.extractor.can_extract("https://video.dmm.co.jp/av/content/?id=midv00047")

    def test_can_extract_movie_id(self):
        assert self.extractor.can_extract("midv00047")
        assert self.extractor.can_extract("1stars00141")

    def test_cannot_extract_invalid(self):
        assert not self.extractor.can_extract("https://example.com/detail/midv00047")
        assert not self.extractor.can_extract("")

    def _mock_html_response(self):
        with open("tests/sites/fanza.html", "r", encoding="utf-8") as f:
            html = f.read()
        mock = MagicMock()
        mock.status_code = 200
        mock.content = html.encode("utf-8")
        mock.text = html
        mock.raise_for_status = MagicMock()
        return mock

    def test_extract_metadata_with_mock(self):
        resp = self._mock_html_response()
        with patch.object(self.extractor, "fetch", return_value=resp):
            metadata = self.extractor.extract_metadata("midv00047")

        assert metadata is not None
        assert "MIDV-047" in metadata.code or "midv00047" in metadata.code
        assert "藤井いよな" in metadata.title or "プレステージ" in metadata.title
        assert "藤井いよな" in metadata.actors
        assert metadata.runtime == 120  # 7200s / 60
        assert metadata.premiered == "2022-02-08"
        assert metadata.studio == "ムーディーズ"
        assert metadata.cover is not None
        assert metadata.official_rating == "JP-18+"
        assert metadata.rating == pytest.approx(4.2, abs=0.1)

    def test_extract_metadata_from_url(self):
        resp = self._mock_html_response()
        with patch.object(self.extractor, "fetch", return_value=resp):
            metadata = self.extractor.extract_metadata("https://video.dmm.co.jp/av/content/?id=midv00047")
        assert metadata is not None

    def test_extract_metadata_invalid(self):
        assert self.extractor.extract_metadata("") is None

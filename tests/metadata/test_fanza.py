"""
FANZA 元数据提取器测试

使用模拟 __NEXT_DATA__ 页面 (tests/sites/fanza.html) 和 GraphQL 模拟数据
参考: metatube-sdk-go/provider/fanza/fanza_test.go
测试 ID: midv00047 (AV), scute1112 (amateur)
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
        assert self.extractor.can_extract("https://video.dmm.co.jp/amateur/content/?id=scute1112")

    def test_can_extract_movie_id(self):
        assert self.extractor.can_extract("midv00047")
        assert self.extractor.can_extract("1stars00141")
        assert self.extractor.can_extract("scute1112")

    def test_cannot_extract_invalid(self):
        assert not self.extractor.can_extract("https://example.com/detail/midv00047")
        assert not self.extractor.can_extract("")

    def test_resolve_amateur_url(self):
        movie_id, page_url, floor = self.extractor._resolve_with_floor("https://video.dmm.co.jp/amateur/content/?id=scute1112")
        assert movie_id == "scute1112"
        assert floor == "amateur"

    def test_resolve_av_url(self):
        movie_id, page_url, floor = self.extractor._resolve_with_floor("https://video.dmm.co.jp/av/content/?id=midv00047")
        assert movie_id == "midv00047"
        assert floor == "av"

    def test_resolve_legacy_url(self):
        movie_id, page_url, floor = self.extractor._resolve_with_floor(
            "https://www.dmm.co.jp/digital/videoa/-/detail/=/cid=midv00047/"
        )
        assert movie_id == "midv00047"
        assert floor == "av"

    def test_resolve_plain_id(self):
        movie_id, page_url, floor = self.extractor._resolve_with_floor("midv00047")
        assert movie_id == "midv00047"
        assert floor == "av"

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
        """测试 __NEXT_DATA__ 回退路径 (GraphQL 不可用时)"""
        resp = self._mock_html_response()
        with (
            patch.object(self.extractor, "_try_graphql", return_value=None),
            patch.object(self.extractor, "fetch", return_value=resp),
        ):
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
        """测试 URL 输入 + __NEXT_DATA__ 回退"""
        resp = self._mock_html_response()
        with (
            patch.object(self.extractor, "_try_graphql", return_value=None),
            patch.object(self.extractor, "fetch", return_value=resp),
        ):
            metadata = self.extractor.extract_metadata("https://video.dmm.co.jp/av/content/?id=midv00047")
        assert metadata is not None

    def test_extract_metadata_invalid(self):
        assert self.extractor.extract_metadata("") is None

    # ── GraphQL 路径测试 ──

    @staticmethod
    def _mock_graphql_av_data():
        return {
            "ppvContent": {
                "id": "midv00047",
                "floor": "AV",
                "title": "M男くんのお家、ついて行ってもイイですか？ 夢見るぅ",
                "description": "某番組で自宅に訪問されるのは経験済み！",
                "packageImage": {
                    "largeUrl": "https://awsimgsrc.dmm.co.jp/pics_dig/digital/video/midv00047/midv00047pl.jpg",
                    "mediumUrl": "https://awsimgsrc.dmm.co.jp/pics_dig/digital/video/midv00047/midv00047ps.jpg",
                },
                "sampleImages": [
                    {"number": 1, "imageUrl": "thumb1.jpg", "largeImageUrl": "large1.jpg"},
                ],
                "sample2DMovie": {"highestMovieUrl": "", "hlsMovieUrl": ""},
                "deliveryStartDate": "2022-02-11T00:00:00Z",
                "duration": 7080,
                "actresses": [{"id": "1", "name": "夢見るぅ", "imageUrl": ""}],
                "directors": [{"id": "1", "name": "ザック荒井"}],
                "series": {"id": "1", "name": ""},
                "maker": {"id": "1", "name": "ムーディーズ"},
                "label": {"id": "1", "name": "MOODYZ DIVA"},
                "genres": [{"id": "1", "name": "単体作品"}, {"id": "2", "name": "巨乳"}],
                "makerContentId": "MIDV-047",
            },
            "reviewSummary": {"average": 4.29, "total": 50},
        }

    @staticmethod
    def _mock_graphql_amateur_data():
        return {
            "ppvContent": {
                "id": "scute1112",
                "floor": "AMATEUR",
                "title": "あみ",
                "description": "萌えボイスに、ショートカットが似合うロリっ子あみちゃん",
                "packageImage": {
                    "largeUrl": None,
                    "mediumUrl": "https://awsimgsrc.dmm.co.jp/pics_dig/digital/amateur/scute1112/scute1112jp.jpg",
                },
                "sampleImages": [],
                "sample2DMovie": {"highestMovieUrl": "", "hlsMovieUrl": ""},
                "deliveryStartDate": "2021-04-06T01:00:00Z",
                "duration": 6041,
                "amateurActress": {"id": "scute1112", "name": "あみ", "imageUrl": ""},
                "maker": {"id": "45114", "name": "S-CUTE"},
                "label": {"id": "5356", "name": "S-CUTE"},
                "genres": [{"id": "1027", "name": "美少女"}, {"id": "48", "name": "制服"}],
                "makerContentId": "scute-1112-ami",
            },
            "reviewSummary": {"average": 4.0, "total": 2},
        }

    def test_graphql_av_metadata(self):
        """测试 GraphQL 路径 (AV 内容)"""
        data = self._mock_graphql_av_data()
        with patch.object(self.extractor, "_fetch_graphql", return_value=data):
            metadata = self.extractor.extract_metadata("https://video.dmm.co.jp/av/content/?id=midv00047")

        assert metadata is not None
        assert metadata.code == "MIDV-047"
        assert "夢見るぅ" in metadata.actors
        assert metadata.director == "ザック荒井"
        assert metadata.studio == "ムーディーズ"
        assert metadata.runtime == 118  # 7080 // 60
        assert metadata.premiered == "2022-02-11"
        assert metadata.rating == pytest.approx(4.29, abs=0.01)
        assert metadata.official_rating == "JP-18+"
        assert metadata.cover is not None
        assert metadata.tagline == "MOODYZ DIVA"

    def test_graphql_amateur_metadata(self):
        """测试 GraphQL 路径 (素人内容)"""
        data = self._mock_graphql_amateur_data()
        with patch.object(self.extractor, "_fetch_graphql", return_value=data):
            metadata = self.extractor.extract_metadata("https://video.dmm.co.jp/amateur/content/?id=scute1112")

        assert metadata is not None
        assert metadata.code == "scute-1112-ami"
        assert "あみ" in metadata.actors
        assert metadata.studio == "S-CUTE"
        assert metadata.runtime == 100  # 6041 // 60
        assert metadata.premiered == "2021-04-06"
        assert metadata.rating == pytest.approx(4.0, abs=0.01)
        assert metadata.official_rating == "JP-18+"
        assert "美少女" in metadata.tags
        assert "制服" in metadata.tags
        assert metadata.tagline == "S-CUTE"
        assert metadata.plot is not None

    def test_graphql_fallback_to_html(self):
        """GraphQL 失败时回退到 HTML 解析"""
        resp = self._mock_html_response()
        with (
            patch.object(self.extractor, "_fetch_graphql", side_effect=Exception("API error")),
            patch.object(self.extractor, "fetch", return_value=resp),
        ):
            metadata = self.extractor.extract_metadata("midv00047")
        assert metadata is not None
        assert "MIDV-047" in metadata.code

"""
FC2PPV-DB (fc2ppv-db.com) 元数据提取器测试

使用模拟 HTML (tests/sites/fc2ppv_db.html)
测试 ID: 4778286

注意: 该站点真实环境受 Cloudflare + 年龄确认页保护，需浏览器抓取；
测试通过 mock ``_fetch_page`` 返回保存的页面 HTML 来验证解析逻辑。
"""

from unittest.mock import MagicMock, patch

from pavone.models import MovieMetadata
from pavone.plugins.metadata.fc2ppv_db_metadata import Fc2ppvDbMetadata


class TestFc2ppvDbMetadata:
    def setup_method(self):
        self.extractor = Fc2ppvDbMetadata()

    # ===================== can_extract =====================

    def test_can_extract_url(self):
        assert self.extractor.can_extract("https://fc2ppv-db.com/ja/videos/4778286")
        assert self.extractor.can_extract("https://www.fc2ppv-db.com/ja/videos/4778286")

    def test_can_extract_movie_id(self):
        assert self.extractor.can_extract("4778286")
        assert self.extractor.can_extract("FC2-4778286")
        assert self.extractor.can_extract("FC2-PPV-4778286")

    def test_cannot_extract_invalid(self):
        # 同为 FC2 数据库但不同域名，不应由本插件按 URL 处理
        assert not self.extractor.can_extract("https://fc2ppvdb.com/articles/4778286")
        assert not self.extractor.can_extract("https://example.com/ja/videos/4778286")
        assert not self.extractor.can_extract("abc")
        assert not self.extractor.can_extract("")

    # ===================== _resolve =====================

    def test_resolve_url(self):
        movie_id, url = self.extractor._resolve("https://fc2ppv-db.com/ja/videos/4778286")  # type: ignore[reportPrivateUsage]
        assert movie_id == "4778286"
        assert url == "https://fc2ppv-db.com/ja/videos/4778286"

    def test_resolve_code(self):
        movie_id, url = self.extractor._resolve("FC2-PPV-4778286")  # type: ignore[reportPrivateUsage]
        assert movie_id == "4778286"
        assert url == "https://fc2ppv-db.com/ja/videos/4778286"

    # ===================== extract_metadata =====================

    def _mock_html_response(self):
        with open("tests/sites/fc2ppv_db.html", "r", encoding="utf-8") as f:
            html = f.read()
        mock = MagicMock()
        mock.status_code = 200
        mock.content = html.encode("utf-8")
        mock.text = html
        mock.raise_for_status = MagicMock()
        return mock

    def test_extract_metadata_with_mock(self):
        resp = self._mock_html_response()
        url = "https://fc2ppv-db.com/ja/videos/4778286"
        with patch.object(self.extractor, "_fetch_page", return_value=resp):
            metadata = self.extractor.extract_metadata(url)

        assert isinstance(metadata, MovieMetadata)
        assert "FC2-4778286" in metadata.code
        # 标题应剥离 FC2-PPV 前缀
        assert metadata.original_title is not None and "FC2-PPV-4778286" not in metadata.original_title
        assert metadata.studio == "ぱすも"
        assert metadata.premiered == "2025-10-13"
        assert metadata.year == 2025
        assert metadata.runtime == 51
        assert metadata.actors is not None and "ゆい" in metadata.actors
        assert metadata.cover is not None and metadata.cover.endswith("4778286.webp")
        assert metadata.backdrops is not None and len(metadata.backdrops) == 8
        assert metadata.official_rating == "JP-18+"

    def test_extract_metadata_invalid(self):
        assert self.extractor.extract_metadata("https://example.com/") is None

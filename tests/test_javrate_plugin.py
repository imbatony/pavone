"""
JavratePlugin 单元测试
"""

import json
import unittest
from unittest.mock import MagicMock, patch

from pavone.models import MovieMetadata, OperationItem, Quality
from pavone.plugins.javrate_plugin import JavratePlugin


class TestJavratePlugin(unittest.TestCase):
    """测试 JavratePlugin 类"""

    def setUp(self):
        """设置测试环境"""
        self.plugin = JavratePlugin()

        # 测试用的示例 URL
        self.test_url = "https://www.javrate.com/Movie/Detail/11b12b10-ca5f-4f09-9b45-768362d4856c.html"

        # JSON-LD 结构化数据
        self.json_ld_data = {
            "@context": "https://schema.org",
            "@type": "VideoObject",
            "name": "SNOS-080 NO.1STYLE 2026最強新人 幼顏 I罩杯 170cm高挑身材驚人細腰的超絕身材 AV DEBUT ~ 雛形美久琉",
            "contentUrl": "https://cloud.avking.xyz/20260205/test-uuid/index.m3u8",
            "thumbnailUrl": "https://picture.avking.xyz/compressed/20260205/cover_s.webp",
            "duration": "PT2H15M30S",
            "uploadDate": "2026-02-05",
            "actor": [{"@type": "Person", "name": "雛形美久琉", "url": "https://www.javrate.com/actor/detail/abc123"}],
            "identifier": {"@type": "PropertyValue", "name": "code", "Value": "SNOS-080"},
            "description": "SNOS-080为S1出品,2026年2月5日发行的有碼成人影片由雛形美久琉出演，这是一部精彩的影片",
        }

        # 示例 HTML 内容（带 JSON-LD）
        self.sample_html = (
            """
        <!DOCTYPE html>
        <html>
        <head>
            <title>SNOS-080 NO.1STYLE 2026最強新人 幼顏 I罩杯 - JAVRATE.COM</title>
            <meta property="og:title" content="SNOS-080 NO.1STYLE 2026最強新人 幼顏 I罩杯 170cm高挑身材驚人細腰的超絕身材 AV DEBUT ~ 雛形美久琉">
            <meta property="og:image" content="https://picture.avking.xyz/compressed/20260205/20260205042615834834_92893_s.webp">
            <meta property="og:description" content="SNOS-080为S1出品,2026年2月5日发行的有碼成人影片由雛形美久琉出演">
            <script type="application/ld+json">
            """
            + json.dumps(self.json_ld_data, ensure_ascii=False)
            + """
            </script>
        </head>
        <body>
            <h4>番號 :</h4>
            <div></div>
            <h4>SNOS-080</h4>

            <h4>出品廠商 :</h4>
            <div class="company-tag">
                <a href="/issuer/S1" class="issuer-link" data-issuer-id="test-id" data-issuer-name="S1">
                    <h4>S1</h4>
                </a>
                <span class="company-tag-abi text-center">
                    <a href="/issuer/S1" class="issuer-link" data-issuer-id="test-id" data-issuer-name="S1">
                        200部
                    </a>
                </span>
            </div>

            <h4>發片日期 :</h4>
            <div></div>
            <h4>2026年2月5日</h4>

            <h4>影片剧情 :</h4>
            <p>來自山梨縣 年齡20歲 職業 照護員</p>

            <a href="https://www.javrate.com/actor/detail/1dc7647a-8a12-4f92-99aa-e284f526bce7.html">雛形美久琉</a>

            <a href="https://www.javrate.com/keywords/movie/苗條">苗條</a>
            <a href="https://www.javrate.com/keywords/movie/後入">後入</a>
            <a href="https://www.javrate.com/keywords/movie/童顏">童顏</a>

            <video>
                <source src="https://example.com/video.m3u8" type="application/x-mpegURL">
            </video>
        </body>
        </html>
        """
        )

        # 不含 JSON-LD 的 HTML（回退测试）
        self.sample_html_no_jsonld = """
        <!DOCTYPE html>
        <html>
        <head>
            <title>SNOS-080 NO.1STYLE 2026最強新人 幼顏 I罩杯 - JAVRATE.COM</title>
            <meta property="og:title" content="SNOS-080 NO.1STYLE 2026最強新人 幼顏 I罩杯 170cm高挑身材驚人細腰的超絕身材 AV DEBUT ~ 雛形美久琉">
            <meta property="og:image" content="https://picture.avking.xyz/compressed/20260205/20260205042615834834_92893_s.webp">
            <meta property="og:description" content="SNOS-080为S1出品,2026年2月5日发行的有碼成人影片由雛形美久琉出演">
        </head>
        <body>
            <h4>番號 :</h4>
            <div></div>
            <h4>SNOS-080</h4>

            <h4>出品廠商 :</h4>
            <div class="company-tag">
                <a href="/issuer/S1" class="issuer-link" data-issuer-id="test-id" data-issuer-name="S1">
                    <h4>S1</h4>
                </a>
                <span class="company-tag-abi text-center">
                    <a href="/issuer/S1" class="issuer-link" data-issuer-id="test-id" data-issuer-name="S1">
                        200部
                    </a>
                </span>
            </div>

            <h4>發片日期 :</h4>
            <div></div>
            <h4>2026年2月5日</h4>

            <h4>影片剧情 :</h4>
            <p>來自山梨縣 年齡20歲 職業 照護員</p>

            <a href="https://www.javrate.com/actor/detail/1dc7647a-8a12-4f92-99aa-e284f526bce7.html">雛形美久琉</a>

            <a href="https://www.javrate.com/keywords/movie/苗條">苗條</a>
            <a href="https://www.javrate.com/keywords/movie/後入">後入</a>
            <a href="https://www.javrate.com/keywords/movie/童顏">童顏</a>

            <video>
                <source src="https://example.com/video.m3u8" type="application/x-mpegURL">
            </video>
        </body>
        </html>
        """

    def test_plugin_initialization(self):
        """测试插件初始化"""
        self.assertEqual(self.plugin.name, "Javrate")
        self.assertEqual(self.plugin.version, "2.1.0")
        self.assertEqual(self.plugin.priority, 30)
        self.assertIn("javrate.com", self.plugin.supported_domains)
        self.assertIn("www.javrate.com", self.plugin.supported_domains)

    # ==================== ExtractorPlugin 接口测试 ====================

    def test_can_handle_valid_url(self):
        """测试 can_handle 方法 - 有效 URL"""
        valid_urls = [
            "https://www.javrate.com/Movie/Detail/11b12b10-ca5f-4f09-9b45-768362d4856c.html",
            "https://javrate.com/Movie/Detail/abc123.html",
            "https://www.javrate.com/menu/censored",
        ]
        for url in valid_urls:
            with self.subTest(url=url):
                self.assertTrue(self.plugin.can_handle(url))

    def test_can_handle_invalid_url(self):
        """测试 can_handle 方法 - 无效 URL"""
        invalid_urls = [
            "https://example.com/video/test/",
            "https://missav.ai/video/test/",
            "https://memojav.com/video/test/",
            "",
        ]
        for url in invalid_urls:
            with self.subTest(url=url):
                self.assertFalse(self.plugin.can_handle(url))

    @patch.object(JavratePlugin, "fetch")
    def test_extract_success(self, mock_fetch):
        """测试成功提取视频信息（使用 JSON-LD）"""
        mock_response = MagicMock()
        mock_response.text = self.sample_html
        mock_fetch.return_value = mock_response

        result = self.plugin.extract(self.test_url)

        self.assertIsInstance(result, list)
        self.assertEqual(len(result), 1)
        self.assertIsInstance(result[0], OperationItem)
        # code 存储在 extra 中，并且会被转换为大写
        from pavone.models.constants import VideoCoreExtraKeys

        self.assertEqual(result[0]._extra.get(VideoCoreExtraKeys.CODE), "SNOS-080")
        # desc 包含 code 和 quality
        self.assertIn("SNOS-080", result[0].desc)

    @patch.object(JavratePlugin, "fetch")
    def test_extract_success_no_jsonld(self, mock_fetch):
        """测试成功提取视频信息（无 JSON-LD，回退到 HTML 正则）"""
        mock_response = MagicMock()
        mock_response.text = self.sample_html_no_jsonld
        mock_fetch.return_value = mock_response

        result = self.plugin.extract(self.test_url)

        self.assertIsInstance(result, list)
        self.assertEqual(len(result), 1)
        self.assertIsInstance(result[0], OperationItem)
        from pavone.models.constants import VideoCoreExtraKeys

        self.assertEqual(result[0]._extra.get(VideoCoreExtraKeys.CODE), "SNOS-080")

    @patch.object(JavratePlugin, "fetch")
    def test_extract_empty_html(self, mock_fetch):
        """测试提取失败 - 空 HTML"""
        mock_response = MagicMock()
        mock_response.text = ""
        mock_fetch.return_value = mock_response

        result = self.plugin.extract(self.test_url)
        self.assertEqual(result, [])

    @patch.object(JavratePlugin, "fetch")
    def test_extract_no_m3u8(self, mock_fetch):
        """测试提取失败 - 未找到 m3u8"""
        html_without_m3u8 = """
        <html>
        <head>
            <title>SNOS-080 Test Title</title>
            <meta property="og:image" content="https://picture.avking.xyz/cover.jpg">
        </head>
        <body>
            <h4>番號 :</h4>
            <div></div>
            <h4>SNOS-080</h4>
        </body>
        </html>
        """
        mock_response = MagicMock()
        mock_response.text = html_without_m3u8
        mock_fetch.return_value = mock_response

        result = self.plugin.extract(self.test_url)
        self.assertEqual(result, [])

    # ==================== MetadataPlugin 接口测试 ====================

    def test_can_extract_valid_url(self):
        """测试 can_extract 方法 - 有效 URL"""
        valid_urls = [
            "https://www.javrate.com/Movie/Detail/11b12b10-ca5f-4f09-9b45-768362d4856c.html",
            "https://javrate.com/Movie/Detail/abc123.html",
        ]
        for url in valid_urls:
            with self.subTest(url=url):
                self.assertTrue(self.plugin.can_extract(url))

    def test_can_extract_invalid_url(self):
        """测试 can_extract 方法 - 无效 URL"""
        invalid_urls = [
            "https://example.com/video/test/",
            "https://missav.ai/video/test/",
            "",
        ]
        for url in invalid_urls:
            with self.subTest(url=url):
                self.assertFalse(self.plugin.can_extract(url))

    @patch.object(JavratePlugin, "fetch")
    def test_extract_metadata_success(self, mock_fetch):
        """测试成功提取元数据（使用 JSON-LD）"""
        mock_response = MagicMock()
        mock_response.text = self.sample_html
        mock_fetch.return_value = mock_response

        result = self.plugin.extract_metadata(self.test_url)

        self.assertIsNotNone(result)
        self.assertIsInstance(result, MovieMetadata)
        self.assertEqual(result.code, "SNOS-080")
        self.assertEqual(result.site, "Javrate")
        self.assertIn("SNOS-080", result.title)

    @patch.object(JavratePlugin, "fetch")
    def test_extract_metadata_success_no_jsonld(self, mock_fetch):
        """测试成功提取元数据（无 JSON-LD，回退到 HTML 正则）"""
        mock_response = MagicMock()
        mock_response.text = self.sample_html_no_jsonld
        mock_fetch.return_value = mock_response

        result = self.plugin.extract_metadata(self.test_url)

        self.assertIsNotNone(result)
        self.assertIsInstance(result, MovieMetadata)
        self.assertEqual(result.code, "SNOS-080")
        self.assertEqual(result.site, "Javrate")

    @patch.object(JavratePlugin, "fetch")
    def test_extract_metadata_with_studio(self, mock_fetch):
        """测试提取元数据 - 包含厂商信息"""
        mock_response = MagicMock()
        mock_response.text = self.sample_html
        mock_fetch.return_value = mock_response

        result = self.plugin.extract_metadata(self.test_url)

        self.assertIsNotNone(result)
        self.assertEqual(result.studio, "S1")

    @patch.object(JavratePlugin, "fetch")
    def test_extract_metadata_with_actors(self, mock_fetch):
        """测试提取元数据 - 包含演员信息"""
        mock_response = MagicMock()
        mock_response.text = self.sample_html
        mock_fetch.return_value = mock_response

        result = self.plugin.extract_metadata(self.test_url)

        self.assertIsNotNone(result)
        self.assertIsNotNone(result.actors)
        self.assertIn("雛形美久琉", result.actors)

    @patch.object(JavratePlugin, "fetch")
    def test_extract_metadata_with_genres(self, mock_fetch):
        """测试提取元数据 - 包含分类标签"""
        mock_response = MagicMock()
        mock_response.text = self.sample_html
        mock_fetch.return_value = mock_response

        result = self.plugin.extract_metadata(self.test_url)

        self.assertIsNotNone(result)
        self.assertIsNotNone(result.genres)
        self.assertIn("苗條", result.genres)
        self.assertIn("童顏", result.genres)

    @patch.object(JavratePlugin, "fetch")
    def test_extract_metadata_with_release_date(self, mock_fetch):
        """测试提取元数据 - 包含发行日期"""
        mock_response = MagicMock()
        mock_response.text = self.sample_html
        mock_fetch.return_value = mock_response

        result = self.plugin.extract_metadata(self.test_url)

        self.assertIsNotNone(result)
        self.assertEqual(result.premiered, "2026-02-05")

    @patch.object(JavratePlugin, "fetch")
    def test_extract_metadata_empty_html(self, mock_fetch):
        """测试提取元数据失败 - 空 HTML"""
        mock_response = MagicMock()
        mock_response.text = ""
        mock_fetch.return_value = mock_response

        result = self.plugin.extract_metadata(self.test_url)
        self.assertIsNone(result)

    @patch.object(JavratePlugin, "fetch")
    def test_extract_metadata_exception(self, mock_fetch):
        """测试提取元数据失败 - 异常处理"""
        mock_fetch.side_effect = Exception("Network error")

        result = self.plugin.extract_metadata(self.test_url)
        self.assertIsNone(result)

    # ==================== 私有方法测试 ====================

    def test_extract_m3u8_from_source_tag(self):
        """测试从 source 标签提取 m3u8 链接"""
        html = '<source src="https://example.com/video.m3u8" type="application/x-mpegURL">'
        result = self.plugin._extract_m3u8(html)
        self.assertEqual(result, "https://example.com/video.m3u8")

    def test_extract_m3u8_from_video_tag(self):
        """测试从 video 标签提取 m3u8 链接"""
        html = '<video src="https://example.com/stream.m3u8"></video>'
        result = self.plugin._extract_m3u8(html)
        self.assertEqual(result, "https://example.com/stream.m3u8")

    def test_extract_m3u8_from_js(self):
        """测试从 JavaScript 中提取 m3u8 链接"""
        html = 'var source = "https://cdn.example.com/hls/video.m3u8";'
        result = self.plugin._extract_m3u8(html)
        self.assertEqual(result, "https://cdn.example.com/hls/video.m3u8")

    def test_extract_m3u8_not_found(self):
        """测试未找到 m3u8 链接"""
        html = "<html><body>No video here</body></html>"
        result = self.plugin._extract_m3u8(html)
        self.assertIsNone(result)

    def test_extract_cover_from_og_image(self):
        """测试从 og:image 提取封面"""
        html = '<meta property="og:image" content="https://picture.avking.xyz/cover.jpg">'
        result = self.plugin._extract_cover(html)
        self.assertEqual(result, "https://picture.avking.xyz/cover.jpg")

    def test_extract_cover_from_avking(self):
        """测试从 avking.xyz 提取封面"""
        html = '<img src="https://picture.avking.xyz/compressed/cover.webp" alt="cover">'
        result = self.plugin._extract_cover(html)
        self.assertEqual(result, "https://picture.avking.xyz/compressed/cover.webp")

    def test_extract_title_from_og_title(self):
        """测试从 og:title 提取标题"""
        html = '<meta property="og:title" content="SNOS-080 Test Video Title">'
        result = self.plugin._extract_title(html)
        self.assertEqual(result, "Test Video Title")

    def test_extract_title_from_title_tag(self):
        """测试从 title 标签提取标题"""
        html = "<title>ABC-123 Test Title - JAVRATE</title>"
        result = self.plugin._extract_title(html)
        # 移除网站后缀后返回
        self.assertIn("Test Title", result)

    def test_extract_code_from_html(self):
        """测试从 HTML 提取视频代码"""
        html = """
        <h4>番號 :</h4>
        <div></div>
        <h4>SNOS-080</h4>
        """
        result = self.plugin._extract_code(html)
        self.assertEqual(result, "SNOS-080")

    def test_extract_code_from_title(self):
        """测试从标题提取视频代码"""
        html = "<title>ABC-123 Test Title</title>"
        result = self.plugin._extract_code(html)
        self.assertEqual(result, "ABC-123")

    def test_extract_release_date(self):
        """测试提取发行日期"""
        html = """
        <h4>發片日期 :</h4>
        <div></div>
        <h4>2026年2月5日</h4>
        """
        result = self.plugin._extract_release_date(html)
        self.assertEqual(result, "2026-02-05")

    def test_extract_studio(self):
        """测试提取出品厂商 - 从 data-issuer-name 属性"""
        html = """
        <h4>出品廠商 :</h4>
        <div class="company-tag">
            <a href="/issuer/麻豆傳媒" class="issuer-link" data-issuer-id="abc" data-issuer-name="麻豆傳媒">
                <h4>麻豆傳媒</h4>
            </a>
            <span class="company-tag-abi text-center">
                <a href="/issuer/麻豆傳媒" class="issuer-link" data-issuer-id="abc" data-issuer-name="麻豆傳媒">
                    417部
                </a>
            </span>
        </div>
        """
        result = self.plugin._extract_studio(html)
        self.assertEqual(result, "麻豆傳媒")

    def test_extract_studio_simple(self):
        """测试提取出品厂商 - 简单结构"""
        html = """
        <a href="/issuer/S1" title="S1" data-issuer-name="S1">S1</a>
        """
        result = self.plugin._extract_studio(html)
        self.assertEqual(result, "S1")

    def test_extract_actors(self):
        """测试提取演员列表"""
        html = """
        <a href="https://www.javrate.com/actor/detail/abc123">雛形美久琉</a>
        <a href="https://www.javrate.com/actor/detail/def456">另一演员</a>
        """
        result = self.plugin._extract_actors(html)
        self.assertIsNotNone(result)
        self.assertIn("雛形美久琉", result)
        self.assertIn("另一演员", result)

    def test_extract_genres(self):
        """测试提取分类标签"""
        html = """
        <a href="https://www.javrate.com/keywords/movie/苗條">苗條</a>
        <a href="https://www.javrate.com/keywords/movie/童顏">童顏</a>
        """
        result = self.plugin._extract_genres(html)
        self.assertIsNotNone(result)
        self.assertIn("苗條", result)
        self.assertIn("童顏", result)

    # ==================== JSON-LD 解析测试 ====================

    def test_parse_json_ld_success(self):
        """测试成功解析 JSON-LD 数据"""
        result = JavratePlugin._parse_json_ld(self.sample_html)
        self.assertIsNotNone(result)
        self.assertEqual(result["@type"], "VideoObject")
        self.assertEqual(result["identifier"]["Value"], "SNOS-080")

    def test_parse_json_ld_not_found(self):
        """测试页面无 JSON-LD 数据"""
        result = JavratePlugin._parse_json_ld("<html><body>No JSON-LD</body></html>")
        self.assertIsNone(result)

    def test_parse_json_ld_invalid_json(self):
        """测试 JSON-LD 数据格式错误"""
        html = '<script type="application/ld+json">{invalid json}</script>'
        result = JavratePlugin._parse_json_ld(html)
        self.assertIsNone(result)

    def test_parse_json_ld_wrong_type(self):
        """测试 JSON-LD 非 VideoObject 类型"""
        html = '<script type="application/ld+json">{"@type": "Article", "name": "test"}</script>'
        result = JavratePlugin._parse_json_ld(html)
        self.assertIsNone(result)

    def test_parse_json_ld_array_format(self):
        """测试 JSON-LD 数组格式"""
        data = [{"@type": "WebSite"}, {"@type": "VideoObject", "name": "test"}]
        html = f'<script type="application/ld+json">{json.dumps(data)}</script>'
        result = JavratePlugin._parse_json_ld(html)
        self.assertIsNotNone(result)
        self.assertEqual(result["@type"], "VideoObject")

    # ==================== JSON-LD 优先提取测试 ====================

    def test_extract_m3u8_from_json_ld(self):
        """测试从 JSON-LD contentUrl 提取 m3u8"""
        result = self.plugin._extract_m3u8("", self.json_ld_data)
        self.assertEqual(result, "https://cloud.avking.xyz/20260205/test-uuid/index.m3u8")

    def test_extract_cover_from_json_ld(self):
        """测试从 JSON-LD thumbnailUrl 提取封面"""
        result = self.plugin._extract_cover("", self.json_ld_data)
        self.assertEqual(result, "https://picture.avking.xyz/compressed/20260205/cover_s.webp")

    def test_extract_title_from_json_ld(self):
        """测试从 JSON-LD name 提取标题（去除代码前缀）"""
        result = self.plugin._extract_title("", self.json_ld_data)
        self.assertNotIn("SNOS-080", result)
        self.assertIn("NO.1STYLE", result)

    def test_extract_code_from_json_ld(self):
        """测试从 JSON-LD identifier.Value 提取代码"""
        result = self.plugin._extract_code("", self.json_ld_data)
        self.assertEqual(result, "SNOS-080")

    def test_extract_release_date_from_json_ld(self):
        """测试从 JSON-LD uploadDate 提取日期"""
        result = self.plugin._extract_release_date("", self.json_ld_data)
        self.assertEqual(result, "2026-02-05")

    def test_extract_actors_from_json_ld(self):
        """测试从 JSON-LD actor 数组提取演员"""
        result = self.plugin._extract_actors("", self.json_ld_data)
        self.assertIsNotNone(result)
        self.assertIn("雛形美久琉", result)

    def test_extract_description_from_json_ld(self):
        """测试从 JSON-LD description 提取描述"""
        result = self.plugin._extract_description("", self.json_ld_data)
        self.assertIsNotNone(result)
        self.assertIn("SNOS-080", result)

    def test_extract_actors_from_json_ld_multiple(self):
        """测试从 JSON-LD 提取多个演员"""
        json_ld = {
            **self.json_ld_data,
            "actor": [
                {"@type": "Person", "name": "演员A"},
                {"@type": "Person", "name": "演员B"},
                {"@type": "Person", "name": "演员C"},
            ],
        }
        result = self.plugin._extract_actors("", json_ld)
        self.assertIsNotNone(result)
        self.assertEqual(len(result), 3)
        self.assertIn("演员A", result)
        self.assertIn("演员B", result)
        self.assertIn("演员C", result)


if __name__ == "__main__":
    unittest.main()

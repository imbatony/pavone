"""
MemojavPlugin 单元测试
"""

import unittest
from unittest.mock import MagicMock, patch

from pavone.models import MovieMetadata, OperationItem, Quality
from pavone.plugins.memojav_plugin import MemojavPlugin


class TestMemojavPlugin(unittest.TestCase):
    """测试 MemojavPlugin 类"""

    def setUp(self):
        """设置测试环境"""
        self.plugin = MemojavPlugin()
        
        # 测试用的示例 URL
        self.test_url = "https://memojav.com/video/sone-768/"
        self.test_embed_url = "https://memojav.com/embed/sone-768/"
        
        # 示例 HTML 内容
        self.sample_html = """
        <html>
        <head>
            <meta property="og:image" content="https://memojav.com/cover.jpg">
            <meta name="title" content="SONE-768 | Test video title">
        </head>
        </html>
        """
        
        # 示例视频信息内容
        self.sample_video_info = '{"url":"https%3A%2F%2Fexample.com%2Fvideo.m3u8"}'

    def test_plugin_initialization(self):
        """测试插件初始化"""
        self.assertEqual(self.plugin.name, "Memojav")
        self.assertEqual(self.plugin.version, "2.0.0")
        self.assertEqual(self.plugin.priority, 30)
        self.assertIn("memojav.com", self.plugin.supported_domains)

    # ==================== ExtractorPlugin 接口测试 ====================

    def test_can_handle_valid_url(self):
        """测试 can_handle 方法 - 有效 URL"""
        valid_urls = [
            "https://memojav.com/video/sone-768/",
            "https://www.memojav.com/video/abc-123/",
            "https://memojav.com/embed/test-video/",
        ]
        for url in valid_urls:
            with self.subTest(url=url):
                self.assertTrue(self.plugin.can_handle(url))

    def test_can_handle_invalid_url(self):
        """测试 can_handle 方法 - 无效 URL"""
        invalid_urls = [
            "https://example.com/video/test/",
            "https://missav.ai/video/test/",
            "https://jp.jable.tv/videos/test/",
            "",
        ]
        for url in invalid_urls:
            with self.subTest(url=url):
                self.assertFalse(self.plugin.can_handle(url))

    @patch.object(MemojavPlugin, "fetch")
    @patch.object(MemojavPlugin, "_get_vid_from_url")
    @patch.object(MemojavPlugin, "_extract_m3u8")
    @patch.object(MemojavPlugin, "_extract_cover")
    @patch.object(MemojavPlugin, "_extract_title")
    def test_extract_success(
        self,
        mock_extract_title,
        mock_extract_cover,
        mock_extract_m3u8,
        mock_get_vid,
        mock_fetch,
    ):
        """测试成功提取视频信息"""
        # 设置 mock
        mock_get_vid.return_value = "sone-768"
        mock_extract_m3u8.return_value = "https://example.com/video.m3u8"
        mock_extract_cover.return_value = "https://memojav.com/cover.jpg"
        mock_extract_title.return_value = "Test video title"
        
        mock_response = MagicMock()
        mock_response.text = self.sample_html
        mock_fetch.return_value = mock_response

        result = self.plugin.extract(self.test_url)

        self.assertIsInstance(result, list)
        self.assertEqual(len(result), 1)
        self.assertIsInstance(result[0], OperationItem)
        # code 存储在 extra 中，并且会被转换为大写
        from pavone.models.constants import VideoCoreExtraKeys
        self.assertEqual(result[0]._extra.get(VideoCoreExtraKeys.CODE), "SONE-768")
        # desc 包含 code, title 和 quality
        self.assertIn("SONE-768", result[0].desc)
        self.assertIn("Test video title", result[0].desc)

    @patch.object(MemojavPlugin, "fetch")
    def test_extract_empty_html(self, mock_fetch):
        """测试提取失败 - 空 HTML"""
        mock_response = MagicMock()
        mock_response.text = ""
        mock_fetch.return_value = mock_response

        result = self.plugin.extract(self.test_url)
        self.assertEqual(result, [])

    @patch.object(MemojavPlugin, "fetch")
    @patch.object(MemojavPlugin, "_get_vid_from_url")
    @patch.object(MemojavPlugin, "_extract_m3u8")
    def test_extract_no_m3u8(self, mock_extract_m3u8, mock_get_vid, mock_fetch):
        """测试提取失败 - 未找到 m3u8"""
        mock_get_vid.return_value = "sone-768"
        mock_extract_m3u8.return_value = None
        
        mock_response = MagicMock()
        mock_response.text = self.sample_html
        mock_fetch.return_value = mock_response

        result = self.plugin.extract(self.test_url)
        self.assertEqual(result, [])

    # ==================== MetadataPlugin 接口测试 ====================

    def test_can_extract_valid_url(self):
        """测试 can_extract 方法 - 有效 URL"""
        valid_urls = [
            "https://memojav.com/video/sone-768/",
            "https://www.memojav.com/video/abc-123/",
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

    @patch.object(MemojavPlugin, "fetch")
    @patch.object(MemojavPlugin, "_get_vid_from_url")
    @patch.object(MemojavPlugin, "_extract_title")
    @patch.object(MemojavPlugin, "_extract_cover")
    def test_extract_metadata_success(
        self,
        mock_extract_cover,
        mock_extract_title,
        mock_get_vid,
        mock_fetch,
    ):
        """测试成功提取元数据"""
        # 设置 mock
        mock_get_vid.return_value = "sone-768"
        mock_extract_title.return_value = "Test video title"
        mock_extract_cover.return_value = "https://memojav.com/cover.jpg"
        
        mock_response = MagicMock()
        mock_response.text = self.sample_html
        mock_fetch.return_value = mock_response

        result = self.plugin.extract_metadata(self.test_url)

        self.assertIsInstance(result, MovieMetadata)
        self.assertEqual(result.code, "SONE-768")  # code 会被转换为大写
        self.assertEqual(result.title, "SONE-768 Test video title")
        self.assertEqual(result.poster, "https://memojav.com/cover.jpg")
        self.assertEqual(result.url, self.test_url)  # 使用 url 而不是 source_url

    @patch.object(MemojavPlugin, "fetch")
    def test_extract_metadata_empty_html(self, mock_fetch):
        """测试提取元数据失败 - 空 HTML"""
        mock_response = MagicMock()
        mock_response.text = ""
        mock_fetch.return_value = mock_response

        result = self.plugin.extract_metadata(self.test_url)
        self.assertIsNone(result)

    @patch.object(MemojavPlugin, "fetch")
    @patch.object(MemojavPlugin, "_get_vid_from_url")
    @patch.object(MemojavPlugin, "_extract_title")
    def test_extract_metadata_no_title(self, mock_extract_title, mock_get_vid, mock_fetch):
        """测试提取元数据失败 - 未找到标题"""
        mock_get_vid.return_value = "sone-768"
        mock_extract_title.return_value = None
        
        mock_response = MagicMock()
        mock_response.text = self.sample_html
        mock_fetch.return_value = mock_response

        result = self.plugin.extract_metadata(self.test_url)
        self.assertIsNone(result)

    # ==================== 私有方法测试 ====================

    def test_extract_m3u8_success(self):
        """测试从视频信息中提取 m3u8 链接"""
        video_info = '{"url":"https%3A%2F%2Fexample.com%2Fvideo.m3u8"}'
        result = self.plugin._extract_m3u8(video_info)
        self.assertEqual(result, "https://example.com/video.m3u8")

    def test_extract_m3u8_not_found(self):
        """测试提取 m3u8 失败"""
        video_info = '{"other":"value"}'
        result = self.plugin._extract_m3u8(video_info)
        self.assertIsNone(result)

    def test_extract_cover_success(self):
        """测试从 HTML 中提取封面"""
        html = '<meta property="og:image" content="https://memojav.com/cover.jpg">'
        result = self.plugin._extract_cover(html)
        self.assertEqual(result, "https://memojav.com/cover.jpg")

    def test_extract_cover_not_found(self):
        """测试提取封面失败"""
        html = "<html><body>No cover</body></html>"
        result = self.plugin._extract_cover(html)
        self.assertIsNone(result)

    def test_extract_title_success(self):
        """测试从 HTML 中提取标题"""
        html = '<meta name="title" content="SONE-768 | Test video title">'
        result = self.plugin._extract_title(html)
        self.assertEqual(result, "Test video title")

    def test_extract_title_not_found(self):
        """测试提取标题失败"""
        html = "<html><body>No title</body></html>"
        with self.assertRaises(ValueError):
            self.plugin._extract_title(html)

    def test_get_vid_from_url_success(self):
        """测试从 URL 中提取视频 ID"""
        urls = [
            ("https://memojav.com/video/sone-768/", "sone-768"),
            ("https://memojav.com/embed/abc-123/", "abc-123"),
            ("https://www.memojav.com/video/test-video/", "test-video"),
        ]
        for url, expected_vid in urls:
            with self.subTest(url=url):
                result = self.plugin._get_vid_from_url(url)
                self.assertEqual(result, expected_vid)

    def test_get_vid_from_url_invalid(self):
        """测试从无效 URL 提取视频 ID"""
        # 根据修复后的逻辑，只有当 path 为空或只有斜杠时才会抛出异常
        invalid_url = "https://memojav.com"
        with self.assertRaises(ValueError):
            self.plugin._get_vid_from_url(invalid_url)


if __name__ == "__main__":
    unittest.main()

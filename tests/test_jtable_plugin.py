"""
JTable 插件测试
"""

import os
import unittest
from datetime import datetime
from unittest.mock import MagicMock, Mock, patch

from pavone.models.metadata import MovieMetadata
from pavone.models.operation import OperationItem
from pavone.plugins.jtable_plugin import JTablePlugin


class TestJTablePlugin(unittest.TestCase):
    """JTable插件测试"""

    def setUp(self):
        """设置测试环境"""
        self.plugin = JTablePlugin()

        # 获取测试HTML文件路径
        self.test_html_path = os.path.join(os.path.dirname(__file__), "sites", "jtable.html")

        # 读取测试HTML内容
        with open(self.test_html_path, "r", encoding="utf-8") as f:
            self.test_html_content = f.read()

    def test_initialization(self):
        """测试初始化"""
        self.assertEqual(self.plugin.name, "JTable")
        self.assertEqual(self.plugin.version, "2.0.0")
        self.assertEqual(self.plugin.priority, 30)
        self.assertIn("jp.jable.tv", self.plugin.supported_domains)
        self.assertEqual(self.plugin.site_name, "Jable")
        self.assertTrue(self.plugin.initialize())

    # ==================== 视频下载功能测试 ====================

    def test_can_handle_valid_urls(self):
        """测试能处理的有效URL"""
        valid_urls = [
            "https://jp.jable.tv/videos/dass-247/",
            "http://jp.jable.tv/videos/dass-247/",
            "https://jp.jable.tv/some-video",
            "http://jp.jable.tv/some-video",
            "https://jable.tv/videos/abc-123/",
        ]

        for url in valid_urls:
            with self.subTest(url=url):
                self.assertTrue(self.plugin.can_handle(url))

    def test_can_handle_invalid_urls(self):
        """测试不能处理的无效URL"""
        invalid_urls = [
            "https://youtube.com/watch?v=123",
            "https://pornhub.com/video/123",
            "https://other-site.com/video",
            "https://missav.ai/video",
            "not-a-url",
            "ftp://jp.jable.tv/video",
            "",
        ]

        for url in invalid_urls:
            with self.subTest(url=url):
                self.assertFalse(self.plugin.can_handle(url))

    @patch("pavone.plugins.jtable_plugin.JTablePlugin.fetch")
    def test_extract_success(self, mock_fetch: MagicMock) -> None:
        """测试成功提取下载选项"""
        # Mock HTTP 响应
        mock_response = Mock()
        mock_response.text = self.test_html_content
        mock_fetch.return_value = mock_response

        url = "https://jp.jable.tv/videos/dass-247/"
        result = self.plugin.extract(url)

        self.assertIsInstance(result, list)
        self.assertGreater(len(result), 0)

        # 检查第一个操作项
        item = result[0]
        self.assertIsInstance(item, OperationItem)
        # 检查描述包含演员名
        self.assertTrue("黒川すみれ" in item.desc or "美咲かんな" in item.desc, f"Expected actors in desc. Got: {item.desc}")

        # 检查是否包含元数据子项
        children = item.get_children()
        has_metadata = any(child.item_type == "metadata" for child in children)
        self.assertTrue(has_metadata)

    @patch("pavone.plugins.jtable_plugin.JTablePlugin.fetch")
    def test_extract_no_m3u8(self, mock_fetch: MagicMock) -> None:
        """测试没有m3u8链接的情况"""
        # Mock HTTP 响应，不包含 m3u8
        mock_response = Mock()
        mock_response.text = "<html><body>No m3u8 here</body></html>"
        mock_fetch.return_value = mock_response

        url = "https://jp.jable.tv/videos/test/"
        result = self.plugin.extract(url)

        self.assertEqual(result, [])

    # ==================== 元数据提取功能测试 ====================

    def test_can_extract_with_url(self):
        """测试能提取元数据的URL"""
        valid_identifiers = [
            "https://jp.jable.tv/videos/dass-247/",
            "http://jp.jable.tv/videos/abc-123/",
            "https://jable.tv/videos/test/",
        ]

        for identifier in valid_identifiers:
            with self.subTest(identifier=identifier):
                self.assertTrue(self.plugin.can_extract(identifier))

    def test_can_extract_with_code(self):
        """测试能提取元数据的视频代码"""
        valid_codes = [
            "DASS-247",
            "ABC-123",
            "SSIS-001",
        ]

        for code in valid_codes:
            with self.subTest(code=code):
                self.assertTrue(self.plugin.can_extract(code))

    def test_can_extract_invalid(self):
        """测试不能提取元数据的标识符"""
        invalid_identifiers = [
            "https://youtube.com/watch?v=123",
            "not-a-valid-code",
            "123456",  # 纯数字
            "",
        ]

        for identifier in invalid_identifiers:
            with self.subTest(identifier=identifier):
                self.assertFalse(self.plugin.can_extract(identifier))

    @patch("pavone.plugins.jtable_plugin.JTablePlugin.fetch")
    def test_extract_metadata_with_url(self, mock_fetch: MagicMock) -> None:
        """测试从URL提取元数据"""
        # Mock HTTP 响应
        mock_response = Mock()
        mock_response.text = self.test_html_content
        mock_fetch.return_value = mock_response

        url = "https://jp.jable.tv/videos/dass-247/"
        metadata = self.plugin.extract_metadata(url)

        self.assertIsNotNone(metadata)
        self.assertIsInstance(metadata, MovieMetadata)
        assert metadata is not None  # Type narrowing for pyright
        self.assertEqual(metadata.code, "DASS-247")
        self.assertEqual(metadata.site, "Jable")
        self.assertIn("黒川すみれ", metadata.title)
        self.assertIsNotNone(metadata.cover)
        assert metadata.actors is not None  # Type narrowing
        self.assertGreater(len(metadata.actors), 0)
        assert metadata.genres is not None  # Type narrowing
        self.assertGreater(len(metadata.genres), 0)

    @patch("pavone.plugins.jtable_plugin.JTablePlugin.fetch")
    def test_extract_metadata_with_code(self, mock_fetch: MagicMock) -> None:
        """测试从视频代码提取元数据"""
        # Mock HTTP 响应
        mock_response = Mock()
        mock_response.text = self.test_html_content
        mock_fetch.return_value = mock_response

        code = "DASS-247"
        metadata = self.plugin.extract_metadata(code)

        self.assertIsNotNone(metadata)
        self.assertIsInstance(metadata, MovieMetadata)
        assert metadata is not None  # Type narrowing for pyright
        self.assertEqual(metadata.code, "DASS-247")

        # 验证构造的URL
        mock_fetch.assert_called_once()
        called_url = mock_fetch.call_args[0][0]
        self.assertIn("dass-247", called_url.lower())

    @patch("pavone.plugins.jtable_plugin.JTablePlugin.fetch")
    def test_extract_metadata_failure(self, mock_fetch: MagicMock) -> None:
        """测试提取元数据失败的情况"""
        # Mock HTTP 响应为空
        mock_response = Mock()
        mock_response.text = ""
        mock_fetch.return_value = mock_response

        url = "https://jp.jable.tv/videos/test/"
        metadata = self.plugin.extract_metadata(url)

        self.assertIsNone(metadata)

    # ==================== 私有方法测试 ====================

    def test_extract_m3u8_url(self) -> None:
        """测试m3u8链接提取"""
        m3u8_url = self.plugin._extract_m3u8_url(self.test_html_content)  # type: ignore[reportPrivateUsage]
        self.assertIsNotNone(m3u8_url)
        assert m3u8_url is not None  # Type narrowing
        self.assertTrue(m3u8_url.startswith("http"))
        self.assertIn("m3u8", m3u8_url.lower() if "m3u8" in m3u8_url.lower() else "")

    def test_extract_m3u8_url_no_match(self) -> None:
        """测试没有m3u8链接的情况"""
        html_without_m3u8 = "<html><body>No m3u8 here</body></html>"
        m3u8_url = self.plugin._extract_m3u8_url(html_without_m3u8)  # type: ignore[reportPrivateUsage]
        self.assertIsNone(m3u8_url)

    def test_extract_code_title(self) -> None:
        """测试标题和代码提取"""
        code, title = self.plugin._extract_code_title(self.test_html_content)  # type: ignore[reportPrivateUsage]
        self.assertEqual(code, "DASS-247")
        self.assertEqual(
            title,
            "媚薬絶頂への恐怖に悪堕ちする誇り高き女捜査官。 黒川すみれ 美咲かんな",
        )

    def test_extract_code_title_no_space(self) -> None:
        """测试没有空格分隔的标题"""
        html_no_space = '<meta property="og:title" content="DASS-247媚薬絶頂への恐怖に悪堕ちする誇り高き女捜査官。">'
        code, _title = self.plugin._extract_code_title(html_no_space)  # type: ignore[reportPrivateUsage]
        self.assertEqual(code, "DASS-247")

    def test_extract_code_title_no_title(self) -> None:
        """测试没有标题的情况"""
        html_no_title = "<html><body>No title here</body></html>"
        code, title = self.plugin._extract_code_title(html_no_title)  # type: ignore[reportPrivateUsage]
        # 应该返回默认值
        self.assertIsNotNone(code)
        self.assertIsNotNone(title)

    def test_extract_actors(self) -> None:
        """测试演员提取"""
        actors = self.plugin._extract_actors(self.test_html_content)  # type: ignore[reportPrivateUsage]
        self.assertIsInstance(actors, list)
        self.assertGreater(len(actors), 0)
        # HTML中可能只包含部分演员
        self.assertTrue("黒川すみれ" in actors or "美咲かんな" in actors, f"Expected actors not found. Got: {actors}")

    def test_extract_actors_no_match(self) -> None:
        """测试没有演员信息的情况"""
        html_no_actors = "<html><body>No actors here</body></html>"
        actors = self.plugin._extract_actors(html_no_actors)  # type: ignore[reportPrivateUsage]
        self.assertEqual(actors, [])

    def test_extract_release_date(self) -> None:
        """测试发布日期提取"""
        release_date = self.plugin._extract_release_date(self.test_html_content)  # type: ignore[reportPrivateUsage]
        self.assertIsInstance(release_date, datetime)
        # 验证日期格式
        self.assertGreater(release_date.year, 2000)

    def test_extract_release_date_no_match(self) -> None:
        """测试没有发布日期的情况"""
        html_no_date = "<html><body>No date here</body></html>"
        release_date = self.plugin._extract_release_date(html_no_date)  # type: ignore[reportPrivateUsage]
        # 应该返回当前日期
        self.assertIsInstance(release_date, datetime)

    def test_extract_genres(self) -> None:
        """测试类型提取"""
        genres = self.plugin._extract_genres(self.test_html_content)  # type: ignore[reportPrivateUsage]
        self.assertIsInstance(genres, list)
        # 根据实际HTML内容验证
        if len(genres) > 0:
            self.assertIsInstance(genres[0], str)

    def test_extract_genres_no_match(self) -> None:
        """测试没有类型信息的情况"""
        html_no_genres = "<html><body>No genres here</body></html>"
        genres = self.plugin._extract_genres(html_no_genres)  # type: ignore[reportPrivateUsage]
        self.assertEqual(genres, [])

    def test_extract_tags(self) -> None:
        """测试标签提取"""
        tags = self.plugin._extract_tags(self.test_html_content)  # type: ignore[reportPrivateUsage]
        self.assertIsInstance(tags, list)
        # 根据实际HTML内容验证
        if len(tags) > 0:
            self.assertIsInstance(tags[0], str)

    def test_extract_tags_no_match(self) -> None:
        """测试没有标签的情况"""
        html_no_tags = "<html><body>No tags here</body></html>"
        tags = self.plugin._extract_tags(html_no_tags)  # type: ignore[reportPrivateUsage]
        self.assertEqual(tags, [])

    def test_extract_all_metadata(self) -> None:
        """测试完整元数据提取"""
        url = "https://jp.jable.tv/videos/dass-247/"
        metadata_dict = self.plugin._extract_all_metadata(self.test_html_content, url)  # type: ignore[reportPrivateUsage]

        self.assertIsInstance(metadata_dict, dict)
        self.assertIn("code", metadata_dict)
        self.assertIn("title", metadata_dict)
        self.assertIn("cover", metadata_dict)
        self.assertIn("actors", metadata_dict)
        self.assertIn("release_date", metadata_dict)
        self.assertIn("year", metadata_dict)
        self.assertIn("genres", metadata_dict)
        self.assertIn("tags", metadata_dict)

        # 验证数据类型
        self.assertIsInstance(metadata_dict["code"], str)
        self.assertIsInstance(metadata_dict["title"], str)
        self.assertIsInstance(metadata_dict["actors"], list)
        self.assertIsInstance(metadata_dict["release_date"], str)
        self.assertIsInstance(metadata_dict["year"], int)
        self.assertIsInstance(metadata_dict["genres"], list)
        self.assertIsInstance(metadata_dict["tags"], list)


if __name__ == "__main__":
    unittest.main()

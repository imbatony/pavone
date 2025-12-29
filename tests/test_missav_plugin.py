"""
MissAV统一插件测试
整合了搜索、元数据提取和视频提取三个功能的测试
"""

import os
import unittest
from unittest.mock import Mock, patch

import pytest

from pavone.models.constants import Quality
from pavone.models.metadata import MovieMetadata
from pavone.models.operation import OperationItem
from pavone.models.search_result import SearchResult
from pavone.plugins.missav_plugin import MissAVPlugin


class TestMissAVPlugin(unittest.TestCase):
    """MissAV统一插件测试"""

    def setUp(self):
        """设置测试环境"""
        self.plugin = MissAVPlugin()

        # 获取测试HTML文件路径
        self.test_html_path = os.path.join(os.path.dirname(__file__), "sites", "missav.html")

        # 读取测试HTML内容
        with open(self.test_html_path, "r", encoding="utf-8") as f:
            self.test_html_content = f.read()

    # ==================== 基础功能测试 ====================

    def test_initialization(self):
        """测试初始化"""
        self.assertEqual(self.plugin.name, "MissAV")
        self.assertEqual(self.plugin.version, "2.0.0")
        self.assertEqual(self.plugin.priority, 30)
        self.assertIn("missav.ai", self.plugin.supported_domains)
        self.assertIn("www.missav.ai", self.plugin.supported_domains)
        self.assertIn("missav.com", self.plugin.supported_domains)
        self.assertIn("www.missav.com", self.plugin.supported_domains)

    def test_initialize(self):
        """测试初始化方法"""
        result = self.plugin.initialize()
        self.assertTrue(result)

    def test_cleanup(self):
        """测试清理方法"""
        # cleanup方法应该能正常执行而不抛出异常
        try:
            self.plugin.cleanup()
        except Exception as e:
            self.fail(f"cleanup() raised {e} unexpectedly!")

    # ==================== 搜索功能测试 ====================

    def test_parse_search_results(self):
        """测试搜索结果解析"""
        # 读取搜索结果HTML文件
        html_path = os.path.join(os.path.dirname(__file__), "sites", "missav_search.html")
        with open(html_path, "r", encoding="utf-8") as f:
            html_content = f.read()

        # 解析搜索结果
        results = self.plugin._parse_search_results(html_content, 5, "优等生")

        # 验证结果数量
        self.assertEqual(len(results), 5)

        # 检查第一个结果
        first_result = results[0]
        self.assertIsInstance(first_result, SearchResult)
        self.assertEqual(first_result.site, "MissAV")
        self.assertEqual(first_result.keyword, "优等生")

        # code 可能为 None，需要处理
        if first_result.code is not None:
            self.assertIn("GOAL-052", first_result.code.upper())
        self.assertIn("優等生", first_result.title)

        # 验证所有结果的URL格式
        for result in results:
            self.assertTrue(result.url.startswith("https://missav.ai/"))
            self.assertIsNotNone(result.code)
            self.assertNotEqual(result.code, "")

    # ==================== 元数据提取功能测试 ====================

    def test_can_extract_url(self):
        """测试是否能识别MissAV URL"""
        # 测试不同格式的URL
        self.assertTrue(self.plugin.can_extract("https://missav.ai/ja/sdmt-415"))
        self.assertTrue(self.plugin.can_extract("https://www.missav.ai/ja/test-123"))
        self.assertTrue(self.plugin.can_extract("https://missav.com/en/video-456"))
        self.assertTrue(self.plugin.can_extract("https://www.missav.com/en/another-789"))

    def test_can_extract_code(self):
        """测试是否能识别视频代码"""
        # 测试不同格式的代码
        self.assertTrue(self.plugin.can_extract("SDMT-415"))
        self.assertTrue(self.plugin.can_extract("sdmt-415"))
        self.assertTrue(self.plugin.can_extract("TEST-123"))
        self.assertTrue(self.plugin.can_extract("test-456"))

    def test_cannot_extract_invalid(self):
        """测试无效的identifier"""
        # 测试无效格式
        self.assertFalse(self.plugin.can_extract("ftp://example.com"))
        self.assertFalse(self.plugin.can_extract("invalid string"))
        self.assertFalse(self.plugin.can_extract("123-456-789"))  # 太多分隔符
        self.assertFalse(self.plugin.can_extract(""))

    def test_extract_metadata_url_requires_network(self):
        """
        测试从URL提取元数据（需要网络）
        这是一个集成测试，实际测试时需要网络连接
        """
        url = "https://missav.ai/ja/sdmt-415"

        if not self.plugin.can_extract(url):
            pytest.skip("Invalid URL format")

    def test_extract_metadata_code_not_supported(self):
        """测试从code提取元数据（当前不支持）"""
        # 当前实现中，直接使用代码format会返回None
        result = self.plugin.extract_metadata("SDMT-415")

        # 应该返回None，因为还需要实现搜索功能
        self.assertIsNone(result)

    # ==================== 视频提取功能测试 ====================

    def test_can_handle_valid_urls(self):
        """测试能处理的有效URL"""
        valid_urls = [
            "https://missav.ai/dm18/sdab-183",
            "https://www.missav.ai/dm18/sdab-183",
            "https://missav.com/dm18/sdab-183",
            "https://www.missav.com/dm18/sdab-183",
            "http://missav.ai/some-video",
            "http://www.missav.ai/some-video",
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
            "not-a-url",
            "ftp://missav.ai/video",
        ]

        for url in invalid_urls:
            with self.subTest(url=url):
                self.assertFalse(self.plugin.can_handle(url))

        # 测试空字符串单独处理
        self.assertFalse(self.plugin.can_handle(""))

    # ==================== 元数据提取方法测试 ====================

    def test_extract_uuid(self):
        """测试UUID提取功能"""
        uuid = self.plugin._extract_uuid(self.test_html_content)
        expected_uuid = "b8e4c00d-0a85-4dc5-badd-024a7765d391"
        self.assertEqual(uuid, expected_uuid)

    def test_extract_uuid_no_match(self):
        """测试UUID提取失败的情况"""
        html_without_uuid = "<html><body>No UUID here</body></html>"
        uuid = self.plugin._extract_uuid(html_without_uuid)
        self.assertIsNone(uuid)

    def test_extract_title_and_code(self):
        """测试标题和代码提取"""
        title_with_code, title, code = self.plugin._extract_title_and_code(self.test_html_content)
        self.assertEqual(code, "SDAB-183")
        self.assertEqual(
            title,
            "ボーイッシュ女子が男子の格好で初中出し 男装コスで生チ○ポ3本番！ 早見なな",
        )
        self.assertEqual(title_with_code, f"{code} {title}")

    def test_extract_title_and_code_no_match(self):
        """测试标题和代码提取失败的情况"""
        html_without_title = "<html><body>No title here</body></html>"
        title_with_code, title, code = self.plugin._extract_title_and_code(html_without_title)
        self.assertEqual(title, "MissAV Video")
        self.assertEqual(code, "Unknown")
        self.assertEqual(title_with_code, "Unknown MissAV Video")

    def test_extract_actors(self):
        """测试演员提取"""
        actors = self.plugin._extract_actors(self.test_html_content)
        expected_actors = ["早見なな", "マッスル澤野", "結城結弦", "羽田"]
        self.assertEqual(actors, expected_actors)

    def test_extract_actors_no_match(self):
        """测试演员提取失败的情况"""
        html_without_actors = "<html><body>No actors here</body></html>"
        actors = self.plugin._extract_actors(html_without_actors)
        self.assertEqual(actors, [])

    def test_extract_director(self):
        """测试导演提取"""
        director = self.plugin._extract_director(self.test_html_content)
        self.assertEqual(director, "キョウセイ")

    def test_extract_director_no_match(self):
        """测试导演提取失败的情况"""
        html_without_director = "<html><body>No director here</body></html>"
        director = self.plugin._extract_director(html_without_director)
        self.assertIsNone(director)

    def test_extract_duration(self):
        """测试时长提取"""
        duration = self.plugin._extract_duration(self.test_html_content)
        # 新实现返回分钟，8397秒 = 139分钟 (向下取整)
        self.assertEqual(duration, 139)

    def test_extract_duration_no_match(self):
        """测试时长提取失败的情况"""
        html_without_duration = "<html><body>No duration here</body></html>"
        duration = self.plugin._extract_duration(html_without_duration)
        self.assertIsNone(duration)

    def test_extract_release_date(self):
        """测试发布日期提取"""
        release_date = self.plugin._extract_release_date(self.test_html_content)
        self.assertEqual(release_date, "2021-06-14")

    def test_extract_release_date_no_match(self):
        """测试发布日期提取失败的情况"""
        html_without_date = "<html><body>No release date here</body></html>"
        release_date = self.plugin._extract_release_date(html_without_date)
        self.assertIsNone(release_date)

    def test_extract_genres(self):
        """测试类型提取"""
        genres = self.plugin._extract_genres(self.test_html_content)
        self.assertIsInstance(genres, list)
        expected_genres = ["単体作品", "コスプレ", "アニメ", "中出し", "ハイビジョン"]
        self.assertEqual(genres, expected_genres)

    def test_extract_genres_multilingual(self):
        """测试多语言类型提取"""
        # 测试日语
        japanese_html = """
        <div class="text-secondary">
            <span>ジャンル:</span>
            <a href="https://missav.ai/genres/solo" class="text-nord13 font-medium">単体作品</a>,
            <a href="https://missav.ai/genres/creampie" class="text-nord13 font-medium">中出し</a>
        </div>
        """
        genres = self.plugin._extract_genres(japanese_html)
        self.assertEqual(genres, ["単体作品", "中出し"])

        # 测试中文简体
        chinese_html = """
        <div class="text-secondary">
            <span>类型:</span>
            <a href="https://missav.ai/genres/solo" class="text-nord13 font-medium">单体作品</a>,
            <a href="https://missav.ai/genres/creampie" class="text-nord13 font-medium">中出</a>
        </div>
        """
        genres = self.plugin._extract_genres(chinese_html)
        self.assertEqual(genres, ["单体作品", "中出"])

        # 测试英语
        english_html = """
        <div class="text-secondary">
            <span>Genre:</span>
            <a href="https://missav.ai/genres/solo" class="text-nord13 font-medium">Solo Work</a>,
            <a href="https://missav.ai/genres/creampie" class="text-nord13 font-medium">Creampie</a>
        </div>
        """
        genres = self.plugin._extract_genres(english_html)
        self.assertEqual(genres, ["Solo Work", "Creampie"])

    def test_extract_genres_no_fallback(self):
        """测试没有标签时返回空列表"""
        # 测试没有任何语言标签的HTML
        no_label_html = """
        <div>
            <a href="https://missav.ai/genres/solo" class="text-nord13 font-medium">单体作品</a>
            <a href="https://missav.ai/genres/cosplay" class="text-nord13 font-medium">角色扮演</a>
            <a href="https://missav.ai/actors/someone" class="text-nord13 font-medium">某演员</a>
        </div>
        """
        genres = self.plugin._extract_genres(no_label_html)
        self.assertEqual(genres, [])

        # 测试完全无关的HTML
        random_html = """
        <div>
            <a href="https://missav.ai/something" class="text-nord13 font-medium">随机内容</a>
            <a href="https://missav.ai/other" class="text-nord13 font-medium">其他内容</a>
        </div>
        """
        genres = self.plugin._extract_genres(random_html)
        self.assertEqual(genres, [])

    # ==================== 播放列表提取测试 ====================

    def test_get_key_for_url(self):
        """测试URL键生成"""
        test_urls = [
            "https://example.com/video_1080p.m3u8",
            "https://example.com/video_720p.m3u8",
            "https://example.com/video_480p.m3u8",
        ]

        for url in test_urls:
            key = self.plugin._get_key_for_url(url)
            expected_quality = Quality.guess(url)
            self.assertEqual(key, expected_quality)

    @patch("pavone.plugins.missav_plugin.MissAVPlugin.fetch")
    def test_extract_master_playlist(self, mock_fetch):
        """测试主播放列表提取"""
        # 模拟m3u8响应内容
        m3u8_content = """#EXTM3U
#EXT-X-VERSION:3
#EXT-X-STREAM-INF:BANDWIDTH=1000000,RESOLUTION=1280x720
1280x720/video.m3u8
#EXT-X-STREAM-INF:BANDWIDTH=500000,RESOLUTION=842x480
842x480/video.m3u8
"""

        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = m3u8_content
        mock_fetch.return_value = mock_response

        master_url = "https://surrit.com/test-uuid/playlist.m3u8"
        result = self.plugin._extract_master_playlist(master_url)

        # 验证结果
        self.assertIsInstance(result, dict)
        self.assertGreater(len(result), 0)

        # 验证生成的完整URL
        for quality, url in result.items():
            self.assertTrue(url.startswith("https://surrit.com/test-uuid/"))
            self.assertTrue(url.endswith(".m3u8"))

    @patch("pavone.plugins.missav_plugin.MissAVPlugin.fetch")
    def test_extract_master_playlist_failure(self, mock_fetch):
        """测试主播放列表提取失败"""
        mock_response = Mock()
        mock_response.status_code = 404
        mock_fetch.return_value = mock_response

        master_url = "https://surrit.com/invalid-uuid/playlist.m3u8"
        result = self.plugin._extract_master_playlist(master_url)

        self.assertEqual(result, {})

    # ==================== 完整提取流程测试 ====================

    @patch("pavone.plugins.missav_plugin.MissAVPlugin.fetch")
    def test_extract_with_uuid(self, mock_fetch):
        """测试带UUID的完整提取流程"""
        # 模拟获取页面的响应
        mock_page_response = Mock()
        mock_page_response.text = self.test_html_content

        # 模拟m3u8播放列表响应
        m3u8_content = """#EXTM3U
#EXT-X-VERSION:3
#EXT-X-STREAM-INF:BANDWIDTH=1000000,RESOLUTION=1280x720
1280x720/video.m3u8
#EXT-X-STREAM-INF:BANDWIDTH=500000,RESOLUTION=842x480
842x480/video.m3u8
"""
        mock_m3u8_response = Mock()
        mock_m3u8_response.status_code = 200
        mock_m3u8_response.text = m3u8_content

        # 设置fetch的不同返回值
        mock_fetch.side_effect = [mock_page_response, mock_m3u8_response]

        test_url = "https://missav.ai/dm18/sdab-183"
        result = self.plugin.extract(test_url)

        # 验证结果
        self.assertIsInstance(result, list)
        self.assertGreater(len(result), 0)

        # 验证第一个下载项的属性
        if result:
            first_item = result[0]
            self.assertIsInstance(first_item, OperationItem)

            # 验证子项中包含元数据项
            children = first_item.get_children()
            self.assertGreater(len(children), 0)

            # 查找元数据项并验证code字段
            metadata_item = None
            for child in children:
                if child.item_type == "metadata":
                    metadata_item = child
                    break

            self.assertIsNotNone(metadata_item, "元数据项不应为空")
            if metadata_item:
                metadata = metadata_item.get_metadata()
                self.assertIsNotNone(metadata)
                self.assertIsInstance(metadata, MovieMetadata)
                # 验证code字段已正确设置
                m_metadata: MovieMetadata = metadata  # type: ignore
                self.assertEqual(m_metadata.code, "SDAB-183")

    @patch("pavone.plugins.missav_plugin.MissAVPlugin.fetch")
    def test_extract_no_uuid(self, mock_fetch):
        """测试没有UUID的提取流程"""
        html_without_uuid = "<html><body>No UUID here</body></html>"
        mock_response = Mock()
        mock_response.text = html_without_uuid
        mock_fetch.return_value = mock_response

        test_url = "https://missav.ai/some-video"
        result = self.plugin.extract(test_url)

        # 没有UUID应该返回空列表
        self.assertEqual(result, [])

    @patch("pavone.plugins.missav_plugin.MissAVPlugin.fetch")
    def test_extract_fetch_failure(self, mock_fetch):
        """测试页面获取失败的情况"""
        mock_fetch.side_effect = Exception("Network error")

        test_url = "https://missav.ai/some-video"
        result = self.plugin.extract(test_url)

        # 网络错误应该返回空列表
        self.assertEqual(result, [])


if __name__ == "__main__":
    # 设置测试运行时的日志级别
    import logging

    logging.getLogger().setLevel(logging.ERROR)

    unittest.main()

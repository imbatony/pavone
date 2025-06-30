"""
MissAV提取器测试
"""

import unittest
from unittest.mock import Mock, patch, MagicMock
from typing import List
import os

from pavone.plugins.extractors.missav_extractor import MissAVExtractor
from pavone.models.operation import OperationItem
from pavone.models.constants import Quality


class TestMissAVExtractor(unittest.TestCase):
    """MissAV提取器测试"""

    def setUp(self):
        """设置测试环境"""
        self.extractor = MissAVExtractor()

        # 获取测试HTML文件路径
        self.test_html_path = os.path.join(os.path.dirname(__file__), "sites", "missav.html")

        # 读取测试HTML内容
        with open(self.test_html_path, "r", encoding="utf-8") as f:
            self.test_html_content = f.read()

    def test_initialization(self):
        """测试初始化"""
        self.assertEqual(self.extractor.name, "MissAVExtractor")
        self.assertEqual(self.extractor.version, "1.0.0")
        self.assertEqual(self.extractor.priority, 30)
        self.assertIn("missav.ai", self.extractor.supported_domains)
        self.assertIn("www.missav.ai", self.extractor.supported_domains)
        self.assertIn("missav.com", self.extractor.supported_domains)
        self.assertIn("www.missav.com", self.extractor.supported_domains)

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
                self.assertTrue(self.extractor.can_handle(url))

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
                self.assertFalse(self.extractor.can_handle(url))

        # 测试空字符串单独处理，因为urlparse('')返回的netloc是空字符串
        self.assertFalse(self.extractor.can_handle(""))

    def test_extract_uuid(self):
        """测试UUID提取功能"""
        uuid = self.extractor._extract_uuid(self.test_html_content)
        # 基于测试HTML中的真实数据
        expected_uuid = "b8e4c00d-0a85-4dc5-badd-024a7765d391"
        self.assertEqual(uuid, expected_uuid)

    def test_extract_uuid_no_match(self):
        """测试UUID提取失败的情况"""
        html_without_uuid = "<html><body>No UUID here</body></html>"
        uuid = self.extractor._extract_uuid(html_without_uuid)
        self.assertIsNone(uuid)

    def test_extract_title_and_code(self):
        """测试标题和代码提取"""
        title, code = self.extractor._extract_title_and_code(self.test_html_content)
        self.assertEqual(code, "SDAB-183")
        self.assertEqual(title, "ボーイッシュ女子が男子の格好で初中出し 男装コスで生チ○ポ3本番！ 早見なな")

    def test_extract_title_and_code_no_match(self):
        """测试标题和代码提取失败的情况"""
        html_without_title = "<html><body>No title here</body></html>"
        title, code = self.extractor._extract_title_and_code(html_without_title)
        self.assertEqual(title, "MissAV Video")
        self.assertEqual(code, "Unknown")

    def test_extract_actors(self):
        """测试演员提取"""
        actors = self.extractor._extract_actors(self.test_html_content)
        expected_actors = ["早見なな", "マッスル澤野", "結城結弦", "羽田"]
        self.assertEqual(actors, expected_actors)

    def test_extract_actors_no_match(self):
        """测试演员提取失败的情况"""
        html_without_actors = "<html><body>No actors here</body></html>"
        actors = self.extractor._extract_actors(html_without_actors)
        self.assertEqual(actors, [])

    def test_extract_director(self):
        """测试导演提取"""
        director = self.extractor._extract_director(self.test_html_content)
        self.assertEqual(director, "キョウセイ")

    def test_extract_director_no_match(self):
        """测试导演提取失败的情况"""
        html_without_director = "<html><body>No director here</body></html>"
        director = self.extractor._extract_director(html_without_director)
        self.assertIsNone(director)

    def test_extract_duration(self):
        """测试时长提取"""
        duration = self.extractor._extract_duration(self.test_html_content)
        self.assertEqual(duration, 8397)  # 基于测试HTML中的真实数据

    def test_extract_duration_no_match(self):
        """测试时长提取失败的情况"""
        html_without_duration = "<html><body>No duration here</body></html>"
        duration = self.extractor._extract_duration(html_without_duration)
        self.assertIsNone(duration)

    def test_extract_release_date(self):
        """测试发布日期提取"""
        release_date = self.extractor._extract_release_date(self.test_html_content)
        # 基于测试HTML中的真实数据
        self.assertEqual(release_date, "2021-06-14")

    def test_extract_release_date_no_match(self):
        """测试发布日期提取失败的情况"""
        html_without_date = "<html><body>No release date here</body></html>"
        release_date = self.extractor._extract_release_date(html_without_date)
        self.assertIsNone(release_date)

    def test_extract_genres(self):
        """测试类型提取"""
        genres = self.extractor._extract_genres(self.test_html_content)
        # 这将根据实际HTML内容返回类型列表
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
        genres = self.extractor._extract_genres(japanese_html)
        self.assertEqual(genres, ["単体作品", "中出し"])

        # 测试中文简体
        chinese_html = """
        <div class="text-secondary">
            <span>类型:</span>
            <a href="https://missav.ai/genres/solo" class="text-nord13 font-medium">单体作品</a>,
            <a href="https://missav.ai/genres/creampie" class="text-nord13 font-medium">中出</a>
        </div>
        """
        genres = self.extractor._extract_genres(chinese_html)
        self.assertEqual(genres, ["单体作品", "中出"])

        # 测试英语
        english_html = """
        <div class="text-secondary">
            <span>Genre:</span>
            <a href="https://missav.ai/genres/solo" class="text-nord13 font-medium">Solo Work</a>,
            <a href="https://missav.ai/genres/creampie" class="text-nord13 font-medium">Creampie</a>
        </div>
        """
        genres = self.extractor._extract_genres(english_html)
        self.assertEqual(genres, ["Solo Work", "Creampie"])

    def test_extract_genres_no_fallback(self):
        """测试没有标签时返回空列表"""
        # 测试没有任何语言标签的HTML，应该返回空列表
        no_label_html = """
        <div>
            <a href="https://missav.ai/genres/solo" class="text-nord13 font-medium">单体作品</a>
            <a href="https://missav.ai/genres/cosplay" class="text-nord13 font-medium">角色扮演</a>
            <a href="https://missav.ai/actors/someone" class="text-nord13 font-medium">某演员</a>
        </div>
        """
        genres = self.extractor._extract_genres(no_label_html)
        self.assertEqual(genres, [])

        # 测试完全无关的HTML
        random_html = """
        <div>
            <a href="https://missav.ai/something" class="text-nord13 font-medium">随机内容</a>
            <a href="https://missav.ai/other" class="text-nord13 font-medium">其他内容</a>
        </div>
        """
        genres = self.extractor._extract_genres(random_html)
        self.assertEqual(genres, [])

    def test_get_key_for_url(self):
        """测试URL键生成"""
        test_urls = [
            "https://example.com/video_1080p.m3u8",
            "https://example.com/video_720p.m3u8",
            "https://example.com/video_480p.m3u8",
        ]

        for url in test_urls:
            key = self.extractor._get_key_for_url(url)
            expected_quality = Quality.guess(url)
            self.assertEqual(key, expected_quality)

    @patch("pavone.plugins.extractors.missav_extractor.MissAVExtractor.fetch_webpage")
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
        result = self.extractor._extract_master_playlist(master_url)

        # 验证结果
        self.assertIsInstance(result, dict)
        self.assertGreater(len(result), 0)

        # 验证生成的完整URL
        for quality, url in result.items():
            self.assertTrue(url.startswith("https://surrit.com/test-uuid/"))
            self.assertTrue(url.endswith(".m3u8"))

    @patch("pavone.plugins.extractors.missav_extractor.MissAVExtractor.fetch_webpage")
    def test_extract_master_playlist_failure(self, mock_fetch):
        """测试主播放列表提取失败"""
        mock_response = Mock()
        mock_response.status_code = 404
        mock_fetch.return_value = mock_response

        master_url = "https://surrit.com/invalid-uuid/playlist.m3u8"
        result = self.extractor._extract_master_playlist(master_url)

        self.assertEqual(result, {})

    @patch("pavone.plugins.extractors.missav_extractor.MissAVExtractor.fetch_webpage")
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

        # 设置fetch_webpage的不同返回值
        mock_fetch.side_effect = [mock_page_response, mock_m3u8_response]

        test_url = "https://missav.ai/dm18/sdab-183"
        result = self.extractor.extract(test_url)

        # 验证结果
        self.assertIsInstance(result, list)
        self.assertGreater(len(result), 0)

        # 验证第一个下载项的属性
        if result:
            first_item = result[0]
            self.assertIsInstance(first_item, OperationItem)

    @patch("pavone.plugins.extractors.missav_extractor.MissAVExtractor.fetch_webpage")
    def test_extract_no_uuid(self, mock_fetch):
        """测试没有UUID的提取流程"""
        html_without_uuid = "<html><body>No UUID here</body></html>"
        mock_response = Mock()
        mock_response.text = html_without_uuid
        mock_fetch.return_value = mock_response

        test_url = "https://missav.ai/some-video"
        result = self.extractor.extract(test_url)

        # 没有UUID应该返回空列表
        self.assertEqual(result, [])

    @patch("pavone.plugins.extractors.missav_extractor.MissAVExtractor.fetch_webpage")
    def test_extract_fetch_failure(self, mock_fetch):
        """测试页面获取失败的情况"""
        mock_fetch.side_effect = Exception("Network error")

        test_url = "https://missav.ai/some-video"
        result = self.extractor.extract(test_url)

        # 网络错误应该返回空列表
        self.assertEqual(result, [])

    def test_initialize(self):
        """测试初始化方法"""
        result = self.extractor.initialize()
        self.assertTrue(result)

    def test_cleanup(self):
        """测试清理方法"""
        # cleanup方法应该能正常执行而不抛出异常
        try:
            self.extractor.cleanup()
        except Exception as e:
            self.fail(f"cleanup() raised {e} unexpectedly!")

    def test_execute_with_url(self):
        """测试execute方法使用URL参数"""
        with patch.object(self.extractor, "extract") as mock_extract:
            mock_extract.return_value = []

            test_url = "https://missav.ai/test"
            result = self.extractor.execute(test_url)

            mock_extract.assert_called_once_with(test_url)
            self.assertEqual(result, [])

    def test_execute_without_args(self):
        """测试execute方法无参数"""
        result = self.extractor.execute()
        self.assertEqual(result, [])

    def test_execute_with_non_string_args(self):
        """测试execute方法使用非字符串参数"""
        result = self.extractor.execute(123, 456)
        self.assertEqual(result, [])


if __name__ == "__main__":
    # 设置测试运行时的日志级别
    import logging

    logging.getLogger().setLevel(logging.ERROR)

    unittest.main()

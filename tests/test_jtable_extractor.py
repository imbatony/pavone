"""
JTable提取器测试
"""

import os
import unittest
from datetime import datetime
from typing import Optional
from unittest.mock import Mock, patch

from pavone.models.metadata import BaseMetadata, MovieMetadata
from pavone.models.operation import OperationItem
from pavone.plugins.extractors.jtable import JTableExtractor


class DummyTableJTableExtractor(JTableExtractor):
    """可测试的JTable提取器，实现了抽象方法"""

    def initialize(self) -> bool:
        """实现抽象方法"""
        return True

    def execute(self, *args, **kwargs):
        """实现抽象方法"""
        pass


class TestJTableExtractor(unittest.TestCase):
    """JTable提取器测试"""

    def setUp(self):
        """设置测试环境"""
        self.extractor = DummyTableJTableExtractor()

        # 获取测试HTML文件路径
        self.test_html_path = os.path.join(os.path.dirname(__file__), "sites", "jtable.html")

        # 读取测试HTML内容
        with open(self.test_html_path, "r", encoding="utf-8") as f:
            self.test_html_content = f.read()

    def test_initialization(self):
        """测试初始化"""
        self.assertEqual(self.extractor.name, "JTableExtractor")
        self.assertEqual(self.extractor.version, "1.0.0")
        self.assertEqual(self.extractor.priority, 30)
        self.assertIn("jp.jable.tv", self.extractor.supported_domains)
        self.assertEqual(self.extractor.site_name, "Jable")

    def test_can_handle_valid_urls(self):
        """测试能处理的有效URL"""
        valid_urls = [
            "https://jp.jable.tv/videos/dass-247/",
            "http://jp.jable.tv/videos/dass-247/",
            "https://jp.jable.tv/some-video",
            "http://jp.jable.tv/some-video",
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
            "https://missav.ai/video",
            "not-a-url",
            "ftp://jp.jable.tv/video",
            "",
        ]

        for url in invalid_urls:
            with self.subTest(url=url):
                self.assertFalse(self.extractor.can_handle(url))

    def test_extract_cover(self):
        """测试封面图片提取功能"""
        cover_url = self.extractor._extract_cover(self.test_html_content)
        expected_cover = "https://assets-cdn.jable.tv/contents/videos_screenshots/36000/36865/preview.jpg"
        self.assertEqual(cover_url, expected_cover)

    def test_extract_cover_no_match(self):
        """测试封面图片提取失败的情况"""
        html_without_cover = "<html><body>No cover here</body></html>"
        cover_url = self.extractor._extract_cover(html_without_cover)
        self.assertIsNone(cover_url)

    def test_extract_code_title(self):
        """测试标题和代码提取"""
        code, title = self.extractor._extract_code_title(self.test_html_content)
        self.assertEqual(code, "DASS-247")
        self.assertEqual(title, "媚薬絶頂への恐怖に悪堕ちする誇り高き女捜査官。 黒川すみれ 美咲かんな")

    def test_extract_code_title_no_space(self):
        """测试标题没有空格分隔符的情况"""
        html_with_title_no_space = '<meta property="og:title" content="SomeVideoTitle"'
        code, title = self.extractor._extract_code_title(html_with_title_no_space)
        # 当没有空格分隔时，应该使用hash作为code
        self.assertNotEqual(code, "SomeVideoTitle")
        self.assertEqual(title, "SomeVideoTitle")

    def test_extract_code_title_no_match(self):
        """测试标题和代码提取失败的情况"""
        html_without_title = "<html><body>No title here</body></html>"
        with self.assertRaises(ValueError) as context:
            self.extractor._extract_code_title(html_without_title)
        self.assertIn("未找到视频标题", str(context.exception))

    def test_extract_actors(self):
        """测试演员提取"""
        actors = self.extractor._extract_actors(self.test_html_content)
        expected_actors = ["美咲かんな"]
        self.assertEqual(actors, expected_actors)

    def test_extract_actors_no_match(self):
        """测试演员提取失败的情况"""
        html_without_actors = "<html><body>No actors here</body></html>"
        actors = self.extractor._extract_actors(html_without_actors)
        self.assertEqual(actors, [])

    def test_extract_release_date(self):
        """测试发布日期提取"""
        release_date = self.extractor._extract_release_date(self.test_html_content)
        expected_date = datetime(2023, 10, 20)
        self.assertEqual(release_date, expected_date)

    def test_extract_release_date_no_match(self):
        """测试发布日期提取失败的情况"""
        html_without_date = "<html><body>No release date here</body></html>"
        release_date = self.extractor._extract_release_date(self.test_html_content.replace("発売された", "removed"))
        # 应该返回当前日期
        self.assertIsInstance(release_date, datetime)
        # 检查是否是最近的日期（今天）
        now = datetime.now()
        self.assertEqual(release_date.date(), now.date())

    def test_extract_release_date_invalid_format(self):
        """测试发布日期格式无效的情况"""
        html_invalid_date = '<span class="inactive-color">発売された invalid-date</span>'
        release_date = self.extractor._extract_release_date(html_invalid_date)
        # 应该返回当前日期
        self.assertIsInstance(release_date, datetime)
        now = datetime.now()
        self.assertEqual(release_date.date(), now.date())

    def test_extract_genres(self):
        """测试类型提取"""
        genres = self.extractor._extract_genres(self.test_html_content)
        # 基于测试HTML内容 - 只包含实际在categories中的genre
        expected_genres = ["ビーディーエスエム", "レズ", "パンスト", "ドラマ"]
        self.assertEqual(genres, expected_genres)

    def test_extract_genres_no_match(self):
        """测试类型提取失败的情况"""
        html_without_genres = "<html><body>No genres here</body></html>"
        genres = self.extractor._extract_genres(html_without_genres)
        self.assertEqual(genres, [])

    def test_extract_tags(self):
        """测试标签提取"""
        tags = self.extractor._extract_tags(self.test_html_content)
        # 基于测试HTML内容中的实际标签，按出现顺序
        expected_tags = [
            "少女",
            "パンスト",
            "3P",
            "痴女",
            "黒ストッキング",
            "調教・奴隷",
            "美脚",
            "辱め",
            "キス",
            "ガーターベルト",
            "ラブポーション",
            "男M",
            "捜査官",
        ]
        # 只检查测试中预期的标签是否全部存在，忽略顺序
        for expected_tag in expected_tags:
            self.assertIn(expected_tag, tags)

    def test_extract_tags_no_match(self):
        """测试标签提取失败的情况"""
        html_without_tags = "<html><body>No tags here</body></html>"
        tags = self.extractor._extract_tags(html_without_tags)
        self.assertEqual(tags, [])

    @patch("pavone.plugins.extractors.jtable.JTableExtractor.fetch")
    def test_extract_success(self, mock_fetch):
        """测试成功提取的情况"""
        # 模拟网页响应
        mock_response = Mock()
        mock_response.text = self.test_html_content
        mock_fetch.return_value = mock_response

        url = "https://jp.jable.tv/videos/dass-247/"
        result = self.extractor.extract(url)

        # 验证调用
        mock_fetch.assert_called_once_with(url)

        # 验证结果
        self.assertEqual(len(result), 1)

        main_item = result[0]
        self.assertEqual(
            main_item.get_url(),
            "https://gmas-clena.mushroomtrack.com/hls/bXNwsqF7g4nB5Wr29gK2DA/1750698775/36000/36865/36865.m3u8",
        )
        self.assertEqual(main_item.get_title(), "媚薬絶頂への恐怖に悪堕ちする誇り高き女捜査官。 黒川すみれ 美咲かんな")
        self.assertEqual(main_item.get_code(), "DASS-247")
        self.assertEqual(main_item.get_actors(), ["美咲かんな"])
        self.assertEqual(main_item.get_year(), 2023)

        # 验证子项目
        children = main_item.get_children()
        self.assertEqual(len(children), 2)  # cover和metadata

        # 验证封面项目和元数据项目
        cover_item = None
        metadata_item: Optional[OperationItem] = None
        for child in children:
            if child.get_subtype() == "cover":
                cover_item = child
            elif child.item_type == "metadata":
                metadata_item = child

        # 验证封面项目存在
        self.assertIsNotNone(cover_item)
        if cover_item:
            self.assertEqual(
                cover_item.get_url(), "https://assets-cdn.jable.tv/contents/videos_screenshots/36000/36865/preview.jpg"
            )

        # 验证元数据项目存在
        self.assertIsNotNone(metadata_item)
        if metadata_item:
            # 验证元数据内容
            metadata: Optional[BaseMetadata] = metadata_item.get_metadata()
            self.assertIsNotNone(metadata)
            self.assertIsInstance(metadata, MovieMetadata)
            # 验证元数据字段
            m_metadata: MovieMetadata = metadata  # type: ignore # 类型转换
            if metadata:
                self.assertEqual(m_metadata.code, "DASS-247")
                self.assertEqual(m_metadata.title, "媚薬絶頂への恐怖に悪堕ちする誇り高き女捜査官。 黒川すみれ 美咲かんな")
                self.assertEqual(m_metadata.actors, ["美咲かんな"])
                # release_date 已转换为 premiered 格式
                self.assertEqual(m_metadata.premiered, "2023-10-20")
                self.assertEqual(m_metadata.year, 2023)
                self.assertEqual(m_metadata.site, "Jable")
                self.assertIsNotNone(m_metadata.genres)
                self.assertIn("ビーディーエスエム", m_metadata.genres)  # type: ignore
                self.assertIsNotNone(m_metadata.tags)
                self.assertIn("黒ストッキング", m_metadata.tags)  # type: ignore

    @patch("pavone.plugins.extractors.jtable.JTableExtractor.fetch")
    def test_extract_invalid_url(self, mock_fetch):
        """测试无效URL的情况"""
        url = "https://invalid-site.com/video"
        result = self.extractor.extract(url)

        # 不应该调用fetch
        mock_fetch.assert_not_called()

        # 应该返回空列表
        self.assertEqual(result, [])

    @patch("pavone.plugins.extractors.jtable.JTableExtractor.fetch")
    def test_extract_fetch_failure(self, mock_fetch):
        """测试网页获取失败的情况"""
        mock_fetch.return_value = None

        url = "https://jp.jable.tv/videos/dass-247/"
        result = self.extractor.extract(url)

        # 验证调用
        mock_fetch.assert_called_once_with(url)

        # 应该返回空列表
        self.assertEqual(result, [])

    @patch("pavone.plugins.extractors.jtable.JTableExtractor.fetch")
    def test_extract_no_m3u8(self, mock_fetch):
        """测试没有找到m3u8的情况"""
        mock_response = Mock()
        mock_response.text = "<html><body>No m3u8 here</body></html>"
        mock_fetch.return_value = mock_response

        url = "https://jp.jable.tv/videos/dass-247/"
        result = self.extractor.extract(url)

        # 验证调用
        mock_fetch.assert_called_once_with(url)

        # 应该返回空列表
        self.assertEqual(result, [])

    @patch("pavone.plugins.extractors.jtable.JTableExtractor.fetch")
    def test_extract_exception_handling(self, mock_fetch):
        """测试异常处理"""
        mock_fetch.side_effect = Exception("Network error")

        url = "https://jp.jable.tv/videos/dass-247/"
        result = self.extractor.extract(url)

        # 验证调用
        mock_fetch.assert_called_once_with(url)

        # 应该返回空列表
        self.assertEqual(result, [])

    @patch("pavone.plugins.extractors.jtable.JTableExtractor.fetch")
    def test_extract_with_missing_cover(self, mock_fetch):
        """测试没有封面的情况"""
        # 创建没有封面的HTML
        html_without_cover = self.test_html_content.replace(
            '<meta property="og:image" content="https://assets-cdn.jable.tv/contents/videos_screenshots/36000/36865/preview.jpg"/>',
            "",
        )

        mock_response = Mock()
        mock_response.text = html_without_cover
        mock_fetch.return_value = mock_response

        url = "https://jp.jable.tv/videos/dass-247/"
        result = self.extractor.extract(url)

        # 验证结果
        self.assertEqual(len(result), 1)

        main_item = result[0]
        children = main_item.get_children()
        # 应该只有metadata子项目，没有cover
        self.assertEqual(len(children), 1)
        self.assertEqual(children[0].item_type, "metadata")


if __name__ == "__main__":
    unittest.main()

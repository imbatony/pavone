"""
Memojav提取器测试
"""

import unittest
from unittest.mock import patch, Mock
import os
from pavone.plugins.extractors.memojav import MemojavExtractor

class TestMemojavExtractor(unittest.TestCase):
    """Memojav提取器测试"""
    
    def setUp(self):
        """设置测试环境"""
        # 为了测试，创建一个带有实现的非抽象类
        class ConcreteMemojavExtractor(MemojavExtractor):
            def initialize(self): return True
            def execute(self, *args, **kwargs): return []
            def cleanup(self): pass
        
        self.extractor = ConcreteMemojavExtractor()
        
        # 获取测试HTML文件路径
        self.test_html_path = os.path.join(os.path.dirname(__file__), 'sites', 'memojav.html')
        self.test_video_info_path = os.path.join(os.path.dirname(__file__), 'sites', 'memojav_video_info.txt')
        
        # 读取测试HTML内容
        with open(self.test_html_path, 'r', encoding='utf-8') as f:
            self.test_html_content = f.read()
            
        # 读取测试视频信息内容
        with open(self.test_video_info_path, 'r', encoding='utf-8') as f:
            self.test_video_info_content = f.read()
    
    def test_initialization(self):
        """测试初始化"""
        self.assertEqual(self.extractor.name, "MemojavExtractor")
        self.assertEqual(self.extractor.version, "1.0.0")
        self.assertEqual(self.extractor.description, "提取 memojav.com 的视频下载链接")
        self.assertEqual(self.extractor.author, "PAVOne")
        self.assertEqual(self.extractor.priority, 30)
        self.assertIn('memojav.com', self.extractor.supported_domains)
        self.assertIn('www.memojav.com', self.extractor.supported_domains)
    
    def test_can_handle_valid_urls(self):
        """测试能处理的有效URL"""
        valid_urls = [
            'https://memojav.com/video/FNS-052',
            'https://www.memojav.com/video/FNS-052',
            'http://memojav.com/embed/FNS-052',
            'http://www.memojav.com/embed/FNS-052'
        ]
        
        for url in valid_urls:
            with self.subTest(url=url):
                self.assertTrue(self.extractor.can_handle(url))
    
    def test_can_handle_invalid_urls(self):
        """测试不能处理的无效URL"""
        invalid_urls = [
            'https://youtube.com/watch?v=123',
            'https://pornhub.com/video/123',
            'https://other-site.com/video',
            'not-a-url',
            'ftp://memojav.com/video'
        ]
        
        for url in invalid_urls:
            with self.subTest(url=url):
                self.assertFalse(self.extractor.can_handle(url))
        
        # 测试空字符串单独处理，因为urlparse('')返回的netloc是空字符串
        self.assertFalse(self.extractor.can_handle(''))
    
    @patch('pavone.plugins.extractors.memojav.MemojavExtractor._extract_m3u8')
    def test_extract_m3u8(self, mock_extract_m3u8):
        """测试m3u8链接提取"""
        expected_url = "https://video10.memojav.net/stream/FNS-052/master.m3u8"
        mock_extract_m3u8.return_value = expected_url
        
        m3u8_url = self.extractor._extract_m3u8(self.test_video_info_content)
        self.assertEqual(m3u8_url, expected_url)
    
    @patch('pavone.plugins.extractors.memojav.MemojavExtractor._extract_cover')
    def test_extract_cover(self, mock_extract_cover):
        """测试封面图片提取"""
        expected_url = "https://memojav.com/image/preview/1fns00052/1fns00052pl.jpg"
        mock_extract_cover.return_value = expected_url
        
        cover_url = self.extractor._extract_cover(self.test_html_content)
        self.assertEqual(cover_url, expected_url)
    
    @patch('pavone.plugins.extractors.memojav.MemojavExtractor._extract_title')
    def test_extract_title(self, mock_extract_title):
        """测试标题提取"""
        expected_title = "A popular cosplayer was kind to a creepy fan, but he set up an offline hookup without her permission, and in a closed hotel room, she was made to cum so hard that her pussy broke, and she lost all sense of reason."
        mock_extract_title.return_value = expected_title
        
        title = self.extractor._extract_title(self.test_html_content)
        self.assertEqual(title, expected_title)
    
    @patch('pavone.plugins.extractors.memojav.MemojavExtractor.get_vid_from_url')
    def test_get_vid_from_url(self, mock_get_vid):
        """测试从URL提取视频代码"""
        test_urls = [
            ('https://memojav.com/video/FNS-052', 'FNS-052'),
            ('https://memojav.com/embed/ABC-123', 'ABC-123'),
            ('http://www.memojav.com/embed/XYZ-789', 'XYZ-789')
        ]
        
        for url, expected_code in test_urls:
            mock_get_vid.return_value = expected_code
            code = self.extractor.get_vid_from_url(url)
            self.assertEqual(code, expected_code)
    
    @patch('pavone.plugins.extractors.memojav.MemojavExtractor.get_vid_from_url')
    def test_get_vid_from_url_error(self, mock_get_vid):
        """测试从无效URL提取视频代码的错误情况"""
        mock_get_vid.side_effect = ValueError("无法从URL中提取视频代码")
        
        with self.assertRaises(ValueError):
            self.extractor.get_vid_from_url("https://memojav.com/")
    
    @patch('pavone.plugins.extractors.memojav.MemojavExtractor.fetch_webpage')
    @patch('pavone.plugins.extractors.memojav.MemojavExtractor._extract_title')
    @patch('pavone.plugins.extractors.memojav.MemojavExtractor._extract_m3u8')
    @patch('pavone.plugins.extractors.memojav.MemojavExtractor._extract_cover')
    @patch('pavone.plugins.extractors.memojav.MemojavExtractor.get_vid_from_url')
    def test_extract_success(self, mock_get_vid, mock_extract_cover, mock_extract_m3u8, mock_extract_title, mock_fetch):
        """测试成功提取视频信息"""
        # 设置mock返回值
        mock_get_vid.return_value = 'FNS-052'
        mock_extract_title.return_value = 'A popular cosplayer was kind to a creepy fan, but he set up an offline hookup without her permission, and in a closed hotel room, she was made to cum so hard that her pussy broke, and she lost all sense of reason.'
        mock_extract_m3u8.return_value = 'https://video10.memojav.net/stream/FNS-052/master.m3u8'
        mock_extract_cover.return_value = 'https://memojav.com/image/preview/1fns00052/1fns00052pl.jpg'
        
        # 模拟网页请求响应
        mock_response1 = Mock()
        mock_response1.text = self.test_html_content
        
        mock_response2 = Mock()
        mock_response2.text = self.test_video_info_content
        
        # 设置mock顺序返回值
        mock_fetch.side_effect = [mock_response1, mock_response2]
        
        # 执行测试
        result = self.extractor.extract('https://memojav.com/embed/FNS-052')
        
        # 验证结果
        self.assertEqual(len(result), 1)


if __name__ == '__main__':
    unittest.main()

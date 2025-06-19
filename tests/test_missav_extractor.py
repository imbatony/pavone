"""
MissAV 提取器测试
"""

import unittest
from unittest.mock import patch, MagicMock
from pavone.plugins.extractors.missav_extractor import MissAVExtractor
from pavone.core.downloader.options import LinkType


class TestMissAVExtractor(unittest.TestCase):
    """MissAV 提取器测试类"""
    
    def setUp(self):
        """设置测试环境"""
        self.extractor = MissAVExtractor()
        self.extractor.initialize()
    
    def test_can_handle_valid_urls(self):
        """测试能否正确识别 MissAV URL"""
        valid_urls = [
            'https://missav.ai/video123',
            'https://www.missav.ai/zh/123456',
            'https://missav.com/video/test',
            'https://www.missav.com/en/video123'
        ]
        
        for url in valid_urls:
            with self.subTest(url=url):
                self.assertTrue(self.extractor.can_handle(url))
    
    def test_can_handle_invalid_urls(self):
        """测试不能处理非 MissAV URL"""
        invalid_urls = [
            'https://youtube.com/watch?v=123',
            'https://example.com/video',
            'https://pornhub.com/view_video.php?viewkey=123',
            'not_a_url'
        ]
        
        for url in invalid_urls:
            with self.subTest(url=url):
                self.assertFalse(self.extractor.can_handle(url))
    
    @patch('requests.get')
    def test_extract_m3u8_video(self, mock_get):
        """测试提取 M3U8 视频链接"""
        # 读取真实的MissAV页面内容
        with open('tests/sites/missav.html', 'r', encoding='utf-8') as f:
            real_html_content = f.read()        # 读取真实的M3U8链接内容
        with open('tests/sites/missav.m3u8', 'r', encoding='utf-8') as f:
            real_m3u8_content = f.read()    
        # 模拟HTML响应
        mock_response1 = MagicMock()
        mock_response1.text = real_html_content
        mock_response1.status_code = 200
        mock_response1.raise_for_status = MagicMock()
        # 模拟大师m3u8链接返回
        mock_response2 = MagicMock()
        mock_response2.text = real_m3u8_content
        mock_response2.status_code = 200
        mock_response2.raise_for_status = MagicMock()
        # 设置模拟请求返回
        # 依次返回HTML和M3U8内容
        mock_get.side_effect = [mock_response1, mock_response2]

        
        url = 'https://missav.ai/dm18/ja/sdab-183'
        options = self.extractor.extract(url)
        
        self.assertEqual(len(options), 4)
        if len(options) > 0:
            # MissAV提取器现在只提取M3U8流媒体链接
            self.assertEqual(options[0].link_type, LinkType.STREAM)
            self.assertIsNotNone(options[0].filename)
            if options[0].filename:
                # 文件名应该以.mp4结尾（即使是M3U8流也会转换为MP4）
                self.assertTrue(options[0].filename.endswith('.mp4'))
                # 检查文件名是否包含真实页面的标题内容
                self.assertIn('SDAB-183', options[0].filename)
    
    @patch('requests.get')
    def test_extract_m3u8_video2(self, mock_get):
        """测试提取 M3U8 视频链接"""
        # 读取真实的MissAV页面内容
        with open('tests/sites/missav2.html', 'r', encoding='utf-8') as f:
            real_html_content = f.read()        # 读取真实的M3U8链接内容
        with open('tests/sites/missav2.m3u8', 'r', encoding='utf-8') as f:
            real_m3u8_content = f.read()    
        # 模拟HTML响应
        mock_response1 = MagicMock()
        mock_response1.text = real_html_content
        mock_response1.status_code = 200
        mock_response1.raise_for_status = MagicMock()
        # 模拟大师m3u8链接返回
        mock_response2 = MagicMock()
        mock_response2.text = real_m3u8_content
        mock_response2.status_code = 200
        mock_response2.raise_for_status = MagicMock()        # 设置模拟请求返回
        # 依次返回HTML和M3U8内容
        mock_get.side_effect = [mock_response1, mock_response2]
        
        url = 'https://missav.ai/dm18/ja/mds-884'
        options = self.extractor.extract(url)
        self.assertEqual(len(options), 3)  # missav2.m3u8只有3个分辨率
        if len(options) > 0:
            # MissAV提取器现在只提取M3U8流媒体链接
            self.assertEqual(options[0].link_type, LinkType.STREAM)
            self.assertIsNotNone(options[0].filename)
            if options[0].filename:
                # 文件名应该以.mp4结尾（即使是M3U8流也会转换为MP4）
                self.assertTrue(options[0].filename.endswith('.mp4'))
                # 检查文件名是否包含真实页面的标题内容，对于第二个测试使用MDS-884
                self.assertIn('MDS-884', options[0].filename)
    
    def test_sanitize_filename(self):
        """测试文件名清理功能"""
        test_cases = [
            ('Test<>Video', 'Test__Video'),
            ('Video: Title', 'Video_ Title'),
            ('Normal Video', 'Normal Video'),
            ('', 'video'),
            ('A' * 250, 'A' * 200)
        ]
        
        for input_name, expected in test_cases:
            with self.subTest(input_name=input_name):
                result = self.extractor.sanitize_filename(input_name)
                self.assertEqual(result, expected)
    
    @patch('requests.get')
    def test_extract_handles_request_error(self, mock_get):
        """测试处理请求错误"""
        mock_get.side_effect = Exception("Network error")
        
        url = 'https://missav.ai/video123'
        options = self.extractor.extract(url)
        
        self.assertEqual(len(options), 0)
    
    def test_plugin_properties(self):
        """测试插件属性"""
        self.assertEqual(self.extractor.name, "MissAVExtractor")
        self.assertEqual(self.extractor.version, "1.0.0")
        self.assertEqual(self.extractor.priority, 30)
        self.assertIn("missav.ai", self.extractor.description.lower())


if __name__ == '__main__':
    unittest.main()

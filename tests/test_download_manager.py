"""
测试下载管理器
"""

import unittest
from unittest.mock import Mock, patch, MagicMock
from pavone.config.settings import DownloadConfig
from pavone.cli.commands.download import DownloadManager, create_download_manager
from pavone.core.downloader.options import DownloadOpt, LinkType
from pavone.plugins.manager import PluginManager


class TestDownloadManager(unittest.TestCase):
    """测试下载管理器类"""
    
    def setUp(self):
        """设置测试环境"""
        self.config = DownloadConfig(
            output_dir="./test_downloads",
            max_concurrent_downloads=2,
            timeout=10
        )
        
        # 创建模拟的插件管理器
        self.mock_plugin_manager = Mock(spec=PluginManager)
        self.mock_plugin_manager.extractor_plugins = []
        
    def test_init(self):
        """测试初始化"""
        manager = DownloadManager(self.config, self.mock_plugin_manager)
        
        self.assertEqual(manager.config, self.config)
        self.assertEqual(manager.plugin_manager, self.mock_plugin_manager)
        self.assertIsNotNone(manager.http_downloader)
        self.assertIsNotNone(manager.m3u8_downloader)
    
    def test_create_download_manager(self):
        """测试便利函数"""
        manager = create_download_manager(self.config, self.mock_plugin_manager)
        self.assertIsInstance(manager, DownloadManager)
    
    def test_extract_download_options_success(self):
        """测试成功提取下载选项"""
        # 创建模拟提取器
        mock_extractor = Mock()
        mock_extractor.name = "TestExtractor"
        mock_extractor.extract.return_value = [
            DownloadOpt("https://example.com/video.mp4", "video.mp4", link_type=LinkType.VIDEO)
        ]
        
        # 设置插件管理器返回提取器
        self.mock_plugin_manager.get_extractor_for_url.return_value = mock_extractor
        
        manager = DownloadManager(self.config, self.mock_plugin_manager)
        
        # 测试提取
        url = "https://example.com/test"
        options = manager.extract_download_options(url)
        
        self.assertEqual(len(options), 1)
        self.assertEqual(options[0].url, "https://example.com/video.mp4")
        
        # 验证调用
        self.mock_plugin_manager.get_extractor_for_url.assert_called_once_with(url)
        mock_extractor.extract.assert_called_once_with(url)
    
    def test_extract_download_options_no_extractor(self):
        """测试没有找到提取器的情况"""
        self.mock_plugin_manager.get_extractor_for_url.return_value = None
        
        manager = DownloadManager(self.config, self.mock_plugin_manager)
        
        with self.assertRaises(ValueError) as context:
            manager.extract_download_options("https://example.com/test")
        
        self.assertIn("没有找到能处理URL的提取器", str(context.exception))
    
    def test_extract_download_options_no_options(self):
        """测试提取器返回空选项的情况"""
        mock_extractor = Mock()
        mock_extractor.name = "TestExtractor"
        mock_extractor.extract.return_value = []
        
        self.mock_plugin_manager.get_extractor_for_url.return_value = mock_extractor
        
        manager = DownloadManager(self.config, self.mock_plugin_manager)
        
        with self.assertRaises(ValueError) as context:
            manager.extract_download_options("https://example.com/test")
        
        self.assertIn("没有找到下载选项", str(context.exception))
    
    def test_get_downloader_for_option_stream(self):
        """测试为流媒体选择下载器"""
        manager = DownloadManager(self.config, self.mock_plugin_manager)
        
        # 测试stream类型
        stream_option = DownloadOpt(
            "https://example.com/stream.m3u8",
            link_type=LinkType.STREAM
        )
        
        downloader_type, downloader = manager.get_downloader_for_option(stream_option)
        self.assertEqual(downloader_type, "M3U8")
        self.assertEqual(downloader, manager.m3u8_downloader)
    
    def test_get_downloader_for_option_http(self):
        """测试为其他类型选择HTTP下载器"""
        manager = DownloadManager(self.config, self.mock_plugin_manager)
        
        # 测试video类型
        video_option = DownloadOpt(
            "https://example.com/video.mp4",
            link_type=LinkType.VIDEO
        )
        
        downloader_type, downloader = manager.get_downloader_for_option(video_option)
        self.assertEqual(downloader_type, "HTTP")
        self.assertEqual(downloader, manager.http_downloader)
        
        # 测试image类型
        image_option = DownloadOpt(
            "https://example.com/image.jpg",
            link_type=LinkType.IMAGE
        )
        
        downloader_type, downloader = manager.get_downloader_for_option(image_option)
        self.assertEqual(downloader_type, "HTTP")
        self.assertEqual(downloader, manager.http_downloader)
    
    def test_select_download_option_single(self):
        """测试单个选项的选择"""
        manager = DownloadManager(self.config, self.mock_plugin_manager)        
        options = [DownloadOpt("https://example.com/video.mp4", display_name="测试视频")]
        
        # 由于已经替换为logger，我们只需要验证功能正常工作
        selected = manager.select_download_option(options)
        self.assertEqual(selected, options[0])
    
    @patch('builtins.input')
    def test_select_download_option_multiple(self, mock_input):
        """测试多个选项的选择"""
        manager = DownloadManager(self.config, self.mock_plugin_manager)
        
        options = [
            DownloadOpt("https://example.com/video1.mp4", display_name="视频1", quality="1080p"),
            DownloadOpt("https://example.com/video2.mp4", display_name="视频2", quality="720p")
        ]
        
        # 模拟用户选择第一个选项
        mock_input.return_value = "1"        
        with patch('builtins.print'):
            selected = manager.select_download_option(options)
            
            self.assertEqual(selected, options[0])
    
    @patch('builtins.input')
    def test_select_download_option_cancel(self, mock_input):
        """测试用户取消选择"""
        manager = DownloadManager(self.config, self.mock_plugin_manager)
        
        # 创建多个选项，这样才会要求用户选择
        options = [
            DownloadOpt("https://example.com/video1.mp4", display_name="测试视频1"),
            DownloadOpt("https://example.com/video2.mp4", display_name="测试视频2")
        ]
        
        # 模拟用户选择取消
        mock_input.return_value = "0"
        
        with patch('builtins.print'):
            with self.assertRaises(ValueError) as context:
                manager.select_download_option(options)
            
            self.assertIn("用户取消了下载", str(context.exception))
    
    @patch('pavone.core.downloader.download_manager.DownloadManager.extract_download_options')
    @patch('pavone.core.downloader.download_manager.DownloadManager.select_download_option')
    @patch('pavone.core.downloader.download_manager.DownloadManager.get_downloader_for_option')
    def test_download_from_url_success(self, mock_get_downloader, mock_select, mock_extract):
        """测试完整下载流程成功"""
        manager = DownloadManager(self.config, self.mock_plugin_manager)
        
        # 设置模拟返回值
        test_option = DownloadOpt("https://example.com/video.mp4", display_name="测试视频")
        mock_extract.return_value = [test_option]
        mock_select.return_value = test_option
        
        mock_downloader = Mock()
        mock_downloader.download.return_value = True
        mock_get_downloader.return_value = ("HTTP", mock_downloader)
        
        # 执行下载
        with patch('builtins.print'):
            result = manager.download_from_url("https://example.com/test")
        
        self.assertTrue(result)
        mock_extract.assert_called_once()
        mock_select.assert_called_once()
        mock_get_downloader.assert_called_once()
        mock_downloader.download.assert_called_once()
    
    @patch('pavone.core.downloader.download_manager.DownloadManager.get_downloader_for_option')
    def test_download_option_success(self, mock_get_downloader):
        """测试直接下载选项成功"""
        manager = DownloadManager(self.config, self.mock_plugin_manager)
        
        test_option = DownloadOpt("https://example.com/video.mp4", display_name="测试视频")
        
        mock_downloader = Mock()
        mock_downloader.download.return_value = True
        mock_get_downloader.return_value = ("HTTP", mock_downloader)
        
        with patch('builtins.print'):
            result = manager.download_option(test_option)
        
        self.assertTrue(result)
        mock_downloader.download.assert_called_once_with(test_option, None)


if __name__ == '__main__':
    unittest.main()

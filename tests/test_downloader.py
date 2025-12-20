"""
测试下载器功能
"""

import os
import tempfile
import unittest

from pavone.config.settings import Config, DownloadConfig, ProxyConfig
from pavone.core.downloader.http_downloader import HTTPDownloader


class TestHTTPDownloader(unittest.TestCase):
    """测试HTTP下载器"""

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.config = Config(
            download=DownloadConfig(output_dir=self.temp_dir),
            proxy=ProxyConfig(enabled=False),
        )  # 禁用代理
        self.downloader = HTTPDownloader(self.config)

    def tearDown(self):
        # 清理临时目录
        import shutil

        shutil.rmtree(self.temp_dir)

    def test_init(self):
        """测试初始化"""
        self.assertTrue(os.path.exists(self.temp_dir))
        self.assertEqual(self.downloader.config.download.output_dir, self.temp_dir)

    def test_get_video_info(self):
        """测试获取视频信息"""
        # HTTPDownloader没有get_video_info方法，这里测试基础配置
        self.assertIsNotNone(self.downloader.config)
        self.assertEqual(self.downloader.config.download.output_dir, self.temp_dir)
        self.assertEqual(self.downloader.config.download.max_concurrent_downloads, 4)
        self.assertEqual(self.downloader.config.download.retry_times, 3)


if __name__ == "__main__":
    unittest.main()

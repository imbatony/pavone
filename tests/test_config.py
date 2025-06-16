"""
测试配置管理功能
"""

import unittest
import tempfile
import json
from pathlib import Path
from pavone.config.settings import ConfigManager, Config, DownloadConfig, OrganizeConfig, SearchConfig, ProxyConfig


class TestConfigManager(unittest.TestCase):
    """测试配置管理器"""
    
    def setUp(self):
        """设置测试环境"""
        self.temp_dir = tempfile.mkdtemp()
        self.config_manager = ConfigManager(self.temp_dir)
    
    def tearDown(self):
        """清理测试环境"""
        import shutil
        shutil.rmtree(self.temp_dir)
    
    def test_init_with_default_config(self):
        """测试使用默认配置初始化"""
        self.assertTrue(Path(self.temp_dir).exists())
        self.assertEqual(self.config_manager.config_dir, Path(self.temp_dir))
        self.assertIsInstance(self.config_manager.config, Config)
    
    def test_save_and_load_config(self):
        """测试保存和加载配置"""
        # 修改配置 - 使用绝对路径避免验证时的路径转换
        test_download_dir = str(Path(self.temp_dir) / "test_downloads")
        self.config_manager.config.download.output_dir = test_download_dir
        self.config_manager.config.download.max_concurrent_downloads = 5
        self.config_manager.config.proxy.enabled = True
        self.config_manager.config.proxy.http_proxy = "http://127.0.0.1:7890"
        
        # 保存配置
        self.config_manager.save_config()
        
        # 验证配置文件存在
        self.assertTrue(self.config_manager.config_file.exists())
        
        # 创建新的配置管理器来测试加载
        new_config_manager = ConfigManager(self.temp_dir)
        
        # 验证配置正确加载
        self.assertEqual(new_config_manager.config.download.output_dir, test_download_dir)
        self.assertEqual(new_config_manager.config.download.max_concurrent_downloads, 5)
        self.assertTrue(new_config_manager.config.proxy.enabled)
        self.assertEqual(new_config_manager.config.proxy.http_proxy, "http://127.0.0.1:7890")
    
    def test_config_validation(self):
        """测试配置验证功能"""
        # 设置无效配置
        self.config_manager.config.download.max_concurrent_downloads = -1
        self.config_manager.config.download.retry_times = -1
        self.config_manager.config.download.timeout = 0
        self.config_manager.config.search.max_results_per_site = 0
        self.config_manager.config.organize.organize_by = "invalid"
        self.config_manager.config.search.enabled_sites = []
        
        # 运行验证
        result = self.config_manager.validate_and_fix_config()
        
        # 验证修复结果
        self.assertTrue(result)
        self.assertEqual(self.config_manager.config.download.max_concurrent_downloads, 3)
        self.assertEqual(self.config_manager.config.download.retry_times, 3)
        self.assertEqual(self.config_manager.config.download.timeout, 30)
        self.assertEqual(self.config_manager.config.search.max_results_per_site, 20)
        self.assertEqual(self.config_manager.config.organize.organize_by, "studio")
        self.assertEqual(self.config_manager.config.search.enabled_sites, ["javbus", "javlibrary", "pornhub"])
    
    def test_proxy_sync(self):
        """测试代理设置同步"""
        # 设置代理配置
        self.config_manager.config.proxy.enabled = True
        self.config_manager.config.proxy.http_proxy = "http://127.0.0.1:7890"
        self.config_manager.config.proxy.https_proxy = "http://127.0.0.1:7890"
        
        # 同步设置
        self.config_manager.config._sync_proxy_settings()
        
        # 验证同步结果
        self.assertTrue(self.config_manager.config.download.proxy_enabled)
        self.assertEqual(self.config_manager.config.download.http_proxy, "http://127.0.0.1:7890")
        self.assertEqual(self.config_manager.config.download.https_proxy, "http://127.0.0.1:7890")
    
    def test_reset_config(self):
        """测试重置配置"""
        # 修改配置
        self.config_manager.config.download.output_dir = "/custom/path"
        self.config_manager.config.download.max_concurrent_downloads = 10
        
        # 重置配置
        self.config_manager.reset_config()
        
        # 验证配置已重置为默认值
        self.assertEqual(self.config_manager.config.download.output_dir, "./downloads")
        self.assertEqual(self.config_manager.config.download.max_concurrent_downloads, 3)
    
    def test_update_config(self):
        """测试更新配置"""
        # 使用update_config方法更新 - 使用绝对路径
        new_download_dir = str(Path(self.temp_dir) / "new_downloads")
        new_download_config = DownloadConfig(
            output_dir=new_download_dir,
            max_concurrent_downloads=8
        )
        
        self.config_manager.update_config(download=new_download_config)
        
        # 验证配置已更新
        self.assertEqual(self.config_manager.config.download.output_dir, new_download_dir)
        self.assertEqual(self.config_manager.config.download.max_concurrent_downloads, 8)
    
    def test_invalid_config_file(self):
        """测试处理无效的配置文件"""
        # 创建无效的JSON文件
        with open(self.config_manager.config_file, 'w') as f:
            f.write("invalid json content")
        
        # 重新加载配置
        self.config_manager.load_config()
        
        # 验证使用了默认配置，但路径会被转换为绝对路径
        expected_download_dir = str(Path(self.temp_dir) / "downloads")
        self.assertEqual(self.config_manager.config.download.output_dir, expected_download_dir)
        self.assertEqual(self.config_manager.config.download.max_concurrent_downloads, 3)


if __name__ == '__main__':
    unittest.main()

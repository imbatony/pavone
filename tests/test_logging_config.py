"""
日志配置测试
"""

import unittest
import tempfile
import os
from pathlib import Path
from pavone.config.logging_config import LoggingConfig, LogManager, get_logger
from pavone.config.settings import ConfigManager


class TestLoggingConfig(unittest.TestCase):
    """日志配置测试"""
    
    def setUp(self):
        """测试准备"""
        self.temp_dir = tempfile.mkdtemp()
        self.config = LoggingConfig(
            level="DEBUG",
            file_path=os.path.join(self.temp_dir, "test.log")
        )
        self.log_manager = LogManager(self.config)
    
    def tearDown(self):
        """测试清理"""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_logging_config_creation(self):
        """测试日志配置创建"""
        self.assertEqual(self.config.level, "DEBUG")
        self.assertTrue(self.config.console_enabled)
        self.assertTrue(self.config.file_enabled)
        self.assertEqual(self.config.get_log_level(), 10)  # DEBUG = 10
    
    def test_log_manager_configuration(self):
        """测试日志管理器配置"""
        self.log_manager.configure_logging()
        logger = self.log_manager.get_logger("test")
        
        # 测试日志记录
        logger.info("测试信息")
        logger.debug("测试调试信息")
        
        # 检查日志文件是否创建
        self.assertTrue(Path(self.config.file_path).exists())
    
    def test_config_manager_logging(self):
        """测试配置管理器的日志功能"""
        with tempfile.TemporaryDirectory() as temp_dir:
            config_manager = ConfigManager(temp_dir)
            
            # 测试获取日志器
            logger = config_manager.get_logger("test.module")
            logger.info("测试配置管理器日志")
            
            # 测试修改日志级别
            config_manager.set_log_level("ERROR")
            self.assertEqual(config_manager.config.logging.level, "ERROR")
            
            # 测试禁用控制台日志
            config_manager.disable_console_logging()
            self.assertFalse(config_manager.config.logging.console_enabled)
            
            # 测试启用控制台日志
            config_manager.enable_console_logging()
            self.assertTrue(config_manager.config.logging.console_enabled)
    
    def test_logging_config_validation(self):
        """测试日志配置验证"""
        with tempfile.TemporaryDirectory() as temp_dir:
            config_manager = ConfigManager(temp_dir)
            
            # 测试无效的日志级别
            config_manager.config.logging.level = "INVALID"
            config_manager.validate_and_fix_config()
            self.assertEqual(config_manager.config.logging.level, "INFO")
            
            # 测试无效的文件大小
            config_manager.config.logging.max_file_size = -1
            config_manager.validate_and_fix_config()
            self.assertEqual(config_manager.config.logging.max_file_size, 10 * 1024 * 1024)


if __name__ == "__main__":
    unittest.main()

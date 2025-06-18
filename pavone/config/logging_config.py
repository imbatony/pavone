"""
日志管理配置
"""

import logging
import logging.handlers
from pathlib import Path
from typing import Optional, Dict, Any
from dataclasses import dataclass, asdict
import json


@dataclass
class LoggingConfig:
    """日志配置"""
    level: str = "INFO"  # DEBUG, INFO, WARNING, ERROR, CRITICAL
    console_enabled: bool = True
    file_enabled: bool = True
    file_path: str = "./logs/pavone.log"
    max_file_size: int = 10 * 1024 * 1024  # 10MB
    backup_count: int = 5
    format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    date_format: str = "%Y-%m-%d %H:%M:%S"
    
    def get_log_level(self) -> int:
        """获取日志级别"""
        level_map = {
            "DEBUG": logging.DEBUG,
            "INFO": logging.INFO,
            "WARNING": logging.WARNING,
            "ERROR": logging.ERROR,
            "CRITICAL": logging.CRITICAL
        }
        return level_map.get(self.level.upper(), logging.INFO)


class LogManager:
    """日志管理器"""
    
    def __init__(self, config: LoggingConfig):
        self.config = config
        self._loggers: Dict[str, logging.Logger] = {}
        self._configured = False
        
    def configure_logging(self):
        """配置日志系统"""
        if self._configured:
            return
            
        # 创建日志目录
        log_path = Path(self.config.file_path)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        
        # 创建格式化器
        formatter = logging.Formatter(
            fmt=self.config.format,
            datefmt=self.config.date_format
        )
        
        # 配置根日志器
        root_logger = logging.getLogger()
        root_logger.setLevel(self.config.get_log_level())
        
        # 清除现有的处理器
        for handler in root_logger.handlers[:]:
            root_logger.removeHandler(handler)
        
        # 添加控制台处理器
        if self.config.console_enabled:
            console_handler = logging.StreamHandler()
            console_handler.setLevel(self.config.get_log_level())
            console_handler.setFormatter(formatter)
            root_logger.addHandler(console_handler)
        
        # 添加文件处理器（使用轮转文件处理器）
        if self.config.file_enabled:
            file_handler = logging.handlers.RotatingFileHandler(
                filename=self.config.file_path,
                maxBytes=self.config.max_file_size,
                backupCount=self.config.backup_count,
                encoding='utf-8'
            )
            file_handler.setLevel(self.config.get_log_level())
            file_handler.setFormatter(formatter)
            root_logger.addHandler(file_handler)
        
        self._configured = True
    
    def get_logger(self, name: str) -> logging.Logger:
        """获取日志器"""
        if not self._configured:
            self.configure_logging()
            
        if name not in self._loggers:
            logger = logging.getLogger(name)
            self._loggers[name] = logger
        
        return self._loggers[name]
    
    def update_config(self, new_config: LoggingConfig):
        """更新日志配置"""
        self.config = new_config
        self._configured = False
        self.configure_logging()
    
    def set_level(self, level: str):
        """设置日志级别"""
        self.config.level = level
        log_level = self.config.get_log_level()
        
        # 更新所有处理器的级别
        root_logger = logging.getLogger()
        root_logger.setLevel(log_level)
        
        for handler in root_logger.handlers:
            handler.setLevel(log_level)
    
    def disable_console_logging(self):
        """禁用控制台日志"""
        self.config.console_enabled = False
        root_logger = logging.getLogger()
        
        # 移除控制台处理器
        for handler in root_logger.handlers[:]:
            if isinstance(handler, logging.StreamHandler) and not isinstance(handler, logging.FileHandler):
                root_logger.removeHandler(handler)
    
    def enable_console_logging(self):
        """启用控制台日志"""
        if not self.config.console_enabled:
            self.config.console_enabled = True
            self._configured = False
            self.configure_logging()
    
    def disable_file_logging(self):
        """禁用文件日志"""
        self.config.file_enabled = False
        root_logger = logging.getLogger()
        
        # 移除文件处理器
        for handler in root_logger.handlers[:]:
            if isinstance(handler, (logging.FileHandler, logging.handlers.RotatingFileHandler)):
                root_logger.removeHandler(handler)
    
    def enable_file_logging(self):
        """启用文件日志"""
        if not self.config.file_enabled:
            self.config.file_enabled = True
            self._configured = False
            self.configure_logging()
    
    def get_config_dict(self) -> Dict[str, Any]:
        """获取配置字典"""
        return asdict(self.config)
    
    def load_config_from_dict(self, config_dict: Dict[str, Any]):
        """从字典加载配置"""
        self.config = LoggingConfig(**config_dict)
        self._configured = False
        self.configure_logging()


# 日志管理器单例
_log_manager: Optional[LogManager] = None


def get_log_manager() -> LogManager:
    """获取日志管理器单例"""
    global _log_manager
    if _log_manager is None:
        # 使用默认配置
        _log_manager = LogManager(LoggingConfig())
    return _log_manager


def init_log_manager(config: LoggingConfig):
    """初始化日志管理器"""
    global _log_manager
    _log_manager = LogManager(config)
    _log_manager.configure_logging()


def get_logger(name: str) -> logging.Logger:
    """获取日志器的便捷函数"""
    return get_log_manager().get_logger(name)

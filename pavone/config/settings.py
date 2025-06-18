"""
配置管理
"""

import json
from pathlib import Path
from typing import Optional, List
from dataclasses import dataclass, asdict, field
from .logging_config import LoggingConfig, get_log_manager, init_log_manager


@dataclass
class DownloadConfig:
    """下载配置"""
    output_dir: str = "./downloads"
    max_concurrent_downloads: int = 3
    retry_times: int = 3
    timeout: int = 30
    user_agent: str = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    # 代理设置
    proxy_enabled: bool = False
    http_proxy: str = ""
    https_proxy: str = ""


@dataclass
class OrganizeConfig:
    """整理配置"""
    auto_organize: bool = True
    organize_by: str = "studio"  # studio, genre, actor
    naming_pattern: str = "{studio}-{code}-{title}"
    create_nfo: bool = True
    download_cover: bool = True


@dataclass
class SearchConfig:
    """搜索配置"""
    max_results_per_site: int = 20
    search_timeout: int = 10
    enabled_sites: Optional[List[str]] = None
    
    def __post_init__(self):
        if self.enabled_sites is None:
            self.enabled_sites = ["javbus", "javlibrary", "pornhub"]


@dataclass
class ProxyConfig:
    """代理配置"""
    enabled: bool = False
    http_proxy: str = ""
    https_proxy: str = ""


@dataclass
class Config:
    """主配置类"""
    download: DownloadConfig = field(default_factory=DownloadConfig)
    organize: OrganizeConfig = field(default_factory=OrganizeConfig)
    search: SearchConfig = field(default_factory=SearchConfig)
    proxy: ProxyConfig = field(default_factory=ProxyConfig)
    logging: LoggingConfig = field(default_factory=LoggingConfig)
    
    def __post_init__(self):
        # 同步代理设置到下载配置
        self._sync_proxy_settings()
        # 初始化日志管理器
        self._init_logging()
    
    def _sync_proxy_settings(self):
        """将代理设置同步到下载配置中"""
        self.download.proxy_enabled = self.proxy.enabled
        self.download.http_proxy = self.proxy.http_proxy
        self.download.https_proxy = self.proxy.https_proxy
    
    def _init_logging(self):
        """初始化日志系统"""
        init_log_manager(self.logging)


class ConfigManager:
    """配置管理器"""
    
    def __init__(self, config_dir: Optional[str] = None):
        if config_dir is None:
            self.config_dir = Path.home() / ".pavone"
        else:
            self.config_dir = Path(config_dir)
        
        self.config_dir.mkdir(exist_ok=True)
        self.config_file = self.config_dir / "config.json"
        self.config = Config()
        
        self.load_config()
    
    def load_config(self):
        """加载配置"""
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                  # 更新配置
                if 'download' in data:
                    self.config.download = DownloadConfig(**data['download'])
                if 'organize' in data:
                    self.config.organize = OrganizeConfig(**data['organize'])
                if 'search' in data:
                    self.config.search = SearchConfig(**data['search'])
                if 'proxy' in data:
                    self.config.proxy = ProxyConfig(**data['proxy'])
                if 'logging' in data:
                    self.config.logging = LoggingConfig(**data['logging'])
                    
            except Exception as e:
                print(f"加载配置失败: {e}")
                # 使用默认配置
                self.config = Config()
          # 验证并修复配置
        if not self.validate_and_fix_config():
            print("配置验证失败，使用默认配置")
            self.config = Config()
            self.save_config()
    
    def save_config(self):
        """保存配置"""
        try:
            # 在保存前同步代理设置
            self.config._sync_proxy_settings()
            
            config_dict = {
                'download': asdict(self.config.download),
                'organize': asdict(self.config.organize),
                'search': asdict(self.config.search),
                'proxy': asdict(self.config.proxy),
                'logging': asdict(self.config.logging),
            }
            
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(config_dict, f, indent=2, ensure_ascii=False)
                
        except Exception as e:
            print(f"保存配置失败: {e}")
    
    def get_config(self) -> Config:
        """获取配置"""
        return self.config
    
    def update_config(self, **kwargs):
        """更新配置"""
        for key, value in kwargs.items():
            if hasattr(self.config, key):
                setattr(self.config, key, value)
        
        self.save_config()
    
    def reset_config(self):
        """重置配置为默认值"""
        self.config = Config()
        self.save_config()
    
    def validate_and_fix_config(self):
        """验证并修复配置"""
        try:
            # 验证下载目录
            output_dir = Path(self.config.download.output_dir)
            if not output_dir.is_absolute():
                # 如果是相对路径，转换为基于配置目录的绝对路径
                self.config.download.output_dir = str(self.config_dir / "downloads")
            
            # 验证并发下载数
            if self.config.download.max_concurrent_downloads <= 0:
                self.config.download.max_concurrent_downloads = 3
            
            # 验证重试次数
            if self.config.download.retry_times < 0:
                self.config.download.retry_times = 3
            
            # 验证超时时间
            if self.config.download.timeout <= 0:
                self.config.download.timeout = 30
            
            # 验证搜索结果数
            if self.config.search.max_results_per_site <= 0:
                self.config.search.max_results_per_site = 20
            
            # 验证启用的网站列表
            if not self.config.search.enabled_sites:
                self.config.search.enabled_sites = ["javbus", "javlibrary", "pornhub"]
              # 验证整理方式
            valid_organize_by = ["studio", "genre", "actor"]
            if self.config.organize.organize_by not in valid_organize_by:
                self.config.organize.organize_by = "studio"
            
            # 验证日志配置
            valid_log_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
            if self.config.logging.level.upper() not in valid_log_levels:
                self.config.logging.level = "INFO"
            
            # 验证日志文件大小
            if self.config.logging.max_file_size <= 0:
                self.config.logging.max_file_size = 10 * 1024 * 1024  # 10MB
            
            # 验证备份文件数
            if self.config.logging.backup_count < 0:
                self.config.logging.backup_count = 5
            
            # 验证日志文件路径
            log_path = Path(self.config.logging.file_path)
            if not log_path.is_absolute():
                self.config.logging.file_path = str(self.config_dir / "logs" / "pavone.log")
            
            # 同步代理设置
            self.config._sync_proxy_settings()
            
            return True
            
        except Exception as e:
            print(f"配置验证失败: {e}")
            return False
    
    def get_logger(self, name: str):
        """获取日志器"""
        return get_log_manager().get_logger(name)
    
    def update_logging_config(self, **kwargs):
        """更新日志配置"""
        for key, value in kwargs.items():
            if hasattr(self.config.logging, key):
                setattr(self.config.logging, key, value)
        
        # 更新日志管理器配置
        get_log_manager().update_config(self.config.logging)
        self.save_config()
    
    def set_log_level(self, level: str):
        """设置日志级别"""
        self.config.logging.level = level
        get_log_manager().set_level(level)
        self.save_config()
    
    def enable_console_logging(self):
        """启用控制台日志"""
        self.config.logging.console_enabled = True
        get_log_manager().enable_console_logging()
        self.save_config()
    
    def disable_console_logging(self):
        """禁用控制台日志"""
        self.config.logging.console_enabled = False
        get_log_manager().disable_console_logging()
        self.save_config()
    
    def enable_file_logging(self):
        """启用文件日志"""
        self.config.logging.file_enabled = True
        get_log_manager().enable_file_logging()
        self.save_config()
    
    def disable_file_logging(self):
        """禁用文件日志"""
        self.config.logging.file_enabled = False
        get_log_manager().disable_file_logging()
        self.save_config()


# 全局配置管理器实例
config_manager = ConfigManager()

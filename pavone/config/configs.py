"""
配置类定义
"""

from typing import Optional, List
from dataclasses import dataclass, field
from .logging_config import LoggingConfig


@dataclass
class DownloadConfig:
    """下载配置"""
    output_dir: str = "./downloads"
    max_concurrent_downloads: int = 3
    retry_times: int = 3
    retry_interval: int = 3000  # 重试间隔，单位为毫秒
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
class PluginConfig:
    """插件配置"""
    # 插件目录
    plugin_dir: str = "./pavone/plugins"
    # 插件配置目录  
    plugin_config_dir: str = "./plugins_config"
    # 禁用的插件名称列表
    disabled_plugins: List[str] = field(default_factory=list)
    # 插件优先级设置（插件名 -> 优先级数值）
    plugin_priorities: dict = field(default_factory=dict)
    # 是否启用插件自动发现
    auto_discovery: bool = True
    # 插件加载超时时间（秒）
    load_timeout: int = 30


@dataclass
class Config:
    """主配置类"""
    download: DownloadConfig = field(default_factory=DownloadConfig)
    organize: OrganizeConfig = field(default_factory=OrganizeConfig)
    search: SearchConfig = field(default_factory=SearchConfig)
    proxy: ProxyConfig = field(default_factory=ProxyConfig)
    logging: LoggingConfig = field(default_factory=LoggingConfig)
    plugin: PluginConfig = field(default_factory=PluginConfig)
    
    def __post_init__(self):
        # 同步代理设置到下载配置
        self._sync_proxy_settings()
    
    def _sync_proxy_settings(self):
        """将代理设置同步到下载配置中"""
        self.download.proxy_enabled = self.proxy.enabled
        self.download.http_proxy = self.proxy.http_proxy
        self.download.https_proxy = self.proxy.https_proxy

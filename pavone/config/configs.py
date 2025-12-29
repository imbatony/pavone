"""
配置类定义
"""

from dataclasses import dataclass, field
from typing import List, Optional

from .logging_config import LoggingConfig

default_user_agent = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3"
)


@dataclass
class DownloadConfig:
    """下载配置"""

    output_dir: str = "./downloads"
    auto_select: bool = True  # 是否自动选择下载链接
    max_concurrent_downloads: int = 4
    retry_times: int = 3
    retry_interval: int = 3000  # 重试间隔，单位为毫秒
    timeout: int = 30
    cache_dir: Optional[str] = None  # 缓存目录，默认为None, 如果为None则使用系统默认缓存目录
    headers: dict[str, str] = field(default_factory=lambda: {"User-Agent": default_user_agent})
    overwrite_existing: bool = False  # 是否覆盖已存在的文件


@dataclass
class OrganizeConfig:
    """整理配置"""

    auto_organize: bool = True
    naming_pattern: str = "{code}"  # 命名模式, 例如 "{code}" 或 "{code} - {title}"
    folder_structure: str = "{code}"  # 文件夹结构, 例如 "{code}"
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
            self.enabled_sites = ["All"]  # 默认启用所有站点


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
    disabled_plugins: List[str] = field(default_factory=list[str])
    # 插件优先级设置（插件名 -> 优先级数值）
    plugin_priorities: dict[str, int] = field(default_factory=dict[str, int])
    # 是否启用插件自动发现
    auto_discovery: bool = True
    # 插件加载超时时间（秒）
    load_timeout: int = 30


@dataclass
class JellyfinConfig:
    """Jellyfin 配置"""

    enabled: bool = False
    server_url: str = ""
    username: Optional[str] = None
    password: Optional[str] = None
    api_key: Optional[str] = None
    libraries: List[str] = field(default_factory=list[str])
    verify_ssl: bool = True
    timeout: int = 30
    auto_match: bool = True  # 是否自动匹配元数据


@dataclass
class Config:
    """主配置类"""

    download: DownloadConfig = field(default_factory=DownloadConfig)
    organize: OrganizeConfig = field(default_factory=OrganizeConfig)
    search: SearchConfig = field(default_factory=SearchConfig)
    proxy: ProxyConfig = field(default_factory=ProxyConfig)
    logging: LoggingConfig = field(default_factory=LoggingConfig)
    plugin: PluginConfig = field(default_factory=PluginConfig)
    jellyfin: JellyfinConfig = field(default_factory=JellyfinConfig)

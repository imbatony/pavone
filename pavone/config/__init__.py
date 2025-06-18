"""
配置管理模块
"""

from .settings import (
    Config,
    DownloadConfig,
    OrganizeConfig, 
    SearchConfig,
    ProxyConfig,
    PluginConfig,
    ConfigManager,
    ConfigValidator,
    config_manager,
    get_config,
    get_config_manager,
    get_download_config,
    get_organize_config,
    get_search_config,
    get_proxy_config,
    get_plugin_config,
)

from .logging_config import (
    LoggingConfig,
    LogManager,
    get_log_manager,
    get_logger
)

__all__ = [
    'Config',
    'DownloadConfig',
    'OrganizeConfig',
    'SearchConfig', 
    'ProxyConfig',
    'PluginConfig',
    'ConfigManager',
    'ConfigValidator',
    'config_manager',
    'get_config',
    'get_config_manager',
    'get_download_config',
    'get_organize_config',
    'get_search_config',
    'get_proxy_config',
    'get_plugin_config',
    'LoggingConfig',
    'LogManager',
    'get_log_manager',
    'get_logger'
]

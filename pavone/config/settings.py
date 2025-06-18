"""
配置管理 - 主入口文件
"""

# 导入所有配置相关的类和功能
from .configs import (
    Config,
    DownloadConfig,
    OrganizeConfig,
    SearchConfig,
    ProxyConfig,
    PluginConfig
)
from .manager import ConfigManager
from .validator import ConfigValidator

# 全局配置管理器实例
config_manager = ConfigManager()

# 向后兼容的函数
def get_config() -> Config:
    """获取配置"""
    return config_manager.get_config()

def get_config_manager() -> ConfigManager:
    """获取配置管理器"""
    return config_manager

# 便捷函数
def get_download_config() -> DownloadConfig:
    """获取下载配置"""
    return config_manager.get_config().download

def get_organize_config() -> OrganizeConfig:
    """获取整理配置"""
    return config_manager.get_config().organize

def get_search_config() -> SearchConfig:
    """获取搜索配置"""
    return config_manager.get_config().search

def get_proxy_config() -> ProxyConfig:
    """获取代理配置"""
    return config_manager.get_config().proxy

def get_plugin_config() -> PluginConfig:
    """获取插件配置"""
    return config_manager.get_config().plugin

# 导出常用的类和函数
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
]

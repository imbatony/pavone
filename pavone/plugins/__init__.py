"""
插件系统
提供插件化的扩展功能

插件通过 PluginManager 自动发现加载, 无需在此手动导入注册.
此模块仅导出基类类型, 供外部引用和类型检查使用.
"""

from .base import BasePlugin
from .extractors import ExtractorPlugin
from .metadata import MetadataPlugin
from .search import SearchPlugin

__all__ = [
    "BasePlugin",
    "ExtractorPlugin",
    "MetadataPlugin",
    "SearchPlugin",
]


# 向后兼容：延迟导入 PluginManager 和 plugin_manager 以避免循环导入
def __getattr__(name: str):
    """延迟导入以避免循环导入"""
    if name == "PluginManager":
        from ..manager import PluginManager

        return PluginManager
    elif name == "get_plugin_manager":
        from ..manager import get_plugin_manager

        return get_plugin_manager
    elif name == "plugin_manager":
        from ..manager import get_plugin_manager

        return get_plugin_manager()
    raise AttributeError(f"module '{__name__}' has no attribute '{name}'")

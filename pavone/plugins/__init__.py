"""
插件系统
提供插件化的扩展功能
"""

from .av01_plugin import AV01Plugin
from .base import BasePlugin
from .extractors import ExtractorPlugin
from .jtable_plugin import JTablePlugin
from .memojav_plugin import MemojavPlugin
from .metadata import MetadataPlugin
from .missav_plugin import MissAVPlugin
from .search import JellyfinSearch, SearchPlugin

__all__ = [
    "BasePlugin",
    "ExtractorPlugin",
    "MetadataPlugin",
    "SearchPlugin",
    "AV01Plugin",
    "MissAVPlugin",
    "JTablePlugin",
    "MemojavPlugin",
    "JellyfinSearch",
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

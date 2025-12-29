"""
插件系统
提供插件化的扩展功能
"""

from .av01_plugin import AV01Plugin
from .base import BasePlugin
from .extractors import ExtractorPlugin
from .manager import PluginManager, plugin_manager
from .metadata import MetadataPlugin
from .missav_plugin import MissAVPlugin
from .search import SearchPlugin

__all__ = [
    "BasePlugin",
    "ExtractorPlugin",
    "MetadataPlugin",
    "SearchPlugin",
    "AV01Plugin",
    "MissAVPlugin",
    "PluginManager",
    "plugin_manager",
]

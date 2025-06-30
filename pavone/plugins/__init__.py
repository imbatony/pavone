"""
插件系统
提供插件化的扩展功能
"""

from .base import BasePlugin
from .extractors import ExtractorPlugin
from .manager import PluginManager, plugin_manager
from .metadata import MetadataPlugin
from .search import MissavSearch, SearchPlugin

__all__ = [
    "BasePlugin",
    "ExtractorPlugin",
    "MetadataPlugin",
    "SearchPlugin",
    "MissavSearch",
    "PluginManager",
    "plugin_manager",
]

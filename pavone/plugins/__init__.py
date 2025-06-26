"""
插件系统
提供插件化的扩展功能
"""

from .base import BasePlugin
from .extractors import ExtractorPlugin
from .metadata import MetadataPlugin
from .search import SearchPlugin, MissavSearch
from .manager import PluginManager, plugin_manager

__all__ = [
    'BasePlugin',
    'ExtractorPlugin', 
    'MetadataPlugin',
    'SearchPlugin',
    'MissavSearch',
    'PluginManager',
    'plugin_manager'
]
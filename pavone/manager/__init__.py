"""
管理器模块

提供进度显示、执行管理、搜索管理、插件管理、元数据管理等功能
"""

from .metadata_manager import MetadataManager, get_metadata_manager
from .plugin_manager import PluginManager, get_plugin_manager
from .progress import (
    create_console_progress_callback,
    create_silent_progress_callback,
    create_status_only_progress,
    format_bytes,
)
from .search_manager import SearchManager, get_search_manager

__all__ = [
    "MetadataManager",
    "get_metadata_manager",
    "PluginManager",
    "get_plugin_manager",
    "create_console_progress_callback",
    "create_silent_progress_callback",
    "create_status_only_progress",
    "format_bytes",
    "SearchManager",
    "get_search_manager",
]

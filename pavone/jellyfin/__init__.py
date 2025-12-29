"""
Jellyfin 集成模块

提供与 Jellyfin 服务器交互的功能，包括连接、搜索、库管理等。
"""

from .client import JellyfinClientWrapper
from .download_helper import JellyfinDownloadHelper
from .exceptions import (
    JellyfinAPIError,
    JellyfinAuthenticationError,
    JellyfinConnectionError,
    JellyfinException,
    JellyfinLibraryError,
    JellyfinVideoMatchError,
)
from .library_manager import LibraryManager
from .models import JellyfinItem, JellyfinMetadata, LibraryInfo

__all__ = [
    "JellyfinClientWrapper",
    "LibraryManager",
    "JellyfinDownloadHelper",
    "JellyfinException",
    "JellyfinConnectionError",
    "JellyfinAuthenticationError",
    "JellyfinAPIError",
    "JellyfinVideoMatchError",
    "JellyfinLibraryError",
    "JellyfinItem",
    "JellyfinMetadata",
    "LibraryInfo",
]

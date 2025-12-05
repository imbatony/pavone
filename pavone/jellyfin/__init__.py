"""
Jellyfin 集成模块

提供与 Jellyfin 服务器交互的功能，包括连接、搜索、库管理等。
"""

from .exceptions import (
    JellyfinAPIError,
    JellyfinAuthenticationError,
    JellyfinConnectionError,
    JellyfinException,
    JellyfinVideoMatchError,
)
from .models import JellyfinItem, JellyfinMetadata, LibraryInfo

__all__ = [
    "JellyfinException",
    "JellyfinConnectionError",
    "JellyfinAuthenticationError",
    "JellyfinAPIError",
    "JellyfinVideoMatchError",
    "JellyfinItem",
    "JellyfinMetadata",
    "LibraryInfo",
]

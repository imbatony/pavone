"""
Jellyfin 相关异常定义
"""


class JellyfinException(Exception):
    """Jellyfin 异常基类"""

    pass


class JellyfinConnectionError(JellyfinException):
    """Jellyfin 连接错误"""

    pass


class JellyfinAuthenticationError(JellyfinException):
    """Jellyfin 认证错误"""

    pass


class JellyfinAPIError(JellyfinException):
    """Jellyfin API 调用错误"""

    pass


class JellyfinVideoMatchError(JellyfinException):
    """Jellyfin 视频匹配错误"""

    pass


class JellyfinLibraryError(JellyfinException):
    """Jellyfin 库操作错误"""

    pass

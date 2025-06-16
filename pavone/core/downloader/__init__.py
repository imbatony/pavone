"""
核心功能模块
"""

# 导入基础类和接口
from .base import BaseDownloader
from .options import DownloadOpt, create_download_opt
from .progress import ProgressInfo, ProgressCallback, format_bytes, create_console_progress_callback, create_silent_progress_callback

# 导入具体实现
from .http_downloader import HTTPDownloader
from .m3u8_downloader import M3U8Downloader

# 导入工具函数
from .utils import (
    example_usage, 
    example_usage_with_proxy, 
    example_multithreaded_download,
    create_high_performance_config,
    create_config_with_proxy
)

# 导入下载管理器
from .download_manager import DownloadManager, create_download_manager

# 向后兼容的导入 - 保持原有的 downloader.py 中的导入路径可用
from .http_downloader import HTTPDownloader as BaseDownloader  # 向后兼容
from .options import DownloadOpt
from .progress import ProgressInfo, ProgressCallback

__all__ = [
    # 基础类
    'BaseDownloader',
    'DownloadOpt', 
    'ProgressInfo',
    'ProgressCallback',
      # 实现类
    'HTTPDownloader',
    'M3U8Downloader',
    
    # 工具函数
    'create_download_opt',
    'format_bytes',
    'create_console_progress_callback',
    'create_silent_progress_callback',
    'create_high_performance_config',
    'create_config_with_proxy',
    
    # 示例函数
    'example_usage',
    'example_usage_with_proxy', 
    'example_multithreaded_download',
]
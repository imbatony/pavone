"""
提取器插件模块
包含所有提取器相关的插件类
"""

from .base import ExtractorPlugin
from .jtable import JTableExtractor
from .m3u8_direct import M3U8DirectExtractor
from .memojav import MemojavExtractor
from .mp4_direct import MP4DirectExtractor

# MissAV插件在missav_plugin.py中定义
# AV01插件在av01_plugin.py中定义

__all__ = [
    "ExtractorPlugin",
    "MP4DirectExtractor",
    "M3U8DirectExtractor",
    "MemojavExtractor",
    "JTableExtractor",
]

"""
提取器插件模块
包含所有提取器相关的插件类
"""

from .base import ExtractorPlugin
from .m3u8_direct import M3U8DirectExtractor
from .mp4_direct import MP4DirectExtractor

# JTable插件已升级为复合型插件，在 jtable_plugin.py 中定义
# Memojav插件已升级为复合型插件，在 memojav_plugin.py 中定义
# MissAV插件在 missav_plugin.py 中定义
# AV01插件在 av01_plugin.py 中定义

__all__ = [
    "ExtractorPlugin",
    "MP4DirectExtractor",
    "M3U8DirectExtractor",
]

"""
核心功能模块
"""

# 导入主要类
from .organizer import FileOrganizer
from .metadata import BaseMetadataExtractor
from .searcher import BaseSearcher

# 导入下载器模块
from . import downloader

__all__ = [
    'FileOrganizer',
    'BaseMetadataExtractor', 
    'BaseSearcher',
    'downloader'
]
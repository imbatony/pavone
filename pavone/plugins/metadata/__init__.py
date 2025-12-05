"""
元数据提取器插件
"""

from .base import MetadataPlugin
from .missav_metadata import MissavMetadata

__all__ = ["MetadataPlugin", "MissavMetadata"]

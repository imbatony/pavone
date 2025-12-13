"""
元数据提取器插件
"""

from .base import MetadataPlugin
from .missav_metadata import MissavMetadata
from .av01_metadata import AV01Metadata

__all__ = ["MetadataPlugin", "MissavMetadata", "AV01Metadata"]

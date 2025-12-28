"""
元数据提取器插件
"""

from .av01_metadata import AV01Metadata
from .base import MetadataPlugin
from .ppvdatabank_metadata import PPVDataBankMetadata
from .supfc2_metadata import SupFC2Metadata

# MissAV插件在missav_plugin.py中定义

__all__ = [
    "MetadataPlugin",
    "AV01Metadata",
    "PPVDataBankMetadata",
    "SupFC2Metadata",
]

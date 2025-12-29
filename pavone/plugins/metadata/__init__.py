"""
元数据提取器插件
"""

from .base import MetadataPlugin
from .ppvdatabank_metadata import PPVDataBankMetadata
from .supfc2_metadata import SupFC2Metadata

# MissAV插件在missav_plugin.py中定义
# AV01插件在av01_plugin.py中定义

__all__ = [
    "MetadataPlugin",
    "PPVDataBankMetadata",
    "SupFC2Metadata",
]

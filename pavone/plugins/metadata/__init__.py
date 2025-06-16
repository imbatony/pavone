"""
元数据插件基类
"""

from abc import abstractmethod
from typing import Dict, Any
from ..base import BasePlugin


class MetadataPlugin(BasePlugin):
    """元数据插件基类"""
    
    @abstractmethod
    def can_extract(self, identifier: str) -> bool:
        """检查是否能提取该标识符的元数据"""
        pass
    
    @abstractmethod
    def extract_metadata(self, identifier: str) -> Dict[str, Any]:
        """提取元数据"""
        pass

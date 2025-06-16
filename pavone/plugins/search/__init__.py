"""
搜索插件基类
"""

from abc import abstractmethod
from typing import List, Dict, Any
from ..base import BasePlugin


class SearchPlugin(BasePlugin):
    """搜索插件基类"""
    
    @abstractmethod
    def search(self, keyword: str, limit: int = 20) -> List[Dict[str, Any]]:
        """搜索功能"""
        pass

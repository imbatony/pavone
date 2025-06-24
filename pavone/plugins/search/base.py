"""
搜索插件基类
"""

from abc import abstractmethod
from typing import List
from ..base import BasePlugin
from ...models import SearchResult


class SearchPlugin(BasePlugin):
    """搜索插件基类"""

    def __init__(self, name: str = "SearchPlugin", version: str = "1.0.0", description: str = "", author: str = ""):
        super().__init__(name, version, description, author)
    
    @abstractmethod
    def search(self, keyword: str, limit: int = 20) -> List[SearchResult]:
        """搜索功能"""
        pass
    
    def initialize(self) -> bool:
        """初始化搜索插件"""
        # 默认实现可以返回 True，子类可以重写以提供自定义初始化逻辑
        return True

    def execute(self, *args, **kwargs)-> List[SearchResult]:
        """执行搜索操作"""
        if not args:
            raise ValueError("Keyword is required for search.")
        keyword = args[0]
        limit = kwargs.get('limit', 20)
        return self.search(keyword, limit)

    def cleanup(self):
        """清理搜索插件资源"""
        # 默认实现可以留空，子类可以重写以提供自定义清理逻辑
        pass
"""
搜索插件基类
"""

from abc import abstractmethod
from typing import List

from pavone.config.settings import get_config_manager

from ...config.logging_config import get_logger
from ...models import SearchResult
from ..base import BasePlugin


class SearchPlugin(BasePlugin):
    """搜索插件基类"""

    def __init__(
        self,
        name: str = "SearchPlugin",
        version: str = "1.0.0",
        description: str = "",
        author: str = "",
        priority: int = 50,
    ):
        super().__init__(name, version, description, author, priority)
        self.logger = get_logger(__name__)
        self.config = get_config_manager().get_config()
        self.priority = priority

    @abstractmethod
    def search(self, keyword: str, limit: int = 20) -> List[SearchResult]:
        """搜索功能"""
        pass

    def initialize(self) -> bool:
        """初始化搜索插件"""
        # 默认实现可以返回 True，子类可以重写以提供自定义初始化逻辑
        return True

    def cleanup(self):
        """清理搜索插件资源"""
        # 默认实现可以留空，子类可以重写以提供自定义清理逻辑
        pass

    @abstractmethod
    def get_site_name(self) -> str:
        """获取搜索插件对应的网站名称"""
        pass

from abc import abstractmethod
from typing import List, Optional

from ...models import OperationItem
from ..base import BasePlugin


class ExtractorPlugin(BasePlugin):
    """提取器插件基类

    提取器插件负责分析给定的URL并提取出可下载的资源列表，
    而不直接进行下载操作
    """

    def __init__(
        self,
        name: Optional[str] = None,
        version: Optional[str] = "1.0.0",
        description: Optional[str] = "",
        author: Optional[str] = "",
        priority: Optional[int] = 50,
    ):
        super().__init__(
            name=name,
            version=version,
            description=description,
            author=author,
            priority=priority,
        )

    def initialize(self) -> bool:
        """初始化插件"""
        self.logger.info(f"初始化 {self.name} 插件")
        return True

    def execute(self, *args, **kwargs) -> List[OperationItem]:
        """执行插件功能"""
        if len(args) >= 1:
            return self.extract(args[0])
        return []

    @abstractmethod
    def can_handle(self, url: str) -> bool:
        """检查是否能处理该URL"""
        pass

    @abstractmethod
    def extract(self, url: str) -> List[OperationItem]:
        """从给定的URL提取下载选项
        Args:
            url: 要处理的URL

        Returns:
            可用的下载选项列表
        """
        pass

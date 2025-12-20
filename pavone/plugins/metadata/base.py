"""
元数据提取器插件基类
"""

from abc import abstractmethod
from typing import Optional

from ...models import BaseMetadata
from ..base import BasePlugin


class MetadataPlugin(BasePlugin):
    """元数据提取器插件基类

    元数据提取器插件负责从指定的identifier中提取元数据，
    包括视频代码、标题、演员、导演、发行日期等信息。
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

    def execute(self, *args, **kwargs) -> Optional[BaseMetadata]:
        """执行插件功能"""
        if len(args) >= 1:
            return self.extract_metadata(args[0])
        return None

    @abstractmethod
    def can_extract(self, identifier: str) -> bool:
        """检查是否能处理该identifier

        Args:
            identifier: 可以是URL、视频代码等标识符

        Returns:
            如果能处理返回True，否则返回False
        """
        pass

    @abstractmethod
    def extract_metadata(self, identifier: str) -> Optional[BaseMetadata]:
        """从给定的identifier提取元数据

        Args:
            identifier: 可以是URL、视频代码等标识符

        Returns:
            提取到的元数据对象，如果失败返回None
        """
        pass

"""
插件基类
"""

from abc import ABC, abstractmethod
from typing import Any, Optional


class BasePlugin(ABC):
    """插件基类"""

    def __init__(self, name: Optional[str] = None, version: Optional[str] = "1.0.0", description: Optional[str] = "", author: Optional[str] = ""):
        self.name = name or self.__class__.__name__
        self.version = version
        self.description = description
        self.author = author

    @abstractmethod
    def initialize(self) -> bool:
        """初始化插件"""
        pass

    @abstractmethod
    def execute(self, *args, **kwargs) -> Any:
        """执行插件功能"""
        pass

    def cleanup(self):
        """清理插件资源"""
        pass

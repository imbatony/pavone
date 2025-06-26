"""
插件基类
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional

import requests
from pavone.config.settings import get_config_manager
from pavone.config.logging_config import get_logger
from pavone.utils.http_utils import HttpUtils


class BasePlugin(ABC):
    """插件基类"""

    def __init__(
        self,
        name: Optional[str] = None,
        version: Optional[str] = "1.0.0",
        description: Optional[str] = "",
        author: Optional[str] = "",
        priority: Optional[int] = 50,
    ):
        self.name = name or self.__class__.__name__
        self.version = version
        self.description = description
        self.author = author
        self.priority = priority or 50  # 默认优先级为50
        self.logger = get_logger(__name__)
        self.config = get_config_manager().get_config()

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

    def set_priority(self, priority: int):
        """设置插件优先级"""
        self.priority = priority

    def get_priority(self) -> int:
        """获取插件优先级"""
        return self.priority

    def fetch(
        self, url: str, headers: Optional[Dict[str, str]] = None, timeout: int = 10, verify_ssl: bool = True
    ) -> requests.Response:
        return HttpUtils.fetch(
            download_config=self.config.download,
            proxy_config=self.config.proxy,
            url=url,
            logger=self.logger,
            headers=headers,
            timeout=timeout,
            verify_ssl=verify_ssl,
        )

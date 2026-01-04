from __future__ import annotations

from abc import ABC, abstractmethod

from pavone.config.logging_config import get_logger

from ..config.settings import Config
from ..models import OperationItem


class Operator(ABC):
    """
    基础操作类
    所有具体操作类（如下载器、组织器等）都应继承自此类
    提供统一的接口和配置管理
    Attributes:
        config: 配置对象
        operator_name: 操作名称
        logger: 日志记录器
    """

    def __init__(self, config: Config, operator_name: str):
        """
        初始化操作类
        Args:
            config: 配置对象
            operator_name: 操作名称，用于日志记录和标识
        """
        self.config = config
        self.operator_name = operator_name
        # 使用子类的模块名作为 logger 名称
        self.logger = get_logger(self.__class__.__module__)

    @abstractmethod
    def execute(self, item: OperationItem) -> bool:
        """
        执行操作
        该方法会被子类重写以实现具体的操作逻辑

        Args:
            item: 操作项对象,包含URL和其他操作信息
            target_path: 保存文件的路径
            progress_callback: 进度回调函数,接收ProgressInfo对象

        Returns:
            bool: 操作是否成功
        """
        pass

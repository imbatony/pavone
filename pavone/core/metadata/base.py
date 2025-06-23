from abc import ABC, abstractmethod
from typing import Optional

from ...models.operation import OperationItem
from ...config.settings import Config
from ..base import Operator

class BaseMetadataOperator(Operator):
    """
    基础元数据操作类
    所有具体元数据操作类（如下载器、组织器等）都应继承自此类
    提供统一的接口和配置管理
    """

    def __init__(self, config: Config, operator_name: Optional[str] = None):
        """
        初始化元数据操作类
        Args:
            config: 配置对象
            operator_name: 操作名称，用于日志记录和标识
        """
        name = operator_name if operator_name else "元数据操作"
        super().__init__(config, name)

    @abstractmethod
    def execute(self, item: OperationItem) -> bool:
        """
        执行元数据操作
        该方法会被子类重写以实现具体的操作逻辑
        
        Args:
            item: 操作项对象,包含URL和其他操作信息
            
        Returns:
            bool: 操作是否成功
        """
        pass
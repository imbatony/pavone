from ..config.settings import Config
from ..models.operation import OperationItem
from .base import Operator


class DummyOperator(Operator):
    """
    Dummy操作类，用于测试和占位
    继承自Operator，提供一个空的execute方法
    """

    def __init__(self, config: Config):
        super().__init__(config, "Dummy")

    def execute(self, item: OperationItem) -> bool:
        """
        执行Dummy操作
        该方法不会执行任何实际操作，仅用于测试和占位
        """
        self.logger.info(f"Executing dummy operation for item: {item}")
        return True

from ...config.settings import Config
from ...models import ItemType, OperationItem
from .base import BaseMetadataOperator


class MetadataSaver(BaseMetadataOperator):
    """
    元数据保存器
    负责将元数据保存到指定的存储位置
    """

    def __init__(self, config: Config):
        """
        初始化元数据保存器
        Args:
            config: 配置对象
            operator_name: 操作名称，用于日志记录和标识
        """
        super().__init__(config, "保存元数据")

    def execute(self, item: OperationItem) -> bool:
        """
        执行元数据保存操作
        Args:
            item: 包含要保存的元数据的对象

        Returns:
            bool: 操作是否成功
        """
        # 实现具体的保存逻辑
        # 例如，将item中的数据写入文件或数据库
        if not item or item.item_type != ItemType.META_DATA:
            self.logger.error("无效的操作项或缺少元数据")
            return False

        target_path = item.get_target_path()
        metadata = item.get_metadata()
        if not target_path or not metadata:
            self.logger.error("目标路径或元数据缺失")
            return False
        try:
            with open(target_path, "w", encoding="utf-8") as f:
                f.write(metadata.to_nfo())  # 假设metadata有to_nfo方法将其转换为NFO格式
            self.logger.info(f"元数据已保存到 {target_path}")
        except Exception as e:
            self.logger.error(f"保存元数据失败: {e}")
            return False

        return True  # 返回操作结果

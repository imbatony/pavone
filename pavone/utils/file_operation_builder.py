"""
文件操作构建器

根据元数据和配置生成文件操作（移动/重命名）。
"""

from pathlib import Path
from typing import TYPE_CHECKING, Optional

from ..config.logging_config import get_logger
from ..models.constants import ItemType, OperationType
from .template_utils import TemplateUtils

if TYPE_CHECKING:
    from ..config.configs import OrganizeConfig
    from ..models.metadata import MovieMetadata
    from ..models.operation import OperationItem


class FileOperationBuilder:
    """文件操作构建器

    负责根据源文件、元数据和配置生成文件操作项。
    主要功能：
    1. 根据元数据和命名模式生成目标文件名
    2. 处理文件名冲突（追加序号、跳过、覆盖）
    3. 创建 MOVE 类型的 OperationItem
    """

    def __init__(self):
        """初始化文件操作构建器"""
        self.logger = get_logger(__name__)

    def build_operation(
        self,
        source_path: Path,
        metadata: "MovieMetadata",
        config: "OrganizeConfig",
        base_dir: Optional[Path] = None,
    ) -> Optional["OperationItem"]:
        """构建文件操作

        Args:
            source_path: 源文件路径
            metadata: 电影元数据
            config: 整理配置
            base_dir: 基础输出目录，如果为 None 则使用当前目录

        Returns:
            操作项，如果无法构建则返回 None

        异常:
            ValueError: 源文件不存在或不是视频文件
        """
        # 动态导入以避免循环依赖
        from ..models.operation import OperationItem

        # 验证源文件
        if not source_path.exists():
            raise ValueError(f"源文件不存在: {source_path}")

        if not source_path.is_file():
            raise ValueError(f"源路径不是文件: {source_path}")

        # 生成目标文件名
        target_filename = self._build_filename(metadata, config, source_path.suffix)

        # 解析目录结构模板
        folder_structure = TemplateUtils.resolve_template(config.folder_structure, metadata)

        # 构建目标路径
        if base_dir is None:
            base_dir = Path.cwd()
        elif not base_dir.is_absolute():
            base_dir = Path.cwd() / base_dir

        # 组合基础目录、文件夹结构和文件名
        target_path = base_dir / folder_structure / target_filename

        # 处理文件名冲突
        conflict_strategy = getattr(config, "on_conflict", "rename")
        target_path = self._resolve_conflict(target_path, conflict_strategy)

        # 创建操作项
        operation = OperationItem(
            opt_type=OperationType.MOVE,
            item_type=ItemType.VIDEO,
            desc=f"移动 {source_path.name} 到 {target_path}",
        )

        # 设置源路径和目标路径
        operation.set_source_path(str(source_path))
        operation.set_target_path(str(target_path))

        # 设置代码
        if metadata.code:
            operation.set_code(metadata.code)

        # 添加子操作项（元数据和封面）
        self._add_child_operations(operation, metadata, config)

        self.logger.debug(
            f"构建文件操作: {source_path} -> {target_path}",
            extra={"source": str(source_path), "target": str(target_path), "code": metadata.code},
        )

        return operation

    def _add_child_operations(
        self,
        operation: "OperationItem",
        metadata: "MovieMetadata",
        config: "OrganizeConfig",
    ) -> None:
        """为操作项添加子操作（元数据和封面）

        Args:
            operation: 主操作项（MOVE）
            metadata: 电影元数据
            config: 整理配置
        """
        # 导入创建子操作项的辅助函数
        from ..utils.operation_item_builder import create_cover_item, create_metadata_item

        # 添加元数据（如果配置允许）
        if config.create_nfo:
            metadata_item = create_metadata_item(meta_data=metadata, title=metadata.title or metadata.code)
            operation.append_child(metadata_item)
            self.logger.debug(f"添加元数据子操作: {metadata.code}")

        # 添加封面（如果配置允许且有封面 URL）
        if config.download_cover and metadata.cover:
            cover_item = create_cover_item(url=metadata.cover, title=metadata.title or metadata.code)
            operation.append_child(cover_item)
            self.logger.debug(f"添加封面子操作: {metadata.cover}")

    def _build_filename(
        self,
        metadata: "MovieMetadata",
        config: "OrganizeConfig",
        extension: str,
    ) -> str:
        """根据元数据和命名模式生成文件名

        Args:
            metadata: 电影元数据
            config: 整理配置
            extension: 文件扩展名（包含点号，如 .mp4）

        Returns:
            生成的文件名（包含扩展名）

        示例:
            naming_pattern="{code}" -> "SSIS-123.mp4"
            naming_pattern="{code} - {title}" -> "SSIS-123 - 美少女.mp4"
            naming_pattern="{code} [{studio}]" -> "SSIS-123 [S1].mp4"
        """
        # 使用模板解析生成文件名
        filename = TemplateUtils.resolve_template(config.naming_pattern, metadata)

        # 添加扩展名
        if not filename.endswith(extension):
            filename += extension

        return filename

    def _resolve_conflict(self, target_path: Path, strategy: str) -> Path:
        """处理文件名冲突

        Args:
            target_path: 目标路径
            strategy: 冲突处理策略
                - "rename": 追加序号 (默认)
                - "skip": 跳过（返回原路径，由调用方处理）
                - "overwrite": 覆盖（返回原路径）

        Returns:
            处理后的目标路径

        示例:
            strategy="rename":
                video.mp4 存在 -> video (1).mp4
                video (1).mp4 存在 -> video (2).mp4

            strategy="skip" 或 "overwrite":
                返回原路径不变
        """
        if not target_path.exists():
            return target_path

        if strategy == "overwrite":
            self.logger.warning(
                f"文件冲突，将覆盖: {target_path}",
                extra={"path": str(target_path), "strategy": strategy},
            )
            return target_path

        if strategy == "skip":
            self.logger.info(
                f"文件冲突，将跳过: {target_path}",
                extra={"path": str(target_path), "strategy": strategy},
            )
            return target_path

        # 默认策略: rename
        # 追加序号直到找到不存在的文件名
        base_name = target_path.stem
        extension = target_path.suffix
        parent = target_path.parent

        counter = 1
        while True:
            new_name = f"{base_name} ({counter}){extension}"
            new_path = parent / new_name

            if not new_path.exists():
                self.logger.info(
                    f"文件冲突，重命名: {target_path.name} -> {new_name}",
                    extra={"original": str(target_path), "renamed": str(new_path)},
                )
                return new_path

            counter += 1

            # 防止无限循环
            if counter > 9999:
                raise RuntimeError(f"无法解决文件冲突: {target_path}")

    def build_batch_operations(
        self,
        files_metadata: list[tuple[Path, "MovieMetadata"]],
        config: "OrganizeConfig",
        base_dir: Optional[Path] = None,
    ) -> list["OperationItem"]:
        """批量构建文件操作

        Args:
            files_metadata: 文件路径和元数据对列表
            config: 整理配置
            base_dir: 基础输出目录，如果为 None 则使用当前目录

        Returns:
            操作项列表

        注意:
            失败的操作会被跳过，不会抛出异常
        """
        operations: list["OperationItem"] = []

        for source_path, metadata in files_metadata:
            try:
                operation = self.build_operation(source_path, metadata, config, base_dir)
                if operation:
                    operations.append(operation)
            except Exception as e:
                self.logger.error(
                    f"构建操作失败: {source_path}",
                    extra={"source": str(source_path), "error": str(e)},
                    exc_info=True,
                )
                # 继续处理其他文件
                continue

        return operations

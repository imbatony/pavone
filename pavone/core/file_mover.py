"""
文件移动操作器

负责执行文件移动操作，包括安全检查和错误处理。
"""

import os
import shutil
from pathlib import Path
from typing import Optional

from ..config.logging_config import get_logger
from ..config.settings import Config
from ..models import OperationItem
from .base import Operator


class FileMover(Operator):
    """文件移动操作器

    负责执行文件移动操作，包括：
    1. 源文件存在性检查
    2. 目标目录权限检查
    3. 文件移动执行
    4. 错误处理和回滚
    """

    def __init__(self, config: Config):
        """初始化文件移动器

        Args:
            config: 配置对象
        """
        super().__init__(config, "FileMover")
        self.logger = get_logger(__name__)

    def execute(self, item: OperationItem) -> bool:
        """执行文件移动操作

        Args:
            item: 操作项，必须包含：
                - source_path: 源文件路径（在 extra 中）
                - target_path: 目标文件路径（通过 get_target_path()）

        Returns:
            是否成功移动文件

        Raises:
            FileNotFoundError: 源文件不存在
            ValueError: 源路径或目标路径不是文件
            PermissionError: 目标目录不可写
            FileExistsError: 目标文件已存在且不允许覆盖
        """
        # 获取源路径和目标路径
        source_path_str = item.get_source_path()
        target_path_str = item.get_target_path()

        if not source_path_str:
            self.logger.error("操作项缺少源文件路径 (source_path)")
            return False

        if not target_path_str:
            self.logger.error("操作项缺少目标文件路径 (target_path)")
            return False

        source_path = Path(source_path_str)
        target_path = Path(target_path_str)

        # 安全检查（会抛出异常）
        if not self._validate_move(source_path, target_path):
            # _validate_move 返回 False 仅在源和目标相同时（不是错误情况）
            return True

        # 执行移动
        return self._perform_move(source_path, target_path)

    def _validate_move(self, source: Path, target: Path) -> bool:
        """验证移动操作是否可行

        Args:
            source: 源文件路径
            target: 目标文件路径

        Returns:
            是否可以执行移动

        Raises:
            FileNotFoundError: 源文件不存在
            ValueError: 源路径不是文件或目标路径不是文件
            PermissionError: 目标目录不可写
        """
        # 检查源文件是否存在
        if not source.exists():
            error_msg = f"源文件不存在: {source}"
            self.logger.error(error_msg)
            raise FileNotFoundError(error_msg)

        # 检查源路径是否是文件
        if not source.is_file():
            error_msg = f"源路径必须是文件: {source}"
            self.logger.error(error_msg)
            raise ValueError(error_msg)

        # 检查源文件是否可读
        if not source.is_file() or not source.stat().st_size > 0:
            error_msg = f"源文件不可读或为空: {source}"
            self.logger.error(error_msg)
            raise ValueError(error_msg)

        # 检查源文件和目标文件是否相同（必须在其他检查之前）
        if source.resolve() == target.resolve():
            self.logger.warning(f"源文件和目标文件相同，跳过移动: {source}")
            return False

        # 检查目标目录是否存在，不存在则尝试创建
        target_dir = target.parent
        if not target_dir.exists():
            try:
                target_dir.mkdir(parents=True, exist_ok=True)
                self.logger.info(f"创建目标目录: {target_dir}")
            except Exception as e:
                error_msg = f"无法创建目标目录 {target_dir}: {e}"
                self.logger.error(error_msg)
                raise PermissionError(error_msg) from e

        # 检查目标目录是否可写
        if not target_dir.is_dir():
            error_msg = f"目标路径的父目录必须是目录: {target_dir}"
            self.logger.error(error_msg)
            raise ValueError(error_msg)

        # 检查目标目录是否可写
        if not os.access(target_dir, os.W_OK):
            error_msg = f"目标目录不可写: {target_dir}"
            self.logger.error(error_msg)
            raise PermissionError(error_msg)

        # 检查目标路径是否指向目录
        if target.exists() and target.is_dir():
            error_msg = f"目标路径必须是文件，而不是目录: {target}"
            self.logger.error(error_msg)
            raise ValueError(error_msg)

        # 检查目标文件是否已存在
        if target.exists():
            if self.config.download.overwrite_existing:
                self.logger.warning(f"目标文件已存在，将被覆盖: {target}")
            else:
                error_msg = f"目标文件已存在: {target}"
                self.logger.error(error_msg)
                raise FileExistsError(error_msg)

        return True

    def _perform_move(self, source: Path, target: Path) -> bool:
        """执行文件移动

        Args:
            source: 源文件路径
            target: 目标文件路径

        Returns:
            是否成功移动

        Raises:
            Exception: 移动操作失败时重新抛出异常
        """
        backup_path: Optional[Path] = None

        try:
            # 如果目标文件存在且允许覆盖，先备份
            if target.exists() and self.config.download.overwrite_existing:
                backup_path = target.with_suffix(target.suffix + ".bak")
                self.logger.info(f"备份现有文件: {target} -> {backup_path}")
                shutil.move(str(target), str(backup_path))

            # 执行移动
            self.logger.info(f"移动文件: {source} -> {target}")
            shutil.move(str(source), str(target))

            # 验证移动成功
            if not target.exists():
                raise RuntimeError(f"移动后目标文件不存在: {target}")

            if source.exists():
                raise RuntimeError(f"移动后源文件仍然存在: {source}")

            # 删除备份文件
            if backup_path and backup_path.exists():
                backup_path.unlink()
                self.logger.debug(f"删除备份文件: {backup_path}")

            self.logger.info(f"文件移动成功: {source.name} -> {target}")
            return True

        except Exception as e:
            self.logger.error(f"文件移动失败: {e}")

            # 尝试回滚
            if backup_path and backup_path.exists():
                try:
                    self.logger.info(f"回滚操作，恢复备份文件: {backup_path} -> {target}")
                    shutil.move(str(backup_path), str(target))
                except Exception as rollback_error:
                    self.logger.error(f"回滚失败: {rollback_error}")

            # 重新抛出原始异常
            raise

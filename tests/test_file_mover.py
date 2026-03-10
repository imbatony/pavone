"""
测试 FileMover 功能
"""

import os
import shutil
from pathlib import Path
from tempfile import TemporaryDirectory

import pytest

from pavone.config.configs import Config
from pavone.core.file_mover import FileMover
from pavone.models.constants import ItemType, OperationType
from pavone.models.operation import OperationItem


@pytest.fixture
def config():
    """创建测试配置"""
    return Config()


@pytest.fixture
def temp_workspace():
    """创建临时工作目录"""
    with TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def file_mover(config):
    """创建 FileMover 实例"""
    return FileMover(config)


def create_test_file(path: Path, content: str = "test content") -> Path:
    """创建测试文件"""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    return path


def create_move_operation(source_path: str, target_path: str, description: str = "Test move") -> OperationItem:
    """创建移动操作项"""
    item = OperationItem(
        opt_type=OperationType.MOVE,
        item_type=ItemType.VIDEO,
        desc=description,
        target_path=target_path,
    )
    item._extra["source_path"] = source_path
    return item


class TestFileMoverBasic:
    """测试 FileMover 基本功能"""

    def test_init(self, file_mover, config):
        """测试 FileMover 初始化"""
        assert file_mover.config == config
        assert file_mover.logger is not None

    def test_simple_move(self, file_mover, temp_workspace):
        """测试简单文件移动"""
        # 创建源文件
        source = temp_workspace / "source" / "test.mp4"
        create_test_file(source, "video content")

        # 目标路径
        target = temp_workspace / "target" / "test.mp4"

        # 创建操作项
        item = create_move_operation(str(source), str(target), "Move test.mp4")

        # 执行移动
        file_mover.execute(item)

        # 验证结果
        assert not source.exists(), "源文件应该被移动"
        assert target.exists(), "目标文件应该存在"
        assert target.read_text(encoding="utf-8") == "video content"

    def test_move_with_target_dir_creation(self, file_mover, temp_workspace):
        """测试移动时自动创建目标目录"""
        source = temp_workspace / "source.mp4"
        create_test_file(source)

        # 目标目录不存在
        target = temp_workspace / "new" / "dir" / "target.mp4"

        item = create_move_operation(str(source), str(target))
        file_mover.execute(item)

        assert target.exists()
        assert not source.exists()

    def test_move_with_rename(self, file_mover, temp_workspace):
        """测试移动并重命名"""
        source = temp_workspace / "old_name.mp4"
        create_test_file(source, "content")

        target = temp_workspace / "new_name.mp4"

        item = create_move_operation(str(source), str(target))
        file_mover.execute(item)

        assert target.exists()
        assert target.read_text(encoding="utf-8") == "content"
        assert not source.exists()


class TestFileMoverValidation:
    """测试 FileMover 验证功能"""

    def test_source_not_exists(self, file_mover, temp_workspace):
        """测试源文件不存在"""
        source = temp_workspace / "nonexistent.mp4"
        target = temp_workspace / "target.mp4"

        item = create_move_operation(str(source), str(target))

        with pytest.raises(FileNotFoundError, match="源文件不存在"):
            file_mover.execute(item)

    def test_source_is_directory(self, file_mover, temp_workspace):
        """测试源路径是目录"""
        source = temp_workspace / "source_dir"
        source.mkdir()
        target = temp_workspace / "target.mp4"

        item = create_move_operation(str(source), str(target))

        with pytest.raises(ValueError, match="源路径必须是文件"):
            file_mover.execute(item)

    def test_target_is_directory(self, file_mover, temp_workspace):
        """测试目标路径是目录"""
        source = temp_workspace / "source.mp4"
        create_test_file(source)

        target = temp_workspace / "target_dir"
        target.mkdir()

        item = create_move_operation(str(source), str(target))

        with pytest.raises(ValueError, match="目标路径必须是文件"):
            file_mover.execute(item)

    def test_same_source_and_target(self, file_mover, temp_workspace):
        """测试源和目标是同一文件"""
        source = temp_workspace / "same.mp4"
        create_test_file(source)

        item = create_move_operation(str(source), str(source))

        # 应该跳过移动，不抛出异常
        file_mover.execute(item)
        assert source.exists()

    def test_target_parent_not_writable(self, file_mover, temp_workspace, monkeypatch):
        """测试目标目录不可写"""
        source = temp_workspace / "source.mp4"
        create_test_file(source)

        target = temp_workspace / "readonly" / "target.mp4"
        target.parent.mkdir(parents=True, exist_ok=True)

        # 模拟目录不可写
        def mock_access(path, mode):
            if Path(path) == target.parent and mode == os.W_OK:
                return False
            return os.access.__wrapped__(path, mode)

        monkeypatch.setattr(os, "access", mock_access)

        item = create_move_operation(str(source), str(target))

        with pytest.raises(PermissionError, match="目标目录不可写"):
            file_mover.execute(item)


class TestFileMoverOverwrite:
    """测试 FileMover 覆盖功能"""

    def test_overwrite_existing_file(self, temp_workspace):
        """测试覆盖已存在的文件"""
        # 创建启用覆盖的配置
        config = Config()
        config.download.overwrite_existing = True
        file_mover = FileMover(config)

        source = temp_workspace / "source.mp4"
        create_test_file(source, "new content")

        target = temp_workspace / "target.mp4"
        create_test_file(target, "old content")

        # 确认目标文件存在
        assert target.exists()
        assert target.read_text(encoding="utf-8") == "old content"

        item = create_move_operation(str(source), str(target))
        file_mover.execute(item)

        # 验证覆盖成功
        assert target.exists()
        assert target.read_text(encoding="utf-8") == "new content"
        assert not source.exists()

    def test_backup_created_on_overwrite(self, temp_workspace):
        """测试覆盖时创建备份"""
        # 创建启用覆盖的配置
        config = Config()
        config.download.overwrite_existing = True
        file_mover = FileMover(config)

        source = temp_workspace / "source.mp4"
        create_test_file(source, "new content")

        target = temp_workspace / "target.mp4"
        create_test_file(target, "old content")

        item = create_move_operation(str(source), str(target))
        file_mover.execute(item)

        # 备份文件应该被清理（成功移动后）
        backup_files = list(target.parent.glob("target.mp4.backup.*"))
        assert len(backup_files) == 0, "备份文件应该在成功移动后被清理"


class TestFileMoverRollback:
    """测试 FileMover 回滚功能"""

    def test_rollback_on_move_failure(self, temp_workspace, monkeypatch):
        """测试移动失败时回滚"""
        # 创建启用覆盖的配置
        config = Config()
        config.download.overwrite_existing = True
        file_mover = FileMover(config)

        source = temp_workspace / "source.mp4"
        create_test_file(source, "content")

        target = temp_workspace / "target.mp4"
        create_test_file(target, "old content")

        # 模拟 shutil.move 失败
        original_move = shutil.move

        def mock_move(src, dst):
            if Path(src) == source:
                raise IOError("Mock move failure")
            return original_move(src, dst)

        monkeypatch.setattr(shutil, "move", mock_move)

        item = create_move_operation(str(source), str(target))

        with pytest.raises(IOError, match="Mock move failure"):
            file_mover.execute(item)

        # 验证回滚：目标文件恢复原内容
        assert target.exists()
        assert target.read_text(encoding="utf-8") == "old content"

    def test_rollback_restores_backup(self, temp_workspace, monkeypatch):
        """测试回滚恢复备份文件"""
        # 创建启用覆盖的配置
        config = Config()
        config.download.overwrite_existing = True
        file_mover = FileMover(config)

        source = temp_workspace / "source.mp4"
        create_test_file(source, "new content")

        target = temp_workspace / "target.mp4"
        original_content = "original content"
        create_test_file(target, original_content)

        # 模拟移动过程中失败
        move_count = 0
        original_move = shutil.move

        def mock_move(src, dst):
            nonlocal move_count
            move_count += 1
            # 第一次调用（创建备份）成功，第二次调用（实际移动）失败
            if move_count == 2:
                raise IOError("Simulated failure during move")
            return original_move(src, dst)

        monkeypatch.setattr(shutil, "move", mock_move)

        item = create_move_operation(str(source), str(target))

        with pytest.raises(IOError):
            file_mover.execute(item)

        # 验证目标文件恢复原内容
        assert target.exists()
        assert target.read_text(encoding="utf-8") == original_content


class TestFileMoverEdgeCases:
    """测试 FileMover 边界情况"""

    def test_move_with_special_characters(self, file_mover, temp_workspace):
        """测试包含特殊字符的文件名"""
        source = temp_workspace / "测试文件 (1).mp4"
        create_test_file(source, "content")

        target = temp_workspace / "目标文件 [2].mp4"

        item = create_move_operation(str(source), str(target))
        file_mover.execute(item)

        assert target.exists()
        assert not source.exists()

    def test_move_large_file(self, file_mover, temp_workspace):
        """测试移动大文件"""
        source = temp_workspace / "large.mp4"
        # 创建 1MB 的文件
        content = "x" * (1024 * 1024)
        create_test_file(source, content)

        target = temp_workspace / "target_large.mp4"

        item = create_move_operation(str(source), str(target))
        file_mover.execute(item)

        assert target.exists()
        assert target.stat().st_size == len(content)
        assert not source.exists()

    def test_move_to_same_directory(self, file_mover, temp_workspace):
        """测试在同一目录内重命名"""
        source = temp_workspace / "old.mp4"
        create_test_file(source, "content")

        target = temp_workspace / "new.mp4"

        item = create_move_operation(str(source), str(target))
        file_mover.execute(item)

        assert target.exists()
        assert not source.exists()

    def test_move_across_drives(self, file_mover, temp_workspace):
        """测试跨驱动器移动（模拟）"""
        # 在同一临时目录模拟跨驱动器场景
        source = temp_workspace / "drive1" / "file.mp4"
        create_test_file(source, "content")

        target = temp_workspace / "drive2" / "file.mp4"

        item = create_move_operation(str(source), str(target))
        file_mover.execute(item)

        assert target.exists()
        assert not source.exists()


class TestFileMoverIntegration:
    """测试 FileMover 集成场景"""

    def test_batch_moves(self, file_mover, temp_workspace):
        """测试批量移动文件"""
        # 创建多个源文件
        sources = []
        targets = []
        for i in range(5):
            source = temp_workspace / "source" / f"file{i}.mp4"
            create_test_file(source, f"content {i}")
            sources.append(source)

            target = temp_workspace / "target" / f"renamed{i}.mp4"
            targets.append(target)

        # 执行批量移动
        for source, target in zip(sources, targets):
            item = create_move_operation(str(source), str(target))
            file_mover.execute(item)

        # 验证所有文件都移动成功
        for i, (source, target) in enumerate(zip(sources, targets)):
            assert not source.exists()
            assert target.exists()
            assert target.read_text(encoding="utf-8") == f"content {i}"

    def test_move_with_metadata_operation(self, file_mover, temp_workspace):
        """测试移动操作携带元数据"""
        source = temp_workspace / "ABC-123.mp4"
        create_test_file(source, "video")

        target = temp_workspace / "organized" / "ABC" / "ABC-123" / "ABC-123.mp4"

        item = create_move_operation(str(source), str(target), "Organize ABC-123 to library structure")

        file_mover.execute(item)

        assert target.exists()
        assert not source.exists()
        # 验证目录结构正确创建
        assert (temp_workspace / "organized" / "ABC" / "ABC-123").is_dir()

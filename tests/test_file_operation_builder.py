"""
FileOperationBuilder 测试
"""

import shutil
from datetime import datetime
from pathlib import Path

import pytest

from pavone.config.configs import OrganizeConfig
from pavone.models.constants import ItemType, OperationType
from pavone.models.metadata import MovieMetadata
from pavone.utils.file_operation_builder import FileOperationBuilder
from pavone.utils.template_utils import TemplateUtils


def create_test_metadata(
    code: str = "SSIS-123",
    title: str = "测试电影",
    site: str = "test",
    studio: str = "S1",
    release_year: int = 2024,
) -> MovieMetadata:
    """创建测试用的元数据对象"""
    return MovieMetadata(
        identifier=f"{site}-{code}",
        code=code,
        title=title,
        url=f"https://{site}.com/video/{code}",
        site=site,
        studio=studio,
        actors=["演员A", "演员B"],
        year=release_year,
        premiered=f"{release_year}-01-15",
        cover="https://example.com/cover.jpg",
    )


@pytest.fixture
def temp_video_file(tmp_path: Path) -> Path:
    """创建临时视频文件"""
    video_file = tmp_path / "test_video.mp4"
    video_file.write_text("fake video content")
    return video_file


@pytest.fixture
def organize_config() -> OrganizeConfig:
    """创建测试用的整理配置"""
    config = OrganizeConfig()
    config.naming_pattern = "{code}"
    config.folder_structure = "organized"
    return config


@pytest.fixture
def test_metadata() -> MovieMetadata:
    """创建测试用的元数据"""
    return create_test_metadata()


@pytest.fixture
def builder() -> FileOperationBuilder:
    """创建 FileOperationBuilder 实例"""
    return FileOperationBuilder()


class TestFileOperationBuilder:
    """FileOperationBuilder 基础测试"""

    def test_init(self, builder: FileOperationBuilder):
        """测试初始化"""
        assert builder is not None
        assert builder.logger is not None

    def test_build_operation_success(
        self,
        builder: FileOperationBuilder,
        temp_video_file: Path,
        test_metadata: MovieMetadata,
        organize_config: OrganizeConfig,
        tmp_path: Path,
    ):
        """测试成功构建操作"""
        # 设置目标目录为临时目录
        organize_config.folder_structure = str(tmp_path / "organized")

        operation = builder.build_operation(temp_video_file, test_metadata, organize_config)

        assert operation is not None
        assert operation.opt_type == OperationType.MOVE
        assert operation.item_type == ItemType.VIDEO
        assert "SSIS-123.mp4" in operation.get_target_path()
        assert operation.get_code() == "SSIS-123"

    def test_build_operation_source_not_exists(
        self,
        builder: FileOperationBuilder,
        test_metadata: MovieMetadata,
        organize_config: OrganizeConfig,
        tmp_path: Path,
    ):
        """测试源文件不存在"""
        non_existent_file = tmp_path / "non_existent.mp4"

        with pytest.raises(ValueError, match="源文件不存在"):
            builder.build_operation(non_existent_file, test_metadata, organize_config)

    def test_build_operation_source_is_directory(
        self,
        builder: FileOperationBuilder,
        test_metadata: MovieMetadata,
        organize_config: OrganizeConfig,
        tmp_path: Path,
    ):
        """测试源路径是目录"""
        directory = tmp_path / "test_dir"
        directory.mkdir()

        with pytest.raises(ValueError, match="源路径不是文件"):
            builder.build_operation(directory, test_metadata, organize_config)


class TestFilenameBuild:
    """文件名构建测试"""

    def test_build_filename_code_only(
        self,
        builder: FileOperationBuilder,
        test_metadata: MovieMetadata,
        organize_config: OrganizeConfig,
    ):
        """测试只使用代码的文件名"""
        organize_config.naming_pattern = "{code}"

        filename = builder._build_filename(test_metadata, organize_config, ".mp4")

        assert filename == "SSIS-123.mp4"

    def test_build_filename_with_title(
        self,
        builder: FileOperationBuilder,
        test_metadata: MovieMetadata,
        organize_config: OrganizeConfig,
    ):
        """测试包含标题的文件名"""
        organize_config.naming_pattern = "{code} - {title}"

        filename = builder._build_filename(test_metadata, organize_config, ".mp4")

        assert filename == "SSIS-123 - 测试电影.mp4"

    def test_build_filename_with_studio(
        self,
        builder: FileOperationBuilder,
        test_metadata: MovieMetadata,
        organize_config: OrganizeConfig,
    ):
        """测试包含制作公司的文件名"""
        organize_config.naming_pattern = "{code} [{studio}]"

        filename = builder._build_filename(test_metadata, organize_config, ".mp4")

        assert filename == "SSIS-123 [S1].mp4"

    def test_build_filename_with_year(
        self,
        builder: FileOperationBuilder,
        test_metadata: MovieMetadata,
        organize_config: OrganizeConfig,
    ):
        """测试包含年份的文件名"""
        organize_config.naming_pattern = "{code} ({year})"

        filename = builder._build_filename(test_metadata, organize_config, ".mp4")

        assert filename == "SSIS-123 (2024).mp4"

    def test_build_filename_with_actors(
        self,
        builder: FileOperationBuilder,
        test_metadata: MovieMetadata,
        organize_config: OrganizeConfig,
    ):
        """测试包含演员的文件名"""
        organize_config.naming_pattern = "{code} - {actors}"

        filename = builder._build_filename(test_metadata, organize_config, ".mp4")

        assert filename == "SSIS-123 - 演员A, 演员B.mp4"

    def test_build_filename_complex_pattern(
        self,
        builder: FileOperationBuilder,
        test_metadata: MovieMetadata,
        organize_config: OrganizeConfig,
    ):
        """测试复杂命名模式"""
        organize_config.naming_pattern = "{code} - {title} [{studio}] ({year})"

        filename = builder._build_filename(test_metadata, organize_config, ".mp4")

        assert filename == "SSIS-123 - 测试电影 [S1] (2024).mp4"

    def test_build_filename_no_title(
        self,
        builder: FileOperationBuilder,
        organize_config: OrganizeConfig,
    ):
        """测试没有标题的元数据"""
        metadata = MovieMetadata(
            identifier="test-TEST-456",
            code="TEST-456",
            title="",
            url="https://test.com/video/TEST-456",
            site="test",
        )
        organize_config.naming_pattern = "{code} - {title}"

        filename = builder._build_filename(metadata, organize_config, ".mp4")

        # 应该处理空标题
        assert "TEST-456" in filename
        assert filename.endswith(".mp4")

    def test_build_filename_no_code(
        self,
        builder: FileOperationBuilder,
        organize_config: OrganizeConfig,
    ):
        """测试没有代码的元数据"""
        metadata = MovieMetadata(
            identifier="test-UNKNOWN",
            code="",
            title="测试电影",
            url="https://test.com/video/unknown",
            site="test",
        )
        organize_config.naming_pattern = "{code}"

        filename = builder._build_filename(metadata, organize_config, ".mp4")

        # 应该使用 UNKNOWN 作为代码
        assert filename == "UNKNOWN.mp4"


class TestSanitizeFilename:
    """文件名清理测试"""

    def test_sanitize_filename_with_illegal_chars(self, builder: FileOperationBuilder):
        """测试清理非法字符"""
        name = 'test<file>name:with"illegal/chars\\and|more?*'
        sanitized = TemplateUtils.sanitize_filename(name)

        # 非法字符应该被替换为空格
        assert "<" not in sanitized
        assert ">" not in sanitized
        assert ":" not in sanitized
        assert '"' not in sanitized
        assert "/" not in sanitized
        assert "\\" not in sanitized
        assert "|" not in sanitized
        assert "?" not in sanitized
        assert "*" not in sanitized

    def test_sanitize_filename_empty(self, builder: FileOperationBuilder):
        """测试空字符串"""
        assert TemplateUtils.sanitize_filename("") == ""

    def test_sanitize_filename_with_spaces(self, builder: FileOperationBuilder):
        """测试多余空格"""
        name = "test   multiple   spaces"
        sanitized = TemplateUtils.sanitize_filename(name)

        # 多余空格应该被清理
        assert "   " not in sanitized
        assert sanitized == "test multiple spaces"


class TestConflictResolution:
    """文件名冲突处理测试"""

    def test_resolve_conflict_no_conflict(
        self,
        builder: FileOperationBuilder,
        tmp_path: Path,
    ):
        """测试没有冲突的情况"""
        target_path = tmp_path / "new_file.mp4"

        result = builder._resolve_conflict(target_path, "rename")

        assert result == target_path

    def test_resolve_conflict_rename(
        self,
        builder: FileOperationBuilder,
        tmp_path: Path,
    ):
        """测试重命名策略"""
        # 创建已存在的文件
        existing_file = tmp_path / "existing.mp4"
        existing_file.write_text("existing content")

        result = builder._resolve_conflict(existing_file, "rename")

        # 应该返回带序号的新路径
        assert result != existing_file
        assert result.stem == "existing (1)"
        assert result.suffix == ".mp4"
        assert not result.exists()

    def test_resolve_conflict_rename_multiple(
        self,
        builder: FileOperationBuilder,
        tmp_path: Path,
    ):
        """测试多次冲突重命名"""
        # 创建多个已存在的文件
        (tmp_path / "existing.mp4").write_text("content")
        (tmp_path / "existing (1).mp4").write_text("content")
        (tmp_path / "existing (2).mp4").write_text("content")

        target_path = tmp_path / "existing.mp4"
        result = builder._resolve_conflict(target_path, "rename")

        # 应该返回 existing (3).mp4
        assert result.stem == "existing (3)"
        assert result.suffix == ".mp4"
        assert not result.exists()

    def test_resolve_conflict_skip(
        self,
        builder: FileOperationBuilder,
        tmp_path: Path,
    ):
        """测试跳过策略"""
        existing_file = tmp_path / "existing.mp4"
        existing_file.write_text("existing content")

        result = builder._resolve_conflict(existing_file, "skip")

        # 应该返回原路径
        assert result == existing_file

    def test_resolve_conflict_overwrite(
        self,
        builder: FileOperationBuilder,
        tmp_path: Path,
    ):
        """测试覆盖策略"""
        existing_file = tmp_path / "existing.mp4"
        existing_file.write_text("existing content")

        result = builder._resolve_conflict(existing_file, "overwrite")

        # 应该返回原路径
        assert result == existing_file


class TestBatchOperations:
    """批量操作测试"""

    def test_build_batch_operations_success(
        self,
        builder: FileOperationBuilder,
        organize_config: OrganizeConfig,
        tmp_path: Path,
    ):
        """测试成功批量构建操作"""
        # 创建多个测试文件
        file1 = tmp_path / "video1.mp4"
        file2 = tmp_path / "video2.mp4"
        file3 = tmp_path / "video3.mp4"
        file1.write_text("content1")
        file2.write_text("content2")
        file3.write_text("content3")

        # 创建元数据
        metadata1 = create_test_metadata(code="TEST-001", title="电影1")
        metadata2 = create_test_metadata(code="TEST-002", title="电影2")
        metadata3 = create_test_metadata(code="TEST-003", title="电影3")

        # 设置目标目录
        organize_config.folder_structure = str(tmp_path / "organized")

        # 批量构建
        files_metadata = [
            (file1, metadata1),
            (file2, metadata2),
            (file3, metadata3),
        ]
        operations = builder.build_batch_operations(files_metadata, organize_config)

        assert len(operations) == 3
        assert all(op.opt_type == OperationType.MOVE for op in operations)

    def test_build_batch_operations_with_errors(
        self,
        builder: FileOperationBuilder,
        organize_config: OrganizeConfig,
        tmp_path: Path,
    ):
        """测试批量操作时部分失败"""
        # 创建一个存在的文件和一个不存在的文件
        existing_file = tmp_path / "existing.mp4"
        existing_file.write_text("content")
        non_existing_file = tmp_path / "non_existing.mp4"

        metadata1 = create_test_metadata(code="TEST-001", title="电影1")
        metadata2 = create_test_metadata(code="TEST-002", title="电影2")

        organize_config.folder_structure = str(tmp_path / "organized")

        # 批量构建（包含一个失败的）
        files_metadata = [
            (existing_file, metadata1),
            (non_existing_file, metadata2),  # 这个会失败
        ]
        operations = builder.build_batch_operations(files_metadata, organize_config)

        # 应该只返回成功的操作
        assert len(operations) == 1
        assert operations[0].get_code() == "TEST-001"

    def test_build_batch_operations_empty(
        self,
        builder: FileOperationBuilder,
        organize_config: OrganizeConfig,
    ):
        """测试空列表"""
        operations = builder.build_batch_operations([], organize_config)

        assert operations == []


class TestTemplateResolution:
    """模板解析测试"""

    def test_resolve_template_code_only(
        self,
        builder: FileOperationBuilder,
        test_metadata: MovieMetadata,
    ):
        """测试仅包含 code 的模板"""
        result = TemplateUtils.resolve_template("{code}", test_metadata)
        assert result == "SSIS-123"

    def test_resolve_template_with_folder_structure(
        self,
        builder: FileOperationBuilder,
        test_metadata: MovieMetadata,
    ):
        """测试文件夹结构模板"""
        result = TemplateUtils.resolve_template("{studio}/{code}", test_metadata)
        assert result == "S1/SSIS-123"

    def test_resolve_template_complex(
        self,
        builder: FileOperationBuilder,
        test_metadata: MovieMetadata,
    ):
        """测试复杂模板"""
        result = TemplateUtils.resolve_template("{year}/{studio}/{code}", test_metadata)
        assert result == "2024/S1/SSIS-123"

    def test_resolve_template_with_title(
        self,
        builder: FileOperationBuilder,
        test_metadata: MovieMetadata,
    ):
        """测试包含标题的模板"""
        result = TemplateUtils.resolve_template("{code} - {title}", test_metadata)
        assert result == "SSIS-123 - 测试电影"

    def test_resolve_template_no_placeholders(
        self,
        builder: FileOperationBuilder,
        test_metadata: MovieMetadata,
    ):
        """测试没有占位符的模板"""
        result = TemplateUtils.resolve_template("organized", test_metadata)
        assert result == "organized"

    def test_resolve_template_special_chars_in_title(
        self,
        builder: FileOperationBuilder,
    ):
        """测试标题包含特殊字符"""
        metadata = create_test_metadata(code="TEST-001", title='测试<>:"/\\|?*电影')
        result = TemplateUtils.resolve_template("{code} - {title}", metadata)
        # 特殊字符应该被替换为空格
        assert "<" not in result
        assert ">" not in result
        assert ":" not in result


class TestBaseDirSupport:
    """base_dir 参数支持测试"""

    def test_build_operation_with_base_dir(
        self,
        builder: FileOperationBuilder,
        temp_video_file: Path,
        test_metadata: MovieMetadata,
        organize_config: OrganizeConfig,
        tmp_path: Path,
    ):
        """测试使用 base_dir 参数"""
        base_dir = tmp_path / "output"
        organize_config.folder_structure = "{code}"

        operation = builder.build_operation(
            temp_video_file,
            test_metadata,
            organize_config,
            base_dir=base_dir,
        )

        target_path = Path(operation.get_target_path())
        assert str(base_dir) in str(target_path)
        assert "SSIS-123" in str(target_path)

    def test_build_operation_with_folder_structure_template(
        self,
        builder: FileOperationBuilder,
        temp_video_file: Path,
        test_metadata: MovieMetadata,
        organize_config: OrganizeConfig,
        tmp_path: Path,
    ):
        """测试文件夹结构模板解析"""
        base_dir = tmp_path / "library"
        organize_config.folder_structure = "{studio}/{code}"
        organize_config.naming_pattern = "{code}"

        operation = builder.build_operation(
            temp_video_file,
            test_metadata,
            organize_config,
            base_dir=base_dir,
        )

        target_path = Path(operation.get_target_path())
        # 应该包含 base_dir/studio/code/filename.mp4
        assert str(base_dir) in str(target_path)
        assert "S1" in str(target_path)  # studio
        assert "SSIS-123" in str(target_path)  # code 和 filename

    def test_build_operation_without_base_dir(
        self,
        builder: FileOperationBuilder,
        temp_video_file: Path,
        test_metadata: MovieMetadata,
        organize_config: OrganizeConfig,
    ):
        """测试不提供 base_dir 时使用当前目录"""
        organize_config.folder_structure = "output"

        operation = builder.build_operation(
            temp_video_file,
            test_metadata,
            organize_config,
        )

        target_path = Path(operation.get_target_path())
        # 应该基于当前工作目录
        assert target_path.is_absolute()
        assert "output" in str(target_path)

    def test_build_operation_relative_base_dir(
        self,
        builder: FileOperationBuilder,
        temp_video_file: Path,
        test_metadata: MovieMetadata,
        organize_config: OrganizeConfig,
        tmp_path: Path,
    ):
        """测试相对路径 base_dir 转换为绝对路径"""
        organize_config.folder_structure = "{code}"
        relative_base = Path("relative/path")

        operation = builder.build_operation(
            temp_video_file,
            test_metadata,
            organize_config,
            base_dir=relative_base,
        )

        target_path = Path(operation.get_target_path())
        # 应该转换为绝对路径
        assert target_path.is_absolute()
        assert "relative" in str(target_path)
        assert "path" in str(target_path)

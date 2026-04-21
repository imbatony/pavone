"""jellyfin list 命令测试"""

from unittest.mock import MagicMock, patch

from click.testing import CliRunner

from pavone.cli.commands.jellyfin import _format_date, _truncate_text, jellyfin
from pavone.jellyfin.models import JellyfinItem, LibraryInfo


def _make_library(name: str = "测试库", lib_id: str = "lib-1", lib_type: str = "movies", item_count: int = 10) -> LibraryInfo:
    """创建测试用 LibraryInfo"""
    return LibraryInfo(name=name, id=lib_id, type=lib_type, item_count=item_count)


def _make_item(
    name: str = "测试视频",
    item_id: str = "item-1",
    path: str = "/media/test.mkv",
    metadata: dict | None = None,
) -> JellyfinItem:
    """创建测试用 JellyfinItem"""
    base_metadata = {
        "Id": item_id,
        "Name": name,
        "Type": "Movie",
        "Path": path,
        "DateCreated": "2026-04-15T10:00:00.0000000Z",
    }
    if metadata:
        base_metadata.update(metadata)
    return JellyfinItem(
        id=item_id,
        name=name,
        type="Movie",
        container="mkv",
        path=path,
        metadata=base_metadata,
    )


def _make_rich_item(name: str = "丰富视频", item_id: str = "item-rich") -> JellyfinItem:
    """创建元数据丰富的 JellyfinItem"""
    return _make_item(
        name=name,
        item_id=item_id,
        metadata={
            "Overview": "这是一个描述",
            "Genres": ["动作"],
            "ProductionYear": 2026,
            "People": [{"Name": "演员A", "Type": "Actor"}, {"Name": "导演B", "Type": "Director"}],
            "ImageTags": {"Primary": "abc"},
            "CommunityRating": 8.0,
            "Tags": ["推荐"],
            "Studios": [{"Name": "工作室"}],
        },
    )


def _make_poor_item(name: str = "贫乏视频", item_id: str = "item-poor") -> JellyfinItem:
    """创建元数据贫乏的 JellyfinItem"""
    return _make_item(name=name, item_id=item_id)


class TestTruncateText:
    """_truncate_text 辅助函数测试"""

    def test_short_text_unchanged(self) -> None:
        assert _truncate_text("hello", 10) == "hello"

    def test_long_text_truncated(self) -> None:
        result = _truncate_text("a" * 50, 10)
        assert result.endswith("...")
        assert len(result) <= 13  # 最多 10 char + "..."

    def test_chinese_text_truncated(self) -> None:
        result = _truncate_text("中文测试字符串很长很长", 10)
        assert result.endswith("...")

    def test_empty_text(self) -> None:
        assert _truncate_text("", 10) == ""


class TestFormatDate:
    """_format_date 辅助函数测试"""

    def test_none_returns_na(self) -> None:
        assert _format_date(None) == "N/A"

    def test_iso_date_truncated(self) -> None:
        assert _format_date("2026-04-15T10:00:00.0000000Z") == "2026-04-15"

    def test_short_date_unchanged(self) -> None:
        assert _format_date("2026-04") == "2026-04"


@patch("pavone.cli.commands.jellyfin.get_config_manager")
@patch("pavone.cli.commands.jellyfin.JellyfinClientWrapper")
class TestListCommand:
    """jellyfin list 命令测试"""

    def test_list_with_valid_library(self, mock_client_cls: MagicMock, mock_config: MagicMock) -> None:
        """指定有效库名时输出表头和数据行"""
        # Arrange
        config = MagicMock()
        config.jellyfin.enabled = True
        mock_config.return_value.get_config.return_value = config

        client = MagicMock()
        mock_client_cls.return_value = client
        client.get_libraries.return_value = [_make_library()]
        client.get_library_items.return_value = [_make_item()]

        runner = CliRunner()

        # Act
        result = runner.invoke(jellyfin, ["list", "测试库"])

        # Assert
        assert result.exit_code == 0
        assert "名称" in result.output
        assert "加入时间" in result.output
        assert "评分" in result.output
        assert "路径" in result.output
        assert "测试视频" in result.output

    def test_list_invalid_library_shows_error(self, mock_client_cls: MagicMock, mock_config: MagicMock) -> None:
        """库名不存在时输出错误并列出可用库"""
        config = MagicMock()
        config.jellyfin.enabled = True
        mock_config.return_value.get_config.return_value = config

        client = MagicMock()
        mock_client_cls.return_value = client
        client.get_libraries.return_value = [_make_library("库A"), _make_library("库B", lib_id="lib-2")]

        runner = CliRunner()
        result = runner.invoke(jellyfin, ["list", "不存在的库"])

        assert "不存在" in result.output
        assert "库A" in result.output
        assert "库B" in result.output

    def test_list_empty_library(self, mock_client_cls: MagicMock, mock_config: MagicMock) -> None:
        """空库时输出友好提示"""
        config = MagicMock()
        config.jellyfin.enabled = True
        mock_config.return_value.get_config.return_value = config

        client = MagicMock()
        mock_client_cls.return_value = client
        client.get_libraries.return_value = [_make_library()]
        client.get_library_items.return_value = []

        runner = CliRunner()
        result = runner.invoke(jellyfin, ["list", "测试库"])

        assert result.exit_code == 0
        assert "为空" in result.output

    def test_list_sort_by_name_asc(self, mock_client_cls: MagicMock, mock_config: MagicMock) -> None:
        """--sort-by name --order asc 参数正确传递"""
        config = MagicMock()
        config.jellyfin.enabled = True
        mock_config.return_value.get_config.return_value = config

        client = MagicMock()
        mock_client_cls.return_value = client
        client.get_libraries.return_value = [_make_library()]
        client.get_library_items.return_value = [_make_item()]

        runner = CliRunner()
        result = runner.invoke(jellyfin, ["list", "测试库", "--sort-by", "name", "--order", "asc"])

        assert result.exit_code == 0
        client.get_library_items.assert_called_once_with(
            library_ids=["lib-1"],
            limit=50,
            sort_by="SortName",
            sort_order="Ascending",
        )

    def test_list_limit_parameter(self, mock_client_cls: MagicMock, mock_config: MagicMock) -> None:
        """--limit 参数限制输出行数"""
        config = MagicMock()
        config.jellyfin.enabled = True
        mock_config.return_value.get_config.return_value = config

        client = MagicMock()
        mock_client_cls.return_value = client
        client.get_libraries.return_value = [_make_library()]
        client.get_library_items.return_value = [_make_item()]

        runner = CliRunner()
        result = runner.invoke(jellyfin, ["list", "测试库", "-n", "5"])

        assert result.exit_code == 0
        client.get_library_items.assert_called_once()
        call_kwargs = client.get_library_items.call_args
        assert call_kwargs.kwargs.get("limit") == 5 or call_kwargs[1].get("limit") == 5

    def test_list_metadata_score_sort_asc(self, mock_client_cls: MagicMock, mock_config: MagicMock) -> None:
        """-s metadata_score -o asc 时评分低的在前"""
        config = MagicMock()
        config.jellyfin.enabled = True
        mock_config.return_value.get_config.return_value = config

        client = MagicMock()
        mock_client_cls.return_value = client
        client.get_libraries.return_value = [_make_library()]
        # 第一页返回两个item，第二页返回空（分页终止）
        client.get_library_items.side_effect = [
            [_make_rich_item(), _make_poor_item()],
            [],
        ]

        runner = CliRunner()
        result = runner.invoke(jellyfin, ["list", "测试库", "-s", "metadata_score", "-o", "asc"])

        assert result.exit_code == 0
        lines = result.output.strip().split("\n")
        # 找到数据行（跳过标题和分隔线），评分低的应在前
        data_lines = [line for line in lines if line.strip() and line.strip()[0].isdigit()]
        assert len(data_lines) == 2
        assert "贫乏视频" in data_lines[0]
        assert "丰富视频" in data_lines[1]

    def test_list_metadata_score_sort_desc(self, mock_client_cls: MagicMock, mock_config: MagicMock) -> None:
        """-s metadata_score -o desc 时评分高的在前"""
        config = MagicMock()
        config.jellyfin.enabled = True
        mock_config.return_value.get_config.return_value = config

        client = MagicMock()
        mock_client_cls.return_value = client
        client.get_libraries.return_value = [_make_library()]
        client.get_library_items.side_effect = [
            [_make_poor_item(), _make_rich_item()],
            [],
        ]

        runner = CliRunner()
        result = runner.invoke(jellyfin, ["list", "测试库", "-s", "metadata_score", "-o", "desc"])

        assert result.exit_code == 0
        data_lines = [line for line in result.output.strip().split("\n") if line.strip() and line.strip()[0].isdigit()]
        assert len(data_lines) == 2
        assert "丰富视频" in data_lines[0]
        assert "贫乏视频" in data_lines[1]

    def test_list_metadata_score_with_limit(self, mock_client_cls: MagicMock, mock_config: MagicMock) -> None:
        """metadata_score 排序后 --limit 截断生效"""
        config = MagicMock()
        config.jellyfin.enabled = True
        mock_config.return_value.get_config.return_value = config

        client = MagicMock()
        mock_client_cls.return_value = client
        client.get_libraries.return_value = [_make_library()]
        client.get_library_items.side_effect = [
            [_make_rich_item("A", "i1"), _make_poor_item("B", "i2"), _make_item("C", "i3")],
            [],
        ]

        runner = CliRunner()
        result = runner.invoke(jellyfin, ["list", "测试库", "-s", "metadata_score", "-o", "asc", "-n", "1"])

        assert result.exit_code == 0
        data_lines = [line for line in result.output.strip().split("\n") if line.strip() and line.strip()[0].isdigit()]
        assert len(data_lines) == 1

    def test_list_interactive_multi_library(self, mock_client_cls: MagicMock, mock_config: MagicMock) -> None:
        """多个库时交互式选择"""
        config = MagicMock()
        config.jellyfin.enabled = True
        mock_config.return_value.get_config.return_value = config

        client = MagicMock()
        mock_client_cls.return_value = client
        client.get_libraries.return_value = [
            _make_library("库A", "lib-a"),
            _make_library("库B", "lib-b"),
        ]
        client.get_library_items.return_value = [_make_item()]

        runner = CliRunner()
        # 输入 "2" 选择第二个库
        result = runner.invoke(jellyfin, ["list"], input="2\n")

        assert result.exit_code == 0
        assert "库A" in result.output
        assert "库B" in result.output
        assert "已选择库: 库B" in result.output

    def test_list_interactive_single_library_auto_select(self, mock_client_cls: MagicMock, mock_config: MagicMock) -> None:
        """仅一个库时自动选择"""
        config = MagicMock()
        config.jellyfin.enabled = True
        mock_config.return_value.get_config.return_value = config

        client = MagicMock()
        mock_client_cls.return_value = client
        client.get_libraries.return_value = [_make_library("唯一库")]
        client.get_library_items.return_value = [_make_item()]

        runner = CliRunner()
        result = runner.invoke(jellyfin, ["list"])

        assert result.exit_code == 0
        assert "自动选择库: 唯一库" in result.output
        assert "测试视频" in result.output

    def test_list_no_libraries_error(self, mock_client_cls: MagicMock, mock_config: MagicMock) -> None:
        """无库时输出错误提示"""
        config = MagicMock()
        config.jellyfin.enabled = True
        mock_config.return_value.get_config.return_value = config

        client = MagicMock()
        mock_client_cls.return_value = client
        client.get_libraries.return_value = []

        runner = CliRunner()
        result = runner.invoke(jellyfin, ["list"])

        assert "没有可用的媒体库" in result.output

    def test_list_summary_line(self, mock_client_cls: MagicMock, mock_config: MagicMock) -> None:
        """验证摘要行输出"""
        config = MagicMock()
        config.jellyfin.enabled = True
        mock_config.return_value.get_config.return_value = config

        client = MagicMock()
        mock_client_cls.return_value = client
        client.get_libraries.return_value = [_make_library("我的视频", item_count=128)]
        client.get_library_items.return_value = [_make_item()]

        runner = CliRunner()
        result = runner.invoke(jellyfin, ["list", "我的视频"])

        assert result.exit_code == 0
        assert "我的视频" in result.output
        assert "128" in result.output
        assert "加入时间" in result.output
        assert "升序" in result.output

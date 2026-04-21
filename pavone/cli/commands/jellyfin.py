"""
Jellyfin 相关命令

提供 Jellyfin 库管理命令
"""

from typing import Any, List, Optional
from unicodedata import east_asian_width

import click

from ...config.logging_config import get_logger
from ...config.settings import get_config_manager
from ...jellyfin import (
    JellyfinClientWrapper,
    JellyfinDownloadHelper,
    LibraryManager,
)
from ...jellyfin.models import JellyfinItem
from ...models import ItemMetadata
from .utils import (
    confirm_action,
    echo_colored,
    echo_error,
    echo_info,
    echo_inline,
    echo_success,
    echo_success_inline,
    echo_warning,
    prompt_int,
    prompt_text,
)

logger = get_logger(__name__)


def get_display_width(text: str) -> int:
    """计算字符串的显示宽度（考虑中文字符宽度）"""
    width = 0
    for char in text:
        ea = east_asian_width(char)
        if ea in ("F", "W"):
            width += 2
        else:
            width += 1
    return width


def pad_text(text: str, target_width: int) -> str:
    """根据显示宽度填充文本"""
    current_width = get_display_width(text)
    if current_width >= target_width:
        return text
    padding = target_width - current_width
    return text + " " * padding


@click.group()
def jellyfin():
    """Jellyfin 库管理命令"""
    pass


@jellyfin.command()
def status():
    """查看 Jellyfin 连接状态"""
    config_manager = get_config_manager()
    config = config_manager.get_config()

    if not config.jellyfin.enabled:
        echo_error("Jellyfin 未启用，请在配置中启用")
        return

    try:
        client = JellyfinClientWrapper(config.jellyfin)
        client.authenticate()

        echo_success("Jellyfin 服务器连接成功\n")

        # 获取服务器信息
        server_info = client.get_server_info()
        echo_info("【服务器信息】")
        echo_info(f"  服务器名称: {server_info.get('ServerName', 'Unknown')}")
        echo_info(f"  版本: {server_info.get('Version', 'Unknown')}\n")

        # 获取库信息
        libraries = client.get_libraries()
        echo_info(f"可用的库 ({len(libraries)} 个):\n")
        for lib in libraries:
            echo_info(f"  • {lib.name:<20} | 类型: {lib.type:<8} | 项数: {lib.item_count}")

    except Exception as e:
        echo_error(f"连接失败: {e}")
        return 1


@jellyfin.command()
def libraries():
    """列出 Jellyfin 库"""
    config_manager = get_config_manager()
    config = config_manager.get_config()

    if not config.jellyfin.enabled:
        echo_error("Jellyfin 未启用")
        return

    try:
        client = JellyfinClientWrapper(config.jellyfin)
        client.authenticate()

        libraries = client.get_libraries()

        if not libraries:
            echo_warning("未找到任何库")
            return

        echo_success(f"找到 {len(libraries)} 个库\n")

        click.echo(pad_text("库名", 20) + " " + pad_text("ID", 40) + " " + pad_text("类型", 8) + " 项数")
        click.echo("-" * 80)

        for lib in libraries:
            click.echo(
                pad_text(lib.name[:20], 20)
                + " "
                + pad_text(lib.id[:40], 40)
                + " "
                + pad_text(lib.type, 8)
                + f" {lib.item_count}"
            )

    except Exception as e:
        echo_error(f"获取库列表失败: {e}")
        return 1


@jellyfin.command()
@click.argument("keyword", required=False)
def search(keyword: Optional[str] = None):
    """在 Jellyfin 库中搜索视频"""
    config_manager = get_config_manager()
    config = config_manager.get_config()

    if not config.jellyfin.enabled:
        echo_error("Jellyfin 未启用")
        return

    # 如果未提供关键词，提示用户输入
    if not keyword:
        keyword = prompt_text("请输入搜索关键词")

    try:
        client = JellyfinClientWrapper(config.jellyfin)
        client.authenticate()

        items = client.search_items(keyword, limit=20)

        if not items:
            echo_warning(f"未找到与 '{keyword}' 相关的视频")
            return

        echo_success(f"搜索到 {len(items)} 个结果\n")

        for i, item in enumerate(items, 1):
            echo_info(f"{i}. {item.name}")
            echo_info(f"   类型: {item.type}")
            echo_info(f"   ID: {item.id}")
            if item.path:
                echo_info(f"   路径: {item.path}\n")

        # 如果只有一个结果，自动显示详细信息
        if len(items) == 1:
            echo_info("只有一个搜索结果，自动显示详细信息...\n")
            _display_video_info(items[0].id, client)
            return

        # 询问用户是否查看详细信息
        try:
            if confirm_action("\n是否查看某个视频的详细信息?", default=False):
                try:
                    choice = prompt_int("请输入视频编号 (1-{})".format(len(items)), default=1)
                    if 1 <= choice <= len(items):
                        selected_item = items[choice - 1]
                        _display_video_info(selected_item.id, client)
                    else:
                        echo_error("无效的编号")
                except ValueError:
                    echo_error("无效的输入")
                except Exception as e:
                    echo_error(f"获取详细信息失败: {e}")
        except (EOFError, click.exceptions.Abort):
            pass

    except KeyboardInterrupt:
        echo_warning("已取消搜索")
        return 1
    except Exception as e:
        echo_error(f"搜索失败: {e}")
        return 1


def _format_section(title: str, fields: list[tuple[str, Any]]) -> None:
    """格式化一个信息段"""
    click.echo(title)
    # 输出表头和分隔符
    click.echo(pad_text("字段", 16) + " 数值")
    click.echo("-" * 80)
    # 输出字段
    for field_name, value in fields:
        if value:
            value_str = str(value)
            if len(value_str) > 60:
                value_str = value_str[:60] + "..."
            click.echo(pad_text(field_name, 16) + " " + value_str)
    click.echo()


def _get_basic_info_fields(item: JellyfinItem) -> list[tuple[str, str]]:
    """获取基本信息字段"""
    return [
        ("ID", item.id),
        ("文件路径", item.path if item.path else ""),
        ("容器", item.container if item.container else ""),
    ]


def _get_metadata_fields(item: JellyfinItem, metadata: ItemMetadata) -> list[tuple[str, str]]:
    """获取元数据字段"""
    fields: list[tuple[str, str]] = []

    # 标题
    fields.append(("标题", item.name))

    # 代码
    if metadata.external_id:
        fields.append(("代码", metadata.external_id))

    # 发行日期
    if metadata.year:
        fields.append(("发行日期", str(metadata.year)))
    elif metadata.premiere_date:
        fields.append(("发行日期", metadata.premiere_date))

    # 时长
    if metadata.runtime_minutes:
        fields.append(("时长", f"{metadata.runtime_minutes} 分钟"))

    # 制作公司
    if metadata.studio_names:
        fields.append(("制作公司", ", ".join(metadata.studio_names)))

    # 导演
    if metadata.directors:
        fields.append(("导演", ", ".join(metadata.directors[:3])))

    # 演员
    if metadata.actors:
        fields.append(("演员", ", ".join(metadata.actors[:5])))

    # 系列
    if metadata.series_name:
        fields.append(("系列", metadata.series_name))

    # 类型
    if metadata.genres:
        fields.append(("类型", ", ".join(metadata.genres)))

    # 标签
    if metadata.tags:
        fields.append(("标签", ", ".join(metadata.tags)))

    # 评分
    if metadata.rating is not None:
        fields.append(("评分", f"{metadata.rating}/10"))

    # 分级
    if metadata.official_rating:
        fields.append(("分级", metadata.official_rating))

    # 描述
    if metadata.overview:
        overview = metadata.overview
        if len(overview) > 60:
            overview = overview[:60] + "..."
        fields.append(("描述", overview))

    # 图片信息
    image_info: list[str] = []
    if metadata.has_primary_image:
        image_info.append("封面")
    if metadata.has_thumb_image:
        image_info.append("缩略图")
    if metadata.backdrop_count > 0:
        image_info.append(f"背景({metadata.backdrop_count})")

    if image_info:
        fields.append(("图片", ", ".join(image_info)))

    return fields


def _get_media_stream_fields(metadata: ItemMetadata) -> list[tuple[str, Any]]:
    """获取媒体流信息字段"""
    if not metadata.media_streams:
        return []

    fields: list[tuple[str, Any]] = []

    # 视频流
    if metadata.video_streams:
        for i, stream in enumerate(metadata.video_streams, 1):
            codec = stream.get("Codec", "未知")
            width = stream.get("Width", 0)
            height = stream.get("Height", 0)
            resolution = f"{width}x{height}" if width and height else "未知"
            bitrate = stream.get("BitRate", 0)
            bitrate_str = f"{bitrate / 1000000:.2f} Mbps" if bitrate else "未知"

            stream_info = f"视频流{i}: {codec} {resolution} {bitrate_str}"
            fields.append(("", stream_info))

    # 音频流
    if metadata.audio_streams:
        for i, stream in enumerate(metadata.audio_streams, 1):
            lang = stream.get("Language", "未知")
            codec = stream.get("Codec", "未知")
            channels = stream.get("Channels", 0)
            bitrate = stream.get("BitRate", 0)
            bitrate_str = f"{bitrate / 1000000:.2f} Mbps" if bitrate else "未知"

            stream_info = f"音频流{i} ({lang}): {codec} {channels}声道 {bitrate_str}"
            fields.append(("", stream_info))

    # 字幕流
    if metadata.subtitle_streams:
        langs = [s.get("Language", "未知") for s in metadata.subtitle_streams]
        fields.append(("字幕", ", ".join(langs)))

    return fields


def _get_file_info_fields(metadata: ItemMetadata) -> list[tuple[str, Any]]:
    """获取文件信息字段"""
    fields: list[tuple[str, Any]] = []
    if metadata.size:
        fields.append(("文件大小", metadata.size_str))
    return fields


def _get_play_info_fields(metadata: ItemMetadata) -> list[tuple[str, Any]]:
    """获取播放信息字段"""
    fields: list[tuple[str, Any]] = []

    if metadata.playback_minutes:
        fields.append(("已播放", f"{metadata.playback_minutes} 分钟"))
    if metadata.is_played:
        status = "是" if metadata.is_played else "否"
        fields.append(("已观看", status))
    if metadata.play_count:
        fields.append(("播放次数", str(metadata.play_count)))
    if metadata.last_played_date:
        fields.append(("最后播放", metadata.last_played_date))

    return fields


def _display_video_info(item_id: str, client: Optional[JellyfinClientWrapper] = None) -> None:
    """显示视频的详细信息"""
    try:
        if client is None:
            config_manager = get_config_manager()
            config = config_manager.get_config()
            client = JellyfinClientWrapper(config.jellyfin)
            client.authenticate()

        item = client.get_item(item_id)
        metadata = ItemMetadata(item.metadata or {})

        echo_success(f"视频详情: {item.name}\n")

        # 基本信息
        basic_fields = _get_basic_info_fields(item)
        _format_section("【基本信息】", basic_fields)

        # 元数据
        metadata_fields = _get_metadata_fields(item, metadata)
        if metadata_fields:
            _format_section("【元数据】", metadata_fields)

        # 媒体流信息
        stream_fields = _get_media_stream_fields(metadata)
        if stream_fields:
            _format_section("【媒体流信息】", stream_fields)

        # 文件信息
        file_fields = _get_file_info_fields(metadata)
        if file_fields:
            _format_section("【文件信息】", file_fields)

        # 播放信息
        play_fields = _get_play_info_fields(metadata)
        if play_fields:
            _format_section("【播放信息】", play_fields)

    except Exception as e:
        echo_error(f"获取详细信息失败: {e}")


@jellyfin.command()
@click.argument("library_name")
def scan(library_name: str):
    """扫描 Jellyfin 库"""
    config_manager = get_config_manager()
    config = config_manager.get_config()

    if not config.jellyfin.enabled:
        echo_error("Jellyfin 未启用")
        return

    try:
        client = JellyfinClientWrapper(config.jellyfin)
        client.authenticate()

        library_manager = LibraryManager(client)
        library_manager.initialize()

        echo_info(f"正在扫描库: {library_name}\n")

        # 扫描库
        with click.progressbar(length=1, label="扫描中") as bar:
            scanned = library_manager.scan_library(force_refresh=True)
            bar.update(1)

        if library_name in scanned:
            items = scanned[library_name]
            echo_success(f"库 '{library_name}' 扫描完成: {len(items)} 项\n")

            # 显示前 10 项
            echo_info("前 10 项:")
            for i, item in enumerate(items[:10], 1):
                click.echo(f"  {i}. {item.name}")

        else:
            echo_warning(f"库 '{library_name}' 未找到")

    except Exception as e:
        echo_error(f"扫描库失败: {e}")
        return 1


@jellyfin.command()
@click.argument("library_name")
@click.option("--force", is_flag=True, help="强制全量扫描（不使用缓存）")
def refresh(library_name: str, force: bool):
    """刷新 Jellyfin 库的元数据（增量或全量扫描）"""
    config_manager = get_config_manager()
    config = config_manager.get_config()

    if not config.jellyfin.enabled:
        echo_error("Jellyfin 未启用")
        return

    try:
        client = JellyfinClientWrapper(config.jellyfin)
        client.authenticate()

        # 创建库管理器
        library_manager = LibraryManager(client)
        library_manager.initialize()

        # 查找库
        libraries = client.get_libraries()
        target_lib = None

        for lib in libraries:
            if lib.name == library_name:
                target_lib = lib
                break

        if not target_lib:
            echo_warning(f"库 '{library_name}' 未找到")
            return 1

        # 扫描库的元数据
        scan_type = "全量" if force else "增量"
        echo_info(f"正在{scan_type}扫描库 '{library_name}' 的元数据...")
        scanned = library_manager.scan_library(force_refresh=force)

        if library_name in scanned:
            items = scanned[library_name]
            echo_success(f"库 '{library_name}' {scan_type}扫描完成: {len(items)} 项\n")
        else:
            echo_warning(f"库 '{library_name}' 未找到任何项")

    except Exception as e:
        echo_error(f"刷新元数据失败: {e}")
        return 1


@jellyfin.command()
@click.argument("item_id", required=False)
def info(item_id: str):
    """查看视频的详细信息"""
    config_manager = get_config_manager()
    config = config_manager.get_config()

    if not config.jellyfin.enabled:
        echo_error("Jellyfin 未启用")
        return

    if not item_id:
        item_id = prompt_text("请输入视频的 ID")

    try:
        client = JellyfinClientWrapper(config.jellyfin)
        client.authenticate()
        _display_video_info(item_id, client)

    except Exception as e:
        echo_error(f"获取信息失败: {e}")
        return 1


@jellyfin.command()
@click.argument("keyword", required=False)
def duplicate_check(keyword: str):
    """检查是否有重复视频"""
    config_manager = get_config_manager()
    config = config_manager.get_config()

    if not config.jellyfin.enabled:
        echo_error("Jellyfin 未启用")
        return

    # 如果未提供关键词，提示用户输入
    if not keyword:
        keyword = click.prompt("请输入要检查的视频标题或番号")

    try:
        helper = JellyfinDownloadHelper(config.jellyfin)

        if not helper.is_available():
            echo_error("Jellyfin 不可用")
            return 1

        # 尝试将输入识别为番号或标题
        import re

        video_code = None
        video_title = keyword

        # 检查是否为视频番号格式
        if re.match(r"^[A-Z0-9]+-\d+$", keyword) or re.match(r"^[A-Z]+\d+$", keyword):
            video_code = keyword
            video_title = keyword

        duplicate_info = helper.check_duplicate(video_title, video_code)

        if duplicate_info and duplicate_info.exists and duplicate_info.item and duplicate_info.quality_info:
            echo_success(f"找到重复项: {duplicate_info.item.name}\n")

            quality_info = duplicate_info.quality_info
            echo_info("【视频质量信息】")
            click.echo(pad_text("路径", 12) + " " + str(quality_info.path)[:60])
            click.echo(pad_text("大小", 12) + " " + str(quality_info.size))
            click.echo(pad_text("分辨率", 12) + " " + str(quality_info.resolution))
            click.echo(pad_text("比特率", 12) + " " + str(quality_info.bitrate))
            click.echo(pad_text("编码", 12) + " " + str(quality_info.codec))
            click.echo(pad_text("时长", 12) + " " + str(quality_info.runtime))
            click.echo(pad_text("添加时间", 12) + " " + str(quality_info.added_date))

        else:
            echo_warning(f"未找到与 '{keyword}' 相关的视频")

    except Exception as e:
        echo_error(f"检查失败: {e}")
        return 1


@jellyfin.command()
@click.argument(
    "source_path",
    type=click.Path(exists=True, file_okay=False, dir_okay=True, path_type=str),
)
def move(source_path: str):  # noqa: C901
    """将下载的文件夹移动到 Jellyfin 库

    示例:
        pavone jellyfin move "/path/to/downloaded/video_folder"
    """
    import os
    from pathlib import Path

    config_manager = get_config_manager()
    config = config_manager.get_config()

    if not config.jellyfin.enabled:
        echo_error("Jellyfin 未启用")
        return

    try:
        # 验证源路径
        source = Path(source_path)
        if not source.is_dir():
            echo_error(f"源路径不是文件夹: {source_path}")
            return 1

        source_folder_name = source.name

        # 初始化 Jellyfin 助手
        helper = JellyfinDownloadHelper(config.jellyfin)

        if not helper.is_available():
            echo_error("Jellyfin 不可用，请检查服务器连接")
            return 1

        # 获取库列表
        library_folders = helper.get_library_folders()
        if not library_folders:
            echo_error("无法获取 Jellyfin 库信息")
            return 1

        # 过滤有有效文件夹路径的库
        valid_libraries = {lib_name: folders for lib_name, folders in library_folders.items() if folders}

        if not valid_libraries:
            echo_error("没有找到任何配置了文件夹路径的库")
            return 1

        # 显示源文件夹信息
        echo_info("\n" + "=" * 70)
        echo_info("准备移动下载文件夹到 Jellyfin")
        echo_info("=" * 70)
        echo_info(f"📁 源文件夹: {source_path}\n")

        # 显示库列表
        echo_info("可用的 Jellyfin 库:")
        libraries_list: list[tuple[str, list[str]]] = list(valid_libraries.items())
        for i, (lib_name, folders) in enumerate(libraries_list, 1):
            echo_inline(f"  {i}. ")
            echo_success_inline(f"{lib_name}")
            for folder in folders:
                echo_info(f"     📁 {folder}")

        selected_folders: list[str] = []
        selected_lib_name: str = ""
        target_folder: str = ""
        # 让用户选择库
        while True:
            try:
                lib_choice_input = click.prompt("\n请选择库", type=click.IntRange(1, len(libraries_list)))
                lib_choice: int = int(lib_choice_input)
                if lib_choice > 0 and lib_choice <= len(libraries_list):
                    selected_lib_name, selected_folders = libraries_list[lib_choice - 1]
                    echo_colored(f"✓ 已选择库: {selected_lib_name}\n", fg="green", bold=True)
                    break
            except click.BadParameter:
                echo_error(f"请输入 1 到 {len(libraries_list)} 之间的数字")

        # 如果库有多个文件夹，让用户选择
        if len(selected_folders) > 1:
            echo_info(f"库 '{selected_lib_name}' 有多个文件夹:")
            for i, folder in enumerate(selected_folders, 1):
                echo_info(f"  {i}. 📁 {folder}")

            while True:
                try:
                    folder_choice: int = click.prompt("请选择文件夹", type=click.IntRange(1, len(selected_folders)))
                    target_folder = str(selected_folders[folder_choice - 1])
                    echo_colored(f"✓ 已选择文件夹: {target_folder}\n", fg="green", bold=True)
                    break
                except click.BadParameter:
                    echo_error(f"请输入 1 到 {len(selected_folders)} 之间的数字")
        else:
            target_folder = selected_folders[0]
            echo_colored(f"✓ 已选择文件夹: {target_folder}\n", fg="green", bold=True)

        # 显示最终的移动确认
        target_location = os.path.join(target_folder, source_folder_name)

        echo_info("=" * 70)
        echo_info("移动确认:")
        echo_info("=" * 70)
        echo_info(f"📁 源位置: {source_path}")
        echo_info(f"📁 目标位置: {target_location}\n")

        confirm = click.confirm("确认移动？", default=True)

        if not confirm:
            echo_warning("已取消移动")
            return

        # 执行文件夹移动
        if helper.move_to_library(source_path, target_folder):
            echo_colored("\n✓ 文件夹移动成功!\n", fg="green", bold=True)
            echo_success(f"源位置: {source_path}")
            echo_success(f"目标位置: {target_location}")

            # 询问是否增量刷新元数据
            refresh = click.confirm("\n是否增量刷新 Jellyfin 库的元数据？", default=True)
            if refresh:
                if helper.refresh_library(selected_lib_name):
                    echo_colored("✓ 元数据增量刷新成功!\n", fg="green", bold=True)
                else:
                    echo_error("元数据刷新失败")
                    return 1
        else:
            echo_error("文件夹移动失败")
            return 1

    except Exception as e:
        echo_error(f"操作失败: {e}")
        logger.exception("移动文件夹时出错")
        return 1


def _truncate_text(text: str, max_width: int) -> str:
    """截断文本至指定显示宽度，超出部分用省略号替代"""
    if get_display_width(text) <= max_width:
        return text
    result = ""
    current_width = 0
    for char in text:
        ea = east_asian_width(char)
        char_width = 2 if ea in ("F", "W") else 1
        if current_width + char_width + 3 > max_width:  # 预留 "..." 的 3 个宽度
            break
        result += char
        current_width += char_width
    return result + "..."


def _format_date(date_str: Optional[str]) -> str:
    """格式化 Jellyfin 日期字符串为 YYYY-MM-DD"""
    if not date_str:
        return "N/A"
    return date_str[:10] if len(date_str) >= 10 else date_str


# 排序字段映射: CLI 参数 → Jellyfin API SortBy 值
_SORT_BY_MAP = {
    "name": "SortName",
    "date_added": "DateCreated",
}

# 需要客户端排序的字段（无法由 Jellyfin API 直接排序）
_CLIENT_SORT_FIELDS = {"metadata_score", "quality"}

# 排序方向映射: CLI 参数 → Jellyfin API SortOrder 值
_SORT_ORDER_MAP = {
    "asc": "Ascending",
    "desc": "Descending",
}

# 排序字段中文标签
_SORT_LABEL_MAP = {
    "name": "名称",
    "date_added": "加入时间",
    "metadata_score": "元数据评分",
    "quality": "视频质量",
}

_ORDER_LABEL_MAP = {
    "asc": "升序",
    "desc": "降序",
}


@jellyfin.command("list")
@click.argument("library_name", required=False, default=None)
@click.option(
    "--sort-by",
    "-s",
    type=click.Choice(["name", "date_added", "metadata_score", "quality"]),
    default="date_added",
    help="排序字段",
)
@click.option("--order", "-o", type=click.Choice(["asc", "desc"]), default="asc", help="排序方向")
@click.option("--limit", "-n", type=click.IntRange(1, 10000), default=50, help="显示记录数上限")
def list_videos(library_name: Optional[str], sort_by: str, order: str, limit: int) -> None:
    """列取媒体库中的视频"""
    config_manager = get_config_manager()
    config = config_manager.get_config()

    if not config.jellyfin.enabled:
        echo_error("Jellyfin 未启用，请在配置中启用")
        return

    try:
        client = JellyfinClientWrapper(config.jellyfin)
        client.authenticate()

        libraries = client.get_libraries()
        if not libraries:
            echo_error("Jellyfin 上没有可用的媒体库")
            return

        # 交互式选择媒体库（T011: US3）
        if library_name is None:
            if len(libraries) == 1:
                selected_lib = libraries[0]
                echo_colored(f"✓ 自动选择库: {selected_lib.name}", fg="green", bold=True)
            else:
                click.echo("请选择媒体库:")
                for i, lib in enumerate(libraries, 1):
                    click.echo(f"  {i}. {lib.name} ({lib.item_count} 项)")
                click.echo()
                lib_choice: int = click.prompt("请选择库", type=click.IntRange(1, len(libraries)))
                selected_lib = libraries[lib_choice - 1]
                echo_colored(f"✓ 已选择库: {selected_lib.name}\n", fg="green", bold=True)
        else:
            # 按名称查找媒体库
            selected_lib = None
            for lib in libraries:
                if lib.name == library_name:
                    selected_lib = lib
                    break
            if selected_lib is None:
                available = ", ".join(lib.name for lib in libraries)
                echo_error(f'媒体库 "{library_name}" 不存在。可用的媒体库: {available}')
                return

        # 获取视频数据
        items: List[JellyfinItem]
        if sort_by in _CLIENT_SORT_FIELDS:
            # 客户端排序: 需要获取全量数据
            items = []
            page_size = 100
            start_index = 0
            while True:
                page = client.get_library_items(
                    library_ids=[selected_lib.id],
                    limit=page_size,
                    start_index=start_index,
                )
                if not page:
                    break
                items.extend(page)
                if len(page) < page_size:
                    break
                start_index += page_size

            reverse = order == "desc"
            if sort_by == "metadata_score":
                items.sort(key=lambda item: ItemMetadata(item.metadata).metadata_score, reverse=reverse)
            elif sort_by == "quality":
                items.sort(key=lambda item: ItemMetadata(item.metadata).video_height, reverse=reverse)
            total_count = len(items)
            items = items[:limit]
        else:
            # 服务端排序
            api_sort_by = _SORT_BY_MAP.get(sort_by)
            api_sort_order = _SORT_ORDER_MAP.get(order)
            items = client.get_library_items(
                library_ids=[selected_lib.id],
                limit=limit,
                sort_by=api_sort_by,
                sort_order=api_sort_order,
            )
            total_count = selected_lib.item_count

        # 展示结果
        if not items:
            click.echo(f'媒体库 "{selected_lib.name}" 为空，没有视频内容。')
            return

        sort_label = _SORT_LABEL_MAP.get(sort_by, sort_by)
        order_label = _ORDER_LABEL_MAP.get(order, order)
        shown = len(items)
        click.echo(
            f"\n媒体库: {selected_lib.name} (共 {total_count} 个视频, 显示前 {shown} 条, 按{sort_label}{order_label})\n"
        )

        rows: list[list[Any]] = []
        for i, item in enumerate(items, 1):
            metadata = ItemMetadata(item.metadata)
            name_display = _truncate_text(item.name, 28)
            date_display = _format_date(metadata.added_date)
            score_display = str(metadata.metadata_score)
            quality_display = metadata.video_quality
            path_display = _truncate_text(item.path or "N/A", 36)
            rows.append([str(i), name_display, date_display, score_display, quality_display, path_display])

        # 手动对齐表格（tabulate 不处理 CJK 宽字符）
        col_widths = [4, 30, 12, 6, 8, 38]
        headers = ["#", "名称", "加入时间", "评分", "质量", "路径"]
        header_line = "  ".join(pad_text(h, w) for h, w in zip(headers, col_widths))
        sep_line = "  ".join("-" * w for w in col_widths)
        click.echo(header_line)
        click.echo(sep_line)
        for row in rows:
            line = "  ".join(pad_text(cell, w) for cell, w in zip(row, col_widths))
            click.echo(line)

    except Exception as e:
        echo_error(f"列取视频失败: {e}")
        logger.exception("列取视频时出错")

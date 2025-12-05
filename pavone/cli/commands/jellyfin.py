"""
Jellyfin 相关命令

提供 Jellyfin 库管理命令
"""

import click
from unicodedata import east_asian_width

from ...config.settings import get_config_manager
from ...jellyfin import (
    JellyfinClientWrapper,
    JellyfinDownloadHelper,
    LibraryManager,
)
from ...models import ItemMetadata
from ...config.logging_config import get_logger
from .utils import echo_error, echo_info, echo_success, echo_warning


logger = get_logger(__name__)


def get_display_width(text: str) -> int:
    """计算字符串的显示宽度（考虑中文字符宽度）"""
    width = 0
    for char in text:
        ea = east_asian_width(char)
        if ea in ('F', 'W'):
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
    return text + ' ' * padding


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
        
        print(pad_text("库名", 20) + " " + pad_text("ID", 40) + " " + pad_text("类型", 8) + " 项数")
        print("-" * 80)
        
        for lib in libraries:
            print(pad_text(lib.name[:20], 20) + " " + pad_text(lib.id[:40], 40) + " " + pad_text(lib.type, 8) + f" {lib.item_count}")
            
    except Exception as e:
        echo_error(f"获取库列表失败: {e}")
        return 1


@jellyfin.command()
@click.argument("keyword", required=False)
def search(keyword):
    """在 Jellyfin 库中搜索视频"""
    config_manager = get_config_manager()
    config = config_manager.get_config()

    if not config.jellyfin.enabled:
        echo_error("Jellyfin 未启用")
        return

    # 如果未提供关键词，提示用户输入
    if not keyword:
        keyword = click.prompt("请输入搜索关键词")

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
            if click.confirm("\n是否查看某个视频的详细信息?", default=False):
                try:
                    choice = click.prompt("请输入视频编号 (1-{})".format(len(items)), type=int, default=1)
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


def _display_video_info(item_id, client=None):
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
        
        def format_section(title: str, fields: list) -> None:
            """格式化一个信息段"""
            print(title)
            # 输出表头和分隔符
            print(pad_text("字段", 16) + " 数值")
            print("-" * 80)
            # 输出字段
            for field_name, value in fields:
                if value:
                    value_str = str(value)
                    if len(value_str) > 60:
                        value_str = value_str[:60] + "..."
                    print(pad_text(field_name, 16) + " " + value_str)
            print()
        
        # 基本信息部分
        basic_fields = [
            ("ID", item.id),
            ("文件路径", item.path if item.path else ""),
            ("容器", item.container if item.container else ""),
        ]
        format_section("【基本信息】", basic_fields)
        
        # 元数据部分 - 与metadata show命令字段完全对标
        metadata_fields = []
        
        # 标题
        metadata_fields.append(("标题", item.name))
        
        # 代码
        if metadata.external_id:
            metadata_fields.append(("代码", metadata.external_id))
        
        # 发行日期
        if metadata.year:
            metadata_fields.append(("发行日期", str(metadata.year)))
        elif metadata.premiere_date:
            metadata_fields.append(("发行日期", metadata.premiere_date))
        
        # 时长
        if metadata.runtime_minutes:
            metadata_fields.append(("时长", f"{metadata.runtime_minutes} 分钟"))
        
        # 制作公司
        if metadata.studio_names:
            metadata_fields.append(("制作公司", ', '.join(metadata.studio_names)))
        
        # 导演
        if metadata.directors:
            metadata_fields.append(("导演", ', '.join(metadata.directors[:3])))
        
        # 演员
        if metadata.actors:
            metadata_fields.append(("演员", ', '.join(metadata.actors[:5])))
        
        # 系列
        if metadata.series_name:
            metadata_fields.append(("系列", metadata.series_name))
        
        # 类型
        if metadata.genres:
            metadata_fields.append(("类型", ', '.join(metadata.genres)))
        
        # 标签
        if metadata.tags:
            metadata_fields.append(("标签", ', '.join(metadata.tags)))
        
        # 评分
        if metadata.rating is not None:
            metadata_fields.append(("评分", f"{metadata.rating}/10"))
        
        # 分级
        if metadata.official_rating:
            metadata_fields.append(("分级", metadata.official_rating))
        
        # 描述
        if metadata.overview:
            overview = metadata.overview
            if len(overview) > 60:
                overview = overview[:60] + "..."
            metadata_fields.append(("描述", overview))
        
        # 图片信息
        image_info = []
        if metadata.has_primary_image:
            image_info.append("封面")
        if metadata.has_thumb_image:
            image_info.append("缩略图")
        if metadata.backdrop_count > 0:
            image_info.append(f"背景({metadata.backdrop_count})")
        
        if image_info:
            metadata_fields.append(("图片", ", ".join(image_info)))
        
        if metadata_fields:
            format_section("【元数据】", metadata_fields)
        
        # 媒体流信息 - 整合为表格式
        if metadata.media_streams:
            stream_fields = []
            
            if metadata.video_streams:
                for i, stream in enumerate(metadata.video_streams, 1):
                    codec = stream.get('Codec', '未知')
                    width = stream.get('Width', 0)
                    height = stream.get('Height', 0)
                    resolution = f"{width}x{height}" if width and height else "未知"
                    bitrate = stream.get('BitRate', 0)
                    bitrate_str = f"{bitrate / 1000000:.2f} Mbps" if bitrate else "未知"
                    
                    stream_info = f"视频流{i}: {codec} {resolution} {bitrate_str}"
                    stream_fields.append(("", stream_info))
            
            if metadata.audio_streams:
                for i, stream in enumerate(metadata.audio_streams, 1):
                    lang = stream.get('Language', '未知')
                    codec = stream.get('Codec', '未知')
                    channels = stream.get('Channels', 0)
                    bitrate = stream.get('BitRate', 0)
                    bitrate_str = f"{bitrate / 1000000:.2f} Mbps" if bitrate else "未知"
                    
                    stream_info = f"音频流{i} ({lang}): {codec} {channels}声道 {bitrate_str}"
                    stream_fields.append(("", stream_info))
            
            if metadata.subtitle_streams:
                langs = [s.get('Language', '未知') for s in metadata.subtitle_streams]
                stream_fields.append(("字幕", ', '.join(langs)))
            
            if stream_fields:
                format_section("【媒体流信息】", stream_fields)
        
        # 文件信息部分
        file_fields = []
        
        if metadata.size:
            file_fields.append(("文件大小", metadata.size_str))
        
        if file_fields:
            format_section("【文件信息】", file_fields)
        
        # 播放信息部分
        play_fields = []
        
        if metadata.playback_minutes:
            play_fields.append(("已播放", f"{metadata.playback_minutes} 分钟"))
        if metadata.is_played:
            status = "是" if metadata.is_played else "否"
            play_fields.append(("已观看", status))
        if metadata.play_count:
            play_fields.append(("播放次数", str(metadata.play_count)))
        if metadata.last_played_date:
            play_fields.append(("最后播放", metadata.last_played_date))
        
        if play_fields:
            format_section("【播放信息】", play_fields)
        
    except Exception as e:
        echo_error(f"获取详细信息失败: {e}")


@jellyfin.command()
@click.argument("library_name")
def scan(library_name):
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
                print(f"  {i}. {item.name}")
                
        else:
            echo_warning(f"库 '{library_name}' 未找到")
            
    except Exception as e:
        echo_error(f"扫描库失败: {e}")
        return 1


@jellyfin.command()
@click.argument("library_name")
@click.option("--force", is_flag=True, help="强制全量扫描（不使用缓存）")
def refresh(library_name, force):
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
def info(item_id):
    """查看视频的详细信息"""
    config_manager = get_config_manager()
    config = config_manager.get_config()

    if not config.jellyfin.enabled:
        echo_error("Jellyfin 未启用")
        return

    if not item_id:
        item_id = click.prompt("请输入视频的 ID")

    try:
        client = JellyfinClientWrapper(config.jellyfin)
        client.authenticate()
        _display_video_info(item_id, client)
            
    except Exception as e:
        echo_error(f"获取信息失败: {e}")
        return 1


@jellyfin.command()
@click.argument("keyword", required=False)
def duplicate_check(keyword):
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
        if re.match(r'^[A-Z0-9]+-\d+$', keyword) or re.match(r'^[A-Z]+\d+$', keyword):
            video_code = keyword
            video_title = keyword
        
        duplicate_info = helper.check_duplicate(video_title, video_code)
        
        if duplicate_info and duplicate_info.get("exists"):
            echo_success(f"找到重复项: {duplicate_info['item'].name}\n")
            
            quality_info = duplicate_info["quality_info"]
            echo_info("【视频质量信息】")
            print(pad_text("路径", 12) + " " + str(quality_info.get('path', '未知'))[:60])
            print(pad_text("大小", 12) + " " + str(quality_info.get('size', '未知')))
            print(pad_text("分辨率", 12) + " " + str(quality_info.get('resolution', '未知')))
            print(pad_text("比特率", 12) + " " + str(quality_info.get('bitrate', '未知')))
            print(pad_text("编码", 12) + " " + str(quality_info.get('codec', '未知')))
            print(pad_text("时长", 12) + " " + str(quality_info.get('runtime', '未知')))
            print(pad_text("添加时间", 12) + " " + str(quality_info.get('added_date', '未知')))
            
        else:
            echo_warning(f"未找到与 '{keyword}' 相关的视频")
            
    except Exception as e:
        echo_error(f"检查失败: {e}")
        return 1

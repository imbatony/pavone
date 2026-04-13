from typing import List, Optional
from unicodedata import east_asian_width

import click

from ...config.settings import get_config
from ...jellyfin.client import JellyfinClientWrapper
from ...manager.plugin_manager import get_plugin_manager
from ...models import BaseMetadata, ItemMetadata
from .enrich_helper import ImageManager, JellyfinMetadataUpdater, MetadataComparison
from .utils import (
    apply_proxy_config,
    common_proxy_option,
    confirm_action,
    echo_error,
    echo_info,
    echo_success,
    echo_warning,
    prompt_int,
)


def get_display_width(text: str) -> int:
    """计算字符串的显示宽度（考虑中文字符宽度）"""
    width = 0
    for char in text:
        # 检查字符的东亚宽度
        ea = east_asian_width(char)
        if ea in ("F", "W"):  # Fullwidth 或 Wide
            width += 2
        else:
            width += 1
    return width


def pad_text(text: str, target_width: int) -> str:
    """根据显示宽度填充文本"""
    current_width = get_display_width(text)
    if current_width >= target_width:
        return text
    # 需要填充的字符数
    padding = target_width - current_width
    return text + " " * padding


def format_metadata_output(metadata: BaseMetadata) -> None:
    """格式化输出元数据信息"""
    echo_success("元数据提取成功\n")

    # 手动格式化输出，确保对齐
    def format_field(name: str, value: str, max_width: int = 60, no_truncate: bool = False) -> str:
        """格式化字段，返回对齐的字符串"""
        # 字段名固定显示宽度为16（中文字符宽度）
        name_padded = pad_text(name, 16)
        # 值截断到指定宽度（链接等字段不截断）
        if not no_truncate and len(value) > max_width:
            value = value[:max_width] + "..."
        return f"{name_padded} {value}"

    # 输出表头
    click.echo(pad_text("字段", 16) + " 数值")
    click.echo("-" * 80)

    # 构建输出行
    lines: List[str] = []

    # 基础字段
    lines.append(format_field("标题", metadata.title))

    original_title = getattr(metadata, "original_title", None)
    if original_title:
        lines.append(format_field("原标题", original_title))

    lines.append(format_field("代码", metadata.code))
    lines.append(format_field("网站", metadata.site))
    lines.append(format_field("URL", metadata.url, no_truncate=True))

    # 如果是MovieMetadata，添加额外字段
    actors = getattr(metadata, "actors", None)
    if actors:
        actors_str = ", ".join(actors)
        lines.append(format_field("演员", actors_str))

    director = getattr(metadata, "director", None)
    if director:
        lines.append(format_field("导演", director))

    premiered = getattr(metadata, "premiered", None)
    if premiered:
        lines.append(format_field("发行日期", premiered))

    runtime = getattr(metadata, "runtime", None)
    if runtime:
        lines.append(format_field("时长", f"{runtime} 分钟"))

    studio = getattr(metadata, "studio", None)
    if studio:
        lines.append(format_field("制作公司", studio))

    serial = getattr(metadata, "serial", None)
    if serial:
        lines.append(format_field("系列", serial))

    genres = getattr(metadata, "genres", None)
    if genres:
        genres_str = ", ".join(genres)
        lines.append(format_field("类型", genres_str))

    tags = getattr(metadata, "tags", None)
    if tags:
        tags_str = ", ".join(tags)
        lines.append(format_field("标签", tags_str))

    rating = getattr(metadata, "rating", None)
    if rating is not None:
        lines.append(format_field("评分", f"{rating}/10"))

    official_rating = getattr(metadata, "official_rating", None)
    if official_rating:
        lines.append(format_field("分级", official_rating))

    plot = getattr(metadata, "plot", None)
    if plot:
        lines.append(format_field("描述", plot))

    cover = getattr(metadata, "cover", None)
    if cover:
        lines.append(format_field("封面", cover, no_truncate=True))

    # 输出所有行
    for line in lines:
        click.echo(line)
    click.echo()


@click.group()
def metadata():
    """元数据命令组"""
    pass


@metadata.command()
@click.argument("identifier")
@common_proxy_option
def show(identifier: str, proxy: str):
    """
    显示指定identifier的元数据信息

    identifier 可以是：
    - URL: https://missav.ai/ja/xxxxx-xxx
    - 视频代码: XXXXX-XXX

    示例:
        pavone metadata show https://missav.ai/ja/sdmt-415
        pavone metadata show SDMT-415
    """
    try:
        # 获取配置
        config = get_config()

        # 处理代理设置
        error_msg = apply_proxy_config(proxy, config)
        if error_msg:
            echo_error(error_msg)
            return 1

        # 获取插件管理器
        plugin_manager = get_plugin_manager()
        plugin_manager.load_plugins()

        # 查找合适的元数据提取器
        metadata_extractor = plugin_manager.get_metadata_extractor(identifier)

        if not metadata_extractor:
            echo_error(f"无法处理该identifier: {identifier}")
            echo_info("没有找到能处理该identifier的元数据插件")
            echo_info("支持的插件:")
            for plugin in plugin_manager.metadata_plugins:
                echo_info(f"  - {plugin.name}: {plugin.description}")
            return 1

        # 提取元数据
        echo_info(f"正在提取元数据: {identifier}")
        metadata_obj = metadata_extractor.extract_metadata(identifier)

        if metadata_obj is None:
            echo_error("元数据提取失败")
            return 1

        # 输出元数据
        format_metadata_output(metadata_obj)
        return 0

    except Exception as e:
        echo_error(f"出错: {e}")
        return 1


@metadata.command()
@click.argument("identifier")
@click.argument("video_id", required=False)
@click.option("--search", "-s", "search_keyword", help="在Jellyfin中搜索匹配的视频")
@click.option("--force", is_flag=True, help="强制覆盖所有字段（默认仅补充缺失信息）")
@common_proxy_option
def enrich(identifier: str, video_id: Optional[str], search_keyword: Optional[str], force: bool, proxy: str):  # noqa: C901
    """
    从指定identifier提取元数据并应用到Jellyfin中的视频

    支持三种使用方式：

    1. 直接指定视频ID:
        pavone metadata enrich <identifier> <video_id>

        示例: pavone metadata enrich https://missav.ai/ja/sdmt-415 12345

    2. 搜索匹配的Jellyfin视频后由用户选择:
        pavone metadata enrich <identifier> --search <keyword>

        示例: pavone metadata enrich https://missav.ai/ja/sdmt-415 --search sdmt-415

    3. 强制覆盖所有字段:
        pavone metadata enrich <identifier> <video_id> --force
    """
    try:
        # 获取配置
        config = get_config()
        jellyfin_config = config.jellyfin

        # 处理代理设置
        error_msg = apply_proxy_config(proxy, config)
        if error_msg:
            echo_error(error_msg)
            return 1

        # 检查Jellyfin配置
        if not jellyfin_config.enabled or not jellyfin_config.server_url:
            echo_error("Jellyfin未配置或未启用")
            echo_info("请先运行: pavone jellyfin config")
            return 1

        # 获取插件管理器
        plugin_manager = get_plugin_manager()
        plugin_manager.load_plugins()

        # 查找合适的元数据提取器
        metadata_extractor = plugin_manager.get_metadata_extractor(identifier)

        if not metadata_extractor:
            echo_error(f"无法处理该identifier: {identifier}")
            echo_info("没有找到能处理该identifier的元数据插件")
            return 1

        # 提取元数据
        echo_info(f"正在提取元数据: {identifier}")
        remote_metadata = metadata_extractor.extract_metadata(identifier)

        if remote_metadata is None:
            echo_error("元数据提取失败")
            return 1

        # 显示提取的元数据
        format_metadata_output(remote_metadata)

        # 创建Jellyfin客户端
        jf_client = JellyfinClientWrapper(jellyfin_config)

        # 尝试认证
        try:
            jf_client.authenticate()
        except Exception as e:
            echo_error(f"Jellyfin认证失败: {e}")
            return 1

        # 根据video_id或search_keyword查找视频
        target_video_id = video_id

        if not target_video_id and not search_keyword:
            # 未指定 video_id 和 search_keyword，默认使用番号搜索
            search_keyword = getattr(remote_metadata, "code", None)
            if not search_keyword:
                echo_error("未指定视频ID或搜索关键词，且无法从元数据获取番号")
                return 1

        if search_keyword:
            # 在Jellyfin中搜索视频
            echo_info(f"\n在Jellyfin中搜索: {search_keyword}")
            search_results = jf_client.search_items(search_keyword, limit=10)

            if not search_results:
                echo_warning("未找到匹配的视频")
                return 1

            # 如果只有一个结果，直接使用
            if len(search_results) == 1:
                echo_success("找到 1 个匹配结果，自动选择:")
                echo_info(f"  {search_results[0].name} (ID: {search_results[0].id})")
                target_video_id = search_results[0].id
            else:
                # 显示搜索结果
                echo_success(f"找到 {len(search_results)} 个匹配结果:")
                for idx, item in enumerate(search_results, 1):
                    echo_info(f"  {idx}. {item.name} (ID: {item.id})")

                # 让用户选择
                try:
                    choice = prompt_int("请选择视频编号", default=1)
                    if choice < 1 or choice > len(search_results):
                        echo_error("选择无效")
                        return 1
                    target_video_id = search_results[choice - 1].id
                except click.Abort:
                    echo_info("已取消")
                    return 1

        if not target_video_id:
            echo_error("未指定或未找到视频ID")
            return 1

        # 获取Jellyfin中的视频元数据
        echo_info("\n正在获取Jellyfin视频信息...")
        jellyfin_item = jf_client.get_item(target_video_id)
        local_metadata = ItemMetadata(jellyfin_item.metadata or {})

        # 对比元数据
        echo_info("对比元数据差异...")
        # 获取远程元数据的来源名称
        remote_source = getattr(remote_metadata, "site", "Remote")

        comparison = MetadataComparison.compare_metadata(
            local_metadata,
            remote_metadata,
            force,
            local_source="Jellyfin",
            remote_source=remote_source,
        )

        # 展示对比结果
        added_count, updated_count, merged_count = MetadataComparison.display_comparison(
            comparison, force, local_source="Jellyfin", remote_source=remote_source
        )

        # 总结变更
        total_changes = added_count + updated_count + merged_count
        if total_changes == 0:
            echo_info("没有需要更新的内容")
            return 0

        echo_success("\n发现以下变更:")
        echo_info(f"  + {added_count} 个新字段会被添加")
        echo_info(f"  ~ {updated_count} 个字段会被更新")
        echo_info(f"  ≈ {merged_count} 个字段会被合并")

        # 用户确认
        echo_info("")
        if not confirm_action("是否继续 enrich？", default=True):
            echo_info("已取消")
            return 1

        # 询问是否替换图片
        replace_images = False
        cover_url = getattr(remote_metadata, "cover", None)
        poster_url = getattr(remote_metadata, "poster", None)
        backdrop_url = getattr(remote_metadata, "backdrop", None)
        backdrop_urls: list[str] = getattr(remote_metadata, "backdrops", None) or []
        if not backdrop_urls and backdrop_url:
            backdrop_urls = [backdrop_url]

        if cover_url or poster_url or backdrop_urls:
            echo_info("\n发现远程图片资源:")
            if cover_url:
                echo_info(f"  📷 封面图 (Cover): {cover_url}")
            if poster_url:
                echo_info(f"  🎬 海报图 (Poster): {poster_url}")
            if backdrop_urls:
                echo_info(f"  🖼️  背景图 (Backdrop): {len(backdrop_urls)} 张")

            echo_info("")
            replace_images = confirm_action("是否下载并替换 Jellyfin 中的图片？", default=True)

        # 合并元数据
        merged_updates = MetadataComparison.merge_metadata(local_metadata, remote_metadata, comparison, force)

        # 下载图片和上传到Jellyfin
        if replace_images:
            echo_info("\n正在处理图片...")

            # 使用 Jellyfin 远程图片下载功能（让 Jellyfin 自己下载）
            # 这样可以避免直接上传的权限问题

            # 下载并上传封面图
            if cover_url:
                try:
                    echo_info(f"  设置封面图: {cover_url}")
                    jf_client.download_remote_image(target_video_id, cover_url, "Primary")
                    echo_success("  ✓ 封面图已更新")
                except Exception:
                    # 如果远程下载失败，尝试本地上传
                    echo_warning("  远程下载失败，尝试本地上传...")
                    try:
                        cover_path = ImageManager.download_image(cover_url, "cover")
                        if cover_path:
                            jf_client.upload_image(target_video_id, str(cover_path), "Primary")
                            echo_success("  ✓ 封面图已更新（本地上传）")
                    except Exception as e2:
                        echo_warning(f"  ✗ 封面图处理失败: {e2}")

            # 下载并上传海报图（作为 Thumb）
            if poster_url:
                try:
                    echo_info(f"  设置海报图: {poster_url}")
                    jf_client.download_remote_image(target_video_id, poster_url, "Thumb")
                    echo_success("  ✓ 海报图已更新")
                except Exception:
                    # 如果远程下载失败，尝试本地上传
                    echo_warning("  远程下载失败，尝试本地上传...")
                    try:
                        poster_path = ImageManager.download_image(poster_url, "poster")
                        if poster_path:
                            jf_client.upload_image(target_video_id, str(poster_path), "Thumb")
                            echo_success("  ✓ 海报图已更新（本地上传）")
                    except Exception as e2:
                        echo_warning(f"  ✗ 海报图处理失败: {e2}")

            # 下载并上传背景图（支持多张）
            for idx, bd_url in enumerate(backdrop_urls):
                try:
                    echo_info(f"  设置背景图 [{idx + 1}/{len(backdrop_urls)}]: {bd_url}")
                    jf_client.download_remote_image(target_video_id, bd_url, "Backdrop")
                    echo_success(f"  ✓ 背景图 {idx + 1} 已更新")
                except Exception:
                    echo_warning("  远程下载失败，尝试本地上传...")
                    try:
                        backdrop_path = ImageManager.download_image(bd_url, f"backdrop_{idx}")
                        if backdrop_path:
                            jf_client.upload_image(target_video_id, str(backdrop_path), "Backdrop")
                            echo_success(f"  ✓ 背景图 {idx + 1} 已更新（本地上传）")
                    except Exception as e2:
                        echo_warning(f"  ✗ 背景图 {idx + 1} 处理失败: {e2}")
        else:
            echo_info("\n跳过图片下载")

        # 调用Jellyfin API更新元数据
        echo_info("正在应用元数据到Jellyfin...")
        success = JellyfinMetadataUpdater.update_jellyfin_metadata(jf_client, target_video_id, merged_updates)

        if success:
            echo_success("\n✓ 元数据已成功应用到Jellyfin")
            echo_info(f"  视频ID: {target_video_id}")
            echo_info(f"  标题: {remote_metadata.title}")
            echo_info(f"  代码: {remote_metadata.code}")
        else:
            echo_warning("元数据应用过程中出现问题")

        # 清理临时文件
        ImageManager.cleanup_temp_dir()

        return 0 if success else 1

    except Exception as e:
        echo_error(f"出错: {e}")
        import traceback

        traceback.print_exc()
        return 1

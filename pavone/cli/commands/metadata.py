import json
from typing import Optional
from unicodedata import east_asian_width

import click
from tabulate import tabulate

from ...config.settings import get_config
from ...models import BaseMetadata, ItemMetadata
from ...plugins.metadata import MissavMetadata
from ...jellyfin.client import JellyfinClientWrapper
from .utils import echo_error, echo_info, echo_success, echo_warning
from .enrich_helper import MetadataComparison, ImageManager, JellyfinMetadataUpdater


def get_display_width(text: str) -> int:
    """计算字符串的显示宽度（考虑中文字符宽度）"""
    width = 0
    for char in text:
        # 检查字符的东亚宽度
        ea = east_asian_width(char)
        if ea in ('F', 'W'):  # Fullwidth 或 Wide
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
    return text + ' ' * padding


def format_metadata_output(metadata: BaseMetadata) -> None:
    """格式化输出元数据信息"""
    echo_success("元数据提取成功\n")
    
    # 手动格式化输出，确保对齐
    def format_field(name: str, value: str, max_width: int = 60) -> str:
        """格式化字段，返回对齐的字符串"""
        # 字段名固定显示宽度为16（中文字符宽度）
        name_padded = pad_text(name, 16)
        # 值截断到指定宽度
        if len(value) > max_width:
            value = value[:max_width] + "..."
        return f"{name_padded} {value}"
    
    # 输出表头
    print(pad_text("字段", 16) + " 数值")
    print("-" * 80)
    
    # 构建输出行
    lines = []
    
    # 基础字段
    lines.append(format_field("标题", metadata.title))
    lines.append(format_field("代码", metadata.code))
    lines.append(format_field("网站", metadata.site))
    lines.append(format_field("URL", metadata.url))
    
    # 如果是MovieMetadata，添加额外字段
    if hasattr(metadata, "actors") and metadata.actors:
        actors_str = ", ".join(metadata.actors)
        lines.append(format_field("演员", actors_str))
    
    if hasattr(metadata, "director") and metadata.director:
        lines.append(format_field("导演", metadata.director))
    
    if hasattr(metadata, "premiered") and metadata.premiered:
        lines.append(format_field("发行日期", metadata.premiered))
    
    if hasattr(metadata, "runtime") and metadata.runtime:
        lines.append(format_field("时长", f"{metadata.runtime} 分钟"))
    
    if hasattr(metadata, "studio") and metadata.studio:
        lines.append(format_field("制作公司", metadata.studio))
    
    if hasattr(metadata, "serial") and metadata.serial:
        lines.append(format_field("系列", metadata.serial))
    
    if hasattr(metadata, "genres") and metadata.genres:
        genres_str = ", ".join(metadata.genres)
        lines.append(format_field("类型", genres_str))
    
    if hasattr(metadata, "tags") and metadata.tags:
        tags_str = ", ".join(metadata.tags)
        lines.append(format_field("标签", tags_str))
    
    if hasattr(metadata, "rating") and metadata.rating is not None:
        lines.append(format_field("评分", f"{metadata.rating}/10"))
    
    if hasattr(metadata, "official_rating") and metadata.official_rating:
        lines.append(format_field("分级", metadata.official_rating))
    
    if hasattr(metadata, "plot") and metadata.plot:
        lines.append(format_field("描述", metadata.plot))
    
    if hasattr(metadata, "cover") and metadata.cover:
        lines.append(format_field("封面", metadata.cover))
    
    # 输出所有行
    for line in lines:
        print(line)
    print()


@click.group()
def metadata():
    """元数据命令组"""
    pass


@metadata.command()
@click.argument("identifier")
def show(identifier: str):
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
        # 创建metadata提取器
        metadata_extractor = MissavMetadata()
        
        # 检查是否能处理该identifier
        if not metadata_extractor.can_extract(identifier):
            echo_error(f"无法处理该identifier: {identifier}")
            echo_info("支持的格式:")
            echo_info("  - URL: https://missav.ai/ja/xxxxx-xxx")
            echo_info("  - 视频代码: XXXXX-XXX")
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
def enrich(identifier: str, video_id: Optional[str], search_keyword: Optional[str], force: bool):
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
        
        # 检查Jellyfin配置
        if not jellyfin_config.enabled or not jellyfin_config.server_url:
            echo_error("Jellyfin未配置或未启用")
            echo_info("请先运行: pavone jellyfin config")
            return 1
        
        # 创建metadata提取器
        metadata_extractor = MissavMetadata()
        
        # 检查是否能处理该identifier
        if not metadata_extractor.can_extract(identifier):
            echo_error(f"无法处理该identifier: {identifier}")
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
        
        if search_keyword:
            # 在Jellyfin中搜索视频
            echo_info(f"\n在Jellyfin中搜索: {search_keyword}")
            search_results = jf_client.search_items(search_keyword, limit=10)
            
            if not search_results:
                echo_warning("未找到匹配的视频")
                return 1
            
            # 如果只有一个结果，直接使用
            if len(search_results) == 1:
                echo_success(f"找到 1 个匹配结果，自动选择:")
                echo_info(f"  {search_results[0].name} (ID: {search_results[0].id})")
                target_video_id = search_results[0].id
            else:
                # 显示搜索结果
                echo_success(f"找到 {len(search_results)} 个匹配结果:")
                for idx, item in enumerate(search_results, 1):
                    echo_info(f"  {idx}. {item.name} (ID: {item.id})")
                
                # 让用户选择
                try:
                    choice = click.prompt("请选择视频编号", type=int, default=1)
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
        echo_info(f"\n正在获取Jellyfin视频信息...")
        jellyfin_item = jf_client.get_item(target_video_id)
        local_metadata = ItemMetadata(jellyfin_item.metadata or {})
        
        # 对比元数据
        echo_info("对比元数据差异...")
        # 获取远程元数据的来源名称
        remote_source = getattr(remote_metadata, 'site', 'Remote')
        
        comparison = MetadataComparison.compare_metadata(
            local_metadata, remote_metadata, force,
            local_source="Jellyfin",
            remote_source=remote_source
        )
        
        # 展示对比结果
        added_count, updated_count, merged_count = MetadataComparison.display_comparison(
            comparison, force,
            local_source="Jellyfin",
            remote_source=remote_source
        )
        
        # 总结变更
        total_changes = added_count + updated_count + merged_count
        if total_changes == 0:
            echo_info("没有需要更新的内容")
            return 0
        
        echo_success(f"\n发现以下变更:")
        echo_info(f"  + {added_count} 个新字段会被添加")
        echo_info(f"  ~ {updated_count} 个字段会被更新")
        echo_info(f"  ≈ {merged_count} 个字段会被合并")
        
        # 用户确认
        echo_info("")
        if not click.confirm("是否继续 enrich？", default=True):
            echo_info("已取消")
            return 0
        
        # 合并元数据
        merged_updates = MetadataComparison.merge_metadata(
            local_metadata, remote_metadata, comparison, force
        )
        
        # TODO: 下载图片和上传到Jellyfin
        echo_info("\n正在下载远程图片...")
        # 图片处理逻辑在这里
        
        # 调用Jellyfin API更新元数据
        echo_info("正在应用元数据到Jellyfin...")
        success = JellyfinMetadataUpdater.update_jellyfin_metadata(
            jf_client, target_video_id, merged_updates
        )
        
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

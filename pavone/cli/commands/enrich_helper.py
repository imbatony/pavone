"""Enrich 功能辅助模块

提供元数据对比、合并、图片处理等功能
"""

import tempfile
import unicodedata
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import click
import requests

from ...jellyfin.client import JellyfinClientWrapper

from ...models import BaseMetadata, ItemMetadata
from .utils import echo_error, echo_info, echo_success, echo_warning


def get_display_width(text: str) -> int:
    """计算文本的显示宽度，考虑中文、日文等全角字符

    Args:
        text: 输入文本

    Returns:
        显示宽度（以字符单位）
    """
    width = 0
    for char in text:
        # East Asian Width 属性
        # 'W' (Wide) 和 'F' (Fullwidth) 占2个单位
        # 其他占1个单位
        east_asian_width = unicodedata.east_asian_width(char)
        if east_asian_width in ("W", "F"):  # Wide or Fullwidth
            width += 2
        else:
            width += 1
    return width


def pad_text_cjk(text: str, width: int) -> str:
    """使用 CJK 感知的填充（考虑中文、日文等全角字符）

    Args:
        text: 输入文本
        width: 目标显示宽度

    Returns:
        填充后的文本
    """
    display_width = get_display_width(text)
    padding_needed = max(0, width - display_width)
    return text + " " * padding_needed


def colorize_tag(tag: str, tag_type: str) -> str:
    """为标签添加颜色

    Args:
        tag: 标签文本（如 "[新增]"）
        tag_type: 标签类型（'added', 'updated', 'merged', 'modified'）

    Returns:
        带颜色的标签文本
    """
    if tag_type == "added":
        # 新增 - 绿色
        return click.style(tag, fg="green", bold=True)
    elif tag_type == "updated":
        # 替换/更新 - 黄色
        return click.style(tag, fg="yellow", bold=True)
    elif tag_type == "merged":
        # 合并 - 青色
        return click.style(tag, fg="cyan", bold=True)
    elif tag_type == "modified":
        # 保留 - 白色
        return click.style(tag, fg="white", bold=True)
    else:
        return tag


class FieldChange(Enum):
    """字段变更类型"""

    SAME = "same"  # 相同
    ADDED = "added"  # 新增
    UPDATED = "updated"  # 更新/合并
    REMOVED = "removed"  # 移除
    MODIFIED = "modified"  # 修改


class MetadataComparison:
    """元数据对比和合并"""

    # 将BaseMetadata和ItemMetadata转换为可比较的字典
    # 支持 Jellyfin 可存储的所有元数据字段
    # 注意: code 和 serial 字段对 Jellyfin 不适用，已排除
    METADATA_FIELDS = [
        # 基础信息
        "title",
        "original_title",
        "sort_name",
        "year",
        "premiere_date",
        "runtime",
        # 描述信息
        "plot",
        # 评分分级
        "rating",
        "official_rating",
        # 人员信息
        "director",
        "actors",
        # 分类信息
        "studio",
        "genres",
        "tags",
        "taglines",
    ]

    # 字段显示标签（用于 UI 展示）
    FIELD_DISPLAY_LABELS = {
        "title": "标题",
        "original_title": "原标题",
        "sort_name": "排序标题",
        "year": "年份",
        "premiere_date": "发行日期",
        "runtime": "时长",
        "plot": "描述",
        "rating": "评分",
        "official_rating": "家长分级",
        "director": "导演",
        "actors": "演员",
        "studio": "制作公司",
        "genres": "类型",
        "tags": "标签",
        "taglines": "标语",
    }

    @staticmethod
    def _extract_field_value(metadata: Any, field_name: str) -> Optional[Any]:
        """从元数据对象提取字段值"""
        if isinstance(metadata, ItemMetadata):
            # 对于ItemMetadata，使用属性
            mapping = {
                "title": "name",  # Jellyfin使用name表示标题
                "original_title": "original_title",  # Jellyfin使用OriginalTitle表示原始标题
                "sort_name": "sort_name",
                "premiere_date": "premiere_date",
                "runtime": "runtime_minutes",
                "director": "directors",  # 返回列表
                "studio": "studio_names",  # 返回列表
                "actors": "actors",
                "genres": "genres",
                "tags": "tags",
                "taglines": "taglines",
                "rating": "rating",
                "official_rating": "official_rating",
                "plot": "overview",
                "year": "year",
                # 注意: code 和 serial 字段对 Jellyfin 不适用，已排除
            }
            actual_field = mapping.get(field_name, field_name)
            return getattr(metadata, actual_field, None)
        else:
            # 对于BaseMetadata，直接获取属性
            return getattr(metadata, field_name, None)

    @staticmethod
    def compare_metadata(
        local_metadata: ItemMetadata,
        remote_metadata: BaseMetadata,
        force: bool = False,
        local_source: str = "Jellyfin",
        remote_source: Optional[str] = None,
    ) -> Dict[str, Dict[str, Any]]:
        """对比本地和远程元数据

        Args:
            local_metadata: 本地元数据（ItemMetadata，Jellyfin）
            remote_metadata: 远程元数据（BaseMetadata）
            force: 是否强制覆盖模式
            local_source: 本地来源名称，默认为"Jellyfin"
            remote_source: 远程来源名称，默认从remote_metadata.site获取

        Returns:
            {
                'field_name': {
                    'change': FieldChange,
                    'local': value,
                    'remote': value,
                    'action': 'skip'/'update'/'merge'
                }
            }
        """
        comparison = {}

        for field_name in MetadataComparison.METADATA_FIELDS:
            # 直接从元数据对象提取字段值
            local_val = MetadataComparison._extract_field_value(local_metadata, field_name)
            remote_val = MetadataComparison._extract_field_value(remote_metadata, field_name)

            # 规范化值用于比较
            local_normalized = MetadataComparison._normalize_value(local_val)
            remote_normalized = MetadataComparison._normalize_value(remote_val)

            # 判断变更类型和动作
            if local_normalized == remote_normalized:
                change = FieldChange.SAME
                action = "skip"
            elif not local_normalized and remote_normalized:
                # 本地无值，远程有值
                change = FieldChange.ADDED
                action = "update"
            elif local_normalized and remote_normalized and local_normalized != remote_normalized:
                # 都有值但不同
                if field_name in ["actors", "genres", "tags", "director", "studio"]:
                    # 列表字段默认合并
                    change = FieldChange.UPDATED
                    action = "merge" if not force else "update"
                else:
                    change = FieldChange.MODIFIED
                    action = "update" if force else "skip"
            elif local_normalized and not remote_normalized:
                change = FieldChange.REMOVED
                action = "skip"
            else:
                change = FieldChange.SAME
                action = "skip"

            comparison[field_name] = {
                "change": change,
                "local": local_val,
                "remote": remote_val,
                "action": action,
            }

        return comparison

    @staticmethod
    def _normalize_value(value: Any) -> Any:
        """规范化值用于比较"""
        if value is None or value == "":
            return None
        if isinstance(value, list):
            # 移除空项，转换为集合用于比较
            return frozenset(v for v in value if v)
        if isinstance(value, str):
            return value.strip() if value else None
        return value

    @staticmethod
    def display_comparison(
        comparison: Dict[str, Dict[str, Any]],
        force: bool = False,
        local_source: str = "Jellyfin",
        remote_source: Optional[str] = "Remote",
    ) -> Tuple[int, int, int]:
        """展示元数据对比结果

        Args:
            comparison: 对比结果
            force: 是否为强制模式
            local_source: 本地来源名称
            remote_source: 远程来源名称

        Returns:
            (added_count, updated_count, merged_count) 变更统计
        """
        added_count = 0
        updated_count = 0
        merged_count = 0

        print("\n【元数据对比】\n")
        local_header = f"{local_source} (本地)"
        remote_header = f"{remote_source} (远程)"
        # 使用 CJK 感知的填充
        local_header_padded = pad_text_cjk(local_header, 30)
        remote_header_padded = pad_text_cjk(remote_header, 30)
        print(f"{'字段':<16} │ {local_header_padded} │ {remote_header_padded}")
        print("-" * 80)

        for field_name, field_info in comparison.items():
            change = field_info["change"]
            local_val = field_info["local"]
            remote_val = field_info["remote"]
            action = field_info["action"]
            # 获取显示标签
            display_field = MetadataComparison.FIELD_DISPLAY_LABELS.get(field_name, field_name)

            if change == FieldChange.SAME:
                # 相同的字段用灰色显示（这里用[相同]标记）
                local_str = MetadataComparison._format_value(local_val)
                remote_str = MetadataComparison._format_value(remote_val)
                if local_str:
                    local_padded = pad_text_cjk(local_str, 30)
                    remote_padded = pad_text_cjk(remote_str, 30)
                    print(f"{display_field:<16} │ {local_padded} │ {remote_padded}")

            elif change == FieldChange.ADDED:
                # 新增字段（绿色，用[新增]标记）
                remote_str = MetadataComparison._format_value(remote_val)
                remote_padded = pad_text_cjk(remote_str, 30)
                none_padded = pad_text_cjk("(无)", 30)
                print(f"{display_field:<16} │ {none_padded} │ {remote_padded} {colorize_tag('[新增]', 'added')}")
                added_count += 1

            elif change == FieldChange.MODIFIED:
                # 修改字段（蓝色，用[修改]标记）
                local_str = MetadataComparison._format_value(local_val)
                remote_str = MetadataComparison._format_value(remote_val)
                local_padded = pad_text_cjk(local_str, 30)
                remote_padded = pad_text_cjk(remote_str, 30)
                if force:
                    print(f"{display_field:<16} │ {local_padded} │ {remote_padded} {colorize_tag('[覆盖]', 'modified')}")
                    updated_count += 1
                else:
                    print(f"{display_field:<16} │ {local_padded} │ {remote_padded} {colorize_tag('[保留]', 'modified')}")

            elif change == FieldChange.UPDATED:
                # 更新/合并字段（蓝色，用[更新]标记）
                local_str = MetadataComparison._format_value(local_val)
                remote_str = MetadataComparison._format_value(remote_val)
                local_padded = pad_text_cjk(local_str, 30)
                remote_padded = pad_text_cjk(remote_str, 30)
                if action == "merge":
                    print(f"{display_field:<16} │ {local_padded} │ {remote_padded} {colorize_tag('[合并]', 'merged')}")
                    merged_count += 1
                else:
                    print(f"{display_field:<16} │ {local_padded} │ {remote_padded} {colorize_tag('[替换]', 'updated')}")
                    updated_count += 1

        print()
        return added_count, updated_count, merged_count

    @staticmethod
    def _format_value(value: Any, max_len: int = 28) -> str:
        """格式化值用于显示"""
        if value is None or value == "":
            return "(无)"
        if isinstance(value, list):
            formatted = ", ".join(str(v) for v in value[:3])
            if len(value) > 3:
                formatted += f" 等{len(value)}项"
            return formatted[:max_len]
        if isinstance(value, (int, float)):
            return str(value)
        formatted = str(value)
        if len(formatted) > max_len:
            return formatted[:max_len] + "..."
        return formatted

    @staticmethod
    def merge_metadata(
        local_metadata: ItemMetadata,
        remote_metadata: BaseMetadata,
        comparison: Dict[str, Dict[str, Any]],
        force: bool = False,
    ) -> Dict[str, Any]:
        """根据对比结果合并元数据

        Args:
            local_metadata: 本地元数据（ItemMetadata，Jellyfin）
            remote_metadata: 远程元数据（BaseMetadata）
            comparison: 对比结果
            force: 是否强制覆盖模式

        Returns:
            可用于Jellyfin API更新的字典
        """
        updates = {}

        for field_name, field_info in comparison.items():
            action = field_info["action"]

            if action == "skip":
                continue

            remote_val = field_info["remote"]
            local_val = field_info["local"]

            if action == "update":
                # 直接使用远程值
                updates[field_name] = remote_val

            elif action == "merge":
                # 合并列表字段
                merged = MetadataComparison._merge_list_field(local_val, remote_val)
                updates[field_name] = merged

        return updates

    @staticmethod
    def _merge_list_field(local_val: Any, remote_val: Any) -> List[str]:
        """合并列表字段（去重排序）"""
        local_list = local_val if isinstance(local_val, list) else ([local_val] if local_val else [])
        remote_list = remote_val if isinstance(remote_val, list) else ([remote_val] if remote_val else [])

        # 合并并去重，保持顺序
        # 使用 dict.fromkeys() 来保持顺序的同时去重
        merged = list(dict.fromkeys(local_list + remote_list))
        # 排序
        try:
            merged.sort()
        except TypeError:
            # 如果排序失败（混合类型），保持原样
            pass

        return merged


class ImageManager:
    """图片管理和处理"""

    TEMP_DIR = Path(tempfile.gettempdir()) / "pavone_images"

    IMAGE_TYPES = {
        "cover": "Primary",
        "thumb": "Thumb",
        "backdrop": "Backdrop",
    }

    @classmethod
    def ensure_temp_dir(cls) -> Path:
        """确保临时目录存在"""
        cls.TEMP_DIR.mkdir(parents=True, exist_ok=True)
        return cls.TEMP_DIR

    @classmethod
    def download_image(cls, image_url: str, image_type: str = "cover", timeout: int = 10) -> Optional[Path]:
        """下载图片到临时目录

        Args:
            image_url: 图片URL
            image_type: 图片类型（cover/thumb/backdrop）
            timeout: 下载超时时间（秒）

        Returns:
            本地图片路径，下载失败返回None
        """
        try:
            temp_dir = cls.ensure_temp_dir()

            # 发送请求下载图片
            response = requests.get(image_url, timeout=timeout, stream=True)
            response.raise_for_status()

            # 从URL推断文件扩展名
            content_type = response.headers.get("content-type", "image/jpeg")
            ext = cls._get_file_ext(content_type, image_url)

            # 生成文件名
            import hashlib

            url_hash = hashlib.md5(image_url.encode()).hexdigest()[:8]
            filename = f"{image_type}_{url_hash}{ext}"
            filepath = temp_dir / filename

            # 写入文件
            with open(filepath, "wb") as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)

            echo_info(f"  ✓ 下载图片: {image_type}")
            return filepath

        except requests.RequestException as e:
            echo_warning(f"  ✗ 图片下载失败 ({image_type}): {e}")
            return None
        except Exception as e:
            echo_error(f"  ✗ 图片处理错误: {e}")
            return None

    @staticmethod
    def _get_file_ext(content_type: str, url: str) -> str:
        """从content-type和URL推断文件扩展名"""
        if "jpeg" in content_type or "jpg" in content_type:
            return ".jpg"
        elif "png" in content_type:
            return ".png"
        elif "gif" in content_type:
            return ".gif"
        elif "webp" in content_type:
            return ".webp"
        else:
            # 尝试从URL获取
            url_path = url.split("?")[0]
            if url_path.endswith(".jpg"):
                return ".jpg"
            elif url_path.endswith(".png"):
                return ".png"
            elif url_path.endswith(".gif"):
                return ".gif"
            elif url_path.endswith(".webp"):
                return ".webp"
            else:
                return ".jpg"  # 默认

    @classmethod
    def cleanup_temp_dir(cls) -> None:
        """清理临时目录"""
        try:
            import shutil

            if cls.TEMP_DIR.exists():
                shutil.rmtree(cls.TEMP_DIR)
                echo_info("✓ 临时文件已清理")
        except Exception as e:
            echo_warning(f"清理临时文件失败: {e}")


class JellyfinMetadataUpdater:
    """Jellyfin元数据更新器"""

    @staticmethod
    def convert_metadata_for_jellyfin(updates: Dict[str, Any]) -> Dict[str, Any]:
        """将合并后的元数据转换为Jellyfin API格式

        Args:
            updates: 合并后的元数据更新字典

        Returns:
            Jellyfin API可接受的格式
        """
        jellyfin_updates = {}

        # 字段映射：内部字段名 -> Jellyfin API字段名
        field_mapping = {
            "title": "Name",
            "original_title": "OriginalTitle",
            "code": "ExternalId",
            "premiere_date": "PremiereDate",
            "runtime": "RunTimeTicks",  # 需要转换为ticks
            "director": "People",  # 需要特殊处理，添加到People数组
            "studio": "Studios",  # 需要特殊处理，转换为对象数组
            "actors": "People",  # 需要特殊处理，添加到People数组
            "genres": "Genres",
            "tags": "Tags",
            "rating": "CommunityRating",
            "official_rating": "OfficialRating",
            "plot": "Overview",
            "serial": "SeriesName",
            "year": "ProductionYear",  # Jellyfin使用ProductionYear而不是Year
        }

        # 收集需要合并到 People 数组的人员信息
        people_list: list[Dict[str, Any]] = []

        for internal_field, jellyfin_field in field_mapping.items():
            if internal_field not in updates:
                continue

            value = updates[internal_field]

            if value is None or value == "":
                continue

            # 特殊处理某些字段
            if internal_field == "runtime" and isinstance(value, int):
                # 转换分钟为ticks (1分钟 = 600000000 ticks)
                jellyfin_updates["RunTimeTicks"] = value * 600000000

            elif internal_field == "director":
                # 导演添加到 People 数组，Type="Director"
                if isinstance(value, list):
                    for director in value:
                        if director:
                            people_list.append({"Name": director, "Type": "Director", "Role": ""})
                elif isinstance(value, str) and value:
                    people_list.append({"Name": value, "Type": "Director", "Role": ""})

            elif internal_field == "actors":
                # 演员添加到 People 数组，Type="Actor"
                if isinstance(value, list):
                    for actor in value:
                        if actor:
                            people_list.append({"Name": actor, "Type": "Actor", "Role": ""})

            elif internal_field == "studio":
                # 制作公司：Jellyfin使用Studios数组，每个元素是 {'Name': 'studio_name'} 格式
                if isinstance(value, list):
                    # 如果已经是列表，转换为Jellyfin格式
                    jellyfin_updates["Studios"] = [{"Name": s} for s in value]
                elif isinstance(value, str) and value:
                    # 如果是字符串，转换为单元素数组
                    jellyfin_updates["Studios"] = [{"Name": value}]

            else:
                # 直接映射
                jellyfin_updates[jellyfin_field] = value

        # 如果有人员信息，添加到更新字典
        if people_list:
            jellyfin_updates["People"] = people_list

        return jellyfin_updates

    @staticmethod
    def update_jellyfin_metadata(client: "JellyfinClientWrapper", item_id: str, updates: Dict[str, Any]) -> bool:
        """更新Jellyfin中的项元数据

        Args:
            client: JellyfinClientWrapper实例
            item_id: 项ID
            updates: 更新字典

        Returns:
            成功返回True
        """
        try:
            if not updates:
                echo_warning("没有需要更新的字段")
                return False

            # 转换为Jellyfin格式
            jellyfin_updates = JellyfinMetadataUpdater.convert_metadata_for_jellyfin(updates)

            if not jellyfin_updates:
                echo_warning("转换后没有有效的更新字段")
                return False

            # 调用API更新
            client.update_item_metadata(item_id, jellyfin_updates)
            echo_success("✓ 元数据已更新")

            return True

        except Exception as e:
            echo_error(f"更新元数据失败: {e}")
            return False

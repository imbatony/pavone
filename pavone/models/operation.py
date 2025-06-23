"""
操作项
"""

from typing import Optional, Dict, Any
from ..utils import StringUtils
from .constants import (
    OperationType,
    ItemType,
    CommonExtraKeys,
    ItemSubType,
    Quality,
    VideoCoreExtraKeys,
    ImageExtraKeys,
    MetadataExtraKeys,
)
from .metadata import BaseMetadata
from .progress_info import ProgressCallback
from datetime import datetime


class OpertionItem:
    """
    操作项
    """

    def __init__(self, opt_type: str, item_type: str, desc: str, **extra):
        self.opt_type = opt_type  # 操作类型, 如下载、移动等
        self.item_type = item_type
        self._extra: Dict[str, Any] = extra
        self._url: Optional[str] = None  # 下载链接
        self.desc = desc
        self._children: list["OpertionItem"] = []

    def support_custom_filename_prefix(self) -> bool:
        """
        判断是否支持自定义文件名
        """
        return True

    def set_subtype(self, subtype: str):
        """
        设置链接子类型
        Args:
            subtype: 子类型, 如 COVER, POSTER, THUMBNAIL, BACKDROP 等
        """
        if not subtype:
            raise ValueError("子类型不能为空")
        self._extra[CommonExtraKeys.ITEM_SUBTYPE] = subtype

    def get_subtype(self) -> str:
        """
        获取链接子类型
        Returns:
            str: 子类型, 如 COVER, POSTER, THUMBNAIL, BACKDROP 等
        """
        return self._extra.get(CommonExtraKeys.ITEM_SUBTYPE, ItemSubType.UNKNOWN)

    def support_children(self) -> bool:
        """判断是否支持子项"""
        return self.item_type in (ItemType.VIDEO, ItemType.STREAM, ItemType.MOVE)

    def get_quality_info(self) -> str:
        """获取质量信息"""
        return self._extra.get(VideoCoreExtraKeys.QUALITY, Quality.UNKNOWN)

    def get_description(self) -> str:
        """获取操作项的描述"""
        return self.desc

    def append_child(self, child: "OpertionItem"):
        """
        将子项添加到复合类型的children中
        """
        if not self.support_children():
            raise ValueError("当前操作项不支持子项")
        self._children.append(child)

    def get_children(self) -> list["OpertionItem"]:
        """
        获取复合类型的所有子项
        """
        if not self.support_children():
            raise ValueError("当前操作项不支持子项")
        return self._children

    def has_children(self) -> bool:
        """判断是否有子项"""
        return bool(self._children)

    def set_url(self, url: str):
        """设置链接"""
        if not url:
            raise ValueError("链接不能为空")
        self._url = url

    def get_url(self) -> Optional[str]:
        """获取链接"""
        if not hasattr(self, "_url"):
            return None
        return self._url

    def get_part(self) -> Optional[int]:
        """获取分集信息"""
        part_str = self._extra.get(VideoCoreExtraKeys.PART, None)
        if part_str is not None:
            try:
                return int(part_str)
            except ValueError:
                return None

    def get_effective_headers(self, default_headers: Optional[Dict[str, str]] = None) -> Dict[str, str]:
        """获取自定义HTTP头部"""
        custom_headers = self._extra.get(CommonExtraKeys.CUSTOM_HEADERS, {})
        default_headers = default_headers.copy() if default_headers else {}
        if not custom_headers:
            return default_headers or {}
        # 合并默认头部和自定义头部
        effective_headers = default_headers
        effective_headers.update(custom_headers)
        return effective_headers

    def set_custom_filename_prefix(self, filename: Optional[str]):
        if not filename:
            return
        if not self.support_custom_filename_prefix():
            raise ValueError("当前操作项不支持自定义文件名")
        """设置自定义文件名"""
        self._extra[CommonExtraKeys.CUSTOM_FILENAME_PREFIX] = filename

    def get_custom_filename_prefix(self) -> Optional[str]:
        """获取自定义文件名"""
        return self._extra.get(CommonExtraKeys.CUSTOM_FILENAME_PREFIX, None)

    def get_target_path(self) -> Optional[str]:
        """获取目标路径"""
        return self._extra.get(CommonExtraKeys.TARGET_PATH, None)

    def set_target_path(self, target_path: str):
        """设置目标路径"""
        if not target_path:
            return
        self._extra[CommonExtraKeys.TARGET_PATH] = target_path

    def set_progress_callback(self, callback: Optional[ProgressCallback]):
        """设置进度回调函数"""
        if callback is not None and not callable(callback):
            raise ValueError("进度回调必须是可调用的函数")
        self._extra[CommonExtraKeys.PROGRESS_CALLBACK] = callback

    def get_progress_callback(self) -> Optional[ProgressCallback]:
        """获取进度回调函数"""
        return self._extra.get(CommonExtraKeys.PROGRESS_CALLBACK, None)

    def get_code(self) -> Optional[str]:
        """获取识别代码"""
        return self._extra.get(VideoCoreExtraKeys.CODE, None)

    def set_code(self, code: str):
        """设置识别代码"""
        if not code:
            raise ValueError("代码不能为空")
        self._extra[VideoCoreExtraKeys.CODE] = code

    def get_studio(self) -> Optional[str]:
        """获取制作公司"""
        return self._extra.get(VideoCoreExtraKeys.STUDIO, None)

    def set_studio(self, studio: Optional[str]):
        """设置制作公司"""
        if not studio:
            studio = "未知"
        self._extra[VideoCoreExtraKeys.STUDIO] = studio

    def get_year(self) -> int:
        """获取年份"""
        return self._extra.get(VideoCoreExtraKeys.YEAR, datetime.now().year)

    def set_year(self, year: Optional[int]):
        """设置年份"""
        if not year:
            # 如果年份为空，则默认为今年
            year = datetime.now().year
        self._extra[VideoCoreExtraKeys.YEAR] = year

    def get_actors(self) -> list[str]:
        """获取演员列表"""
        actors = self._extra.get(VideoCoreExtraKeys.ACTORS, ["未知"])
        if isinstance(actors, str):
            # 如果是字符串，则转换为列表
            return [actor.strip() for actor in actors.split(",")]
        return actors

    def set_actors(self, actors: list[str]):
        """设置演员列表"""
        if not actors:
            self._extra[VideoCoreExtraKeys.ACTORS] = ["未知"]
        self._extra[VideoCoreExtraKeys.ACTORS] = [actor.strip() for actor in actors if actor.strip()]

    def get_title(self) -> Optional[str]:
        """获取标题"""
        return self._extra.get(VideoCoreExtraKeys.TITLE, None)

    def set_title(self, title: str):
        """设置标题"""
        if not title:
            raise ValueError("标题不能为空")
        self._extra[VideoCoreExtraKeys.TITLE] = title

    def set_part(self, part: Optional[int]):
        """设置分集信息"""
        if part is None or part < 1:
            raise ValueError("分集信息必须是大于0的整数")
        self._extra[VideoCoreExtraKeys.PART] = part

    def get_target_subfolder(self, output_dir: str, folder_name_pattern: str) -> Optional[str]:
        """获取目标子文件夹"""
        code: Optional[str] = StringUtils.normalize_string(self.get_code())
        studio: Optional[str] = StringUtils.normalize_string(self.get_studio())
        actors: Optional[list[str]] = (
            [StringUtils.normalize_string(actor) for actor in self.get_actors()] if self.get_actors() else []
        )
        title: Optional[str] = StringUtils.normalize_string(self.get_title())
        year: int = self.get_year()

        # 使用配置的文件夹结构模式生成目标路径
        target_sub_folder = folder_name_pattern.format(
            code=code, studio=studio, actors=" ".join(actors) if actors else "", title=title or "", year=year
        )

        target_folder = StringUtils.normalize_folder_path(output_dir + "/" + target_sub_folder)
        if not target_folder:
            raise ValueError("目标子文件夹路径不能为空")
        return target_folder

    def get_filename_prefix(self, file_name_pattern: Optional[str] = None) -> Optional[str]:
        """
        获取文件名前缀
        如果设置了自定义文件名，则直接返回自定义文件名
        如果没有设置自定义文件名，则根据配置的文件名模式生成目标文件名前缀
        Args:
            file_name_pattern: 文件名模式, 如果为 None 则使用默认模式
        Returns:
            str: 目标文件名前缀
        """
        custom_name = self.get_custom_filename_prefix()
        if custom_name:
            """如果设置了自定义文件名，则直接返回"""
            return StringUtils.normalize_string(custom_name)

        if not file_name_pattern:
            return self.get_title()

        """获取目标文件名"""
        code: Optional[str] = StringUtils.normalize_string(self.get_code())
        studio: Optional[str] = StringUtils.normalize_string(self.get_studio())
        actors: Optional[list[str]] = (
            [StringUtils.normalize_string(actor) for actor in self.get_actors()] if self.get_actors() else []
        )
        title: Optional[str] = StringUtils.normalize_string(self.get_title())
        year: int = self.get_year()

        # 使用配置的文件名模式生成目标文件名
        target_filename = file_name_pattern.format(
            code=code, studio=studio, actors=" ".join(actors) if actors else "", title=title or "", year=year
        )

        if not target_filename:
            raise ValueError("目标文件名不能为空")
        return target_filename

    def get_image_extension(self) -> str:
        """获取图片扩展名"""
        default_image_extensions = [".jpg", ".jpeg", ".png", ".gif", ".webp"]
        extension = default_image_extensions[0]  # 默认使用 .jpg 扩展名
        # 从链接猜测图片格式
        image_url = self.get_url()
        if image_url:
            for ext in default_image_extensions:
                if image_url.lower().endswith(ext):
                    extension = ext
                    break

        extension = self._extra.get(ImageExtraKeys.IMAGE_FORMAT, extension).lower()
        return f".{extension}"

    def get_subtitle_extension(self) -> str:
        """获取字幕扩展名"""
        # 默认使用 .srt 扩展名
        return ".srt"

    def get_file_name_extension(self) -> Optional[str]:
        """获取文件扩展名"""
        if self.item_type == ItemType.VIDEO or self.item_type == ItemType.STREAM:
            # 视频或流媒体类型默认使用 .mp4 扩展名
            return ".mp4"
        elif self.item_type == ItemType.IMAGE:
            # 图片类型根据图片格式获取扩展名
            return self.get_image_extension()
        elif self.item_type == ItemType.MOVE:
            # 移动操作不需要扩展名
            return None
        elif self.item_type == ItemType.SUBTITLE:
            # 字幕类型默认使用 .srt 扩展名
            return self.get_subtitle_extension()
        elif self.item_type == ItemType.TORRENT:
            # 种子文件不需要扩展名
            return None
        elif self.item_type == ItemType.META_DATA:
            # 元数据文件以 .nfo 结尾
            return ".nfo"
        else:
            return None  # 未知类型不返回扩展名

    def get_file_suffix(self) -> Optional[str]:
        """
        获取文件后缀名, 根据操作项类型返回不同的后缀名
        - 视频、流媒体、字幕或元数据类型返回扩展名
        - 图片类型根据子类型返回不同的后缀名
        - 对于其他类型不返回后缀名
        """
        extension = self.get_file_name_extension()
        if (
            self.item_type == ItemType.VIDEO
            or self.item_type == ItemType.STREAM
            or self.item_type == ItemType.SUBTITLE
            or self.item_type == ItemType.META_DATA
        ):
            # 视频、流媒体、字幕或元数据类型返回扩展名
            return extension
        elif self.item_type == ItemType.IMAGE:
            # 需要更细化图片类型的后缀名
            sub_type = self.get_subtype()
            if sub_type == ItemSubType.COVER:
                return f"-cover{extension}"
            elif sub_type == ItemSubType.POSTER:
                return f"-poster{extension}"
            elif sub_type == ItemSubType.THUMBNAIL:
                return f"-thumbnail{extension}"
            elif sub_type == ItemSubType.BACKDROP:
                return f"-backdrop{extension}"
            else:
                return extension
        return None  # 对于其他类型不返回后缀名

    def get_metadata(self) -> Optional[BaseMetadata]:
        """
        获取元数据对象
        如果操作项包含元数据，则返回 BaseMetadata 对象
        否则返回 None
        """
        metadata = self._extra.get(MetadataExtraKeys.METADATA_OBJ, None)
        if metadata and isinstance(metadata, BaseMetadata):
            return metadata
        # 如果没有元数据对象，则返回 None
        return None


def create_video_item(
    url: str,
    quality: str,
    title: str,
    site: str,
    sub_type: Optional[str] = None,
    custom_headers: Optional[Dict[str, str]] = None,
    code: Optional[str] = None,
    actors: Optional[list[str]] = None,
    studio: Optional[str] = None,
    year: Optional[int] = None,
    part: Optional[int] = None,
) -> OpertionItem:
    """
    创建一个下载操作项
    Args:
        url: 下载链接
        item_type: 下载类型
        desc: 描述信息
    Returns:
        OpertionItem: 创建的下载操作项
    """
    if not url:
        raise ValueError("下载链接不能为空")
    if not title:
        raise ValueError("标题不能为空")
    if not site:
        raise ValueError("站点不能为空")

    item_type = ItemType.VIDEO  # 设置为视频类型

    sub_type = sub_type or ItemSubType.UNKNOWN  # 设置子类型，默认为未知

    # 设置默认质量为未知
    if not quality:
        quality = Quality.UNKNOWN

    # 设置描述信息
    desc = f"{title} ({quality})"
    item = OpertionItem(opt_type=OperationType.DOWNLOAD, item_type=item_type, desc=desc)
    item.set_url(url)
    item._extra[VideoCoreExtraKeys.QUALITY] = quality
    if custom_headers:
        item._extra[CommonExtraKeys.CUSTOM_HEADERS] = custom_headers
    # 视频的主要信息
    item.set_title(title)
    item._extra[VideoCoreExtraKeys.SITE] = site
    if not code:
        code = StringUtils.sha_256_hash(title)
        item.set_code(code)
    if actors:
        item.set_actors(actors)
    if studio:
        item.set_studio(studio)
    if year:
        item.set_year(year)
    if part is not None:
        item.set_part(part)

    item.set_subtype(sub_type)
    # 视频的主要信息
    return item


def create_stream_item(
    url: str,
    title: str,
    quality: str,
    site: str,
    code: Optional[str] = None,
    sub_type: Optional[str] = None,
    custom_headers: Optional[Dict[str, str]] = None,
    actors: Optional[list[str]] = None,
    studio: Optional[str] = None,
    year: Optional[int] = None,
    part: Optional[int] = None,
) -> OpertionItem:
    """
    创建一个流媒体下载操作项
    Args:
        url: 下载链接
        title: 标题
        custom_headers: 自定义HTTP头部
    Returns:
        OpertionItem: 创建的下载操作项
    """
    if not url:
        raise ValueError("下载链接不能为空")

    if not title:
        raise ValueError("标题不能为空")

    if not code:
        raise ValueError("代码不能为空")

    if not site:
        raise ValueError("站点不能为空")

    item_type = ItemType.STREAM  # 设置为流媒体类型
    # 设置默认质量为未知
    if not quality:
        quality = Quality.UNKNOWN
    # 设置描述信息
    desc = f"{title} ({quality})"

    item = OpertionItem(opt_type=OperationType.DOWNLOAD, item_type=item_type, desc=desc)
    item.set_url(url)

    if sub_type:
        item.set_subtype(sub_type)

    if custom_headers:
        item._extra[CommonExtraKeys.CUSTOM_HEADERS] = custom_headers

    item._extra[VideoCoreExtraKeys.QUALITY] = quality

    # 视频的主要信息
    item.set_code(code)
    item.set_title(title)
    if actors:
        item.set_actors(actors)
    if studio:
        item.set_studio(studio)
    if year:
        item.set_year(year)
    if part is not None:
        item.set_part(part)
    return item


def create_image_item(
    url: str,
    title: str,
    sub_type: Optional[str] = None,
    custom_headers: Optional[Dict[str, str]] = None,
) -> OpertionItem:
    """
    创建一个图片下载操作项
    Args:
        url: 下载链接
        title: 标题
        sub_type: 图片子类型
        custom_headers: 自定义HTTP头部
    Returns:
        OpertionItem: 创建的下载操作项
    """
    if not url:
        raise ValueError("下载链接不能为空")

    if not title:
        raise ValueError("标题不能为空")

    item_type = ItemType.IMAGE  # 设置为图片类型
    desc = f"{title} ({sub_type})" if sub_type else title

    item = OpertionItem(OperationType.DOWNLOAD, item_type=item_type, desc=desc)
    item.set_url(url)

    if sub_type:
        item.set_subtype(sub_type)

    if custom_headers:
        item._extra[CommonExtraKeys.CUSTOM_HEADERS] = custom_headers

    return item


def create_cover_item(
    url: str,
    title: str,
    custom_headers: Optional[Dict[str, str]] = None,
) -> OpertionItem:
    """
    创建一个封面图片下载操作项
    Args:
        url: 下载链接
        title: 标题
        custom_headers: 自定义HTTP头部
    Returns:
        OpertionItem: 创建的下载操作项
    """
    return create_image_item(url, title, ItemSubType.COVER, custom_headers)


def create_backdrop_item(
    url: str,
    title: str,
    custom_headers: Optional[Dict[str, str]] = None,
) -> OpertionItem:
    """创建一个背景图片下载操作项
    Args:
        url: 下载链接
        title: 标题
        custom_headers: 自定义HTTP头部
    Returns:
        OpertionItem: 创建的下载操作项
    """
    return create_image_item(url, title, ItemSubType.BACKDROP, custom_headers)


def create_thumbnail_item(
    url: str,
    title: str,
    custom_headers: Optional[Dict[str, str]] = None,
) -> OpertionItem:
    """
    创建一个缩略图下载操作项
    Args:
        url: 下载链接
        title: 标题
        custom_headers: 自定义HTTP头部
    Returns:
        OpertionItem: 创建的下载操作项
    """
    return create_image_item(url, title, ItemSubType.THUMBNAIL, custom_headers)


def create_poster_item(
    url: str,
    title: str,
    custom_headers: Optional[Dict[str, str]] = None,
) -> OpertionItem:
    """
    创建一个海报图片下载操作项
    Args:
        url: 下载链接
        title: 标题
        custom_headers: 自定义HTTP头部
    Returns:
        OpertionItem: 创建的下载操作项
    """
    return create_image_item(url, title, ItemSubType.POSTER, custom_headers)


def create_metadata_item(
    title: str,
    meta_data: BaseMetadata,
) -> OpertionItem:
    """
    创建一个元数据下载操作项
    Args:
        url: 下载链接
        title: 标题
        custom_headers: 自定义HTTP头部
    Returns:
        OpertionItem: 创建的下载操作项
    """
    if not title:
        raise ValueError("标题不能为空")

    item_type = ItemType.META_DATA  # 设置为元数据类型
    desc = f"{title} (元数据)"

    item = OpertionItem(OperationType.SAVE_METADATA, item_type=item_type, desc=desc)
    item._extra[MetadataExtraKeys.METADATA_OBJ] = meta_data
    return item

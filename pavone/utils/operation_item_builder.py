"""
Operation Item Builder Utilities - 操作项构建器工具

提供统一的OperationItem创建和组装逻辑，消除插件中的重复代码。
"""

from typing import Dict, List, Optional

from pavone.models.metadata import MovieMetadata
from pavone.models.operation import (
    OperationItem,
    create_backdrop_item,
    create_cover_item,
    create_landscape_item,
    create_metadata_item,
    create_poster_item,
    create_stream_item,
    create_thumbnail_item,
)


class OperationItemBuilder:
    """
    操作项构建器 - 使用链式调用构建OperationItem对象

    Examples:
        >>> builder = OperationItemBuilder("example.com", "示例标题", "CODE-123")
        >>> items = (builder
        ...     .add_stream("https://example.com/video.m3u8", "1080p")
        ...     .set_cover("https://example.com/cover.jpg")
        ...     .set_metadata(metadata)
        ...     .build())
    """

    def __init__(self, site: str, title: str, code: str):
        """
        初始化构建器

        Args:
            site: 站点标识符
            title: 标题
            code: 视频代码
        """
        self.site = site
        self.title = title
        self.code = code
        self._stream_items: List[OperationItem] = []
        self._cover_url: Optional[str] = None
        self._poster_url: Optional[str] = None
        self._landscape_url: Optional[str] = None
        self._backdrop_url: Optional[str] = None
        self._thumbnail_url: Optional[str] = None
        self._metadata: Optional[MovieMetadata] = None
        self._custom_headers: Optional[Dict[str, str]] = None
        self._actors: Optional[list[str]] = None
        self._studio: Optional[str] = None
        self._year: Optional[int] = None

    def add_stream(
        self,
        url: str,
        quality: str,
        custom_headers: Optional[Dict[str, str]] = None,
        part: Optional[int] = None,
    ) -> "OperationItemBuilder":
        """
        添加流媒体项

        Args:
            url: 视频流URL
            quality: 质量标识（如"1080p", "720p"）
            custom_headers: 自定义HTTP头部
            part: 分集编号

        Returns:
            self，支持链式调用
        """
        headers = custom_headers or self._custom_headers
        stream_item = create_stream_item(
            url=url,
            title=self.title,
            quality=quality,
            site=self.site,
            code=self.code,
            custom_headers=headers,
            actors=self._actors,
            studio=self._studio,
            year=self._year,
            part=part,
        )
        self._stream_items.append(stream_item)
        return self

    def set_cover(self, url: Optional[str]) -> "OperationItemBuilder":
        """
        设置封面图片URL

        Args:
            url: 封面图片URL

        Returns:
            self，支持链式调用
        """
        if url:
            self._cover_url = url
        return self

    def set_poster(self, url: Optional[str]) -> "OperationItemBuilder":
        """
        设置海报图片URL

        Args:
            url: 海报图片URL

        Returns:
            self，支持链式调用
        """
        if url:
            self._poster_url = url
        return self

    def set_landscape(self, url: Optional[str]) -> "OperationItemBuilder":
        """
        设置横版封面图片URL

        Args:
            url: 横版封面图片URL

        Returns:
            self，支持链式调用
        """
        if url:
            self._landscape_url = url
        return self

    def set_backdrop(self, url: Optional[str]) -> "OperationItemBuilder":
        """
        设置背景图片URL

        Args:
            url: 背景图片URL

        Returns:
            self，支持链式调用
        """
        if url:
            self._backdrop_url = url
        return self

    def set_thumbnail(self, url: Optional[str]) -> "OperationItemBuilder":
        """
        设置缩略图URL

        Args:
            url: 缩略图URL

        Returns:
            self，支持链式调用
        """
        if url:
            self._thumbnail_url = url
        return self

    def set_metadata(self, metadata: Optional[MovieMetadata]) -> "OperationItemBuilder":
        """
        设置元数据

        Args:
            metadata: MovieMetadata对象

        Returns:
            self，支持链式调用
        """
        if metadata:
            self._metadata = metadata
        return self

    def set_custom_headers(self, headers: Optional[Dict[str, str]]) -> "OperationItemBuilder":
        """
        设置通用的自定义HTTP头部

        Args:
            headers: 自定义HTTP头部字典

        Returns:
            self，支持链式调用
        """
        if headers:
            self._custom_headers = headers
        return self

    def set_actors(self, actors: Optional[list[str]]) -> "OperationItemBuilder":
        """
        设置演员列表

        Args:
            actors: 演员列表

        Returns:
            self，支持链式调用
        """
        if actors:
            self._actors = actors
        return self

    def set_studio(self, studio: Optional[str]) -> "OperationItemBuilder":
        """
        设置制作公司

        Args:
            studio: 制作公司名称

        Returns:
            self，支持链式调用
        """
        if studio:
            self._studio = studio
        return self

    def set_year(self, year: Optional[int]) -> "OperationItemBuilder":
        """
        设置年份

        Args:
            year: 年份

        Returns:
            self，支持链式调用
        """
        if year:
            self._year = year
        return self

    def build(self) -> List[OperationItem]:
        """
        构建所有OperationItem

        Returns:
            OperationItem列表

        Raises:
            ValueError: 如果没有添加任何stream项
        """
        if not self._stream_items:
            raise ValueError("必须至少添加一个stream项")

        result_items: List[OperationItem] = []

        # 为每个stream项添加子项
        for stream_item in self._stream_items:
            # 添加封面
            if self._cover_url:
                cover_item = create_cover_item(
                    url=self._cover_url, title=self.title, custom_headers=self._custom_headers
                )
                stream_item.append_child(cover_item)

            # 添加海报
            if self._poster_url:
                poster_item = create_poster_item(
                    url=self._poster_url, title=self.title, custom_headers=self._custom_headers
                )
                stream_item.append_child(poster_item)

            # 添加横版封面
            if self._landscape_url:
                landscape_item = create_landscape_item(
                    url=self._landscape_url, title=self.title, custom_headers=self._custom_headers
                )
                stream_item.append_child(landscape_item)

            # 添加背景图
            if self._backdrop_url:
                backdrop_item = create_backdrop_item(
                    url=self._backdrop_url, title=self.title, custom_headers=self._custom_headers
                )
                stream_item.append_child(backdrop_item)

            # 添加缩略图
            if self._thumbnail_url:
                thumbnail_item = create_thumbnail_item(
                    url=self._thumbnail_url, title=self.title, custom_headers=self._custom_headers
                )
                stream_item.append_child(thumbnail_item)

            # 添加元数据
            if self._metadata:
                metadata_item = create_metadata_item(meta_data=self._metadata, title=self.title)
                stream_item.append_child(metadata_item)

            result_items.append(stream_item)

        return result_items

    def reset(self) -> "OperationItemBuilder":
        """
        重置构建器，清空所有数据（保留site, title, code）

        Returns:
            self，支持链式调用
        """
        self._stream_items = []
        self._cover_url = None
        self._poster_url = None
        self._landscape_url = None
        self._backdrop_url = None
        self._thumbnail_url = None
        self._metadata = None
        self._custom_headers = None
        self._actors = None
        self._studio = None
        self._year = None
        return self

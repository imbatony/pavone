"""
Metadata Builder Utilities - 元数据构建器工具

提供统一的MovieMetadata对象构建逻辑，消除插件中的重复代码。
"""

from datetime import datetime
from typing import Any, Optional

from pavone.models.metadata import MovieMetadata
from pavone.utils.stringutils import StringUtils


class MetadataBuilder:
    """
    元数据构建器 - 使用链式调用构建MovieMetadata对象

    Examples:
        >>> builder = MetadataBuilder()
        >>> metadata = (builder
        ...     .set_title("示例标题", "CODE-123")
        ...     .set_site("example.com")
        ...     .set_url("https://example.com/video/123")
        ...     .set_release_date("2024-01-15")
        ...     .build())
    """

    def __init__(self):
        """初始化构建器"""
        self._data: dict[str, Any] = {}

    def set_title(self, title: str, code: Optional[str] = None) -> "MetadataBuilder":
        """
        设置标题，自动处理代码前缀

        Args:
            title: 标题文本
            code: 视频代码（如果提供，会自动添加到标题前和设置code字段）

        Returns:
            self，支持链式调用
        """
        if code:
            # 标题包含代码
            self._data["title"] = f"{code} {title}"
            self._data["original_title"] = title
            self._data["code"] = code
        else:
            self._data["title"] = title

        return self

    def set_original_title(self, original_title: str) -> "MetadataBuilder":
        """
        设置原始标题

        Args:
            original_title: 原始标题

        Returns:
            self，支持链式调用
        """
        self._data["original_title"] = original_title
        return self

    def set_code(self, code: str) -> "MetadataBuilder":
        """
        设置视频代码

        Args:
            code: 视频代码

        Returns:
            self，支持链式调用
        """
        self._data["code"] = code
        return self

    def set_site(self, site: str) -> "MetadataBuilder":
        """
        设置站点标识符

        Args:
            site: 站点标识符

        Returns:
            self，支持链式调用
        """
        self._data["site"] = site
        return self

    def set_url(self, url: str) -> "MetadataBuilder":
        """
        设置视频URL

        Args:
            url: 视频URL

        Returns:
            self，支持链式调用
        """
        self._data["url"] = url
        return self

    def set_identifier(self, site: str, code: str, url: str) -> "MetadataBuilder":
        """
        生成并设置标准identifier，同时设置site、code、url字段

        Args:
            site: 站点标识符
            code: 视频代码
            url: 视频URL

        Returns:
            self，支持链式调用
        """
        identifier = StringUtils.create_identifier(site=site, code=code, url=url)
        self._data["identifier"] = identifier
        self._data["site"] = site
        self._data["code"] = code
        self._data["url"] = url
        return self

    def set_release_date(self, release_date: Optional[str]) -> "MetadataBuilder":
        """
        设置发布日期，自动提取年份

        Args:
            release_date: 发布日期（格式：YYYY-MM-DD）

        Returns:
            self，支持链式调用
        """
        if release_date:
            self._data["premiered"] = release_date
            # 自动提取年份
            try:
                year = int(release_date.split("-")[0])
                self._data["year"] = year
            except (ValueError, IndexError):
                # 如果无法解析，使用当前年份
                self._data["year"] = datetime.now().year
        else:
            # 如果没有发布日期，使用当前年份
            self._data["year"] = datetime.now().year

        return self

    def set_year(self, year: int) -> "MetadataBuilder":
        """
        设置年份

        Args:
            year: 年份

        Returns:
            self，支持链式调用
        """
        self._data["year"] = year
        return self

    def set_cover(self, cover: Optional[str]) -> "MetadataBuilder":
        """
        设置封面图片URL

        Args:
            cover: 封面图片URL

        Returns:
            self，支持链式调用
        """
        if cover:
            self._data["cover"] = cover
        return self

    def set_poster(self, poster: Optional[str]) -> "MetadataBuilder":
        """
        设置海报图片URL

        Args:
            poster: 海报图片URL

        Returns:
            self，支持链式调用
        """
        if poster:
            self._data["poster"] = poster
        return self

    def set_backdrop(self, backdrop: Optional[str]) -> "MetadataBuilder":
        """
        设置背景图片URL

        Args:
            backdrop: 背景图片URL

        Returns:
            self，支持链式调用
        """
        if backdrop:
            self._data["backdrop"] = backdrop
        return self

    def set_plot(self, plot: Optional[str]) -> "MetadataBuilder":
        """
        设置简介

        Args:
            plot: 简介文本

        Returns:
            self，支持链式调用
        """
        if plot:
            self._data["plot"] = plot
        return self

    def set_actors(self, actors: Optional[list[str]]) -> "MetadataBuilder":
        """
        设置演员列表

        Args:
            actors: 演员列表

        Returns:
            self，支持链式调用
        """
        if actors:
            self._data["actors"] = actors
        return self

    def set_director(self, director: Optional[str]) -> "MetadataBuilder":
        """
        设置导演

        Args:
            director: 导演名称

        Returns:
            self，支持链式调用
        """
        if director:
            self._data["director"] = director
        return self

    def set_studio(self, studio: Optional[str]) -> "MetadataBuilder":
        """
        设置制作公司

        Args:
            studio: 制作公司名称

        Returns:
            self，支持链式调用
        """
        if studio:
            self._data["studio"] = studio
        return self

    def set_runtime(self, runtime: Optional[int]) -> "MetadataBuilder":
        """
        设置时长

        Args:
            runtime: 时长（分钟）

        Returns:
            self，支持链式调用
        """
        if runtime:
            self._data["runtime"] = runtime
        return self

    def set_genres(self, genres: Optional[list[str]]) -> "MetadataBuilder":
        """
        设置类型列表

        Args:
            genres: 类型列表

        Returns:
            self，支持链式调用
        """
        if genres:
            self._data["genres"] = genres
        return self

    def set_tags(self, tags: Optional[list[str]]) -> "MetadataBuilder":
        """
        设置标签列表

        Args:
            tags: 标签列表

        Returns:
            self，支持链式调用
        """
        if tags:
            self._data["tags"] = tags
        return self

    def set_rating(self, rating: Optional[float]) -> "MetadataBuilder":
        """
        设置评分

        Args:
            rating: 评分（0-10）

        Returns:
            self，支持链式调用
        """
        if rating is not None:
            self._data["rating"] = rating
        return self

    def set_serial(self, serial: Optional[str]) -> "MetadataBuilder":
        """
        设置系列名称

        Args:
            serial: 系列名称

        Returns:
            self，支持链式调用
        """
        if serial:
            self._data["serial"] = serial
        return self

    def build(self) -> MovieMetadata:
        """
        构建最终的MovieMetadata对象

        Returns:
            构建好的MovieMetadata对象

        Raises:
            ValueError: 如果缺少必需字段
        """
        # 验证必需字段
        required_fields = ["title", "url", "site", "code", "identifier"]
        missing_fields = [field for field in required_fields if field not in self._data]

        if missing_fields:
            raise ValueError(f"缺少必需字段: {', '.join(missing_fields)}")

        # 创建 MovieMetadata 对象
        return MovieMetadata(**self._data)

    def reset(self) -> "MetadataBuilder":
        """
        重置构建器，清空所有数据

        Returns:
            self，支持链式调用
        """
        self._data = {}
        return self

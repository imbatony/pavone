"""
JTable统一插件

一个类同时实现元数据提取和视频下载两种功能，最大程度复用代码。
注意：JTable 不支持搜索功能。
"""

import re
from datetime import datetime
from typing import Any, List, Optional, Tuple

from ..models import MovieMetadata, OperationItem, Quality
from ..utils import CodeExtractUtils, StringUtils
from ..utils.html_metadata_utils import HTMLMetadataExtractor
from ..utils.metadata_builder import MetadataBuilder
from ..utils.operation_item_builder import OperationItemBuilder
from .extractors.base import ExtractorPlugin
from .metadata.base import MetadataPlugin

# 定义插件名称和版本
PLUGIN_NAME = "JTable"
PLUGIN_VERSION = "2.0.0"
PLUGIN_DESCRIPTION = "JTable统一插件：支持元数据提取和视频下载"
PLUGIN_AUTHOR = "PAVOne"

# 定义插件优先级
PLUGIN_PRIORITY = 30

# 定义支持的域名
SUPPORTED_DOMAINS = ["jp.jable.tv", "jable.tv"]

SITE_NAME = "Jable"

# JTable 网站的基础 URL
JTABLE_BASE_URL = "https://jp.jable.tv"


class JTablePlugin(ExtractorPlugin, MetadataPlugin):
    """
    JTable统一插件
    同时实现元数据提取和视频下载两种功能（通过多继承）
    """

    def __init__(self):
        """初始化JTable插件"""
        # 调用父类初始化（多继承情况下，使用 super() 会按照 MRO 顺序调用）
        super().__init__(
            name=PLUGIN_NAME,
            version=PLUGIN_VERSION,
            description=PLUGIN_DESCRIPTION,
            author=PLUGIN_AUTHOR,
            priority=PLUGIN_PRIORITY,
        )
        self.supported_domains = SUPPORTED_DOMAINS
        self.site_name = SITE_NAME
        self.base_url = JTABLE_BASE_URL
        # logger already initialized in base classes using subclass module name

    def initialize(self) -> bool:
        """初始化插件"""
        return True

    # ==================== 元数据提取功能接口 ====================

    def can_extract(self, identifier: str) -> bool:
        """检查是否能处理给定的identifier

        Args:
            identifier: URL或视频代码

        Returns:
            是否能处理
        """
        # 如果是URL，检查域名
        if identifier.startswith("http://") or identifier.startswith("https://"):
            return self.can_handle_domain(identifier, self.supported_domains)

        # 检查是否为视频代码格式
        identifier_stripped = identifier.strip()
        code_pattern = r"^[a-zA-Z]+(-|\d)[a-zA-Z0-9]*$"
        if re.match(code_pattern, identifier_stripped):
            if "-" in identifier_stripped:
                parts = identifier_stripped.split("-")
                if len(parts) == 2 and len(parts[0]) > 0 and len(parts[1]) > 0:
                    if parts[0][0].isalpha() and parts[1][0].isdigit():
                        return True

        return False

    def extract_metadata(self, identifier: str) -> Optional[MovieMetadata]:
        """从给定的identifier提取元数据

        Args:
            identifier: URL或视频代码

        Returns:
            元数据对象，提取失败返回None
        """
        try:
            url = identifier
            if not identifier.startswith("http"):
                # 如果是代码，构造URL
                # JTable的URL格式: https://jp.jable.tv/videos/{code}/
                code = identifier.strip().lower()
                url = f"{self.base_url}/videos/{code}/"
                self.logger.info(f"从代码构造URL: {url}")

            response = self.fetch(url, timeout=30)
            html = response.text
            if not html:
                self.logger.error(f"获取页面内容失败: {url}")
                return None

            # 提取所有元数据
            metadata_dict = self._extract_all_metadata(html, url)

            # 使用 MetadataBuilder 构建元数据
            metadata = (
                MetadataBuilder()
                .set_title(metadata_dict["title"], metadata_dict["code"])
                .set_code(metadata_dict["code"])
                .set_site(self.site_name)
                .set_url(url)
                .set_identifier(self.site_name, metadata_dict["code"], url)
                .set_release_date(metadata_dict["release_date"])
                .set_cover(metadata_dict["cover"])
                .set_actors(metadata_dict["actors"])
                .set_genres(metadata_dict["genres"])
                .set_tags(metadata_dict["tags"])
                .build()
            )

            self.logger.info(f"成功提取元数据: {metadata_dict['code']} - {metadata_dict['title']}")
            return metadata

        except Exception as e:
            self.logger.error(f"提取元数据失败: {e}", exc_info=True)
            return None

    def _extract_all_metadata(self, html: str, url: str) -> dict[str, Any]:
        """提取所有元数据（内部方法，供元数据提取和视频下载共享）

        Args:
            html: HTML内容
            url: 视频URL

        Returns:
            包含所有元数据的字典
        """
        # 提取封面
        cover = HTMLMetadataExtractor.extract_og_image(html)

        # 提取代码和标题
        code, title = self._extract_code_title(html)

        # 提取演员
        actors = self._extract_actors(html)

        # 提取发布日期
        release_date_obj = self._extract_release_date(html)
        release_date = release_date_obj.strftime("%Y-%m-%d")
        year = release_date_obj.year

        # 提取类型和标签
        genres = self._extract_genres(html)
        tags = self._extract_tags(html)

        return {
            "code": code,
            "title": title,
            "cover": cover,
            "actors": actors,
            "release_date": release_date,
            "year": year,
            "genres": genres,
            "tags": tags,
        }

    # ==================== 视频提取功能接口 ====================

    def can_handle(self, url: str) -> bool:
        """检查是否能处理给定的URL"""
        return self.can_handle_domain(url, self.supported_domains)

    def extract(self, url: str) -> List[OperationItem]:
        """从给定的URL提取下载选项

        Args:
            url: 视频页面URL

        Returns:
            操作项列表
        """
        if not self.can_handle(url):
            return []

        try:
            # 获取网页内容
            response = self.fetch(url)
            html = response.text
            if not html:
                self.logger.error(f"获取页面内容失败: {url}")
                return []

            # 1. 提取m3u8链接
            m3u8_url = self._extract_m3u8_url(html)
            if not m3u8_url:
                self.logger.error("未找到 m3u8 链接")
                return []

            self.logger.info(f"找到 m3u8: {m3u8_url}")

            # 2. 提取所有元数据
            metadata_dict = self._extract_all_metadata(html, url)

            # 3. 创建完整的元数据对象
            metadata = (
                MetadataBuilder()
                .set_title(metadata_dict["title"], metadata_dict["code"])
                .set_code(metadata_dict["code"])
                .set_site(self.site_name)
                .set_url(url)
                .set_identifier(self.site_name, metadata_dict["code"], url)
                .set_release_date(metadata_dict["release_date"])
                .set_cover(metadata_dict["cover"])
                .set_actors(metadata_dict["actors"])
                .set_genres(metadata_dict["genres"])
                .set_tags(metadata_dict["tags"])
                .build()
            )

            # 4. 使用 OperationItemBuilder 创建操作对象
            builder = OperationItemBuilder(self.site_name, metadata_dict["title"], metadata_dict["code"])

            builder.set_actors(metadata_dict["actors"]).set_year(metadata_dict["year"]).set_studio("")

            # 添加视频流
            quality = Quality.guess(m3u8_url)
            builder.add_stream(url=m3u8_url, quality=quality)

            # 添加封面和背景图
            if metadata_dict["cover"]:
                builder.set_cover(metadata_dict["cover"])
                builder.set_landscape(metadata_dict["cover"])  # JTable 使用同一张图作为 landscape

            # 添加元数据
            builder.set_metadata(metadata)

            return builder.build()

        except Exception as e:
            self.logger.error(f"提取失败: {e}", exc_info=True)
            return []

    # ==================== 私有辅助方法 ====================

    def _extract_m3u8_url(self, html: str) -> Optional[str]:
        """从HTML中提取m3u8链接

        Args:
            html: HTML内容

        Returns:
            m3u8 URL或None
        """
        pattern = r"var hlsUrl = '(https?://[^']+)'"
        match = re.search(pattern, html)
        return match.group(1) if match else None

    def _extract_code_title(self, html: str) -> Tuple[str, str]:
        """从HTML中提取视频标题和代码

        Args:
            html: HTML内容

        Returns:
            (code, title)，其中 title 不包含代码前缀
        """
        default_title = "Jable Video"
        default_code = StringUtils.sha_256_hash(default_title)

        title = HTMLMetadataExtractor.extract_og_title(html)
        if not title:
            self.logger.warning("未找到视频标题，使用默认值")
            return (default_code, default_title)

        # 分离编号和标题
        # 格式通常是: "CODE-123 标题内容"
        title_parts = title.split(" ", 1)
        if len(title_parts) == 2:
            code = CodeExtractUtils.extract_code_from_text(title_parts[0])
            if not code:
                code = default_code
            # 返回代码和纯标题（不含代码前缀）
            return (code, title_parts[1])
        else:
            # 如果没有空格分隔，尝试提取代码
            code = CodeExtractUtils.extract_code_from_text(title)
            if not code:
                code = default_code
            return (code, title)

    def _extract_actors(self, html: str) -> List[str]:
        """从HTML中提取演员信息

        Args:
            html: HTML内容

        Returns:
            演员列表
        """
        # <span class="placeholder rounded-circle" data-toggle="tooltip"
        #       data-placement="bottom" title="演员名">...</span>
        pattern = r'<span class="placeholder rounded-circle" data-toggle="tooltip" data-placement="bottom" title="([^"]+)">'
        matches = re.findall(pattern, html)
        return matches if matches else []

    def _extract_release_date(self, html: str) -> datetime:
        """从HTML中提取发布日期

        Args:
            html: HTML内容

        Returns:
            日期对象，解析失败返回当前日期
        """
        # <span class="inactive-color">発売された 2024-09-28</span>
        pattern = r'<span class="inactive-color">発売された\s*([^<]+)</span>'
        match = re.search(pattern, html)
        if match:
            date_str = match.group(1).strip()
            try:
                return datetime.strptime(date_str, "%Y-%m-%d")
            except ValueError:
                self.logger.warning(f"无法解析发布日期: {date_str}")

        return datetime.now()  # 如果解析失败，返回当前日期

    def _extract_genres(self, html: str) -> List[str]:
        """从HTML中提取视频类型

        Args:
            html: HTML内容

        Returns:
            类型列表
        """
        # <a href="https://jp.jable.tv/categories/bdsm/" class="cat">ビーディーエスエム</a>
        pattern = r'<a href="https://jp\.jable\.tv/categories/[^"]+" class="cat">([^<]+)</a>'
        matches = re.findall(pattern, html)
        return matches if matches else []

    def _extract_tags(self, html: str) -> List[str]:
        """从HTML中提取标签

        Args:
            html: HTML内容

        Returns:
            标签列表
        """
        # <a href="https://jp.jable.tv/tags/girl/">少女</a>
        pattern = r'<a href="https://jp\.jable\.tv/tags/[^"]+">([^<]+)</a>'
        matches = re.findall(pattern, html)
        return matches if matches else []

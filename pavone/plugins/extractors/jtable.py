import re
from datetime import datetime
from typing import List, Optional, Tuple

from ...models import OperationItem, Quality
from ...utils import CodeExtractUtils, StringUtils
from ...utils.html_metadata_utils import HTMLMetadataExtractor
from ...utils.metadata_builder import MetadataBuilder
from ...utils.operation_item_builder import OperationItemBuilder
from .base import ExtractorPlugin

# 定义插件名称和版本
PLUGIN_NAME = "JTableExtractor"
PLUGIN_VERSION = "1.0.0"
PLUGIN_DESCRIPTION = "提取 jp.jable.tv 的视频下载链接"
PLUGIN_AUTHOR = "PAVOne"

# 定义插件优先级
PLUGIN_PRIORITY = 30

# 定义支持的域名
SUPPORTED_DOMAINS = ["jp.jable.tv"]

SITE_NAME = "Jable"


class JTableExtractor(ExtractorPlugin):
    """
    提取 jp.jable.tv 的视频下载链接
    """

    def __init__(self):
        super().__init__(
            name=PLUGIN_NAME,
            version=PLUGIN_VERSION,
            description=PLUGIN_DESCRIPTION,
            author=PLUGIN_AUTHOR,
            priority=PLUGIN_PRIORITY,
        )
        self.supported_domains = SUPPORTED_DOMAINS
        self.site_name = SITE_NAME

    def can_handle(self, url: str) -> bool:
        """检查是否能处理给定的URL"""
        return self.can_handle_domain(url, self.supported_domains)

    def extract(self, url: str) -> List[OperationItem]:
        """从给定的URL提取下载选项"""
        if not self.can_handle(url):
            return []
        try:
            # 获取网页内容
            response = self.fetch(url)
            html = response.text
            # 1. 提取m3u8
            pattern = r"var hlsUrl = '(https?://[^']+)'"
            match = re.search(pattern, html)
            if match:
                m3u8 = match.group(1)
                self.logger.info(f"找到 m3u8: {m3u8}")
            else:
                self.logger.error("未找到 m3u8")
                return []
            # 2. 提取元数据
            cover = self._extract_cover(html)
            code, title = self._extract_code_title(html)
            actors = self._extract_actors(html)
            release_date = self._extract_release_date(html)
            genres = self._extract_genres(html)
            tags = self._extract_tags(html)
            # 2020-10-01 这种格式的日期
            year = release_date.year

            # 3. 创建元数据
            metadata = (
                MetadataBuilder()
                .set_title(title)  # title 已经不包含代码前缀
                .set_code(code)  # 单独设置 code
                .set_identifier(self.site_name, code, url)
                .set_cover(cover)
                .set_actors(actors)
                .set_release_date(release_date.strftime("%Y-%m-%d"))
                .set_genres(genres)
                .set_tags(tags)
                .build()
            )

            # 4. 创建操作对象
            builder = OperationItemBuilder(SITE_NAME, title, code)
            builder.set_actors(actors).set_year(year).set_studio("")
            builder.add_stream(url=m3u8, quality=Quality.guess(title))
            if cover:
                builder.set_cover(cover)
                builder.set_landscape(cover)  # JTable 使用同一张图作为 landscape
            builder.set_metadata(metadata)

            return builder.build()

        except Exception as e:
            self.logger.error(f"提取失败: {e}")
            return []

    def _extract_cover(self, html: str) -> Optional[str]:
        """从HTML中提取封面图片URL"""
        return HTMLMetadataExtractor.extract_og_image(html)

    def _extract_code_title(self, html: str) -> Tuple[str, str]:
        """从HTML中提取视频标题和代码

        返回 (code, title)，其中 title 不包含代码前缀
        """
        default_title = "Jable Video"
        default_code = StringUtils.sha_256_hash(default_title)
        title = HTMLMetadataExtractor.extract_og_title(html)
        if not title:
            raise ValueError("未找到视频标题")
        # 分离编号和标题
        title_parts = title.split(" ", 1)
        if len(title_parts) == 2:
            code = CodeExtractUtils.extract_code_from_text(title_parts[0])
            if not code:
                code = default_code
            # 返回代码和纯标题（不含代码前缀）
            return (code, title_parts[1])
        else:
            code = default_code
            return (code, title)

    def _extract_actors(self, html: str) -> List[str]:
        """从HTML中提取演员信息"""
        pattern = r'<span class="placeholder rounded-circle" data-toggle="tooltip" data-placement="bottom" title="([^"]+)">[^<]+</span>'
        matches = re.findall(pattern, html)
        return matches if matches else []

    def _extract_release_date(self, html: str) -> datetime:
        """从HTML中提取发布日期"""
        # <span class="inactive-color">発売された 2024-09-28</span>
        pattern = r'<span class="inactive-color">発売された\s*([^<]+)</span>'
        match = re.search(pattern, html)
        if match:
            date_str = match.group(1).strip()
            try:
                return datetime.strptime(date_str, "%Y-%m-%d")
            except ValueError:
                self.logger.error(f"无法解析发布日期: {date_str}")
        return datetime.now()  # 如果解析失败，返回当前日期

    def _extract_genres(self, html: str) -> List[str]:
        """从HTML中提取视频类型"""
        # <a href="https://jp.jable.tv/categories/bdsm/" class="cat">ビーディーエスエム</a>
        pattern = r'<a href="https://jp.jable.tv/categories/[^"]+" class="cat">([^<]+)</a>'
        matches = re.findall(pattern, html)
        return matches if matches else []

    def _extract_tags(self, html: str) -> List[str]:
        """从HTML中提取标签"""
        # <a href="https://jp.jable.tv/tags/girl/">少女</a>
        pattern = r'<a href="https://jp.jable.tv/tags/[^"]+">([^<]+)</a>'
        matches = re.findall(pattern, html)
        return matches if matches else []

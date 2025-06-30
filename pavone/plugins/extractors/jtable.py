import re
from typing import List, Optional, Tuple
from urllib.parse import urlparse
from ...models import OperationItem, Quality, create_stream_item, create_cover_item, create_metadata_item
from ...models import MovieMetadata
from .base import ExtractorPlugin
from ...utils import StringUtils, CodeExtractUtils
from datetime import datetime

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
        try:
            parsed_url = urlparse(url)
            # 检查协议是否为HTTP或HTTPS
            if parsed_url.scheme.lower() not in ("http", "https"):
                return False
            # 检查域名是否在支持列表中
            return any(parsed_url.netloc.lower() == domain.lower() for domain in self.supported_domains)
        except Exception:
            return False

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

            # 3. 创建操作对象
            m3u8_item = create_stream_item(
                url=m3u8,
                title=title,
                code=code,
                site=SITE_NAME,
                quality=Quality.guess(title),
                actors=actors,
                year=year,
                studio="",  # JTable 不提供制作公司信息
            )
            if cover:
                cover_item = create_cover_item(url=cover, title=title)
                m3u8_item.append_child(cover_item)

            metadata = MovieMetadata(
                identifier=f"{self.site_name}_{code}",
                code=code,
                title=title,
                url=url,
                site=self.site_name,
                cover=cover,
                actors=actors,
                premiered=release_date.strftime("%Y-%m-%d"),
                genres=genres,
                tags=tags,
                year=year,
            )
            metadata_item = create_metadata_item(title, metadata)
            m3u8_item.append_child(metadata_item)
            return [m3u8_item]

        except Exception as e:
            self.logger.error(f"提取失败: {e}")
            return []

    def _extract_cover(self, html: str) -> Optional[str]:
        """从HTML中提取封面图片URL"""
        pattern = r'<meta property="og:image" content="([^"]+)"'
        match = re.search(pattern, html)
        if match:
            return match.group(1)
        return None

    def _extract_code_title(self, html: str) -> Tuple[str, str]:
        """从HTML中提取视频标题"""
        pattern = r'<meta property="og:title" content="([^"]+)"'
        match = re.search(pattern, html)
        if not match:
            raise ValueError("未找到视频标题")
        title = match.group(1)
        # 分离编号和标题
        title_parts = title.split(" ", 1)
        if len(title_parts) == 2:
            code = CodeExtractUtils.extract_code_from_text(title_parts[0])
            title = title_parts[1]
            if not code:
                code = StringUtils.sha_256_hash(title_parts[0])
        else:
            code = StringUtils.sha_256_hash(title)
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

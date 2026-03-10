"""
Memojav复合型插件

支持从 memojav.com 网站提取视频下载链接和元数据。
"""

import re
from typing import List, Optional
from urllib.parse import unquote, urlparse

from ..models import MovieMetadata, OperationItem, Quality
from ..utils import CodeExtractUtils
from ..utils.html_metadata_utils import HTMLMetadataExtractor
from ..utils.metadata_builder import MetadataBuilder
from ..utils.operation_item_builder import OperationItemBuilder
from .extractors.base import ExtractorPlugin
from .metadata.base import MetadataPlugin

# 定义插件名称和版本
PLUGIN_NAME = "Memojav"
PLUGIN_VERSION = "2.0.0"
PLUGIN_DESCRIPTION = "提取 memojav.com 的视频下载链接和元数据"
PLUGIN_AUTHOR = "PAVOne"

# 定义插件优先级
PLUGIN_PRIORITY = 30

# 定义支持的域名
SUPPORTED_DOMAINS = ["memojav.com", "www.memojav.com"]

SITE_NAME = "Memojav"


class MemojavPlugin(ExtractorPlugin, MetadataPlugin):
    """
    Memojav复合型插件，支持视频下载和元数据提取
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

    # ==================== ExtractorPlugin 接口 ====================

    def can_handle(self, url: str) -> bool:
        """检查是否能处理给定的URL"""
        return self.can_handle_domain(url, self.supported_domains)

    def extract(self, url: str) -> List[OperationItem]:
        """从给定的URL提取下载选项"""
        if not self.can_handle(url):
            return []
        try:
            # 获取内嵌网页内容
            url = url.replace("video", "embed")
            response = self.fetch(url)
            vid = self._get_vid_from_url(url)
            code = CodeExtractUtils.extract_code_from_text(vid) or vid
            # 将 code 转为大写
            code = code.upper()
            html = response.text
            if not html:
                self.logger.error("无法获取网页内容")
                return []
            domain = urlparse(url).netloc.lower()
            get_video_url = f"https://{domain}/hls/get_video_info.php?id={vid}&sig=NTg1NTczNg&sts=7264825"
            response = self.fetch(get_video_url)
            video_info_content = response.text
            if not video_info_content:
                self.logger.error("视频信息内容为空")
                return []
            # 1. 提取m3u8链接
            m3u8_url = self._extract_m3u8(video_info_content)
            if not m3u8_url:
                self.logger.error("未找到m3u8链接")
                return []
            # 2. 提取封面图片
            cover_url = self._extract_cover(html)
            if not cover_url:
                self.logger.error("未找到封面图片链接")
                return []
            # 3. 提取视频标题
            title = self._extract_title(html)
            if not title:
                self.logger.error("未能提取视频标题")
                return []

            # 4. 构建操作项
            return (
                OperationItemBuilder(SITE_NAME, title, code)
                .add_stream(url=m3u8_url, quality=Quality.UNKNOWN)
                .set_cover(cover_url)
                .build()
            )
        except Exception as e:
            self.logger.error(f"提取视频信息失败: {e}")
            return []

    # ==================== MetadataPlugin 接口 ====================

    def can_extract(self, identifier: str) -> bool:
        """检查是否能提取给定identifier的元数据"""
        return self.can_handle(identifier)

    def extract_metadata(self, identifier: str) -> Optional[MovieMetadata]:
        """从给定的URL提取元数据"""
        if not self.can_extract(identifier):
            return None

        try:
            # 获取内嵌网页内容
            url = identifier.replace("video", "embed")
            response = self.fetch(url)
            html = response.text
            if not html:
                self.logger.error("无法获取网页内容")
                return None

            # 提取视频 ID
            vid = self._get_vid_from_url(url)
            code = CodeExtractUtils.extract_code_from_text(vid) or vid
            # 将 code 转为大写
            code = code.upper()

            # 提取标题
            title = self._extract_title(html)
            if not title:
                self.logger.error("未能提取视频标题")
                return None

            # 提取封面
            cover_url = self._extract_cover(html)

            # 使用 MetadataBuilder 构建元数据
            builder = MetadataBuilder()
            builder.set_title(title, code)
            builder.set_code(code)
            builder.set_site(self.site_name)  # 设置 site
            builder.set_url(identifier)
            builder.set_identifier(self.site_name, code, identifier)  # 设置 identifier

            if cover_url:
                builder.set_poster(cover_url)

            return builder.build()

        except Exception as e:
            self.logger.error(f"提取元数据失败: {e}")
            return None

    # ==================== 私有辅助方法 ====================

    def _extract_m3u8(self, html: str) -> Optional[str]:
        """从HTML中提取m3u8链接"""
        pattern = r'"url":"(https?%3A%2F%2F[^"]+)"'
        match = re.search(pattern, html)
        if match:
            return unquote(match.group(1))
        return None

    def _extract_cover(self, html: str) -> Optional[str]:
        """从HTML中提取封面图片链接"""
        return HTMLMetadataExtractor.extract_og_image(html)

    def _extract_title(self, html: str) -> str:
        """从HTML中提取视频代码和标题"""
        # <meta name="title" content="SONE-768 | During the summer vacation of adolescence, childhood friends playfully kiss each other... I got excited watching and ended up having a French kissing threesome Airi Nagisa Sakika Shirakami">
        pattern = r'<meta name="title" content="([^"]+)"'
        match = re.search(pattern, html)
        if match:
            title = match.group(1)
            title = title.split("|", maxsplit=1)[1].strip()
            return title
        raise ValueError("未能提取视频代码和标题")

    def _get_vid_from_url(self, url: str) -> str:
        """从 URL 中提取视频代码"""
        parsed_url = urlparse(url)
        path_parts = parsed_url.path.split("/")
        # 过滤掉空字符串，返回最后一个非空部分
        non_empty_parts = [p for p in path_parts if p]
        if non_empty_parts:
            return non_empty_parts[-1]
        raise ValueError("无法从 URL 中提取视频代码")

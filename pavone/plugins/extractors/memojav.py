"""
Memojav视频提取器插件

支持从 memojav.com 网站提取视频下载链接。
"""

import re
from typing import List, Optional
from urllib.parse import unquote, urlparse

from ...models import OperationItem, Quality
from ...utils import CodeExtractUtils
from ...utils.html_metadata_utils import HTMLMetadataExtractor
from ...utils.operation_item_builder import OperationItemBuilder
from .base import ExtractorPlugin

# 定义插件名称和版本
PLUGIN_NAME = "MemojavExtractor"
PLUGIN_VERSION = "1.0.0"
PLUGIN_DESCRIPTION = "提取 memojav.com 的视频下载链接"
PLUGIN_AUTHOR = "PAVOne"

# 定义插件优先级
PLUGIN_PRIORITY = 30

# 定义支持的域名
SUPPORTED_DOMAINS = ["memojav.com", "www.memojav.com"]

SITE_NAME = "Memojav"


class MemojavExtractor(ExtractorPlugin):
    """
    提取 memojav.com 的视频下载链接
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
            # 获取内嵌网页内容
            url = url.replace("video", "embed")
            response = self.fetch(url)
            vid = self.get_vid_from_url(url)
            code = CodeExtractUtils.extract_code_from_text(vid) or vid
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

    def get_vid_from_url(self, url: str) -> str:
        """从URL中提取视频代码"""
        parsed_url = urlparse(url)
        path_parts = parsed_url.path.split("/")
        if len(path_parts) > 1:
            return path_parts[-1]
        raise ValueError("无法从URL中提取视频代码")

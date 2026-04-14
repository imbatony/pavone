"""
MyWife (舞ワイフ) 元数据提取器插件

参考: D:\\code\\metatube-sdk-go-main\\provider\\mywife\\mywife.go
支持的 URL 模式: https://mywife.cc/teigaku/model/no/{id}
ID 格式: MYWIFE-{数字} 或 纯数字
通过 HTML 页面解析获取元数据。
"""

import re
from typing import List, Optional
from urllib.parse import urlparse

from bs4 import BeautifulSoup

from ...models import MovieMetadata
from ...utils.metadata_builder import MetadataBuilder
from .base import HtmlMetadataPlugin

PLUGIN_NAME = "MyWifeMetadata"
PLUGIN_VERSION = "1.0.0"
PLUGIN_DESCRIPTION = "提取 mywife.cc (舞ワイフ) 的视频元数据"
PLUGIN_AUTHOR = "PAVOne"
PLUGIN_PRIORITY = 50

SUPPORTED_DOMAINS = ["mywife.cc", "www.mywife.cc", "mywife.co.jp"]
SITE_NAME = "MyWife"

MOVIE_URL_TEMPLATE = "https://mywife.cc/teigaku/model/no/{movie_id}"


class MyWifeMetadata(HtmlMetadataPlugin):
    """mywife.cc (舞ワイフ) 元数据提取器，通过 HTML 页面解析获取数据。"""

    def __init__(self):
        super().__init__(
            name=PLUGIN_NAME,
            version=PLUGIN_VERSION,
            description=PLUGIN_DESCRIPTION,
            author=PLUGIN_AUTHOR,
            priority=PLUGIN_PRIORITY,
        )

    def can_extract(self, identifier: str) -> bool:
        if identifier.startswith("http://") or identifier.startswith("https://"):
            return self.can_handle_domain(identifier, SUPPORTED_DOMAINS)
        return bool(re.match(r"^(?:mywife[-_])?(\d+)$", identifier.strip(), re.IGNORECASE))

    def _resolve(self, identifier: str):
        if identifier.startswith("http://") or identifier.startswith("https://"):
            parsed = urlparse(identifier)
            parts = parsed.path.strip("/").split("/")
            if parts:
                movie_id = parts[-1]
                return movie_id, identifier
            return None, None
        m = re.match(r"^(?:mywife[-_])?(\d+)$", identifier.strip(), re.IGNORECASE)
        if m:
            movie_id = m.group(1)
            return movie_id, MOVIE_URL_TEMPLATE.format(movie_id=movie_id)
        return None, None

    def _parse(self, soup: BeautifulSoup, movie_id: str, page_url: str) -> Optional[MovieMetadata]:
        # Title from <head><title>
        title: Optional[str] = None
        title_tag = soup.find("title")
        if title_tag:
            title = title_tag.get_text(strip=True)

        # Summary
        plot: Optional[str] = None
        desc_el = soup.select_one("div.modelsamplephototop span.text_overflow")
        if desc_el:
            plot = desc_el.get_text(strip=True)

        # Cover + Preview video from video element
        cover: Optional[str] = None
        video_el = soup.select_one("div.modelsamplephototop video#video")
        if video_el:
            if video_el.get("poster"):
                cover = self._abs(str(video_el["poster"]), page_url)

        thumbnail = cover

        # Preview images
        backdrops: List[str] = []
        for img in soup.select("div.modelsamplephoto div.modelsample_photowaku img"):
            src = img.get("src")
            if src:
                backdrops.append(self._abs(str(src), page_url))

        display_code = f"MYWIFE-{movie_id}"

        metadata = (
            MetadataBuilder()
            .set_title(title or "", display_code)
            .set_identifier(SITE_NAME, display_code, page_url)
            .set_actors([])
            .set_studio("舞ワイフ")
            .set_tags([])
            .set_cover(cover)
            .set_thumbnail(thumbnail)
            .set_backdrops(backdrops)
            .set_plot(plot)
            .build()
        )
        metadata.official_rating = "JP-18+"
        self.logger.info(f"成功提取元数据: {display_code}")
        return metadata

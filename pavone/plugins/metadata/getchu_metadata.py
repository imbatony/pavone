"""
Getchu 元数据提取器插件

参考: D:\\code\\metatube-sdk-go-main\\provider\\getchu\\getchu.go
支持的 URL 模式: https://dl.getchu.com/i/item{id}
ID 格式: 纯数字
通过 HTML 页面解析获取元数据。
"""

import re
from typing import List, Optional
from urllib.parse import urlparse

from bs4 import BeautifulSoup

from ...models import MovieMetadata
from ...utils.metadata_builder import MetadataBuilder
from .base import HtmlMetadataPlugin

PLUGIN_NAME = "GetchuMetadata"
PLUGIN_VERSION = "1.0.0"
PLUGIN_DESCRIPTION = "提取 dl.getchu.com 的视频元数据"
PLUGIN_AUTHOR = "PAVOne"
PLUGIN_PRIORITY = 50

SUPPORTED_DOMAINS = ["getchu.com", "dl.getchu.com", "www.getchu.com"]
SITE_NAME = "Getchu"

MOVIE_URL_TEMPLATE = "https://dl.getchu.com/i/item{movie_id}"


class GetchuMetadata(HtmlMetadataPlugin):
    """dl.getchu.com 元数据提取器。"""

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
        return bool(re.match(r"^(?:GETCHU[-_])?(\d+)$", identifier.strip(), re.IGNORECASE))

    def _resolve(self, identifier: str):
        if identifier.startswith("http://") or identifier.startswith("https://"):
            parsed = urlparse(identifier)
            base = parsed.path.split("/")[-1]
            m = re.match(r"item(\d+)", base)
            if m:
                return m.group(1), identifier
            return None, None
        m = re.match(r"^(?:GETCHU[-_])?(\d+)$", identifier.strip(), re.IGNORECASE)
        if m:
            movie_id = m.group(1)
            return movie_id, MOVIE_URL_TEMPLATE.format(movie_id=movie_id)
        return None, None

    def _parse(self, soup: BeautifulSoup, movie_id: str, page_url: str) -> Optional[MovieMetadata]:
        code = f"GETCHU-{movie_id}"
        title: Optional[str] = None
        cover: Optional[str] = None
        plot: Optional[str] = None
        label: Optional[str] = None
        tags: List[str] = []
        premiered: Optional[str] = None
        backdrops: List[str] = []

        # Title + Cover from og:meta
        og_title = soup.find("meta", attrs={"property": "og:title"})
        if og_title and og_title.get("content"):
            title = str(og_title["content"])

        og_image = soup.find("meta", attrs={"property": "og:image"})
        if og_image and og_image.get("content"):
            cover = self._abs(str(og_image["content"]), page_url)

        # Fields from table rows
        for tr in soup.find_all("tr"):
            tds = tr.find_all("td")
            if len(tds) >= 2:
                key = tds[0].get_text(strip=True)
                val = tds[1].get_text(strip=True)
                if key == "サークル":
                    label = val
                elif key == "配信開始日":
                    premiered = self._parse_date(val)
                elif key == "趣向":
                    tag_links = tds[1].find_all("a")
                    if tag_links:
                        tags = [a.get_text(strip=True) for a in tag_links if a.get_text(strip=True)]
                    else:
                        tags = [t.strip() for t in val.split() if t.strip()]
                elif key == "作品内容":
                    plot = val

        metadata = (
            MetadataBuilder()
            .set_title(title or "", code)
            .set_identifier(SITE_NAME, code, page_url)
            .set_studio(label)
            .set_tags(tags)
            .set_release_date(premiered)
            .set_cover(cover)
            .set_thumbnail(cover)
            .set_backdrops(backdrops)
            .set_plot(plot)
            .build()
        )
        metadata.official_rating = "JP-18+"
        self.logger.info(f"成功提取元数据: {code}")
        return metadata

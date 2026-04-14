"""
Tokyo-Hot 元数据提取器插件

参考: D:\\code\\metatube-sdk-go-main\\provider\\tokyo-hot\\tokyo-hot.go
支持的 URL 模式: https://my.tokyo-hot.com/product/{id}/?lang=ja
ID 格式: 品番码 (如 n1234, k1234)
通过 HTML 页面解析获取元数据。
"""

import re
from typing import List, Optional
from urllib.parse import urlparse

from bs4 import BeautifulSoup
from bs4.element import NavigableString

from ...models import MovieMetadata
from ...utils.metadata_builder import MetadataBuilder
from .base import HtmlMetadataPlugin

PLUGIN_NAME = "TokyoHotMetadata"
PLUGIN_VERSION = "1.0.0"
PLUGIN_DESCRIPTION = "提取 tokyo-hot.com 的视频元数据"
PLUGIN_AUTHOR = "PAVOne"
PLUGIN_PRIORITY = 50

SUPPORTED_DOMAINS = ["tokyo-hot.com", "my.tokyo-hot.com", "www.tokyo-hot.com"]
SITE_NAME = "TOKYO-HOT"

MOVIE_URL_TEMPLATE = "https://my.tokyo-hot.com/product/{movie_id}/?lang=ja"


class TokyoHotMetadata(HtmlMetadataPlugin):
    """tokyo-hot.com 元数据提取器，通过 HTML 页面解析获取数据。"""

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
        return bool(re.match(r"^[a-zA-Z_]*\d+$", identifier.strip()))

    def _resolve(self, identifier: str):
        if identifier.startswith("http://") or identifier.startswith("https://"):
            parsed = urlparse(identifier)
            parts = parsed.path.strip("/").split("/")
            if len(parts) >= 2 and parts[-2] == "product":
                movie_id = parts[-1].lower()
                return movie_id, identifier
            if parts:
                movie_id = parts[-1].lower()
                return movie_id, identifier
            return None, None
        movie_id = identifier.strip().lower()
        return movie_id, MOVIE_URL_TEMPLATE.format(movie_id=movie_id)

    def _parse(self, soup: BeautifulSoup, movie_id: str, page_url: str) -> Optional[MovieMetadata]:
        # Title
        title: Optional[str] = None
        h2 = soup.select_one("#main div.contents h2")
        if h2:
            title = h2.get_text(strip=True)

        # Summary (text nodes only, not child elements)
        plot: Optional[str] = None
        summary_el = soup.select_one("#main div.sentence")
        if summary_el:
            texts = []
            for child in summary_el.children:
                if isinstance(child, NavigableString):
                    t = child.strip()
                    if t:
                        texts.append(t)
            plot = " ".join(texts) if texts else summary_el.get_text(strip=True)

        # Cover + Thumbnail from package images
        cover: Optional[str] = None
        thumbnail: Optional[str] = None
        for a in soup.select("li.package a"):
            href = a.get("href")
            if not href:
                continue
            href = self._abs(str(href), page_url)
            if "jacket" in href or href.endswith("L.jpg"):
                cover = href
            elif "package" in href or href.endswith("v.jpg") or href.endswith("vb.jpg"):
                thumbnail = href

        # Cover fallback from video poster
        if not cover:
            video_el = soup.select_one("div.flowplayer video")
            if video_el and video_el.get("poster"):
                cover = self._abs(str(video_el["poster"]), page_url)

        if not thumbnail:
            thumbnail = cover
        if not cover:
            cover = thumbnail

        # Preview images
        backdrops: List[str] = []
        for a in soup.select('a[rel="cap"]'):
            href = a.get("href")
            if href:
                backdrops.append(self._abs(str(href), page_url))

        # Fields from dl (dt/dd pairs)
        number: Optional[str] = None
        premiered: Optional[str] = None
        runtime: Optional[int] = None
        serial: Optional[str] = None
        label: Optional[str] = None
        actors: List[str] = []
        tags: List[str] = []

        for dl in soup.select("#main div.infowrapper dl"):
            dts = dl.find_all("dt")
            dds = dl.find_all("dd")
            for dt_el, dd_el in zip(dts, dds):
                key = dt_el.get_text(strip=True)
                if key in ("出演者", "Model"):
                    for a in dd_el.find_all("a"):
                        name = a.get_text(strip=True)
                        if name and name != "不明":
                            actors.append(name)
                elif key in ("プレイ内容", "タグ", "Play", "Tags"):
                    for a in dd_el.find_all("a"):
                        tag = a.get_text(strip=True)
                        if tag and tag not in tags:
                            tags.append(tag)
                elif key in ("シリーズ", "Theme"):
                    serial = dd_el.get_text(strip=True) or None
                elif key in ("レーベル", "Label"):
                    label = dd_el.get_text(strip=True) or None
                elif key in ("配信開始日", "Release Date"):
                    premiered = self._parse_date(dd_el.get_text(strip=True))
                elif key in ("収録時間", "Duration"):
                    runtime = self._parse_runtime(dd_el.get_text(strip=True))
                elif key in ("作品番号", "Product ID"):
                    number = dd_el.get_text(strip=True)

        display_code = number or movie_id

        metadata = (
            MetadataBuilder()
            .set_title(title or "", display_code)
            .set_identifier(SITE_NAME, display_code, page_url)
            .set_actors(actors)
            .set_studio("TOKYO-HOT")
            .set_serial(serial)
            .set_tags(tags)
            .set_release_date(premiered)
            .set_runtime(runtime)
            .set_cover(cover)
            .set_thumbnail(thumbnail)
            .set_backdrops(backdrops)
            .set_plot(plot)
            .build()
        )
        if label:
            metadata.tagline = label
        metadata.official_rating = "JP-18+"
        self.logger.info(f"成功提取元数据: {display_code}")
        return metadata

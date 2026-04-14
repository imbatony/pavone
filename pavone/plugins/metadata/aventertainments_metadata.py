"""
AVEntertainments 元数据提取器插件

参考: D:\\code\\metatube-sdk-go-main\\provider\\aventertainments\\aventertainments.go
支持的 URL 模式:
  - https://www.aventertainments.com/dvd/detail?pro={id}&lang=2&culture=ja-JP&cat=29
站点: aventertainments.com
"""

import re
from typing import List, Optional
from urllib.parse import parse_qs, urlparse

from bs4 import BeautifulSoup

from ...models import MovieMetadata
from ...utils.metadata_builder import MetadataBuilder
from .base import HtmlMetadataPlugin

PLUGIN_NAME = "AvEntertainmentsMetadata"
PLUGIN_VERSION = "1.0.0"
PLUGIN_DESCRIPTION = "提取 aventertainments.com 的视频元数据"
PLUGIN_AUTHOR = "PAVOne"
PLUGIN_PRIORITY = 50

SUPPORTED_DOMAINS = ["aventertainments.com", "www.aventertainments.com"]
SITE_NAME = "AVEntertainments"

MOVIE_URL_TEMPLATE = "https://www.aventertainments.com/dvd/detail?pro={id}&lang=2&culture=ja-JP&cat=29"


class AvEntertainmentsMetadata(HtmlMetadataPlugin):
    """aventertainments.com 元数据提取器，通过 HTML 页面解析获取数据。"""

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
        # 纯数字 ID (是 aventertainments 内部 pro 参数)
        return bool(re.match(r"^\d+$", identifier.strip()))

    def _resolve(self, identifier: str):
        """返回 (product_id, page_url)。"""
        if identifier.startswith("http://") or identifier.startswith("https://"):
            parsed = urlparse(identifier)
            qs = parse_qs(parsed.query)
            pid = qs.get("pro", [None])[0] or qs.get("product_id", [None])[0]
            if not pid:
                # 旧格式: /NNNN/NNNN/NNNN/product_lists
                m = re.search(r"^/(\d+)/\d+/\d+/product_lists", parsed.path)
                if m:
                    pid = m.group(1)
            return pid, identifier
        # 纯数字
        s = identifier.strip()
        if re.match(r"^\d+$", s):
            return s, MOVIE_URL_TEMPLATE.format(id=s)
        return None, None

    def _parse(self, soup: BeautifulSoup, movie_id: str, page_url: str) -> Optional[MovieMetadata]:
        # Title
        title_tag = soup.select_one("#MyBody .section-title h3")
        title = title_tag.get_text(strip=True) if title_tag else ""

        # Cover + Thumb
        cover: Optional[str] = None
        thumbnail: Optional[str] = None
        cover_tag = soup.select_one("#PlayerCover img")
        if cover_tag and cover_tag.get("src"):
            src = str(cover_tag["src"])
            cover = self._abs(src, page_url)
            thumbnail = cover.replace("bigcover", "jacket_images") if "bigcover" in cover else cover

        # Fallback: og:image
        if not cover:
            og_img = soup.find("meta", property="og:image")
            if og_img and og_img.get("content"):
                cover = self._abs(str(og_img["content"]), page_url)
                thumbnail = cover

        # Preview images
        backdrops: List[str] = []
        for a in soup.select(".gallery-block.grid-gallery a.lightbox"):
            href = a.get("href")
            if href:
                backdrops.append(self._abs(str(href), page_url))

        # Fields table
        actors: List[str] = []
        studio: Optional[str] = None
        serial: Optional[str] = None
        tags: List[str] = []
        premiered: Optional[str] = None
        runtime: Optional[int] = None
        code: Optional[str] = None

        for row in soup.select("#MyBody .product-info-block-rev.mt-20 .single-info"):
            spans = row.find_all("span")
            if len(spans) < 2:
                continue
            key = spans[0].get_text(strip=True)
            val_span = spans[1]
            val = val_span.get_text(" ", strip=True)
            if key == "商品番号":
                code = val.strip()
            elif key == "主演女優":
                actors = [a.strip() for a in val.split() if a.strip()]
            elif key == "スタジオ":
                studio = val.strip()
            elif key == "シリーズ":
                serial = val.strip() or None
            elif key == "カテゴリ":
                tags = [t.strip() for t in val.split() if t.strip()]
            elif key == "発売日":
                premiered = self._parse_date(val)
            elif key == "収録時間":
                runtime = self._parse_runtime(val)

        display_code = code or movie_id

        builder = (
            MetadataBuilder()
            .set_title(title, display_code)
            .set_identifier(SITE_NAME, display_code, page_url)
            .set_actors(actors)
            .set_studio(studio)
            .set_serial(serial)
            .set_tags(tags)
            .set_release_date(premiered)
            .set_runtime(runtime)
            .set_cover(cover)
            .set_thumbnail(thumbnail)
            .set_backdrops(backdrops)
        )
        metadata = builder.build()
        metadata.official_rating = "JP-18+"
        self.logger.info(f"成功提取元数据: {display_code}")
        return metadata

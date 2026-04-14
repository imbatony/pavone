"""
JAV321 元数据提取器插件

参考: D:\\code\\metatube-sdk-go-main\\provider\\jav321\\jav321.go
支持的 URL 模式: https://www.jav321.com/video/{id}
ID 格式: 品番码 (如 ABP-123)
通过 HTML 页面解析获取元数据。
"""

import re
from typing import List, Optional
from urllib.parse import urlparse

from bs4 import BeautifulSoup, NavigableString

from ...models import MovieMetadata
from ...utils.metadata_builder import MetadataBuilder
from .base import HtmlMetadataPlugin

PLUGIN_NAME = "Jav321Metadata"
PLUGIN_VERSION = "1.0.0"
PLUGIN_DESCRIPTION = "提取 jav321.com 的视频元数据"
PLUGIN_AUTHOR = "PAVOne"
PLUGIN_PRIORITY = 50

SUPPORTED_DOMAINS = ["jav321.com", "www.jav321.com"]
SITE_NAME = "JAV321"

MOVIE_URL_TEMPLATE = "https://www.jav321.com/video/{movie_id}"


class Jav321Metadata(HtmlMetadataPlugin):
    """jav321.com 元数据提取器，通过 HTML 页面 (聚合数据库) 解析获取数据。"""

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
        return bool(re.match(r"^[a-zA-Z]+-\d+$", identifier.strip()))

    def _resolve(self, identifier: str):
        if identifier.startswith("http://") or identifier.startswith("https://"):
            parsed = urlparse(identifier)
            parts = parsed.path.rstrip("/").split("/")
            if len(parts) >= 3 and parts[-2] == "video":
                movie_id = parts[-1]
                return movie_id, identifier
            return None, None
        movie_id = identifier.strip().upper()
        return movie_id, MOVIE_URL_TEMPLATE.format(movie_id=movie_id)

    def _parse(self, soup: BeautifulSoup, movie_id: str, page_url: str) -> Optional[MovieMetadata]:
        # Title
        title: Optional[str] = None
        h3 = soup.select_one("div.panel-heading h3")
        if h3:
            for child in h3.children:
                if isinstance(child, NavigableString):
                    t = child.strip()
                    if t:
                        title = t
                        break

        # Summary
        plot: Optional[str] = None
        for div in soup.select("div.panel-body div.row div.col-md-12"):
            text = div.get_text(strip=True)
            if text and len(text) > 10:
                plot = text
                break

        # Thumbnail
        thumbnail: Optional[str] = None
        thumb_img = soup.select_one("div.panel-body div.row div.col-md-3 img")
        if thumb_img and thumb_img.get("src"):
            thumbnail = self._abs(str(thumb_img["src"]), page_url)

        # Cover + preview images
        cover: Optional[str] = None
        backdrops: List[str] = []
        for img in soup.select("div.col-xs-12.col-md-12 p a img.img-responsive"):
            src = img.get("src")
            if src:
                src = self._abs(str(src), page_url)
                if not cover:
                    cover = src
                else:
                    backdrops.append(src)

        # Actors
        actors: List[str] = []
        for a in soup.select('div.thumbnail a[href*="/star/"]'):
            name = a.get_text(strip=True)
            if name:
                actors.append(name)

        # Fields from <b> tags
        number: Optional[str] = None
        premiered: Optional[str] = None
        runtime: Optional[int] = None
        serial: Optional[str] = None
        maker: Optional[str] = None
        tags: List[str] = []
        rating: Optional[float] = None

        for b_tag in soup.find_all("b"):
            label = b_tag.get_text(strip=True)
            if "品番" in label:
                next_node = b_tag.next_sibling
                if next_node and isinstance(next_node, NavigableString):
                    number = next_node.strip().lstrip(":").strip().upper()
                else:
                    a = b_tag.find_next_sibling("a")
                    if a:
                        number = a.get_text(strip=True).upper()
            elif "配信開始日" in label:
                next_node = b_tag.next_sibling
                if next_node and isinstance(next_node, NavigableString):
                    premiered = self._parse_date(next_node.strip().lstrip(":"))
            elif "収録時間" in label:
                next_node = b_tag.next_sibling
                if next_node and isinstance(next_node, NavigableString):
                    runtime = self._parse_runtime(next_node.strip().lstrip(":"))
            elif "シリーズ" in label:
                a = b_tag.find_next_sibling("a")
                if a and "/series" in (a.get("href") or ""):
                    serial = a.get_text(strip=True)
            elif "メーカー" in label:
                a = b_tag.find_next_sibling("a")
                if a and "/company" in (a.get("href") or ""):
                    maker = a.get_text(strip=True)
            elif "ジャンル" in label:
                for a in b_tag.find_next_siblings("a"):
                    if "/genre" in (a.get("href") or ""):
                        tags.append(a.get_text(strip=True))
            elif "出演者" in label and not actors:
                for a in b_tag.find_next_siblings("a"):
                    if "/star" in (a.get("href") or ""):
                        actors.append(a.get_text(strip=True))
                if not actors:
                    next_node = b_tag.next_sibling
                    if next_node and isinstance(next_node, NavigableString):
                        name = next_node.strip().lstrip(":").strip()
                        if name:
                            actors.append(name)
            elif "平均評価" in label:
                img = b_tag.find_next_sibling("img")
                if img and img.get("data-original"):
                    m = re.search(r"(\d+)\.gif", str(img["data-original"]))
                    if m:
                        rating = float(m.group(1)) / 10.0
                if rating is None:
                    next_node = b_tag.next_sibling
                    if next_node and isinstance(next_node, NavigableString):
                        val = next_node.strip().lstrip(":")
                        try:
                            rating = float(val)
                        except ValueError:
                            pass

        display_code = number or movie_id.upper()

        metadata = (
            MetadataBuilder()
            .set_title(title or "", display_code)
            .set_identifier(SITE_NAME, display_code, page_url)
            .set_actors(actors)
            .set_studio(maker)
            .set_serial(serial)
            .set_tags(tags)
            .set_release_date(premiered)
            .set_runtime(runtime)
            .set_cover(cover)
            .set_thumbnail(thumbnail)
            .set_backdrops(backdrops)
            .set_plot(plot)
            .set_rating(rating)
            .build()
        )
        metadata.official_rating = "JP-18+"
        self.logger.info(f"成功提取元数据: {display_code}")
        return metadata

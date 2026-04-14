"""
FC2HUB (javten.com) 元数据提取器插件

参考: D:\\code\\metatube-sdk-go-main\\provider\\fc2hub\\fc2hub.go
支持的 URL 模式: https://javten.com/video/{seller_id}/id{content_id}/
ID 格式: {seller_id}-{content_id}
通过 JSON-LD + HTML 解析获取元数据。
"""

import re
from typing import Any, Dict, List, Optional
from urllib.parse import urlparse

from bs4 import BeautifulSoup

from ...models import MovieMetadata
from ...utils.metadata_builder import MetadataBuilder
from .base import JsonLdMetadataPlugin

PLUGIN_NAME = "Fc2HubMetadata"
PLUGIN_VERSION = "1.0.0"
PLUGIN_DESCRIPTION = "提取 javten.com (fc2hub) 的视频元数据"
PLUGIN_AUTHOR = "PAVOne"
PLUGIN_PRIORITY = 49  # slightly lower than FC2 direct

SUPPORTED_DOMAINS = ["javten.com", "www.javten.com", "fc2hub.com", "www.fc2hub.com"]
SITE_NAME = "FC2HUB"

MOVIE_URL_TEMPLATE = "https://javten.com/video/{seller_id}/id{content_id}/"


class Fc2HubMetadata(JsonLdMetadataPlugin):
    """javten.com (fc2hub) 元数据提取器。"""

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
        # ID format: seller_id-content_id (e.g. "1152468-2725031")
        return bool(re.match(r"^\d+-\d+$", identifier.strip()))

    def _resolve(self, identifier: str):
        if identifier.startswith("http://") or identifier.startswith("https://"):
            parsed = urlparse(identifier)
            m = re.search(r"/video/(\d+)/id(\d+)", parsed.path)
            if m:
                dual_id = f"{m.group(1)}-{m.group(2)}"
                return dual_id, identifier
            return None, None
        parts = identifier.strip().split("-")
        if len(parts) == 2 and parts[0].isdigit() and parts[1].isdigit():
            return identifier.strip(), MOVIE_URL_TEMPLATE.format(seller_id=parts[0], content_id=parts[1])
        return None, None

    def _parse_with_jsonld(
        self, soup: BeautifulSoup, jsonld: Optional[Dict[str, Any]], movie_id: str, page_url: str
    ) -> Optional[MovieMetadata]:
        title: Optional[str] = None
        cover: Optional[str] = None
        plot: Optional[str] = None
        premiered: Optional[str] = None
        runtime: Optional[int] = None
        actors: List[str] = []
        maker: Optional[str] = None
        tags: List[str] = []
        fc2_number: Optional[str] = None
        backdrops: List[str] = []

        if jsonld:
            data = jsonld
            title = data.get("name") or title
            plot = data.get("description") or plot
            if data.get("image"):
                cover = data["image"]
            if data.get("datePublished"):
                premiered = self._parse_date(data["datePublished"])
            if data.get("duration"):
                runtime = self._parse_iso_duration(data["duration"])
            actor_list = data.get("actor") or []
            if isinstance(actor_list, list):
                actors = [a if isinstance(a, str) else a.get("name", "") for a in actor_list if a]
            elif isinstance(actor_list, str):
                actors = [actor_list]

        # HTML fallback: title from h1
        if not title:
            h1 = soup.select_one("#content h1")
            if h1:
                title = h1.get_text(strip=True)

        # FC2 number from content area
        h1_el = soup.select_one("#content h1")
        if h1_el:
            num_text = h1_el.get_text(strip=True)
            m = re.search(r"FC2[- ]?(?:PPV[- ]?)?(\d+)", num_text, re.IGNORECASE)
            if m:
                fc2_number = f"FC2-{m.group(1)}"

        # Genres from tag links
        for a in soup.select("#content p a"):
            text = a.get_text(strip=True)
            if text and len(text) < 30:
                tags.append(text)

        # Maker from seller info area
        seller_el = soup.select_one("#content .seller-name, #content .maker-name")
        if seller_el:
            maker = seller_el.get_text(strip=True)

        # Preview images
        for a in soup.select('a[data-fancybox="gallery"]'):
            href = a.get("href")
            if href:
                href_str = str(href)
                backdrops.append(
                    href_str if href_str.startswith("http") else f"https:{href_str}" if href_str.startswith("//") else href_str
                )

        display_code = fc2_number or f"FC2-{movie_id.split('-')[-1]}"

        metadata = (
            MetadataBuilder()
            .set_title(title or "", display_code)
            .set_identifier(SITE_NAME, display_code, page_url)
            .set_actors(actors)
            .set_studio(maker)
            .set_tags(tags)
            .set_release_date(premiered)
            .set_runtime(runtime)
            .set_cover(cover)
            .set_thumbnail(cover)
            .set_backdrops(backdrops)
            .set_plot(plot)
            .build()
        )
        metadata.official_rating = "JP-18+"
        self.logger.info(f"成功提取元数据: {display_code}")
        return metadata

"""
DAHLIA 元数据提取器插件

参考: D:\\code\\metatube-sdk-go-main\\provider\\dahlia\\dahlia.go
      D:\\code\\metatube-sdk-go-main\\provider\\dahlia\\core\\core.go
支持的 URL 模式: https://dahlia-av.jp/works/{movie_id}/
通过 HTML 页面解析获取元数据。
"""

from typing import List, Optional
from urllib.parse import urlparse

import requests
from bs4 import BeautifulSoup

from ...models import MovieMetadata
from ...utils.metadata_builder import MetadataBuilder
from .base import HtmlMetadataPlugin

PLUGIN_NAME = "DahliaMetadata"
PLUGIN_VERSION = "1.0.0"
PLUGIN_DESCRIPTION = "提取 dahlia-av.jp 的视频元数据"
PLUGIN_AUTHOR = "PAVOne"
PLUGIN_PRIORITY = 50

SUPPORTED_DOMAINS = ["dahlia-av.jp", "www.dahlia-av.jp"]
SITE_NAME = "DAHLIA"

MOVIE_URL_TEMPLATE = "https://dahlia-av.jp/works/{movie_id}/"


class DahliaMetadata(HtmlMetadataPlugin):
    """dahlia-av.jp 元数据提取器，通过 HTML 页面解析获取数据。"""

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
        return False  # 无独立番号格式，必须提供 URL

    def _fetch_page(self, url: str) -> requests.Response:
        """跳过年龄弹窗（参考 Go 核心层）"""
        return self.fetch(url, headers={"Cookie": "modal=off"}, timeout=30)

    def _resolve(self, identifier: str):
        if identifier.startswith("http://") or identifier.startswith("https://"):
            parsed = urlparse(identifier)
            parts = [p for p in parsed.path.split("/") if p]
            # /works/{movie_id}/
            if "works" in parts:
                idx = parts.index("works")
                if idx + 1 < len(parts):
                    return parts[idx + 1].lower(), identifier
        return None, None

    def _parse(self, soup: BeautifulSoup, movie_id: str, page_url: str) -> Optional[MovieMetadata]:
        # Title
        title: Optional[str] = None
        for sel in [".bar02_works h1", ".bar02 h1"]:
            t = soup.select_one(sel)
            if t:
                title = t.get_text(strip=True)
                break

        # Cover
        cover: Optional[str] = None
        cover_tag = soup.select_one(".box_works01_img a img")
        if cover_tag and cover_tag.get("src"):
            src = str(cover_tag["src"]).split("?")[0]
            cover = self._abs(src, page_url)

        # Preview images
        backdrops: List[str] = []
        for a in soup.select(".box_works01_ga li a"):
            href = a.get("href")
            if href:
                backdrops.append(self._abs(str(href), page_url))

        # Plot
        plot: Optional[str] = None
        plot_tag = soup.select_one(".box_works01_text")
        if plot_tag:
            text = plot_tag.get_text("\n", strip=True)
            if text:
                plot = text

        # Fields
        actors: List[str] = []
        runtime: Optional[int] = None
        premiered: Optional[str] = None

        for item in soup.select("div[class*='box_works01_list'] ul > *"):
            label = item.select_one("span")
            value = item.select_one("p")
            if not label or not value:
                continue
            key = label.get_text(strip=True)
            val = value.get_text(strip=True)
            if key == "出演女優":
                actors = [a.strip() for a in val.split("/") if a.strip()]
            elif key == "収録時間":
                runtime = self._parse_runtime(val)
            elif key in ("配信開始日", "配信日"):
                premiered = self._parse_date(val)
            elif key == "発売日" and not premiered:
                premiered = self._parse_date(val)

        code = movie_id.lower()

        metadata = (
            MetadataBuilder()
            .set_title(title or "", code)
            .set_identifier(SITE_NAME, code, page_url)
            .set_actors(actors)
            .set_studio(SITE_NAME)
            .set_release_date(premiered)
            .set_runtime(runtime)
            .set_cover(cover)
            .set_thumbnail(cover)
            .set_backdrops(backdrops)
            .set_plot(plot)
            .build()
        )
        metadata.official_rating = "JP-18+"
        self.logger.info(f"成功提取元数据: {code}")
        return metadata

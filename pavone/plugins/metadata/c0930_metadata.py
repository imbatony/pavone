"""
C0930 元数据提取器插件

参考: D:\\code\\metatube-sdk-go-main\\provider\\c0930\\c0930.go
      D:\\code\\metatube-sdk-go-main\\provider\\h0930\\core\\core.go
支持的 URL 模式: https://www.c0930.com/moviepages/{movie_id}/index.html
ID 格式: 小写字母+数字 (如 ki230101)
通过 JSON-LD 与 HTML 解析获取元数据。
"""

import re
from typing import Any, Dict, List, Optional
from urllib.parse import urlparse

from bs4 import BeautifulSoup

from ...models import MovieMetadata
from ...utils.metadata_builder import MetadataBuilder
from .base import JsonLdMetadataPlugin

PLUGIN_NAME = "C0930Metadata"
PLUGIN_VERSION = "1.0.0"
PLUGIN_DESCRIPTION = "提取 c0930.com 的视频元数据"
PLUGIN_AUTHOR = "PAVOne"
PLUGIN_PRIORITY = 50

SUPPORTED_DOMAINS = ["c0930.com", "www.c0930.com"]
SITE_NAME = "C0930"
DEFAULT_MAKER = "人妻斬り"

MOVIE_URL_TEMPLATE = "https://www.c0930.com/moviepages/{movie_id}/index.html"
MOVIE_ID_RE = re.compile(r"^(?:c0930[-_])?([a-z\d]+)$", re.IGNORECASE)


class C0930Metadata(JsonLdMetadataPlugin):
    """c0930.com 元数据提取器，通过 JSON-LD + HTML 解析获取数据。"""

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
        return bool(MOVIE_ID_RE.match(identifier.strip()))

    def _resolve(self, identifier: str):
        if identifier.startswith("http://") or identifier.startswith("https://"):
            parsed = urlparse(identifier)
            # /moviepages/{movie_id}/index.html
            m = re.search(r"/moviepages/([^/]+)/", parsed.path)
            movie_id = m.group(1).lower() if m else None
            return movie_id, identifier
        m = MOVIE_ID_RE.match(identifier.strip())
        if m:
            movie_id = m.group(1).lower()
            return movie_id, MOVIE_URL_TEMPLATE.format(movie_id=movie_id)
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
        maker: Optional[str] = DEFAULT_MAKER
        rating: Optional[float] = None

        if jsonld:
            data = jsonld
            title = data.get("name") or title
            plot = data.get("description") or plot
            if data.get("image"):
                img_url = data["image"]
                if img_url.startswith("//"):
                    img_url = "https:" + img_url
                cover = img_url
            video = data.get("video") or {}
            runtime = self._parse_iso_duration(video.get("duration", ""))
            actor_name = video.get("actor", "") or (data.get("actor") or {}).get("name", "")
            if actor_name:
                actors = [actor_name]
            if video.get("provider"):
                maker = video["provider"]
            released = data.get("releasedEvent") or {}
            start_date = released.get("startDate") or ""
            if start_date:
                premiered = start_date[:10] if len(start_date) >= 10 else start_date
            agg = data.get("aggregateRating") or {}
            if agg.get("ratingValue"):
                try:
                    rating = float(agg["ratingValue"])
                except ValueError:
                    pass

        # HTML fallbacks
        if not title:
            t = soup.select_one("#moviePlay .moviePlay_title h1 span")
            if t:
                title = t.get_text(strip=True)

        # Fields from dl/dt/dd
        for dl in soup.select("#movieInfo section dl"):
            dts = dl.find_all("dt")
            dds = dl.find_all("dd")
            for i, dt in enumerate(dts):
                key = dt.get_text(strip=True)
                val = dds[i].get_text(strip=True) if i < len(dds) else ""
                if key == "動画" and not runtime:
                    runtime = self._parse_iso_duration(val) or runtime
                elif key == "公開日" and not premiered:
                    premiered = self._parse_date(val)

        genres: List[str] = []

        code = f"c0930-{movie_id}"

        metadata = (
            MetadataBuilder()
            .set_title(title or "", code)
            .set_identifier(SITE_NAME, code, page_url)
            .set_actors(actors)
            .set_studio(maker)
            .set_tags(genres)
            .set_release_date(premiered)
            .set_runtime(runtime)
            .set_cover(cover)
            .set_thumbnail(cover)
            .set_plot(plot)
            .set_rating(rating)
            .build()
        )
        metadata.official_rating = "JP-18+"
        self.logger.info(f"成功提取元数据: {code}")
        return metadata

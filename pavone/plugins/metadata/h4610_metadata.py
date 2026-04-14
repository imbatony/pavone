"""
H4610 元数据提取器插件

参考: D:\\code\\metatube-sdk-go-main\\provider\\h4610\\h4610.go
      D:\\code\\metatube-sdk-go-main\\provider\\h0930\\core\\core.go
支持的 URL 模式: https://www.h4610.com/moviepages/{movie_id}/index.html
与 C0930/H0930 共享同一套 core 解析逻辑（JSON-LD + dl/dt/dd）。
"""

import json
import re
from typing import List, Optional
from urllib.parse import urlparse

import requests
from bs4 import BeautifulSoup

from ...models import MovieMetadata
from ...utils.metadata_builder import MetadataBuilder
from .base import MetadataPlugin

PLUGIN_NAME = "H4610Metadata"
PLUGIN_VERSION = "1.0.0"
PLUGIN_DESCRIPTION = "提取 h4610.com 的视频元数据"
PLUGIN_AUTHOR = "PAVOne"
PLUGIN_PRIORITY = 50

SUPPORTED_DOMAINS = ["h4610.com", "www.h4610.com"]
SITE_NAME = "H4610"
DEFAULT_MAKER = "エッチな4610"

MOVIE_URL_TEMPLATE = "https://www.h4610.com/moviepages/{movie_id}/index.html"
MOVIE_ID_RE = re.compile(r"^(?:h4610[-_])?([a-z\d]+)$", re.IGNORECASE)


class H4610Metadata(MetadataPlugin):
    """h4610.com 元数据提取器（与 C0930/H0930 同一 core 结构）。"""

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

    def extract_metadata(self, identifier: str) -> Optional[MovieMetadata]:
        try:
            movie_id, page_url = self._resolve(identifier)
            if not movie_id or not page_url:
                self.logger.error(f"无法解析 identifier: {identifier}")
                return None

            resp = self.fetch(page_url, timeout=30)
            soup = BeautifulSoup(resp.text, "lxml")
            return self._parse(soup, movie_id, page_url)
        except requests.RequestException as e:
            self.logger.error(f"HTTP 请求失败: {e}")
            return None
        except Exception as e:
            self.logger.error(f"提取元数据失败: {e}", exc_info=True)
            return None

    def _resolve(self, identifier: str):
        if identifier.startswith("http://") or identifier.startswith("https://"):
            m = re.search(r"/moviepages/([^/]+)/?", urlparse(identifier).path)
            if m:
                movie_id = m.group(1).lower()
                return movie_id, identifier
            return None, None
        match = MOVIE_ID_RE.match(identifier.strip())
        if match:
            movie_id = match.group(1).lower()
            return movie_id, MOVIE_URL_TEMPLATE.format(movie_id=movie_id)
        return None, None

    def _parse(self, soup: BeautifulSoup, movie_id: str, page_url: str) -> Optional[MovieMetadata]:
        title: Optional[str] = None
        cover: Optional[str] = None
        plot: Optional[str] = None
        premiered: Optional[str] = None
        runtime: Optional[int] = None
        actors: List[str] = []
        maker: Optional[str] = DEFAULT_MAKER
        rating: Optional[float] = None

        for script in soup.find_all("script", type="application/ld+json"):
            try:
                data = json.loads((script.string or "").replace("\n", ""))
                if isinstance(data, list):
                    data = data[0]
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
            except Exception:
                pass

        if not title:
            t = soup.select_one("#moviePlay .moviePlay_title h1 span")
            if t:
                title = t.get_text(strip=True)

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

        code = f"h4610-{movie_id}"

        metadata = (
            MetadataBuilder()
            .set_title(title or "", code)
            .set_identifier(SITE_NAME, code, page_url)
            .set_actors(actors)
            .set_studio(maker)
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

    @staticmethod
    def _parse_iso_duration(s: str) -> Optional[int]:
        if not s:
            return None
        m = re.match(r"PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?", s)
        if m:
            h = int(m.group(1) or 0)
            mins = int(m.group(2) or 0)
            return h * 60 + mins if (h or mins) else None
        m2 = re.match(r"(\d+):(\d+)", s.strip())
        if m2:
            return int(m2.group(1)) * 60 + int(m2.group(2))
        return None

    @staticmethod
    def _parse_date(s: str) -> Optional[str]:
        m = re.match(r"(\d{4})[/\-.](\d{1,2})[/\-.](\d{1,2})", s.strip())
        if m:
            return f"{m.group(1)}-{int(m.group(2)):02d}-{int(m.group(3)):02d}"
        return None

"""
Pacopacomama (パコパコママ) 元数据提取器插件

参考: D:\\code\\metatube-sdk-go-main\\provider\\pacopacomama\\pacopacomama.go
支持的 URL 模式: https://www.pacopacomama.com/movies/{id}/
ID 格式: DDDDDD_DDD (如 011215_178)
通过 JSON API 获取元数据（与 1pondo 相同的 Core API 结构）。
"""

import re
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import urlparse

import requests

from ...models import MovieMetadata
from ...utils.metadata_builder import MetadataBuilder
from .base import ApiMetadataPlugin

PLUGIN_NAME = "PacopacomamaMetadata"
PLUGIN_VERSION = "1.0.0"
PLUGIN_DESCRIPTION = "提取 pacopacomama.com 的视频元数据"
PLUGIN_AUTHOR = "PAVOne"
PLUGIN_PRIORITY = 50

SUPPORTED_DOMAINS = ["pacopacomama.com", "www.pacopacomama.com"]
SITE_NAME = "Pacopacomama"

MOVIE_ID_PATTERN = r"\d{6}_\d{3}"
API_URL_TEMPLATE = "https://www.pacopacomama.com/dyn/phpauto/movie_details/movie_id/{movie_id}.json"
MOVIE_URL_TEMPLATE = "https://www.pacopacomama.com/movies/{movie_id}/"


class PacopacomamaMetadata(ApiMetadataPlugin):
    """pacopacomama.com (パコパコママ) 元数据提取器，通过 JSON API 获取数据。"""

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
        return bool(re.match(rf"^{MOVIE_ID_PATTERN}$", identifier.strip()))

    def _fetch_api(self, url: str) -> requests.Response:
        return self.fetch(
            url,
            timeout=30,
            headers={
                "Content-Type": "application/json",
                "Connection": "keep-alive",
            },
        )

    def _build_api_url(self, movie_id: str) -> str:
        return API_URL_TEMPLATE.format(movie_id=movie_id)

    def _resolve(self, identifier: str) -> Tuple[Optional[str], Optional[str]]:
        if identifier.startswith("http://") or identifier.startswith("https://"):
            parsed = urlparse(identifier)
            m = re.search(rf"/movies/({MOVIE_ID_PATTERN})/?", parsed.path)
            if m:
                return m.group(1), identifier
            parts = parsed.path.strip("/").split("/")
            if parts:
                movie_id = parts[-1]
                if re.match(rf"^{MOVIE_ID_PATTERN}$", movie_id):
                    return movie_id, identifier
            return None, None
        movie_id = identifier.strip()
        if re.match(rf"^{MOVIE_ID_PATTERN}$", movie_id):
            return movie_id, MOVIE_URL_TEMPLATE.format(movie_id=movie_id)
        return None, None

    def _parse(self, data: Dict[str, Any], movie_id: str, page_url: str) -> Optional[MovieMetadata]:
        if not data:
            return None

        title = data.get("Title", "")
        actors: List[str] = data.get("ActressesJa") or []
        tags: List[str] = data.get("UCNAME") or []
        plot = data.get("Desc")
        release_date = data.get("Release")

        # Duration (seconds → minutes)
        runtime: Optional[int] = None
        duration = data.get("Duration")
        if duration and isinstance(duration, (int, float)):
            runtime = round(duration / 60)

        # Rating (5-point → 10-point)
        rating: Optional[float] = None
        avg = data.get("AvgRating")
        if avg is not None:
            try:
                rating = round(float(avg) * 2, 1)
            except (ValueError, TypeError):
                pass

        # Cover
        cover = data.get("ThumbUltra") or data.get("ThumbHigh") or data.get("ThumbMed") or data.get("ThumbLow")
        thumbnail = data.get("MovieThumb") or cover

        # Backdrops
        backdrops = [f"https://www.pacopacomama.com/dyn/dla/images/{movie_id}/{n}.jpg" for n in range(1, 4)]

        metadata = (
            MetadataBuilder()
            .set_title(title, movie_id)
            .set_identifier(SITE_NAME, movie_id, page_url)
            .set_actors(actors)
            .set_studio("パコパコママ")
            .set_tags(tags)
            .set_release_date(release_date)
            .set_runtime(runtime)
            .set_cover(cover)
            .set_thumbnail(thumbnail)
            .set_backdrops(backdrops)
            .set_plot(plot)
            .set_rating(rating)
            .build()
        )
        metadata.official_rating = "JP-18+"
        self.logger.info(f"成功提取元数据: {movie_id}")
        return metadata

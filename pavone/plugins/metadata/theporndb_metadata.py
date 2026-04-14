"""
ThePornDB 元数据提取器插件

参考: D:\\code\\metatube-sdk-go-main\\provider\\theporndb\\theporndb.go
支持的 URL 模式: https://theporndb.net/scenes/{slug}
ID 格式: slug (如 bbc-slut-training-camp-4-scene-1)
通过 REST API (api.theporndb.net) 获取元数据。需要 API Key。
注意: 默认禁用，需配置 API access token。
"""

import re
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import urlparse

import requests

from ...models import BaseMetadata, MovieMetadata
from ...utils.metadata_builder import MetadataBuilder
from .base import ApiMetadataPlugin

PLUGIN_NAME = "ThePorndbMetadata"
PLUGIN_VERSION = "1.0.0"
PLUGIN_DESCRIPTION = "提取 theporndb.net 的视频元数据 (需要 API Key)"
PLUGIN_AUTHOR = "PAVOne"
PLUGIN_PRIORITY = 0  # Disabled by default

SUPPORTED_DOMAINS = ["theporndb.net", "api.theporndb.net"]
SITE_NAME = "ThePornDB"

API_URL_TEMPLATE = "https://api.theporndb.net/scenes/{slug}"
PAGE_URL_TEMPLATE = "https://theporndb.net/scenes/{slug}"


class ThePorndbMetadata(ApiMetadataPlugin):
    """theporndb.net 元数据提取器，通过 REST API 获取数据。需要配置 API token。"""

    def __init__(self):
        super().__init__(
            name=PLUGIN_NAME,
            version=PLUGIN_VERSION,
            description=PLUGIN_DESCRIPTION,
            author=PLUGIN_AUTHOR,
            priority=PLUGIN_PRIORITY,
        )
        self._access_token: Optional[str] = None

    def initialize(self) -> bool:
        """初始化插件，读取 API token 配置。"""
        self.logger.info(f"初始化 {self.name} 插件")
        if hasattr(self, "config") and self.config:
            self._access_token = getattr(self.config, "access_token", None) or getattr(self.config, "api_key", None)
        return True

    def can_extract(self, identifier: str) -> bool:
        if identifier.startswith("http://") or identifier.startswith("https://"):
            return self.can_handle_domain(identifier, SUPPORTED_DOMAINS)
        # Slug format: alphanumeric with dashes
        return bool(re.match(r"^[a-zA-Z0-9][-a-zA-Z0-9]+$", identifier.strip()))

    def extract_metadata(self, identifier: str) -> Optional[BaseMetadata]:
        if not self._access_token:
            self.logger.warning("ThePornDB 需要配置 API access_token")
            return None
        return super().extract_metadata(identifier)

    def _fetch_api(self, url: str) -> requests.Response:
        return self.fetch(url, timeout=30, headers={"Authorization": f"Bearer {self._access_token}"})

    def _build_api_url(self, movie_id: str) -> str:
        return API_URL_TEMPLATE.format(slug=movie_id)

    def _resolve(self, identifier: str) -> Tuple[Optional[str], Optional[str]]:
        if identifier.startswith("http://") or identifier.startswith("https://"):
            parsed = urlparse(identifier)
            parts = parsed.path.strip("/").split("/")
            if parts:
                slug = parts[-1]
                return slug, identifier
            return None, None
        slug = identifier.strip()
        return slug, PAGE_URL_TEMPLATE.format(slug=slug)

    def _parse(self, data: Dict[str, Any], movie_id: str, page_url: str) -> Optional[MovieMetadata]:
        inner_data = data.get("data", data)
        if not inner_data:
            return None

        title = inner_data.get("title", "")
        plot = inner_data.get("description")
        cover = inner_data.get("image")
        thumbnail = inner_data.get("poster") or cover
        trailer = inner_data.get("trailer")

        # Rating
        rating: Optional[float] = None
        if inner_data.get("rating") is not None:
            try:
                rating = float(inner_data["rating"])
            except (ValueError, TypeError):
                pass

        # Release date
        premiered = inner_data.get("date")

        # Runtime
        runtime: Optional[int] = None
        if inner_data.get("duration"):
            try:
                runtime = int(inner_data["duration"])
            except (ValueError, TypeError):
                pass

        # Maker
        maker = None
        site = inner_data.get("site")
        if isinstance(site, dict):
            maker = site.get("name")

        # Tags
        tags: List[str] = []
        for tag in inner_data.get("tags") or []:
            name = tag.get("name") if isinstance(tag, dict) else str(tag)
            if name:
                tags.append(name)

        # Actors
        actors: List[str] = []
        for performer in inner_data.get("performers") or []:
            name = performer.get("name") if isinstance(performer, dict) else str(performer)
            if name:
                actors.append(name)

        # Director
        director: Optional[str] = None
        directors = inner_data.get("directors") or []
        if directors:
            d = directors[0]
            director = d.get("name") if isinstance(d, dict) else str(d)

        display_code = inner_data.get("slug") or movie_id

        metadata = (
            MetadataBuilder()
            .set_title(title, display_code)
            .set_identifier(SITE_NAME, display_code, page_url)
            .set_actors(actors)
            .set_studio(maker)
            .set_tags(tags)
            .set_release_date(premiered)
            .set_runtime(runtime)
            .set_cover(cover)
            .set_thumbnail(thumbnail)
            .set_plot(plot)
            .set_rating(rating)
            .build()
        )
        if director:
            metadata.director = director
        if trailer:
            metadata.trailer = trailer
        self.logger.info(f"成功提取元数据: {display_code}")
        return metadata

"""
ModelMediaAsia (麻豆傳媒) 元数据提取器插件

参考: D:\\code\\metatube-sdk-go-main\\provider\\modelmediaasia\\modelmediaasia.go
支持的 URL 模式: https://modelmediaasia.com/zh-CN/videos/{id}
ID 格式: 番号 slug (如 mdx-0236)
通过 JSON API 获取元数据。中文站点。
"""

import re
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import urlparse

import requests

from ...models import MovieMetadata
from ...utils.metadata_builder import MetadataBuilder
from .base import ApiMetadataPlugin

PLUGIN_NAME = "ModelMediaAsiaMetadata"
PLUGIN_VERSION = "1.0.0"
PLUGIN_DESCRIPTION = "提取 modelmediaasia.com 的视频元数据"
PLUGIN_AUTHOR = "PAVOne"
PLUGIN_PRIORITY = 50

SUPPORTED_DOMAINS = ["modelmediaasia.com", "www.modelmediaasia.com"]
SITE_NAME = "ModelMediaAsia"

API_URL_TEMPLATE = "https://model-api.bvncmsldo.com/api/v2/videos/{movie_id}"
MOVIE_URL_TEMPLATE = "https://modelmediaasia.com/zh-CN/videos/{movie_id}"


class ModelMediaAsiaMetadata(ApiMetadataPlugin):
    """modelmediaasia.com (麻豆傳媒) 元数据提取器，通过 JSON API 获取数据。"""

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

    def _fetch_api(self, url: str) -> requests.Response:
        return self.fetch(url, timeout=30, headers={"Referer": "https://modelmediaasia.com/"})

    def _build_api_url(self, movie_id: str) -> str:
        return API_URL_TEMPLATE.format(movie_id=movie_id)

    def _resolve(self, identifier: str) -> Tuple[Optional[str], Optional[str]]:
        if identifier.startswith("http://") or identifier.startswith("https://"):
            parsed = urlparse(identifier)
            parts = parsed.path.strip("/").split("/")
            if parts:
                movie_id = parts[-1]
                return movie_id, identifier
            return None, None
        movie_id = identifier.strip()
        return movie_id, MOVIE_URL_TEMPLATE.format(movie_id=movie_id)

    def _parse(self, resp_data: Dict[str, Any], movie_id: str, page_url: str) -> Optional[MovieMetadata]:
        data = resp_data.get("data", resp_data)
        if not data:
            return None

        number = data.get("serial_number", movie_id)
        title = data.get("title_cn") or data.get("title") or ""
        plot = data.get("description_cn") or data.get("description")
        cover = data.get("cover")

        # Release date from timestamp (millis)
        premiered: Optional[str] = None
        pub_at = data.get("published_at")
        if pub_at and isinstance(pub_at, (int, float)):
            from datetime import datetime, timezone

            dt = datetime.fromtimestamp(pub_at / 1000, tz=timezone.utc)
            premiered = dt.strftime("%Y-%m-%d")

        # Genres from tags
        tags: List[str] = []
        for tag in data.get("tags") or []:
            name = tag.get("name_cn") or tag.get("name") if isinstance(tag, dict) else str(tag)
            if name:
                tags.append(name)

        # Actors from models
        actors: List[str] = []
        for model in data.get("models") or []:
            name = model.get("name_cn") or model.get("name") if isinstance(model, dict) else str(model)
            if name:
                actors.append(name)

        display_code = number.upper() if number else movie_id.upper()

        metadata = (
            MetadataBuilder()
            .set_title(title, display_code)
            .set_identifier(SITE_NAME, display_code, page_url)
            .set_actors(actors)
            .set_studio("麻豆傳媒映畫")
            .set_tags(tags)
            .set_release_date(premiered)
            .set_cover(cover)
            .set_thumbnail(cover)
            .set_plot(plot)
            .build()
        )
        metadata.official_rating = "JP-18+"
        self.logger.info(f"成功提取元数据: {display_code}")
        return metadata

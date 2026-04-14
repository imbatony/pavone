"""
10musume 元数据提取器插件

参考: D:\\code\\metatube-sdk-go-main\\provider\\10musume\\10musume.go
支持的 URL 模式：https://www.10musume.com/movies/{movie_id}/
ID 格式: XXXXXX_XX (6位日期_2位序号，如 010123_01)
通过 JSON API 获取结构化数据（与 1pondo 同一套 API 体系）。
"""

import re
from typing import Any, Dict, List, Optional

from ...models import MovieMetadata
from ...utils.metadata_builder import MetadataBuilder
from .base import ApiMetadataPlugin

PLUGIN_NAME = "TenMusumeMetadata"
PLUGIN_VERSION = "1.0.0"
PLUGIN_DESCRIPTION = "提取 10musume.com 的视频元数据"
PLUGIN_AUTHOR = "PAVOne"
PLUGIN_PRIORITY = 50

SUPPORTED_DOMAINS = ["10musume.com", "www.10musume.com"]
SITE_NAME = "10musume"
DEFAULT_MAKER = "天然むすめ"

# ID 格式: 6位数字_2位数字
MOVIE_ID_PATTERN = r"\d{6}_\d{2}"

API_URL_TEMPLATE = "https://www.10musume.com/dyn/phpauto/movie_details/movie_id/{movie_id}.json"
MOVIE_URL_TEMPLATE = "https://www.10musume.com/movies/{movie_id}/"


class TenMusumeMetadata(ApiMetadataPlugin):
    """10musume.com 元数据提取器，通过 JSON API 获取数据。"""

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

    def _resolve(self, identifier: str):
        if identifier.startswith("http://") or identifier.startswith("https://"):
            match = re.search(rf"/movies/({MOVIE_ID_PATTERN})/?", identifier)
            movie_id = match.group(1) if match else None
            if movie_id:
                return movie_id, MOVIE_URL_TEMPLATE.format(movie_id=movie_id)
            return None, None
        s = identifier.strip()
        if re.match(rf"^{MOVIE_ID_PATTERN}$", s):
            return s, MOVIE_URL_TEMPLATE.format(movie_id=s)
        return None, None

    def _build_api_url(self, movie_id: str) -> str:
        return API_URL_TEMPLATE.format(movie_id=movie_id)

    def _parse(self, data: Dict[str, Any], movie_id: str, page_url: str) -> Optional[MovieMetadata]:
        if not data:
            return None
        try:
            title = data.get("Title", "")

            actors: List[str] = [a.strip("-").strip() for a in (data.get("ActressesJa") or []) if a.strip("-").strip()]

            duration_sec = data.get("Duration")
            runtime: Optional[int] = round(duration_sec / 60) if duration_sec else None

            tags: List[str] = data.get("UCNAME") or []

            avg_rating = data.get("AvgRating")
            rating: Optional[float] = round(float(avg_rating) * 2, 1) if avg_rating else None

            metadata = (
                MetadataBuilder()
                .set_title(title, movie_id)
                .set_identifier(SITE_NAME, movie_id, page_url)
                .set_actors(actors)
                .set_runtime(runtime)
                .set_release_date(data.get("Release"))
                .set_serial(data.get("Series") or None)
                .set_tags(tags)
                .set_rating(rating)
                .set_plot(data.get("Desc") or None)
                .set_cover(data.get("MovieThumb") or None)
                .set_studio(DEFAULT_MAKER)
                .build()
            )
            metadata.official_rating = "JP-18+"
            self.logger.info(f"成功提取元数据: {movie_id}")
            return metadata
        except Exception as e:
            self.logger.error(f"构建元数据失败: {e}", exc_info=True)
            return None

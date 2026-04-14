"""
1Pondo元数据提取器插件

支持从 1pondo.tv 网站提取视频元数据。
通过 JSON API 获取结构化数据。
"""

import re
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import urlparse

from ...models import MovieMetadata
from ...utils.metadata_builder import MetadataBuilder
from .base import ApiMetadataPlugin

# 定义插件名称和版本
PLUGIN_NAME = "OnePondoMetadata"
PLUGIN_VERSION = "1.0.0"
PLUGIN_DESCRIPTION = "提取 1pondo.tv 的视频元数据"
PLUGIN_AUTHOR = "PAVOne"

# 定义插件优先级
PLUGIN_PRIORITY = 20

# 定义支持的域名
SUPPORTED_DOMAINS = ["1pondo.tv", "www.1pondo.tv", "en.1pondo.tv"]

SITE_NAME = "1Pondo"

# 1pondo 番号格式: 6位日期_3位序号，如 032417_504
MOVIE_ID_PATTERN = r"\d{6}_\d{3}"

# JSON API URL 模板
API_URL_TEMPLATE = "https://www.1pondo.tv/dyn/phpauto/movie_details/movie_id/{movie_id}.json"

# 影片页面 URL 模板
MOVIE_URL_TEMPLATE = "https://www.1pondo.tv/movies/{movie_id}/"


class OnePondoMetadata(ApiMetadataPlugin):
    """
    1Pondo元数据提取器
    通过 JSON API 提取 1pondo.tv 视频元数据。
    """

    def __init__(self):
        """初始化1Pondo元数据提取器"""
        super().__init__(
            name=PLUGIN_NAME,
            version=PLUGIN_VERSION,
            description=PLUGIN_DESCRIPTION,
            author=PLUGIN_AUTHOR,
            priority=PLUGIN_PRIORITY,
        )
        self.supported_domains = SUPPORTED_DOMAINS
        self.site_name = SITE_NAME

    def can_extract(self, identifier: str) -> bool:
        """检查是否能处理给定的identifier

        支持两种格式：
        1. URL: https://www.1pondo.tv/movies/032417_504/
        2. 番号: 032417_504
        """
        if identifier.startswith("http://") or identifier.startswith("https://"):
            return self.can_handle_domain(identifier, self.supported_domains)

        # 检查是否为1pondo番号格式
        identifier_stripped = identifier.strip()
        return bool(re.match(rf"^{MOVIE_ID_PATTERN}$", identifier_stripped))

    def _build_api_url(self, movie_id: str) -> str:
        return API_URL_TEMPLATE.format(movie_id=movie_id)

    def _resolve(self, identifier: str) -> Tuple[Optional[str], Optional[str]]:
        """将 identifier 解析为 (movie_id, page_url)"""
        movie_id = self._extract_movie_id(identifier)
        if not movie_id:
            return None, None
        return movie_id, MOVIE_URL_TEMPLATE.format(movie_id=movie_id)

    def _extract_movie_id(self, identifier: str) -> Optional[str]:
        """从identifier中提取番号

        Args:
            identifier: URL或番号字符串

        Returns:
            番号字符串，如 '032417_504'
        """
        if identifier.startswith("http://") or identifier.startswith("https://"):
            return self._extract_movie_id_from_url(identifier)
        # 直接作为番号
        identifier_stripped = identifier.strip()
        if re.match(rf"^{MOVIE_ID_PATTERN}$", identifier_stripped):
            return identifier_stripped
        return None

    def _extract_movie_id_from_url(self, url: str) -> Optional[str]:
        """从URL中提取番号

        Args:
            url: 1pondo页面URL

        Returns:
            番号字符串
        """
        match = re.search(rf"/movies/({MOVIE_ID_PATTERN})/?", url)
        return match.group(1) if match else None

    def _parse(self, data: Dict[str, Any], movie_id: str, page_url: str) -> Optional[MovieMetadata]:
        """从API JSON数据构建MovieMetadata对象"""
        if not data:
            return None
        try:
            title = data.get("Title", "")
            url = page_url
            code = movie_id

            # 演员列表
            actors = data.get("ActressesJa") or []

            # 时长（API返回秒数，转换为分钟）
            duration_sec = data.get("Duration")
            runtime: Optional[int] = None
            if duration_sec and isinstance(duration_sec, (int, float)):
                runtime = round(duration_sec / 60)

            # 发行日期
            release_date = data.get("Release")

            # 系列
            series = data.get("Series")

            # 标签/分类（日文）
            tags: List[str] = data.get("UCNAME") or []

            # 评分（API返回5分制，转换为10分制）
            avg_rating = data.get("AvgRating")
            rating: Optional[float] = None
            if avg_rating is not None:
                rating = round(float(avg_rating) * 2, 1)

            # 描述
            desc = data.get("Desc")

            # 封面图
            cover = data.get("MovieThumb")
            # 海报图
            poster = f"https://www.1pondo.tv/assets/sample/{movie_id}/str.jpg"
            # 背景图（3张）
            backdrops = [f"https://www.1pondo.tv/assets/sample/{movie_id}/popu/{n}.jpg" for n in range(1, 4)]

            metadata = (
                MetadataBuilder()
                .set_title(title, code)
                .set_identifier(SITE_NAME, code, url)
                .set_actors(actors)
                .set_runtime(runtime)
                .set_release_date(release_date)
                .set_serial(series)
                .set_tags(tags)
                .set_rating(rating)
                .set_plot(desc)
                .set_cover(cover)
                .set_poster(poster)
                .set_backdrops(backdrops)
                .set_studio("一本道")
                .build()
            )
            metadata.official_rating = "JP-18+"

            self.logger.info(f"成功提取元数据: {code}")
            return metadata

        except Exception as e:
            self.logger.error(f"构建元数据失败: {str(e)}", exc_info=True)
            return None

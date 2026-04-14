"""
AVBase 元数据提取器插件

参考: D:\\code\\metatube-sdk-go-main\\provider\\avbase\\avbase.go
      D:\\code\\metatube-sdk-go-main\\provider\\avbase\\responses.go
支持的 URL 模式: https://www.avbase.net/works/{movie_id}
通过 Next.js _next/data API 获取结构化数据。
"""

import re
from typing import Any, Dict, List, Optional
from urllib.parse import urlparse

import requests
from bs4 import BeautifulSoup

from ...models import MovieMetadata
from ...utils.metadata_builder import MetadataBuilder
from .base import MetadataPlugin

PLUGIN_NAME = "AvBaseMetadata"
PLUGIN_VERSION = "1.0.0"
PLUGIN_DESCRIPTION = "提取 avbase.net 的视频元数据"
PLUGIN_AUTHOR = "PAVOne"
PLUGIN_PRIORITY = 50

SUPPORTED_DOMAINS = ["avbase.net", "www.avbase.net"]
SITE_NAME = "AVBASE"

MOVIE_URL_TEMPLATE = "https://www.avbase.net/works/{movie_id}"
# Next.js data API，需要先从页面获取 buildId
MOVIE_API_TEMPLATE = "https://www.avbase.net/_next/data/{build_id}/works/{movie_id}.json?id={movie_id}"


class AvBaseMetadata(MetadataPlugin):
    """avbase.net 元数据提取器，通过 Next.js API 获取数据。"""

    def __init__(self):
        super().__init__(
            name=PLUGIN_NAME,
            version=PLUGIN_VERSION,
            description=PLUGIN_DESCRIPTION,
            author=PLUGIN_AUTHOR,
            priority=PLUGIN_PRIORITY,
        )
        self._build_id: Optional[str] = None

    def can_extract(self, identifier: str) -> bool:
        if identifier.startswith("http://") or identifier.startswith("https://"):
            return self.can_handle_domain(identifier, SUPPORTED_DOMAINS)
        # ID 格式: 纯大写字母数字，如 "ABC-123" 或 "dga:pkey12345"
        return bool(re.match(r"^[A-Za-z\d:_-]+$", identifier.strip()) and len(identifier.strip()) > 2)

    def extract_metadata(self, identifier: str) -> Optional[MovieMetadata]:
        try:
            movie_id, page_url = self._resolve(identifier)
            if not movie_id or not page_url:
                self.logger.error(f"无法解析 identifier: {identifier}")
                return None

            build_id = self._get_build_id()
            if not build_id:
                # Fallback: HTML 直接解析
                return self._extract_from_html(movie_id, page_url)

            api_url = MOVIE_API_TEMPLATE.format(build_id=build_id, movie_id=movie_id, movie_id_enc=movie_id)
            try:
                resp = self.fetch(api_url, timeout=30)
                data = resp.json()
                return self._parse_api(data, movie_id, page_url)
            except Exception:
                # API 失败时回退到 HTML 解析
                return self._extract_from_html(movie_id, page_url)

        except requests.RequestException as e:
            self.logger.error(f"HTTP 请求失败: {e}")
            return None
        except Exception as e:
            self.logger.error(f"提取元数据失败: {e}", exc_info=True)
            return None

    def _resolve(self, identifier: str):
        if identifier.startswith("http://") or identifier.startswith("https://"):
            parsed = urlparse(identifier)
            parts = [p for p in parsed.path.split("/") if p]
            if "works" in parts:
                idx = parts.index("works")
                if idx + 1 < len(parts):
                    movie_id = parts[idx + 1].upper()
                    return movie_id, identifier
            return None, None
        movie_id = identifier.strip().upper()
        return movie_id, MOVIE_URL_TEMPLATE.format(movie_id=movie_id)

    def _get_build_id(self) -> Optional[str]:
        if self._build_id:
            return self._build_id
        try:
            resp = self.fetch("https://www.avbase.net/", timeout=15)
            soup = BeautifulSoup(resp.text, "lxml")
            # Next.js 将 buildId 注入到 __NEXT_DATA__ script 中
            script = soup.find("script", id="__NEXT_DATA__")
            if script and script.string:
                import json

                data = json.loads(script.string)
                self._build_id = data.get("buildId")
                return self._build_id
        except Exception as e:
            self.logger.warning(f"获取 avbase buildId 失败: {e}")
        return None

    def _parse_api(self, data: Dict[str, Any], movie_id: str, page_url: str) -> Optional[MovieMetadata]:
        page_props = data.get("pageProps") or {}
        work: Dict[str, Any] = page_props.get("work") or {}
        if not work:
            return None

        # 优先从 products 中提取信息（按 source 优先级：mgs > fanza > duga > ...）
        products = sorted(work.get("products") or [], key=lambda p: p.get("source", ""), reverse=True)

        title: Optional[str] = work.get("title") or ""
        cover: Optional[str] = None
        thumbnail: Optional[str] = None
        maker: Optional[str] = None
        label: Optional[str] = None
        serial: Optional[str] = None
        plot: Optional[str] = None
        premiered: Optional[str] = work.get("min_date") or None
        runtime: Optional[int] = None
        backdrops: List[str] = []

        for product in products:
            if not title:
                title = product.get("title", "")
            if not cover:
                cover = product.get("image_url") or None
            if not thumbnail:
                thumbnail = product.get("thumbnail_url") or None
            if not maker:
                maker = (product.get("maker") or {}).get("name") or None
            if not label:
                label = (product.get("label") or {}).get("name") or None
            if not serial:
                serial = (product.get("series") or {}).get("name") or None
            if not plot:
                plot = (product.get("iteminfo") or {}).get("description") or None
            if not runtime:
                vol = (product.get("iteminfo") or {}).get("volume") or ""
                if vol:
                    runtime = self._parse_runtime(vol)
            if not backdrops:
                for img in product.get("sample_image_urls") or []:
                    url = img.get("l") or img.get("s")
                    if url:
                        backdrops.append(url)
            if not premiered:
                premiered = product.get("date") or None

        # Actors
        actors: List[str] = []
        for actor in work.get("actors") or []:
            name = actor.get("name")
            if name:
                actors.append(name)
        for cast in work.get("casts") or []:
            name = (cast.get("actor") or {}).get("name")
            if name and name not in actors:
                actors.append(name)

        # Genres
        tags: List[str] = [g.get("name", "") for g in (work.get("genres") or []) if g.get("name")]

        display_code = movie_id

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
            .build()
        )
        metadata.official_rating = "JP-18+"
        self.logger.info(f"成功提取元数据: {display_code}")
        return metadata

    def _extract_from_html(self, movie_id: str, page_url: str) -> Optional[MovieMetadata]:
        """当 API 不可用时，直接解析 Next.js 渲染的 HTML。"""
        try:
            import json

            resp = self.fetch(page_url, timeout=30)
            soup = BeautifulSoup(resp.text, "lxml")
            script = soup.find("script", id="__NEXT_DATA__")
            if script and script.string:
                data = json.loads(script.string)
                # __NEXT_DATA__ 中 pageProps 在 props 下: {"props": {"pageProps": {...}}}
                props = data.get("props") or {}
                return self._parse_api(props, movie_id, page_url)
        except Exception as e:
            self.logger.error(f"HTML 解析回退失败: {e}")
        return None

    @staticmethod
    def _parse_runtime(text: str) -> Optional[int]:
        m = re.search(r"(\d+)\s*分", text)
        if m:
            return int(m.group(1))
        m2 = re.match(r"(\d+):(\d+)", text.strip())
        if m2:
            return int(m2.group(1)) * 60 + int(m2.group(2))
        return None

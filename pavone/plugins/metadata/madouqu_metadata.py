"""
MadouQu (麻豆区) 元数据提取器插件

参考: D:\\code\\metatube-sdk-go-main\\provider\\madouqu\\madouqu.go
支持的 URL 模式: https://madouqu.com/{id}/
ID 格式: 番号 slug (如 mdx-0236)
通过 HTML 页面解析获取元数据。中文站点。
注意: 默认优先级 0（禁用），需手动启用。
"""

import re
from typing import List, Optional
from urllib.parse import urlparse

import requests
from bs4 import BeautifulSoup

from ...models import MovieMetadata
from ...utils.metadata_builder import MetadataBuilder
from .base import MetadataPlugin

PLUGIN_NAME = "MadouquMetadata"
PLUGIN_VERSION = "1.0.0"
PLUGIN_DESCRIPTION = "提取 madouqu.com (麻豆区) 的视频元数据"
PLUGIN_AUTHOR = "PAVOne"
PLUGIN_PRIORITY = 0  # Disabled by default

SUPPORTED_DOMAINS = ["madouqu.com", "www.madouqu.com"]
SITE_NAME = "MadouQu"

MOVIE_URL_TEMPLATE = "https://madouqu.com/{movie_id}/"


class MadouquMetadata(MetadataPlugin):
    """madouqu.com (麻豆区) 元数据提取器，中文站点，通过 HTML 解析获取数据。"""

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
            parsed = urlparse(identifier)
            parts = parsed.path.strip("/").split("/")
            if parts:
                movie_id = parts[-1] if parts[-1] else (parts[-2] if len(parts) > 1 else None)
                if movie_id:
                    return movie_id, identifier
            return None, None
        movie_id = identifier.strip().lower()
        return movie_id, MOVIE_URL_TEMPLATE.format(movie_id=movie_id)

    def _parse(self, soup: BeautifulSoup, movie_id: str, page_url: str) -> Optional[MovieMetadata]:
        title: Optional[str] = None
        cover: Optional[str] = None
        number: Optional[str] = None
        actors: List[str] = []
        maker: Optional[str] = None

        # Parse article content paragraphs
        for p in soup.select("article[id^='post'] div.container p"):
            img = p.find("img")
            if img and img.get("src"):
                src = str(img["src"])
                cover = self._extract_img_src(src)
                continue

            text = p.get_text(strip=True)
            if "番號" in text or "番号" in text:
                _, _, nb = text.partition("：")
                if not nb:
                    _, _, nb = text.partition(":")
                if nb:
                    number = nb.strip()
            elif "片名" in text:
                _, _, t = text.partition("：")
                if not t:
                    _, _, t = text.partition(":")
                if t:
                    title = t.strip()
            elif "女郎" in text or "演員" in text:
                _, _, actor_str = text.partition("：")
                if not actor_str:
                    _, _, actor_str = text.partition(":")
                if actor_str:
                    actors = [a.strip() for a in actor_str.split("、") if a.strip()]

        # Maker from category
        cat_el = soup.select_one("article[id^='post'] span.meta-category a")
        if cat_el:
            maker = cat_el.get_text(strip=True)

        # Actor tags (fallback)
        if not actors:
            actor_tags = []
            for a in soup.select("article[id^='post'] div.entry-tags a"):
                tag = a.get_text(strip=True)
                if tag:
                    actor_tags.append(tag)
            if actor_tags:
                actors = actor_tags

        display_code = number or movie_id.upper()

        metadata = (
            MetadataBuilder()
            .set_title(title or "", display_code)
            .set_identifier(SITE_NAME, display_code, page_url)
            .set_actors(actors)
            .set_studio(maker)
            .set_tags([])
            .set_cover(cover)
            .set_thumbnail(cover)
            .build()
        )
        metadata.official_rating = "JP-18+"
        self.logger.info(f"成功提取元数据: {display_code}")
        return metadata

    @staticmethod
    def _extract_img_src(src: str) -> str:
        m = re.search(r"(https?://.+)$", src)
        if m:
            return m.group(1)
        return src

    @staticmethod
    def _parse_date(s: str) -> Optional[str]:
        m = re.match(r"(\d{4})[年/\-.](\d{1,2})[月/\-.](\d{1,2})", s.strip())
        if m:
            return f"{m.group(1)}-{int(m.group(2)):02d}-{int(m.group(3)):02d}"
        return None

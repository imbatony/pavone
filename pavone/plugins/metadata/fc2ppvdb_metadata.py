"""
FC2PPVDB 元数据提取器插件

参考: D:\\code\\metatube-sdk-go-main\\provider\\fc2ppvdb\\fc2ppvdb.go
支持的 URL 模式: https://fc2ppvdb.com/articles/{id}
ID 格式: 纯数字 FC2 PPV 编号
通过 HTML 页面解析获取元数据。
"""

import re
from typing import List, Optional
from urllib.parse import urlparse

import requests
from bs4 import BeautifulSoup

from ...models import MovieMetadata
from ...utils.metadata_builder import MetadataBuilder
from .base import MetadataPlugin

PLUGIN_NAME = "Fc2PpvdbMetadata"
PLUGIN_VERSION = "1.0.0"
PLUGIN_DESCRIPTION = "提取 fc2ppvdb.com 的视频元数据"
PLUGIN_AUTHOR = "PAVOne"
PLUGIN_PRIORITY = 48

SUPPORTED_DOMAINS = ["fc2ppvdb.com", "www.fc2ppvdb.com"]
SITE_NAME = "FC2PPVDB"

MOVIE_URL_TEMPLATE = "https://fc2ppvdb.com/articles/{movie_id}"


class Fc2PpvdbMetadata(MetadataPlugin):
    """fc2ppvdb.com 元数据提取器。"""

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
        return bool(re.match(r"^\d{5,}$", identifier.strip()))

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
            parts = [p for p in parsed.path.split("/") if p]
            if "articles" in parts:
                idx = parts.index("articles")
                if idx + 1 < len(parts):
                    return parts[idx + 1], identifier
            return None, None
        movie_id = identifier.strip()
        if re.match(r"^\d{5,}$", movie_id):
            return movie_id, MOVIE_URL_TEMPLATE.format(movie_id=movie_id)
        return None, None

    def _parse(self, soup: BeautifulSoup, movie_id: str, page_url: str) -> Optional[MovieMetadata]:
        code = f"FC2-{movie_id}"
        title: Optional[str] = None
        cover: Optional[str] = None
        maker: Optional[str] = None
        actors: List[str] = []
        tags: List[str] = []
        premiered: Optional[str] = None
        runtime: Optional[int] = None

        # Cover image
        cover_img = soup.select_one("main .container img")
        if cover_img and cover_img.get("src"):
            cover = str(cover_img["src"])
            if cover.startswith("//"):
                cover = "https:" + cover

        # Title from h2 a
        title_el = soup.select_one("main .container h2 a")
        if title_el:
            title = title_el.get_text(strip=True)

        # Fields from div elements
        for div in soup.select("main .container div"):
            text = div.get_text(strip=True)
            if not text:
                continue
            if text.startswith("ID：") or text.startswith("ID:"):
                span = div.select_one("span")
                if span:
                    movie_id = span.get_text(strip=True)
            elif text.startswith("販売者：") or text.startswith("販売者:"):
                span = div.select_one("span")
                if span:
                    maker = span.get_text(strip=True)
            elif text.startswith("女優：") or text.startswith("女優:"):
                span = div.select_one("span")
                if span:
                    actors = [a.strip() for a in span.get_text(strip=True).split() if a.strip()]
            elif text.startswith("販売日：") or text.startswith("販売日:"):
                span = div.select_one("span")
                if span:
                    premiered = self._parse_date(span.get_text(strip=True))
            elif text.startswith("収録時間：") or text.startswith("収録時間:"):
                span = div.select_one("span")
                if span:
                    runtime = self._parse_runtime(span.get_text(strip=True))
            elif text.startswith("タグ：") or text.startswith("タグ:"):
                span = div.select_one("span")
                if span:
                    tags = [t.strip() for t in span.get_text(strip=True).split() if t.strip()]

        metadata = (
            MetadataBuilder()
            .set_title(title or "", code)
            .set_identifier(SITE_NAME, code, page_url)
            .set_actors(actors)
            .set_studio(maker)
            .set_tags(tags)
            .set_release_date(premiered)
            .set_runtime(runtime)
            .set_cover(cover)
            .set_thumbnail(cover)
            .build()
        )
        metadata.official_rating = "JP-18+"
        self.logger.info(f"成功提取元数据: {code}")
        return metadata

    @staticmethod
    def _parse_runtime(text: str) -> Optional[int]:
        m = re.search(r"(\d+)\s*分", text)
        if m:
            return int(m.group(1))
        m2 = re.match(r"(\d+):(\d+)", text.strip())
        if m2:
            return int(m2.group(1)) * 60 + int(m2.group(2))
        return None

    @staticmethod
    def _parse_date(s: str) -> Optional[str]:
        m = re.match(r"(\d{4})[/\-.](\d{1,2})[/\-.](\d{1,2})", s.strip())
        if m:
            return f"{m.group(1)}-{int(m.group(2)):02d}-{int(m.group(3)):02d}"
        return None

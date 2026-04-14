"""
JavBus 元数据提取器插件

参考: D:\\code\\metatube-sdk-go-main\\provider\\javbus\\javbus.go
支持的 URL 模式: https://www.javbus.com/ja/{id}
ID 格式: 品番码 (如 ABP-123)
通过 HTML 页面解析获取元数据。注意需要设置 existmag=all cookie。
"""

import re
from typing import List, Optional
from urllib.parse import urlparse

import requests
from bs4 import BeautifulSoup

from ...models import MovieMetadata
from ...utils.metadata_builder import MetadataBuilder
from .base import MetadataPlugin

PLUGIN_NAME = "JavbusMetadata"
PLUGIN_VERSION = "1.0.0"
PLUGIN_DESCRIPTION = "提取 javbus.com 的视频元数据"
PLUGIN_AUTHOR = "PAVOne"
PLUGIN_PRIORITY = 50

SUPPORTED_DOMAINS = ["javbus.com", "www.javbus.com"]
SITE_NAME = "JavBus"

MOVIE_URL_TEMPLATE = "https://www.javbus.com/ja/{movie_id}"


class JavbusMetadata(MetadataPlugin):
    """javbus.com 元数据提取器，通过 HTML 页面解析获取数据。"""

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

            resp = self.fetch(
                page_url,
                timeout=30,
                cookies={"existmag": "all"},
                headers={"Referer": "https://www.javbus.com/"},
            )
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
            parts = parsed.path.rstrip("/").split("/")
            if parts:
                movie_id = parts[-1].upper()
                return movie_id, identifier
            return None, None
        movie_id = identifier.strip().upper()
        return movie_id, MOVIE_URL_TEMPLATE.format(movie_id=movie_id)

    def _parse(self, soup: BeautifulSoup, movie_id: str, page_url: str) -> Optional[MovieMetadata]:
        # Title + Cover from bigImage
        title: Optional[str] = None
        cover: Optional[str] = None
        big_img = soup.select_one("a.bigImage img")
        if big_img:
            title = str(big_img["title"]) if big_img.get("title") else None
            src = big_img.get("src")
            if src:
                cover = self._abs(str(src), page_url)

        # Fields
        number: Optional[str] = None
        premiered: Optional[str] = None
        runtime: Optional[int] = None
        director: Optional[str] = None
        maker: Optional[str] = None
        label: Optional[str] = None
        serial: Optional[str] = None

        for p in soup.select("div.col-md-3.info p"):
            span = p.find("span")
            if not span:
                continue
            key = span.get_text(strip=True)
            if key == "品番:":
                span2 = p.find_all("span")
                if len(span2) >= 2:
                    number = span2[1].get_text(strip=True)
            elif key == "発売日:":
                full_text = p.get_text(separator=" ", strip=True)
                date_text = full_text.replace(key, "").strip()
                if date_text:
                    premiered = self._parse_date(date_text)
            elif key == "収録時間:":
                full_text = p.get_text(separator=" ", strip=True)
                rt_text = full_text.replace(key, "").strip()
                if rt_text:
                    runtime = self._parse_runtime(rt_text)
            elif key == "監督:":
                a = p.find("a")
                if a:
                    director = a.get_text(strip=True)
            elif key == "メーカー:":
                a = p.find("a")
                if a:
                    maker = a.get_text(strip=True)
            elif key == "レーベル:":
                a = p.find("a")
                if a:
                    label = a.get_text(strip=True)
            elif key == "シリーズ:":
                a = p.find("a")
                if a:
                    serial = a.get_text(strip=True)

        # Genres
        tags: List[str] = []
        for span in soup.select("span.genre"):
            a = span.select_one("label a")
            if a:
                tag = a.get_text(strip=True)
                if tag:
                    tags.append(tag)

        # Preview images
        backdrops: List[str] = []
        for a in soup.select("#sample-waterfall a"):
            href = a.get("href")
            if href:
                backdrops.append(self._abs(str(href), page_url))

        # Actors
        actors: List[str] = []
        for div in soup.select("div.star-name"):
            a = div.find("a")
            if a and a.get("title"):
                actors.append(str(a["title"]))

        display_code = number or movie_id

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
            .set_thumbnail(cover)
            .set_backdrops(backdrops)
            .set_rating(None)
            .build()
        )
        if director:
            metadata.director = director
        if label:
            metadata.tagline = label
        metadata.official_rating = "JP-18+"
        self.logger.info(f"成功提取元数据: {display_code}")
        return metadata

    @staticmethod
    def _abs(url: str, base: str) -> str:
        if url.startswith("http"):
            return url
        parsed = urlparse(base)
        if url.startswith("//"):
            return f"{parsed.scheme}:{url}"
        return f"{parsed.scheme}://{parsed.netloc}{url}"

    @staticmethod
    def _parse_runtime(text: str) -> Optional[int]:
        m = re.search(r"(\d+)\s*分", text)
        if m:
            return int(m.group(1))
        m2 = re.search(r"(\d+)", text)
        if m2:
            return int(m2.group(1))
        return None

    @staticmethod
    def _parse_date(s: str) -> Optional[str]:
        m = re.match(r"(\d{4})[年/\-.](\d{1,2})[月/\-.](\d{1,2})", s.strip())
        if m:
            return f"{m.group(1)}-{int(m.group(2)):02d}-{int(m.group(3)):02d}"
        return None

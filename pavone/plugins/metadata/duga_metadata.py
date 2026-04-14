"""
DUGA 元数据提取器插件

参考: D:\\code\\metatube-sdk-go-main\\provider\\duga\\duga.go
支持的 URL 模式: https://duga.jp/ppv/{movie_id}/
通过 HTML 页面解析获取元数据。
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

PLUGIN_NAME = "DugaMetadata"
PLUGIN_VERSION = "1.0.0"
PLUGIN_DESCRIPTION = "提取 duga.jp 的视频元数据"
PLUGIN_AUTHOR = "PAVOne"
PLUGIN_PRIORITY = 50

SUPPORTED_DOMAINS = ["duga.jp", "www.duga.jp"]
SITE_NAME = "DUGA"

MOVIE_URL_TEMPLATE = "https://duga.jp/ppv/{movie_id}/"


class DugaMetadata(MetadataPlugin):
    """duga.jp 元数据提取器，通过 HTML 页面解析获取数据。"""

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
        # DUGA 使用小写 ID，如 "pkey0123456789"
        return bool(re.match(r"^[a-z\d_-]+$", identifier.strip()) and len(identifier.strip()) > 3)

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
            # /ppv/{movie_id}/
            m = re.search(r"/ppv/([^/]+)/?", parsed.path)
            if m:
                movie_id = m.group(1).lower()
                return movie_id, identifier
            return None, None
        movie_id = identifier.strip().lower()
        return movie_id, MOVIE_URL_TEMPLATE.format(movie_id=movie_id)

    def _parse(self, soup: BeautifulSoup, movie_id: str, page_url: str) -> Optional[MovieMetadata]:
        # Title
        title: Optional[str] = None
        title_tag = soup.select_one("#contentsname")
        if title_tag:
            title = title_tag.get_text(strip=True)

        # Fallback title from og:title
        if not title:
            og = soup.find("meta", property="og:title")
            if og and og.get("content"):
                title = str(og["content"])

        # Plot from JSON-LD
        plot: Optional[str] = None
        for script in soup.find_all("script", type="application/ld+json"):
            try:
                data = json.loads(script.string or "")
                if isinstance(data, list):
                    data = data[0]
                plot = data.get("description") or plot
            except Exception:
                pass

        if not plot:
            og_desc = soup.find("meta", property="og:description")
            if og_desc and og_desc.get("content"):
                plot = str(og_desc["content"])

        # Thumb
        thumbnail: Optional[str] = None
        thumb_tag = soup.select_one(".imagebox img#productjpg")
        if thumb_tag and thumb_tag.get("src"):
            thumbnail = self._abs(str(thumb_tag["src"]), page_url)

        if not thumbnail:
            og_img = soup.find("meta", property="og:image")
            if og_img and og_img.get("content"):
                thumbnail = self._abs(str(og_img["content"]), page_url)

        # Cover
        cover: Optional[str] = None
        cover_a = soup.select_one(".imagebox a")
        if cover_a and cover_a.get("href"):
            cover = self._abs(str(cover_a["href"]), page_url)
        if not cover:
            cover = thumbnail

        # Preview images
        backdrops: List[str] = []
        for li in soup.select("#digestthumbbox li"):
            a = li.find("a")
            if a and a.get("href"):
                backdrops.append(self._abs(str(a["href"]), page_url))

        # Fields from summary table
        makers: Optional[str] = None
        label: Optional[str] = None
        code: Optional[str] = None
        number: Optional[str] = None
        serial: Optional[str] = None
        premiered: Optional[str] = None
        runtime: Optional[int] = None

        for tr in soup.select(".summaryinner table tr"):
            th = tr.find("th")
            td = tr.find("td")
            if not th or not td:
                continue
            key = th.get_text(strip=True)
            val = td.get_text(strip=True)
            if key in ("配信開始日", "発売日") and not premiered:
                premiered = self._parse_date(val)
            elif key == "メーカー":
                makers = val
            elif key == "レーベル":
                label = val
            elif key == "作品ID":
                code = val
            elif key == "メーカー品番":
                number = val
            elif key == "シリーズ":
                serial = val or None

        # Runtime from download table
        for tr in soup.select(".downloadbox table tr"):
            th = tr.find("th")
            td = tr.find("td")
            if th and td and th.get_text(strip=True) == "再生時間":
                runtime = self._parse_runtime(td.get_text(strip=True))
                break

        # Score
        rating: Optional[float] = None
        score_tag = soup.select_one(".summaryinner .ratingstar-total img")
        if score_tag and score_tag.get("alt"):
            try:
                rating = float(str(score_tag["alt"]))
            except ValueError:
                pass

        # Actors + Genres
        actors: List[str] = [a.get_text(strip=True) for a in soup.select("ul.performer li a")]
        tags: List[str] = [a.get_text(strip=True) for a in soup.select("ul.categorylist li a")]
        director: Optional[str] = None
        dirs = soup.select("ul.director li a")
        if dirs:
            director = dirs[0].get_text(strip=True)

        display_code = number or code or movie_id

        metadata = (
            MetadataBuilder()
            .set_title(title or "", display_code)
            .set_identifier(SITE_NAME, display_code, page_url)
            .set_actors(actors)
            .set_studio(makers)
            .set_serial(serial)
            .set_tags(tags)
            .set_release_date(premiered)
            .set_runtime(runtime)
            .set_cover(cover)
            .set_thumbnail(thumbnail)
            .set_backdrops(backdrops)
            .set_plot(plot)
            .set_rating(rating)
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
        m2 = re.match(r"(\d+):(\d+)", text.strip())
        if m2:
            return int(m2.group(1)) * 60 + int(m2.group(2))
        return None

    @staticmethod
    def _parse_date(s: str) -> Optional[str]:
        m = re.match(r"(\d{4})[年/\-.](\d{1,2})[月/\-.](\d{1,2})", s.strip())
        if m:
            return f"{m.group(1)}-{int(m.group(2)):02d}-{int(m.group(3)):02d}"
        return None

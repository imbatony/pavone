"""
SOD (ソフト・オン・デマンド) 元数据提取器插件

参考: D:\\code\\metatube-sdk-go-main\\provider\\sod\\sod.go
支持的 URL 模式: https://ec.sod.co.jp/prime/videos/?id={id}
ID 格式: 品番码 (如 STARS-123)
通过 HTML 页面解析获取元数据。
"""

import re
from typing import List, Optional
from urllib.parse import parse_qs, urlparse

import requests
from bs4 import BeautifulSoup

from ...models import MovieMetadata
from ...utils.metadata_builder import MetadataBuilder
from .base import MetadataPlugin

PLUGIN_NAME = "SodMetadata"
PLUGIN_VERSION = "1.0.0"
PLUGIN_DESCRIPTION = "提取 ec.sod.co.jp 的视频元数据"
PLUGIN_AUTHOR = "PAVOne"
PLUGIN_PRIORITY = 50

SUPPORTED_DOMAINS = ["ec.sod.co.jp", "sod.co.jp"]
SITE_NAME = "SOD"

MOVIE_URL_TEMPLATE = "https://ec.sod.co.jp/prime/videos/?id={movie_id}"


class SodMetadata(MetadataPlugin):
    """ec.sod.co.jp (SOD) 元数据提取器，通过 HTML 页面解析获取数据。"""

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
                headers={"Referer": "https://ec.sod.co.jp/prime/"},
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
            qs = parse_qs(parsed.query)
            mid = qs.get("id", [None])[0]
            if mid:
                return mid.upper(), identifier
            return None, None
        movie_id = identifier.strip().upper()
        return movie_id, MOVIE_URL_TEMPLATE.format(movie_id=movie_id)

    def _parse(self, soup: BeautifulSoup, movie_id: str, page_url: str) -> Optional[MovieMetadata]:
        # Title
        title: Optional[str] = None
        title_el = soup.select_one("p.product_title")
        if title_el:
            title = title_el.get_text(strip=True)

        # Summary
        plot: Optional[str] = None
        desc_el = soup.select_one("div.videos_textli article")
        if desc_el:
            plot = desc_el.get_text(strip=True)

        # Cover
        cover: Optional[str] = None
        cover_el = soup.select_one("#videos_toptable div.videos_samimg a")
        if cover_el and cover_el.get("href"):
            cover = self._abs(str(cover_el["href"]), page_url)

        # Thumbnail
        thumbnail: Optional[str] = None
        thumb_img = soup.select_one("#videos_toptable div.videos_samimg a img")
        if thumb_img and thumb_img.get("src"):
            thumbnail = self._abs(str(thumb_img["src"]), page_url)

        # Preview images
        backdrops: List[str] = []
        for a in soup.select("#videos_samsbox a"):
            href = a.get("href")
            if href:
                img_url = self._abs(str(href), page_url)
                if not re.search(r"thumbnail/now_\w+\.jpg", img_url):
                    backdrops.append(img_url)

        # Fields from introduction table
        number: Optional[str] = None
        premiered: Optional[str] = None
        serial: Optional[str] = None
        actors: List[str] = []
        runtime: Optional[int] = None
        director: Optional[str] = None
        maker: Optional[str] = None
        label: Optional[str] = None
        tags: List[str] = []

        for tr in soup.select("#v_introduction tbody tr"):
            tds = tr.find_all("td")
            if len(tds) < 2:
                continue
            key = tds[0].get_text(strip=True)
            val_td = tds[1]
            val = val_td.get_text(strip=True)
            if key == "品番":
                number = val
            elif key == "発売年月日":
                premiered = self._parse_date(val)
            elif key == "シリーズ名":
                serial = val or None
            elif key == "出演者":
                actors = [a.strip() for a in val.split() if a.strip()]
            elif key == "再生時間":
                runtime = self._parse_runtime(val)
            elif key == "監督":
                director = val or None
            elif key == "メーカー":
                maker = val or None
            elif key == "レーベル":
                label = val or None
            elif key == "ジャンル":
                tags = [a.get_text(strip=True) for a in val_td.find_all("a") if a.get_text(strip=True)]

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
            .set_thumbnail(thumbnail)
            .set_backdrops(backdrops)
            .set_plot(plot)
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

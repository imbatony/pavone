"""
Pcolle 元数据提取器插件

参考: D:\\code\\metatube-sdk-go-main\\provider\\pcolle\\pcolle.go
支持的 URL 模式: https://www.pcolle.com/product/detail/?product_id={id}
ID 格式: PCOLLE-{id} 或 {英数字9+}
通过 HTML 页面解析获取元数据。注意需要设置 AGE_CONF=1 cookie。
"""

import re
from typing import List, Optional
from urllib.parse import parse_qs, urlparse

import requests
from bs4 import BeautifulSoup

from ...models import MovieMetadata
from ...utils.metadata_builder import MetadataBuilder
from .base import MetadataPlugin

PLUGIN_NAME = "PcolleMetadata"
PLUGIN_VERSION = "1.0.0"
PLUGIN_DESCRIPTION = "提取 pcolle.com 的视频元数据"
PLUGIN_AUTHOR = "PAVOne"
PLUGIN_PRIORITY = 50

SUPPORTED_DOMAINS = ["pcolle.com", "www.pcolle.com"]
SITE_NAME = "Pcolle"

MOVIE_URL_TEMPLATE = "https://www.pcolle.com/product/detail/?product_id={product_id}"


class PcolleMetadata(MetadataPlugin):
    """pcolle.com 元数据提取器，通过 HTML 页面解析获取数据。"""

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
        return bool(re.match(r"^(?:pcolle[-_])?([a-z\d]{9,})$", identifier.strip(), re.IGNORECASE))

    def extract_metadata(self, identifier: str) -> Optional[MovieMetadata]:
        try:
            product_id, page_url = self._resolve(identifier)
            if not product_id or not page_url:
                self.logger.error(f"无法解析 identifier: {identifier}")
                return None

            resp = self.fetch(
                page_url,
                timeout=30,
                cookies={"AGE_CONF": "1"},
            )
            soup = BeautifulSoup(resp.text, "lxml")
            return self._parse(soup, product_id, page_url)
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
            pid = qs.get("product_id", [None])[0]
            if pid:
                return pid.lower(), identifier
            return None, None
        m = re.match(r"^(?:pcolle[-_])?([a-z\d]{9,})$", identifier.strip(), re.IGNORECASE)
        if m:
            pid = m.group(1).lower()
            return pid, MOVIE_URL_TEMPLATE.format(product_id=pid)
        return None, None

    def _parse(self, soup: BeautifulSoup, product_id: str, page_url: str) -> Optional[MovieMetadata]:
        title: Optional[str] = None
        maker: Optional[str] = None
        premiered: Optional[str] = None
        plot: Optional[str] = None
        tags: List[str] = []

        # Fields from table
        for tr in soup.find_all("tr"):
            th = tr.find("th")
            td = tr.find("td")
            if not th or not td:
                continue
            key = th.get_text(strip=True)
            if key == "販売会員:":
                maker = td.get_text(strip=True)
            elif key == "商品名:":
                title = td.get_text(strip=True)
            elif key == "販売開始日:":
                premiered = self._parse_date(td.get_text(strip=True))

        # Title fallback
        if not title:
            title_el = soup.select_one("div.title-04")
            if title_el:
                title = title_el.get_text(strip=True)

        # Summary
        desc_el = soup.select_one("section.item_description p.fo-14")
        if desc_el:
            plot = desc_el.get_text(strip=True)
        if not plot:
            desc_sec = soup.select_one("section.item_description")
            if desc_sec:
                plot = desc_sec.get_text(strip=True)

        # Cover/Thumbnail
        cover: Optional[str] = None
        cover_el = soup.select_one("div.item-content div.part1 article a")
        if cover_el and cover_el.get("href"):
            cover = self._abs(str(cover_el["href"]), page_url)

        # Genres
        for li in soup.select("section.item_tags ul li"):
            tag = li.get_text(strip=True)
            if tag:
                tags.append(tag)

        # Preview images
        backdrops: List[str] = []
        for a in soup.select("section.item_images ul li a"):
            href = a.get("href")
            if href:
                backdrops.append(self._abs(str(href), page_url))

        # Cover fallback from preview images
        if not cover and backdrops:
            cover = backdrops[0]

        display_code = f"PCOLLE-{product_id}"

        metadata = (
            MetadataBuilder()
            .set_title(title or "", display_code)
            .set_identifier(SITE_NAME, display_code, page_url)
            .set_actors([])
            .set_studio(maker)
            .set_tags(tags)
            .set_release_date(premiered)
            .set_cover(cover)
            .set_thumbnail(cover)
            .set_backdrops(backdrops)
            .set_plot(plot)
            .build()
        )
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
    def _parse_date(s: str) -> Optional[str]:
        m = re.match(r"(\d{4})[年/\-.](\d{1,2})[月/\-.](\d{1,2})", s.strip())
        if m:
            return f"{m.group(1)}-{int(m.group(2)):02d}-{int(m.group(3)):02d}"
        return None

"""
Gcolle 元数据提取器插件

参考: D:\\code\\metatube-sdk-go-main\\provider\\gcolle\\gcolle.go
支持的 URL 模式: https://gcolle.net/product_info.php/products_id/{id}
ID 格式: 纯数字
通过 HTML 页面解析获取元数据。
"""

import re
from typing import List, Optional
from urllib.parse import urlparse

import requests
from bs4 import BeautifulSoup

from ...models import MovieMetadata
from ...utils.metadata_builder import MetadataBuilder
from .base import HtmlMetadataPlugin

PLUGIN_NAME = "GcolleMetadata"
PLUGIN_VERSION = "1.0.0"
PLUGIN_DESCRIPTION = "提取 gcolle.net 的视频元数据"
PLUGIN_AUTHOR = "PAVOne"
PLUGIN_PRIORITY = 50

SUPPORTED_DOMAINS = ["gcolle.net", "www.gcolle.net"]
SITE_NAME = "Gcolle"

MOVIE_URL_TEMPLATE = "https://gcolle.net/product_info.php/products_id/{movie_id}"


class GcolleMetadata(HtmlMetadataPlugin):
    """gcolle.net 元数据提取器。"""

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
        return bool(re.match(r"^(?:GCOLLE[-_])?(\d+)$", identifier.strip(), re.IGNORECASE))

    def _resolve(self, identifier: str):
        if identifier.startswith("http://") or identifier.startswith("https://"):
            parsed = urlparse(identifier)
            parts = [p for p in parsed.path.split("/") if p]
            if parts:
                movie_id = parts[-1]
                if movie_id.isdigit():
                    return movie_id, identifier
            return None, None
        m = re.match(r"^(?:GCOLLE[-_])?(\d+)$", identifier.strip(), re.IGNORECASE)
        if m:
            movie_id = m.group(1)
            return movie_id, MOVIE_URL_TEMPLATE.format(movie_id=movie_id)
        return None, None

    def _fetch_page(self, url: str) -> requests.Response:
        """覆写以处理年龄认证页面"""
        resp = self.fetch(url, timeout=30)
        # 检查是否命中年龄认证页面（内容过短且包含 age_check 链接）
        if len(resp.text) < 2000 and "age_check" in resp.text:
            soup = BeautifulSoup(resp.text, "lxml")
            for a in soup.find_all("a"):
                if a.get_text(strip=True) == "はい" and "age_check" in (a.get("href") or ""):
                    session = requests.Session()
                    session.cookies.update(dict(resp.cookies))
                    session.headers.update({"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"})
                    resp = session.get(str(a["href"]), timeout=30)
                    resp.raise_for_status()
                    break
        return resp

    def _parse(self, soup: BeautifulSoup, movie_id: str, page_url: str) -> Optional[MovieMetadata]:
        code = f"GCOLLE-{movie_id}"
        title: Optional[str] = None
        cover: Optional[str] = None
        plot: Optional[str] = None
        maker: Optional[str] = None
        tags: List[str] = []
        premiered: Optional[str] = None
        backdrops: List[str] = []

        # Title
        t_el = soup.select_one("#cart_quantity h1")
        if t_el:
            title = t_el.get_text(strip=True)

        # Summary/plot
        p_el = soup.select_one("#cart_quantity p")
        if p_el:
            plot = p_el.get_text(strip=True)

        # Genres
        for a in soup.select("#cart_quantity a"):
            href = str(a.get("href", ""))
            text = a.get_text(strip=True)
            if "genre" in href and text:
                tags.append(text)

        # Cover + Thumb
        cover_a = soup.select_one("#cart_quantity a img")
        if cover_a:
            parent = cover_a.find_parent("a")
            if parent and parent.get("href"):
                cover = self._abs(str(parent["href"]), page_url)

        # Preview images
        for img in soup.select("#cart_quantity div img"):
            src = img.get("src")
            if isinstance(src, str) and "sample" in src.lower():
                backdrops.append(self._abs(src, page_url))

        # Fields from table
        for tr in soup.select("table.filesetumei tr"):
            tds = tr.find_all("td")
            if len(tds) >= 2:
                key = tds[0].get_text(strip=True)
                val = tds[1].get_text(strip=True)
                if key == "商品登録日":
                    premiered = self._parse_date(val)

        # Maker
        for td in soup.select("table.contentBoxContentsManufactureInfo td"):
            if "アップロード会員名" in td.get_text():
                b = td.find("b")
                if b:
                    maker = b.get_text(strip=True)

        metadata = (
            MetadataBuilder()
            .set_title(title or "", code)
            .set_identifier(SITE_NAME, code, page_url)
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
        self.logger.info(f"成功提取元数据: {code}")
        return metadata

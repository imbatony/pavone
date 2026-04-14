"""
MGStage 元数据提取器插件

参考: D:\\code\\metatube-sdk-go-main\\provider\\mgstage\\mgstage.go
支持的 URL 模式: https://www.mgstage.com/product/product_detail/{id}/
ID 格式: 品番码 (如 300MIUM-951)
通过 HTML 页面解析获取元数据。注意需要设置 adc=1 cookie (年龄验证)。
"""

import re
from typing import List, Optional
from urllib.parse import urlparse

import requests
from bs4 import BeautifulSoup

from ...models import MovieMetadata
from ...utils.metadata_builder import MetadataBuilder
from .base import MetadataPlugin

PLUGIN_NAME = "MgstageMetadata"
PLUGIN_VERSION = "1.0.0"
PLUGIN_DESCRIPTION = "提取 mgstage.com 的视频元数据"
PLUGIN_AUTHOR = "PAVOne"
PLUGIN_PRIORITY = 50

SUPPORTED_DOMAINS = ["mgstage.com", "www.mgstage.com"]
SITE_NAME = "MGS"

MOVIE_URL_TEMPLATE = "https://www.mgstage.com/product/product_detail/{movie_id}/"


class MgstageMetadata(MetadataPlugin):
    """mgstage.com 元数据提取器，通过 HTML 页面解析获取数据。"""

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
        return bool(re.match(r"^[a-zA-Z0-9]+-\d+$", identifier.strip()))

    def extract_metadata(self, identifier: str) -> Optional[MovieMetadata]:
        try:
            movie_id, page_url = self._resolve(identifier)
            if not movie_id or not page_url:
                self.logger.error(f"无法解析 identifier: {identifier}")
                return None

            resp = self.fetch(
                page_url,
                timeout=30,
                cookies={"adc": "1"},
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
            parts = parsed.path.strip("/").split("/")
            if parts:
                movie_id = parts[-1].upper()
                return movie_id, identifier
            return None, None
        movie_id = identifier.strip().upper()
        return movie_id, MOVIE_URL_TEMPLATE.format(movie_id=movie_id)

    def _parse(self, soup: BeautifulSoup, movie_id: str, page_url: str) -> Optional[MovieMetadata]:
        # Title
        title: Optional[str] = None
        h1 = soup.select_one("#center_column div h1")
        if h1:
            title = h1.get_text(strip=True)

        # Summary
        plot: Optional[str] = None
        og_desc = soup.find("meta", property="og:description")
        if og_desc and og_desc.get("content"):
            plot = str(og_desc["content"])

        # Thumbnail
        thumbnail: Optional[str] = None
        thumb_img = soup.select_one("div.detail_data div h2 img")
        if thumb_img and thumb_img.get("src"):
            thumbnail = self._abs(str(thumb_img["src"]), page_url)

        # Cover
        cover: Optional[str] = None
        enlarge = soup.select_one("#EnlargeImage")
        if enlarge and enlarge.get("href"):
            cover = self._abs(str(enlarge["href"]), page_url)

        # Preview images
        backdrops: List[str] = []
        for li in soup.select("#sample-photo dd ul li"):
            a = li.find("a")
            if a and a.get("href"):
                backdrops.append(self._abs(str(a["href"]), page_url))

        # Fields from table
        actors: List[str] = []
        maker: Optional[str] = None
        number: Optional[str] = None
        premiered: Optional[str] = None
        runtime: Optional[int] = None
        serial: Optional[str] = None
        label: Optional[str] = None
        tags: List[str] = []
        rating: Optional[float] = None

        for tr in soup.find_all("tr"):
            th = tr.find("th")
            td = tr.find("td")
            if not th or not td:
                continue
            key = th.get_text(strip=True)
            if key == "出演：":
                actors = [a.strip() for a in td.get_text().split() if a.strip()]
            elif key == "メーカー：":
                maker = td.get_text(strip=True)
            elif key == "収録時間：":
                runtime = self._parse_runtime(td.get_text(strip=True))
            elif key == "品番：":
                number = td.get_text(strip=True)
            elif key in ("配信開始日：", "商品発売日："):
                if not premiered:
                    premiered = self._parse_date(td.get_text(strip=True))
            elif key == "シリーズ：":
                serial = td.get_text(strip=True) or None
            elif key == "レーベル：":
                label = td.get_text(strip=True) or None
            elif key == "ジャンル：":
                tags = [a.get_text(strip=True) for a in td.find_all("a") if a.get_text(strip=True)]
            elif key == "評価：":
                try:
                    rating = float(td.get_text(strip=True))
                except ValueError:
                    pass

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
            .set_rating(rating)
            .build()
        )
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

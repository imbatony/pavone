"""
FANZA (DMM) 元数据提取器插件

参考: D:\\code\\metatube-sdk-go-main\\provider\\fanza\\fanza.go
支持的 URL 模式:
  - https://www.dmm.co.jp/digital/videoa/-/detail/=/cid={id}/
  - https://www.dmm.co.jp/mono/dvd/-/detail/=/cid={id}/
  - https://video.dmm.co.jp/av/content/?id={id}
ID 格式: 小写英数字（如 midv00047, 1stars00141）
通过 HTML（传统 DMM 页面）或 JSON-LD 解析获取元数据。
"""

import json
import re
from typing import List, Optional, Tuple
from urllib.parse import parse_qs, urlparse

import requests
from bs4 import BeautifulSoup

from ...models import BaseMetadata, MovieMetadata
from ...utils.metadata_builder import MetadataBuilder
from .base import HtmlMetadataPlugin

PLUGIN_NAME = "FanzaMetadata"
PLUGIN_VERSION = "1.0.0"
PLUGIN_DESCRIPTION = "提取 dmm.co.jp (FANZA) 的视频元数据"
PLUGIN_AUTHOR = "PAVOne"
PLUGIN_PRIORITY = 51  # higher priority

SUPPORTED_DOMAINS = [
    "dmm.co.jp",
    "www.dmm.co.jp",
    "video.dmm.co.jp",
    "fanza.com",
    "www.fanza.com",
]
SITE_NAME = "FANZA"

MOVIE_URL_TEMPLATE = "https://www.dmm.co.jp/digital/videoa/-/detail/=/cid={movie_id}/"


class FanzaMetadata(HtmlMetadataPlugin):
    """dmm.co.jp / FANZA 元数据提取器。

    特殊多通道解析: __NEXT_DATA__ → HTML + JSON-LD，覆写 extract_metadata 保持自定义逻辑。
    """

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
        # FANZA IDs: lowercase alphanumeric, e.g. midv00047, 1stars00141
        return bool(re.match(r"^[a-z\d]{5,}$", identifier.strip()))

    def _fetch_page(self, url: str) -> requests.Response:
        """添加年龄验证 Cookie"""
        return self.fetch(url, headers={"Cookie": "age_check_done=1"}, timeout=30)

    def _parse(
        self, soup: BeautifulSoup, movie_id: str, page_url: str
    ) -> Optional[BaseMetadata]:
        """HTML 解析入口 (用于满足 HtmlMetadataPlugin 抽象方法)"""
        return self._parse_html(soup, movie_id, page_url)

    def extract_metadata(self, identifier: str) -> Optional[MovieMetadata]:
        """多通道解析: __NEXT_DATA__ 优先, 回退到 HTML + JSON-LD"""
        try:
            movie_id, page_url = self._resolve(identifier)
            if not movie_id or not page_url:
                self.logger.error(f"无法解析 identifier: {identifier}")
                return None

            resp = self._fetch_page(page_url)
            soup = BeautifulSoup(resp.text, "lxml")

            # Try __NEXT_DATA__ first (new video.dmm.co.jp)
            next_data = soup.find("script", id="__NEXT_DATA__")
            if next_data and next_data.string:
                result = self._parse_next_data(next_data.string, movie_id, page_url)
                if result:
                    return result

            # Traditional HTML page
            return self._parse_html(soup, movie_id, page_url)
        except requests.RequestException as e:
            self.logger.error(f"HTTP 请求失败: {e}")
            return None
        except Exception as e:
            self.logger.error(f"提取元数据失败: {e}", exc_info=True)
            return None

    def _resolve(self, identifier: str) -> Tuple[Optional[str], Optional[str]]:
        if identifier.startswith("http://") or identifier.startswith("https://"):
            parsed = urlparse(identifier)
            # Traditional: /cid=xxx/
            m = re.search(r"/cid=([^/]+)/?", parsed.path)
            if m:
                return m.group(1).lower(), identifier
            # New: ?id=xxx
            qs = parse_qs(parsed.query)
            if "id" in qs:
                return qs["id"][0].lower(), identifier
            return None, None
        movie_id = identifier.strip().lower()
        return movie_id, MOVIE_URL_TEMPLATE.format(movie_id=movie_id)

    def _parse_next_data(self, script_text: str, movie_id: str, page_url: str) -> Optional[MovieMetadata]:
        """解析 video.dmm.co.jp 上的 __NEXT_DATA__"""
        try:
            data = json.loads(script_text)
            props = data.get("props", {}).get("pageProps", {})
            content = props.get("contentDetailPage", {}).get("ppvContent") or props.get("ppvContent") or {}
            if not content or not content.get("title"):
                return None

            title = content.get("title", "")
            cover = (content.get("packageImage") or {}).get("largeURL") or (content.get("packageImage") or {}).get("mediumURL")
            thumb = (content.get("packageImage") or {}).get("mediumURL")
            maker_name = (content.get("maker") or {}).get("name")
            label_name = (content.get("label") or {}).get("name")
            series_name = (content.get("series") or {}).get("name")
            runtime = content.get("duration")
            if runtime and isinstance(runtime, (int, float)):
                runtime = int(runtime) // 60

            actors = [a.get("name", "") for a in (content.get("actresses") or []) if a.get("name")]
            genres = [g.get("name", "") for g in (content.get("genres") or []) if g.get("name")]
            director = None
            for d in content.get("directors") or []:
                director = d.get("name")
                break

            premiered = content.get("deliveryStartDate")
            if premiered and len(premiered) >= 10:
                premiered = premiered[:10]

            review = props.get("reviewSummary") or {}
            rating = review.get("average")

            # Preview images
            backdrops = [
                s.get("largeURL") or s.get("listURL") or ""
                for s in (content.get("sampleImages") or [])
                if s.get("largeURL") or s.get("listURL")
            ]

            display_code = content.get("makerContentID") or content.get("id") or movie_id

            metadata = (
                MetadataBuilder()
                .set_title(title, display_code)
                .set_identifier(SITE_NAME, display_code, page_url)
                .set_actors(actors)
                .set_studio(maker_name)
                .set_serial(series_name)
                .set_tags(genres)
                .set_release_date(premiered)
                .set_runtime(runtime)
                .set_cover(cover)
                .set_thumbnail(thumb)
                .set_backdrops(backdrops)
                .set_rating(rating)
                .set_director(director)
                .build()
            )
            if label_name:
                metadata.tagline = label_name
            metadata.official_rating = "JP-18+"
            self.logger.info(f"成功提取元数据 (NEXT_DATA): {display_code}")
            return metadata
        except Exception:
            return None

    def _parse_html(self, soup: BeautifulSoup, movie_id: str, page_url: str) -> Optional[MovieMetadata]:
        """解析传统 DMM HTML 页面"""
        title: Optional[str] = None
        cover: Optional[str] = None
        plot: Optional[str] = None
        maker: Optional[str] = None
        label: Optional[str] = None
        serial: Optional[str] = None
        director: Optional[str] = None
        actors: List[str] = []
        tags: List[str] = []
        premiered: Optional[str] = None
        runtime: Optional[int] = None
        rating: Optional[float] = None
        backdrops: List[str] = []
        display_code: Optional[str] = None

        # JSON-LD
        for script in soup.find_all("script", type="application/ld+json"):
            try:
                data = json.loads(script.string or "")
                if isinstance(data, list):
                    data = data[0]
                if data.get("@type") == "Product" or data.get("name"):
                    title = data.get("name") or title
                    if data.get("image"):
                        cover = data["image"]
                    agg = data.get("aggregateRating") or {}
                    if agg.get("ratingValue"):
                        try:
                            rating = float(agg["ratingValue"])
                        except ValueError:
                            pass
            except Exception:
                pass

        # Title fallback
        if not title:
            h1 = soup.select_one("#title h1")
            if h1:
                title = h1.get_text(strip=True)
        if not title:
            og = soup.find("meta", property="og:title")
            if og and og.get("content"):
                title = str(og["content"])

        # Cover from package image
        if not cover:
            pkg = soup.select_one("#sample-video a img, .package-image img")
            if pkg and pkg.get("src"):
                cover = str(pkg["src"])
                # DMM uses "ps.jpg" for small, "pl.jpg" for large
                cover = re.sub(r"ps\.jpg$", "pl.jpg", cover)

        # Cover from og:image
        if not cover:
            og = soup.find("meta", property="og:image")
            if og and og.get("content"):
                cover = str(og["content"])

        # Info table
        for tr in soup.select("table.mg-b20 tr, .product-info tr"):
            tds = tr.find_all("td")
            if len(tds) < 2:
                continue
            key = tds[0].get_text(strip=True)
            val_td = tds[1]
            val = val_td.get_text(strip=True)

            if "品番" in key:
                display_code = val
            elif "発売日" in key or "配信開始日" in key or "商品発売日" in key:
                premiered = self._parse_date(val)
            elif "収録時間" in key:
                runtime = self._parse_runtime(val)
            elif "メーカー" in key:
                maker = val
            elif "レーベル" in key:
                label = val
            elif "シリーズ" in key:
                serial = val or None
            elif "監督" in key:
                director = val or None
            elif "出演者" in key or "女優" in key:
                actors = [a.get_text(strip=True) for a in val_td.find_all("a") if a.get_text(strip=True)]
            elif "ジャンル" in key:
                tags = [a.get_text(strip=True) for a in val_td.find_all("a") if a.get_text(strip=True)]

        # Preview images
        for a in soup.select("#sample-image-block a, .sample-image-wrap a"):
            href = a.get("href") or a.get("data-href")
            if href:
                backdrops.append(str(href))

        # Plot
        plot_el = soup.select_one(".mg-b20.lh4, .product-description")
        if plot_el:
            plot = plot_el.get_text(strip=True)

        if not display_code:
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
            .set_thumbnail(cover)
            .set_backdrops(backdrops)
            .set_plot(plot)
            .set_rating(rating)
            .set_director(director)
            .build()
        )
        if label:
            metadata.tagline = label
        metadata.official_rating = "JP-18+"
        self.logger.info(f"成功提取元数据 (HTML): {display_code}")
        return metadata

"""
FANZA (DMM) 元数据提取器插件

参考: metatube-sdk-go/provider/fanza/
支持的 URL 模式:
  - https://video.dmm.co.jp/av/content/?id={id}
  - https://video.dmm.co.jp/amateur/content/?id={id}
  - https://video.dmm.co.jp/anime/content/?id={id}
  - https://video.dmm.co.jp/cinema/content/?id={id}
  - https://www.dmm.co.jp/digital/videoa/-/detail/=/cid={id}/
  - https://www.dmm.co.jp/mono/dvd/-/detail/=/cid={id}/
ID 格式: 小写英数字（如 midv00047, 1stars00141, scute1112）
数据获取优先级: GraphQL API → __NEXT_DATA__ → HTML + JSON-LD
"""

import json
import re
from typing import Any, Dict, List, Optional, Tuple
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
VIDEO_URL_TEMPLATE = "https://video.dmm.co.jp/{floor}/content/?id={movie_id}"
GRAPHQL_URL = "https://api.video.dmm.co.jp/graphql"

# video.dmm.co.jp 各类型路径 → GraphQL 标志
_FLOOR_MAP: Dict[str, str] = {
    "av": "isAv",
    "amateur": "isAmateur",
    "anime": "isAnime",
    "cinema": "isCinema",
    "vr": "isAv",
}

# 精简 GraphQL 查询 (基于 metatube-sdk-go ContentPageData.graphql)
_GRAPHQL_QUERY = """
query ContentPageData(
  $id: ID!
  $isAmateur: Boolean!
  $isAnime: Boolean!
  $isAv: Boolean!
  $isCinema: Boolean!
) {
  ppvContent(id: $id) {
    id
    floor
    title
    description
    packageImage { largeUrl mediumUrl }
    sampleImages { number imageUrl largeImageUrl }
    sample2DMovie { highestMovieUrl hlsMovieUrl }
    ...AmateurData @include(if: $isAmateur)
    ...AvData @include(if: $isAv)
    ...AnimeData @include(if: $isAnime)
    ...CinemaData @include(if: $isCinema)
  }
  reviewSummary(contentId: $id) { average total }
}
fragment AmateurData on PPVContent {
  deliveryStartDate duration makerContentId
  amateurActress { id name imageUrl }
  maker { id name } label { id name } genres { id name }
}
fragment AvData on PPVContent {
  deliveryStartDate makerReleasedAt duration makerContentId
  actresses { id name imageUrl }
  directors { id name }
  series { id name }
  maker { id name } label { id name } genres { id name }
}
fragment AnimeData on PPVContent {
  deliveryStartDate duration makerContentId
  series { id name }
  maker { id name } label { id name } genres { id name }
}
fragment CinemaData on PPVContent {
  deliveryStartDate duration makerContentId
  actresses { id name imageUrl }
  directors { id name }
  series { id name }
  maker { id name } label { id name } genres { id name }
}
"""


class FanzaMetadata(HtmlMetadataPlugin):
    """dmm.co.jp / FANZA 元数据提取器。

    多通道解析: GraphQL API → __NEXT_DATA__ → HTML + JSON-LD
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
        # FANZA IDs: lowercase alphanumeric, e.g. midv00047, 1stars00141, scute1112
        return bool(re.match(r"^[a-z\d]{5,}$", identifier.strip()))

    def _fetch_page(self, url: str) -> requests.Response:
        """添加年龄验证 Cookie"""
        return self.fetch(url, headers={"Cookie": "age_check_done=1"}, timeout=30)

    def _parse(self, soup: BeautifulSoup, movie_id: str, page_url: str) -> Optional[BaseMetadata]:
        """HTML 解析入口 (用于满足 HtmlMetadataPlugin 抽象方法)"""
        return self._parse_html(soup, movie_id, page_url)

    def extract_metadata(self, identifier: str) -> Optional[MovieMetadata]:
        """多通道解析: GraphQL API → __NEXT_DATA__ → HTML + JSON-LD"""
        try:
            movie_id, page_url, floor = self._resolve_with_floor(identifier)
            if not movie_id or not page_url:
                self.logger.error(f"无法解析 identifier: {identifier}")
                return None

            # 1. GraphQL API (video.dmm.co.jp 所有内容类型)
            result = self._try_graphql(movie_id, floor, page_url)
            if result:
                return result

            # 2. HTML 回退 (传统 www.dmm.co.jp 页面)
            resp = self._fetch_page(page_url)
            soup = BeautifulSoup(resp.text, "lxml")

            # 2a. __NEXT_DATA__ (旧版 video.dmm.co.jp 页面)
            next_data = soup.find("script", id="__NEXT_DATA__")
            if next_data and next_data.string:
                result = self._parse_next_data(next_data.string, movie_id, page_url)
                if result:
                    return result

            # 2b. 传统 HTML 页面
            return self._parse_html(soup, movie_id, page_url)
        except requests.RequestException as e:
            self.logger.error(f"HTTP 请求失败: {e}")
            return None
        except Exception as e:
            self.logger.error(f"提取元数据失败: {e}", exc_info=True)
            return None

    # ── URL 解析 ──

    def _resolve(self, identifier: str) -> Tuple[Optional[str], Optional[str]]:
        movie_id, page_url, _ = self._resolve_with_floor(identifier)
        return movie_id, page_url

    def _resolve_with_floor(self, identifier: str) -> Tuple[Optional[str], Optional[str], str]:
        """解析 identifier → (movie_id, page_url, floor)"""
        if identifier.startswith("http://") or identifier.startswith("https://"):
            parsed = urlparse(identifier)
            floor = self._detect_floor(parsed.path)

            # Traditional: /cid=xxx/
            m = re.search(r"/cid=([^/]+)/?", parsed.path)
            if m:
                return m.group(1).lower(), identifier, floor

            # New: ?id=xxx
            qs = parse_qs(parsed.query)
            if "id" in qs:
                return qs["id"][0].lower(), identifier, floor

            return None, None, floor

        movie_id = identifier.strip().lower()
        return movie_id, MOVIE_URL_TEMPLATE.format(movie_id=movie_id), "av"

    @staticmethod
    def _detect_floor(path: str) -> str:
        """从 URL 路径检测内容类型"""
        path_lower = path.lower()
        for floor in _FLOOR_MAP:
            if f"/{floor}/" in path_lower:
                return floor
        # www.dmm.co.jp/digital/videoc/ → amateur
        if "/videoc/" in path_lower:
            return "amateur"
        return "av"

    # ── GraphQL API ──

    def _try_graphql(self, movie_id: str, floor: str, page_url: str) -> Optional[MovieMetadata]:
        """通过 GraphQL API 获取元数据"""
        try:
            data = self._fetch_graphql(movie_id, floor)
            if not data:
                return None
            return self._parse_graphql(data, movie_id, floor, page_url)
        except Exception as e:
            self.logger.debug(f"GraphQL 请求失败, 回退到 HTML: {e}")
            return None

    def _fetch_graphql(self, movie_id: str, floor: str) -> Optional[Dict[str, Any]]:
        """调用 GraphQL API 并返回原始响应数据"""
        from ...utils.http_utils import HttpUtils

        flag_key = _FLOOR_MAP.get(floor, "isAv")
        variables: Dict[str, Any] = {
            "id": movie_id,
            "isAmateur": False,
            "isAnime": False,
            "isAv": False,
            "isCinema": False,
        }
        variables[flag_key] = True

        proxies = HttpUtils.get_proxies(self.config.proxy)
        resp = requests.post(
            GRAPHQL_URL,
            json={"query": _GRAPHQL_QUERY, "variables": variables},
            headers={
                "Content-Type": "application/json",
                "Referer": "https://video.dmm.co.jp/",
                "Cache-Control": "no-cache",
                "Fanza-Device": "BROWSER",
                "User-Agent": "",
            },
            proxies=proxies,
            timeout=30,
        )
        resp.raise_for_status()
        body = resp.json()
        ppv = (body.get("data") or {}).get("ppvContent")
        if not ppv or not ppv.get("title"):
            return None
        review = (body.get("data") or {}).get("reviewSummary") or {}
        return {"ppvContent": ppv, "reviewSummary": review}

    def _parse_graphql(self, data: Dict[str, Any], movie_id: str, floor: str, page_url: str) -> Optional[MovieMetadata]:
        """将 GraphQL 响应转换为 MovieMetadata"""
        content = data["ppvContent"]
        review = data.get("reviewSummary") or {}

        title = content.get("title", "")
        description = content.get("description")
        pkg = content.get("packageImage") or {}
        cover = pkg.get("largeUrl") or pkg.get("mediumUrl")
        thumb = pkg.get("mediumUrl")

        maker_name = (content.get("maker") or {}).get("name")
        label_name = (content.get("label") or {}).get("name")
        series_name = (content.get("series") or {}).get("name")

        runtime = content.get("duration")
        if runtime and isinstance(runtime, (int, float)):
            runtime = int(runtime) // 60

        # amateur 使用 amateurActress (单人), 其它类型使用 actresses (数组)
        actors: List[str] = []
        amateur_actress = content.get("amateurActress")
        if amateur_actress and amateur_actress.get("name"):
            actors = [amateur_actress["name"]]
        else:
            actors = [a.get("name", "") for a in (content.get("actresses") or []) if a.get("name")]

        genres = [g.get("name", "") for g in (content.get("genres") or []) if g.get("name")]
        director = None
        for d in content.get("directors") or []:
            if d.get("name"):
                director = d["name"]
                break

        premiered = content.get("deliveryStartDate") or content.get("makerReleasedAt")
        if premiered and len(premiered) >= 10:
            premiered = premiered[:10]

        rating = review.get("average")

        backdrops = [
            s.get("largeImageUrl") or s.get("imageUrl") or ""
            for s in (content.get("sampleImages") or [])
            if s.get("largeImageUrl") or s.get("imageUrl")
        ]

        display_code = content.get("makerContentId") or content.get("id") or movie_id
        # 如果 page_url 是旧格式, 生成 video.dmm.co.jp 链接
        actual_floor = content.get("floor", "").lower() or floor
        if "video.dmm.co.jp" not in page_url:
            page_url = VIDEO_URL_TEMPLATE.format(floor=actual_floor, movie_id=movie_id)

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
            .set_plot(description)
            .set_rating(rating)
            .set_director(director)
            .build()
        )
        if label_name:
            metadata.tagline = label_name
        metadata.official_rating = "JP-18+"
        self.logger.info(f"成功提取元数据 (GraphQL): {display_code}")
        return metadata

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

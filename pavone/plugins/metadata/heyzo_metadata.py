"""
HEYZO 元数据提取器插件

参考: D:\\code\\metatube-sdk-go-main\\provider\\heyzo\\heyzo.go
支持的 URL 模式: https://www.heyzo.com/moviepages/{id}/index.html
ID 格式: HEYZO-{id} 或 {4位数字}
通过 JSON-LD + HTML 解析获取元数据。
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

PLUGIN_NAME = "HeyzoMetadata"
PLUGIN_VERSION = "1.0.0"
PLUGIN_DESCRIPTION = "提取 heyzo.com 的视频元数据"
PLUGIN_AUTHOR = "PAVOne"
PLUGIN_PRIORITY = 50

SUPPORTED_DOMAINS = ["heyzo.com", "www.heyzo.com"]
SITE_NAME = "HEYZO"

MOVIE_URL_TEMPLATE = "https://www.heyzo.com/moviepages/{movie_id}/index.html"


class HeyzoMetadata(MetadataPlugin):
    """heyzo.com 元数据提取器，通过 JSON-LD + HTML 解析获取数据。"""

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
        return bool(re.match(r"^(?:heyzo[-_])?(\d{4})$", identifier.strip(), re.IGNORECASE))

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
            m = re.search(r"/moviepages/(\d{4})/", parsed.path)
            if m:
                movie_id = m.group(1)
                return movie_id, identifier
            return None, None
        m = re.match(r"^(?:heyzo[-_])?(\d{4})$", identifier.strip(), re.IGNORECASE)
        if m:
            movie_id = m.group(1)
            return movie_id, MOVIE_URL_TEMPLATE.format(movie_id=movie_id)
        return None, None

    def _parse(self, soup: BeautifulSoup, movie_id: str, page_url: str) -> Optional[MovieMetadata]:
        title: Optional[str] = None
        plot: Optional[str] = None
        cover: Optional[str] = None
        premiered: Optional[str] = None
        runtime: Optional[int] = None
        rating: Optional[float] = None
        actors: List[str] = []
        tags: List[str] = []
        serial: Optional[str] = None
        maker: Optional[str] = "HEYZO"

        # JSON-LD
        for script in soup.find_all("script", type="application/ld+json"):
            try:
                data = json.loads(script.string or "")
                if isinstance(data, list):
                    data = data[0]
                title = data.get("name") or title
                plot = data.get("description") or plot
                if data.get("image"):
                    cover = self._abs(data["image"], page_url)
                released = data.get("releasedEvent", {})
                if isinstance(released, dict) and released.get("startDate"):
                    premiered = self._parse_date(released["startDate"])
                video = data.get("video", {})
                if isinstance(video, dict):
                    if video.get("duration"):
                        runtime = self._parse_iso_duration(video["duration"])
                    if video.get("actor"):
                        actors = [video["actor"]]
                    if video.get("provider"):
                        maker = video["provider"]
                agg = data.get("aggregateRating", {})
                if isinstance(agg, dict) and agg.get("ratingValue"):
                    try:
                        rating = float(agg["ratingValue"])
                    except ValueError:
                        pass
            except Exception:
                pass

        # HTML fallback: title
        if not title:
            h1 = soup.select_one("#movie h1")
            if h1:
                title = h1.get_text(strip=True).split("\n")[0].strip()

        # HTML fallback: summary
        if not plot:
            memo = soup.select_one("p.memo")
            if memo:
                plot = memo.get_text(strip=True)

        # HTML fallback: cover
        if not cover:
            og = soup.find("meta", property="og:image")
            if og and og.get("content"):
                cover = self._abs(str(og["content"]), page_url)

        # Fields from table
        for tr in soup.select("table.movieInfo tbody tr"):
            tds = tr.find_all("td")
            if len(tds) < 2:
                continue
            key = tds[0].get_text(strip=True)
            if key == "公開日":
                if not premiered:
                    premiered = self._parse_date(tds[1].get_text(strip=True))
            elif key == "出演":
                found = [span.get_text(strip=True) for span in tds[1].select("a span")]
                if found:
                    actors = found
            elif key == "シリーズ":
                s = tds[1].get_text(strip=True).strip("-").strip()
                if s:
                    serial = s
            elif key == "評価":
                score_el = tds[1].select_one("span[itemprop='ratingValue']")
                if score_el:
                    try:
                        rating = float(score_el.get_text(strip=True))
                    except ValueError:
                        pass

        # Genres
        tag_list = soup.select("ul.tag-keyword-list li a")
        tags = [a.get_text(strip=True) for a in tag_list if a.get_text(strip=True)]

        # Preview images
        backdrops: List[str] = []
        for script in soup.find_all("script"):
            text = script.string or ""
            for m in re.findall(r'"(/contents/.+?/\d+?\.\w+?)"', text):
                backdrops.append(self._abs(m, page_url))

        display_code = f"HEYZO-{movie_id}"

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
    def _parse_iso_duration(s: str) -> Optional[int]:
        if not s:
            return None
        m = re.match(r"PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?", s)
        if m:
            h = int(m.group(1) or 0)
            mins = int(m.group(2) or 0)
            return h * 60 + mins if (h or mins) else None
        m2 = re.search(r"(\d+)\s*分", s)
        if m2:
            return int(m2.group(1))
        return None

    @staticmethod
    def _parse_date(s: str) -> Optional[str]:
        m = re.match(r"(\d{4})[年/\-.](\d{1,2})[月/\-.](\d{1,2})", s.strip())
        if m:
            return f"{m.group(1)}-{int(m.group(2)):02d}-{int(m.group(3)):02d}"
        return None

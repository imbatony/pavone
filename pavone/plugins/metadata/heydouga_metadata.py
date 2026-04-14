"""
HeyDouga 元数据提取器插件

参考: D:\\code\\metatube-sdk-go-main\\provider\\heydouga\\heydouga.go
支持的 URL 模式: https://www.heydouga.com/moviepages/{ppvid}/{movieid}/index.html
ID 格式: HEYDOUGA-{ppvid}-{movieid} 或 {ppvid}-{movieid}
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

PLUGIN_NAME = "HeydougaMetadata"
PLUGIN_VERSION = "1.0.0"
PLUGIN_DESCRIPTION = "提取 heydouga.com 的视频元数据"
PLUGIN_AUTHOR = "PAVOne"
PLUGIN_PRIORITY = 50

SUPPORTED_DOMAINS = ["heydouga.com", "www.heydouga.com"]
SITE_NAME = "HeyDouga"

MOVIE_URL_TEMPLATE = "https://www.heydouga.com/moviepages/{ppvid}/{movieid}/index.html"
MOVIE_TAG_URL = "https://www.heydouga.com/get_movie_tag_all/"


class HeydougaMetadata(HtmlMetadataPlugin):
    """heydouga.com 元数据提取器，通过 HTML 页面解析获取数据。"""

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
        return bool(re.match(r"^(?:heydouga[-_])?(\d{4})-(\d+)$", identifier.strip(), re.IGNORECASE))

    def _fetch_page(self, url: str) -> requests.Response:
        return self.fetch(
            url,
            timeout=30,
            cookies={"lang": "ja", "over18_ppv": "1", "feature_group": "1"},
        )

    def _resolve(self, identifier: str):
        if identifier.startswith("http://") or identifier.startswith("https://"):
            parsed = urlparse(identifier)
            m = re.search(r"/moviepages/(\d+)/(\d+)/", parsed.path)
            if m:
                movie_id = f"{m.group(1)}-{m.group(2)}"
                return movie_id, identifier
            return None, None
        m = re.match(r"^(?:heydouga[-_])?(\d{4})-(\d+)$", identifier.strip(), re.IGNORECASE)
        if m:
            ppvid, movieid = m.group(1), m.group(2)
            movie_id = f"{ppvid}-{movieid}"
            return movie_id, MOVIE_URL_TEMPLATE.format(ppvid=ppvid, movieid=movieid)
        return None, None

    def _parse(self, soup: BeautifulSoup, movie_id: str, page_url: str) -> Optional[MovieMetadata]:
        # Title
        title: Optional[str] = None
        title_el = soup.select_one("#title-bg h1")
        if title_el:
            for child in title_el.children:
                if isinstance(child, str):
                    t = child.strip()
                    if t:
                        title = t
                        break
            if not title:
                title = title_el.get_text(strip=True)

        # Summary
        plot: Optional[str] = None
        detail_el = soup.select_one("#movie-detail-mobile div p")
        if detail_el:
            plot = detail_el.get_text(strip=True)

        # Cover from JS variable
        cover: Optional[str] = None
        for script in soup.find_all("script"):
            text = script.string or ""
            m = re.search(r"var\s+player_poster\s*=\s*['\"](.+?)['\"];", text)
            if m:
                cover = self._abs(m.group(1), page_url)
                break

        thumbnail = cover

        # Fields
        actors: List[str] = []
        maker: Optional[str] = None
        premiered: Optional[str] = None
        runtime: Optional[int] = None

        for li in soup.select("#movie-info ul li"):
            spans = li.find_all("span")
            if len(spans) < 2:
                continue
            key = spans[0].get_text(strip=True)
            val = spans[1].get_text(strip=True)
            if key in ("配信日：", "配信日:"):
                premiered = self._parse_date(val)
            elif key in ("配信期間：", "配信期間:"):
                start_date = val.split("～")[0].strip()
                premiered = self._parse_date(start_date)
            elif key in ("主演：", "主演:"):
                actors = [a.strip() for a in val.split() if a.strip()]
            elif key in ("提供元：", "提供元:"):
                a_tag = spans[1].find("a")
                maker = a_tag.get_text(strip=True) if a_tag else val
            elif key in ("動画再生時間：", "動画再生時間:"):
                runtime = self._parse_runtime(val)

        # Preview images
        backdrops: List[str] = []
        for a in soup.select("#movie-gallery-images a.fancybox"):
            href = a.get("href")
            if href:
                img_url = self._abs(str(href), page_url)
                if img_url not in backdrops:
                    backdrops.append(img_url)

        display_code = f"HEYDOUGA-{movie_id}"

        metadata = (
            MetadataBuilder()
            .set_title(title or "", display_code)
            .set_identifier(SITE_NAME, display_code, page_url)
            .set_actors(actors)
            .set_studio(maker)
            .set_tags([])
            .set_release_date(premiered)
            .set_runtime(runtime)
            .set_cover(cover)
            .set_thumbnail(thumbnail)
            .set_backdrops(backdrops)
            .set_plot(plot)
            .build()
        )
        metadata.official_rating = "JP-18+"
        self.logger.info(f"成功提取元数据: {display_code}")
        return metadata

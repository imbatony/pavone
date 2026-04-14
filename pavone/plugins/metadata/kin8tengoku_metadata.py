"""
KIN8TENGOKU (金髪天國) 元数据提取器插件

参考: D:\\code\\metatube-sdk-go-main\\provider\\kin8tengoku\\kin8tengoku.go
支持的 URL 模式: https://www.kin8tengoku.com/moviepages/{id}/index.html
ID 格式: KIN8-{id} 或 {4位数字}
通过 HTML 页面解析获取元数据。
"""

import re
from typing import List, Optional
from urllib.parse import urlparse

import requests
from bs4 import BeautifulSoup

from ...models import MovieMetadata
from ...utils.metadata_builder import MetadataBuilder
from .base import MetadataPlugin

PLUGIN_NAME = "Kin8tengokuMetadata"
PLUGIN_VERSION = "1.0.0"
PLUGIN_DESCRIPTION = "提取 kin8tengoku.com 的视频元数据"
PLUGIN_AUTHOR = "PAVOne"
PLUGIN_PRIORITY = 50

SUPPORTED_DOMAINS = ["kin8tengoku.com", "www.kin8tengoku.com"]
SITE_NAME = "KIN8"

MOVIE_URL_TEMPLATE = "https://www.kin8tengoku.com/moviepages/{movie_id:>04}/index.html"


class Kin8tengokuMetadata(MetadataPlugin):
    """kin8tengoku.com (金髪天國) 元数据提取器，通过 HTML 页面解析获取数据。"""

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
        return bool(re.match(r"^(?:kin8[-_])?(\d{4})$", identifier.strip(), re.IGNORECASE))

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
            m = re.search(r"/moviepages/(\d+)/", parsed.path)
            if m:
                movie_id = m.group(1)
                return movie_id, identifier
            return None, None
        m = re.match(r"^(?:kin8[-_])?(\d{4})$", identifier.strip(), re.IGNORECASE)
        if m:
            movie_id = m.group(1)
            return movie_id, MOVIE_URL_TEMPLATE.format(movie_id=movie_id)
        return None, None

    def _parse(self, soup: BeautifulSoup, movie_id: str, page_url: str) -> Optional[MovieMetadata]:
        # Title
        title: Optional[str] = None
        title_el = soup.select_one("#sub_main p.sub_title, #sub_main p.sub_title_vip")
        if title_el:
            title = title_el.get_text(strip=True)

        if not title:
            meta_kw = soup.find("meta", attrs={"name": "keywords"})
            if meta_kw and meta_kw.get("content"):
                title = str(meta_kw["content"])

        # Summary
        plot: Optional[str] = None
        comment_el = soup.select_one("#comment")
        if comment_el:
            plot = comment_el.get_text(strip=True)

        # Fields from table
        actors: List[str] = []
        tags: List[str] = []
        runtime: Optional[int] = None
        premiered: Optional[str] = None

        for tr in soup.select("#detail_box tr, #detail_box_vip tr"):
            td1 = tr.select_one("td.movie_table_td")
            td2 = tr.select_one("td.movie_table_td2")
            if not td1 or not td2:
                continue
            key = td1.get_text(strip=True)
            if key == "モデル":
                actors = [a.strip() for a in td2.get_text().split() if a.strip()]
            elif key == "カテゴリー":
                tags = [a.strip() for a in td2.get_text().split() if a.strip()]
            elif key == "再生時間":
                runtime = self._parse_runtime(td2.get_text(strip=True))
            elif key == "更新日":
                premiered = self._parse_date(td2.get_text(strip=True))

        # Cover from JS variable
        cover: Optional[str] = None
        for script in soup.find_all("script"):
            text = script.string or ""
            m = re.search(r"imgurl\s*=\s*'(.+?)';", text)
            if m:
                cover = self._abs(m.group(1), page_url)
                break

        thumbnail = cover

        # Preview images
        backdrops: List[str] = []
        for a in soup.select("#gallery a, #gallery_vip a"):
            href = a.get("href")
            if href:
                backdrops.append(self._abs(str(href), page_url))

        display_code = f"KIN8-{movie_id}"

        metadata = (
            MetadataBuilder()
            .set_title(title or "", display_code)
            .set_identifier(SITE_NAME, display_code, page_url)
            .set_actors(actors)
            .set_studio("金髪天國")
            .set_tags(tags)
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

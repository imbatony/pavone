"""
JavBus 元数据提取器插件

参考: D:\\code\\metatube-sdk-go-main\\provider\\javbus\\javbus.go
支持的 URL 模式: https://www.javbus.com/ja/{id}
ID 格式: 品番码 (如 ABP-123, N0970, HEYZO-0993)
通过 HTML 页面解析获取元数据。
JavBus 使用 Cloudflare 保护并有年龄验证重定向，
普通 requests 会被 302 至 driver-verify 页面，
因此需要先尝试普通请求，失败时自动回退到浏览器模式（预设 age cookie 跳过验证）。
"""

import re
import time
from typing import List, Optional
from urllib.parse import urlparse

import requests
from bs4 import BeautifulSoup

from ...models import MovieMetadata
from ...utils.metadata_builder import MetadataBuilder
from .base import HtmlMetadataPlugin

PLUGIN_NAME = "JavbusMetadata"
PLUGIN_VERSION = "1.1.0"
PLUGIN_DESCRIPTION = "提取 javbus.com 的视频元数据"
PLUGIN_AUTHOR = "PAVOne"
PLUGIN_PRIORITY = 50

SUPPORTED_DOMAINS = ["javbus.com", "www.javbus.com"]
SITE_NAME = "JavBus"

MOVIE_URL_TEMPLATE = "https://www.javbus.com/ja/{movie_id}"

# 封面 URL 中提取缩略图路径的正则: /cover/xxx_b.jpg → /thumbs/xxx.jpg
_COVER_RE = re.compile(r"(?i)/cover/([a-z\d]+)(?:_b)?\.(jpg|png)")


class JavbusMetadata(HtmlMetadataPlugin):
    """javbus.com 元数据提取器，通过 HTML 页面解析获取数据。"""

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
        # 支持 ABC-123、N0970、HEYZO-0993、GACHI918 等格式
        return bool(re.match(r"^[a-zA-Z]{1,10}[-_]?\d{2,6}$", identifier.strip()))

    def _fetch_page(self, url: str) -> requests.Response:
        """获取页面，自动处理 Cloudflare/年龄验证重定向。

        先尝试普通 HTTP 请求，如果被 Cloudflare/年龄验证拦截，
        则使用浏览器模式并预设 age cookie 以跳过年龄验证。
        """
        resp = self.fetch(
            url,
            timeout=10,
            max_retry=1,
            cookies={"existmag": "all"},
            headers={"Referer": "https://www.javbus.com/"},
        )
        if "driver-verify" not in resp.url and "Age Verification" not in resp.text:
            return resp

        self.logger.info("检测到 Cloudflare/年龄验证重定向，使用浏览器获取")
        return self._fetch_with_browser(url)

    def _fetch_with_browser(self, url: str) -> requests.Response:
        """使用 DrissionPage 浏览器获取页面，预设 cookie 跳过年龄验证。"""
        from DrissionPage import Chromium, ChromiumOptions

        options = ChromiumOptions()
        options.auto_port()
        proxy = self.config.proxy
        if proxy and proxy.enabled and proxy.http_proxy:
            options.set_proxy(proxy.http_proxy)

        browser = Chromium(options)
        try:
            tab = browser.latest_tab
            if not hasattr(tab, "get"):
                self.logger.error("无法获取浏览器标签页")
                return self._empty_response(url)

            # 预设 cookie: 年龄验证 + 磁力显示模式
            tab.set.cookies(  # type: ignore[union-attr]
                [
                    {"name": "age", "value": "verified", "domain": ".javbus.com", "path": "/"},
                    {"name": "existmag", "value": "all", "domain": ".javbus.com", "path": "/"},
                ]
            )
            tab.get(url)  # type: ignore[union-attr]
            tab.wait.doc_loaded()  # type: ignore[union-attr]

            # 等待 Cloudflare 解决后真实内容加载
            start = time.time()
            html = ""
            while time.time() - start < 30:
                html = str(tab.html or "")  # type: ignore[union-attr]
                if html and ("bigImage" in html or "品番:" in html):
                    if "Just a moment" not in html:
                        self.logger.info("页面内容加载完成")
                        break
                time.sleep(1)
            else:
                html = str(tab.html or "")  # type: ignore[union-attr]
                if not html or "Just a moment" in html[:500]:
                    self.logger.error("无法获取页面内容（超时）")
                    return self._empty_response(url)
                self.logger.warning("内容标记未找到，尝试使用当前页面内容")

            resp = requests.Response()
            resp.status_code = 200
            resp._content = html.encode("utf-8")
            resp.encoding = "utf-8"
            resp.url = url
            return resp
        except Exception as e:
            self.logger.error(f"浏览器获取页面失败: {e}")
            return self._empty_response(url)
        finally:
            try:
                browser.quit()
            except Exception:
                pass

    @staticmethod
    def _empty_response(url: str) -> requests.Response:
        resp = requests.Response()
        resp.status_code = 503
        resp._content = b""
        resp.url = url
        return resp

    def _resolve(self, identifier: str):
        if identifier.startswith("http://") or identifier.startswith("https://"):
            parsed = urlparse(identifier)
            parts = parsed.path.rstrip("/").split("/")
            if parts:
                movie_id = parts[-1].upper()
                return movie_id, identifier
            return None, None
        movie_id = identifier.strip().upper()
        return movie_id, MOVIE_URL_TEMPLATE.format(movie_id=movie_id)

    @staticmethod
    def _derive_thumb_url(cover_url: str) -> Optional[str]:
        """从封面 URL 推导缩略图 URL (cover/xxx_b.jpg → thumbs/xxx.jpg)"""
        if _COVER_RE.search(cover_url):
            return _COVER_RE.sub(r"/thumbs/\1.\2", cover_url)
        return None

    @staticmethod
    def _clean_title(title: str) -> str:
        """移除标题末尾的站点名称标记"""
        return re.sub(r"\s*[-–]\s*JavBus\s*$", "", title).strip()

    def _parse(self, soup: BeautifulSoup, movie_id: str, page_url: str) -> Optional[MovieMetadata]:
        # Title + Cover from bigImage
        title: Optional[str] = None
        cover: Optional[str] = None
        big_img = soup.select_one("a.bigImage img")
        if big_img:
            raw_title = str(big_img["title"]) if big_img.get("title") else None
            if raw_title:
                title = self._clean_title(raw_title)
            src = big_img.get("src")
            if src:
                cover = self._abs(str(src), page_url)

        # Fields
        number: Optional[str] = None
        premiered: Optional[str] = None
        runtime: Optional[int] = None
        director: Optional[str] = None
        maker: Optional[str] = None
        label: Optional[str] = None
        serial: Optional[str] = None

        for p in soup.select("div.col-md-3.info p"):
            span = p.find("span")
            if not span:
                continue
            key = span.get_text(strip=True)
            if key == "品番:":
                span2 = p.find_all("span")
                if len(span2) >= 2:
                    number = span2[1].get_text(strip=True)
            elif key == "発売日:":
                full_text = p.get_text(separator=" ", strip=True)
                date_text = full_text.replace(key, "").strip()
                if date_text:
                    premiered = self._parse_date(date_text)
            elif key == "収録時間:":
                full_text = p.get_text(separator=" ", strip=True)
                rt_text = full_text.replace(key, "").strip()
                if rt_text:
                    runtime = self._parse_runtime(rt_text)
            elif key == "監督:":
                a = p.find("a")
                if a:
                    director = a.get_text(strip=True)
            elif key == "メーカー:":
                a = p.find("a")
                if a:
                    maker = a.get_text(strip=True)
            elif key == "レーベル:":
                a = p.find("a")
                if a:
                    label = a.get_text(strip=True)
            elif key == "シリーズ:":
                a = p.find("a")
                if a:
                    serial = a.get_text(strip=True)

        # Genres
        genres: List[str] = []
        for span in soup.select("span.genre"):
            a = span.select_one("label a")
            if a:
                tag = a.get_text(strip=True)
                if tag:
                    genres.append(tag)

        # Preview images
        backdrops: List[str] = []
        for a in soup.select("#sample-waterfall a"):
            href = a.get("href")
            if href:
                backdrops.append(self._abs(str(href), page_url))

        # Actors
        actors: List[str] = []
        for div in soup.select("div.star-name"):
            a = div.find("a")
            if a and a.get("title"):
                actors.append(str(a["title"]))

        display_code = (number or movie_id).upper()

        # 从封面推导缩略图 URL
        thumb_url = self._derive_thumb_url(cover) if cover else None

        metadata = (
            MetadataBuilder()
            .set_title(title or "", display_code)
            .set_identifier(SITE_NAME, display_code, page_url)
            .set_actors(actors)
            .set_director(director)
            .set_studio(maker)
            .set_serial(serial)
            .set_genres(genres)
            .set_tags(genres)
            .set_release_date(premiered)
            .set_runtime(runtime)
            .set_cover(cover)
            .set_thumbnail(thumb_url or cover)
            .set_poster(thumb_url)
            .set_backdrop(backdrops[0] if backdrops else None)
            .set_backdrops(backdrops)
            .set_rating(None)
            .build()
        )
        if label:
            metadata.tagline = label
        metadata.official_rating = "JP-18+"
        self.logger.info(f"成功提取元数据: {display_code}")
        return metadata

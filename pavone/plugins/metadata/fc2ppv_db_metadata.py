"""
FC2PPV-DB 元数据提取器插件

站点: https://fc2ppv-db.com
URL 模式: https://fc2ppv-db.com/ja/videos/{id}
ID 格式: 纯数字 FC2 PPV 编号

注意: 该站点同时受 Cloudflare Turnstile 与年龄确认页保护。
- Cloudflare: 需要真实浏览器（DrissionPage）解决挑战。
- 年龄确认: 设置 cookie ``age-verified=true`` 即可绕过，无需点击按钮。

元数据主要来自页面 SSR 注入的 og/twitter meta 标签:
- og:title       -> 标题（含 ``FC2-PPV-{id}`` 前缀）
- og:description -> 标题 + ``販売者 / 公開日 / 再生時間`` 结构化文本
- og:image       -> 封面缩略图（cloudfront thumbnails）
正文中还包含女优链接（/actresses/）与样品图（/samples/{id}/NNN.webp）。
"""

import re
from typing import List, Optional, Tuple
from urllib.parse import urlparse

import requests
from bs4 import BeautifulSoup

from ...models import BaseMetadata
from ...utils.http_utils import HttpUtils
from ...utils.metadata_builder import MetadataBuilder
from .fc2_base import FC2BaseMetadata

PLUGIN_NAME = "Fc2ppvDbMetadata"
PLUGIN_VERSION = "1.0.0"
PLUGIN_DESCRIPTION = "提取 fc2ppv-db.com 的 FC2 视频元数据"
PLUGIN_AUTHOR = "PAVOne"
PLUGIN_PRIORITY = 22

SUPPORTED_DOMAINS = ["fc2ppv-db.com", "www.fc2ppv-db.com"]
SITE_NAME = "FC2PPV-DB"

MOVIE_URL_TEMPLATE = "https://fc2ppv-db.com/ja/videos/{movie_id}"
ROOT_URL = "https://fc2ppv-db.com/ja"
AGE_COOKIE = {"name": "age-verified", "value": "true", "domain": "fc2ppv-db.com", "path": "/"}


class Fc2ppvDbMetadata(FC2BaseMetadata):
    """fc2ppv-db.com 元数据提取器。"""

    def __init__(self):
        super().__init__()
        self.name = PLUGIN_NAME
        self.version = PLUGIN_VERSION
        self.description = PLUGIN_DESCRIPTION
        self.author = PLUGIN_AUTHOR
        self.priority = PLUGIN_PRIORITY
        self.supported_domains = SUPPORTED_DOMAINS

    def can_extract(self, identifier: str) -> bool:
        if identifier.startswith("http://") or identifier.startswith("https://"):
            return self.can_handle_domain(identifier, SUPPORTED_DOMAINS)
        # 纯数字 FC2 ID 或 FC2/FC2-PPV 前缀
        return self._validate_fc2_identifier(identifier)

    def _fetch_page(self, url: str) -> requests.Response:
        """使用浏览器获取页面：先过 Cloudflare，再以 age-verified cookie 绕过年龄确认页。

        注意: 不能用 "年齢確認" 作为 reject 标记——该站点是 Next.js 应用，年龄确认
        文案作为 i18n 数据常驻于真实页面 HTML 中。改用番号 ``FC2-PPV-{id}`` 作为
        真实页已加载的正向标记（年龄确认页 og:title 为"年齢確認"，不含番号）。
        """
        movie_id = url.rstrip("/").split("/")[-1]
        return HttpUtils.fetch_with_browser(
            url=url,
            proxy_config=self.config.proxy,
            logger=self.logger,
            wait_for_content=[f"FC2-PPV-{movie_id}"],
            reject_content=["Just a moment", "請稍候", "请稍候"],
            max_wait=40,
            cookies=[AGE_COOKIE],
            pre_visit_url=ROOT_URL,
        )

    def _resolve(self, identifier: str) -> Tuple[Optional[str], Optional[str]]:
        if identifier.startswith("http://") or identifier.startswith("https://"):
            parsed = urlparse(identifier)
            parts = [p for p in parsed.path.split("/") if p]
            if "videos" in parts:
                idx = parts.index("videos")
                if idx + 1 < len(parts):
                    return parts[idx + 1], identifier
            return None, None
        fc2_id = self._extract_fc2_id(identifier)
        if not fc2_id:
            return None, None
        return fc2_id, MOVIE_URL_TEMPLATE.format(movie_id=fc2_id)

    def _parse(self, soup: BeautifulSoup, movie_id: str, page_url: str) -> Optional[BaseMetadata]:
        og_title = self._meta(soup, "og:title")
        og_desc = self._meta(soup, "og:description")
        og_image = self._meta(soup, "og:image")

        if not og_title:
            self.logger.error(f"页面缺少 og:title，可能未通过年龄确认或影片不存在: {page_url}")
            return None

        code = self._build_fc2_code(movie_id)

        # 标题：剥离 ``FC2-PPV-{id}`` / ``FC2-{id}`` 前缀
        title = re.sub(r"^FC2[-_]?(?:PPV[-_]?)?\d+\s*", "", og_title).strip()

        seller = self._parse_seller(og_desc)
        premiered = self._parse_premiered(og_desc)
        runtime = self._parse_runtime_from_desc(og_desc)
        actors = self._parse_actors(soup)
        tags = self._parse_tags(soup)
        plot = self._parse_plot(soup)
        backdrops = self._parse_samples(soup, movie_id)

        metadata = (
            MetadataBuilder()
            .set_title(title or "Unknown", code)
            .set_identifier(SITE_NAME, code, page_url)
            .set_actors(actors)
            .set_studio(seller)
            .set_tags(tags)
            .set_plot(plot)
            .set_release_date(premiered)
            .set_runtime(runtime)
            .set_cover(og_image)
            .set_thumbnail(og_image)
            .set_poster(og_image)
            .set_backdrops(backdrops)
            .build()
        )
        metadata.official_rating = "JP-18+"
        self.logger.info(f"成功提取元数据: {code}")
        return metadata

    # ── 解析辅助方法 ──

    @staticmethod
    def _meta(soup: BeautifulSoup, prop: str) -> Optional[str]:
        """读取 og/twitter meta 标签的 content（按 property 或 name 匹配）。"""
        tag = soup.find("meta", attrs={"property": prop}) or soup.find("meta", attrs={"name": prop})
        if tag:
            content = tag.get("content")
            if isinstance(content, str):
                return content
        return None

    @staticmethod
    def _parse_seller(desc: Optional[str]) -> Optional[str]:
        """从 og:description 中解析 ``販売者: XXX /``。"""
        if not desc:
            return None
        m = re.search(r"販売者[:：]\s*([^/]+?)\s*(?:/|$)", desc)
        return m.group(1).strip() if m else None

    @staticmethod
    def _parse_premiered(desc: Optional[str]) -> Optional[str]:
        """从 og:description 中解析 ``公開日: YYYY年M月D日`` -> ``YYYY-MM-DD``。"""
        if not desc:
            return None
        m = re.search(r"公開日[:：]\s*(\d{4})年(\d{1,2})月(\d{1,2})日", desc)
        if m:
            return f"{m.group(1)}-{int(m.group(2)):02d}-{int(m.group(3)):02d}"
        return None

    @staticmethod
    def _parse_runtime_from_desc(desc: Optional[str]) -> Optional[int]:
        """从 og:description 中解析 ``再生時間: HH:MM:SS`` 或 ``MM:SS`` -> 分钟数。"""
        if not desc:
            return None
        m = re.search(r"再生時間[:：]\s*(\d+):(\d+)(?::(\d+))?", desc)
        if not m:
            return None
        if m.group(3) is not None:
            return int(m.group(1)) * 60 + int(m.group(2))
        # MM:SS -> 取分钟部分
        return int(m.group(1))

    @staticmethod
    def _parse_actors(soup: BeautifulSoup) -> List[str]:
        """从 ``/actresses/`` 链接中提取女优名。"""
        actors: List[str] = []
        for a in soup.find_all("a", href=re.compile(r"/actresses/")):
            text = a.get_text(strip=True)
            if text and text not in actors:
                actors.append(text)
        return actors

    # RSC payload 中的标签结构: \"tag\":{\"id\":\"...\",\"name\":\"中出し\",\"videoCount\":N}
    _TAG_PATTERN = re.compile(r'\\"tag\\":\{\\"id\\":\\"[^"\\]+\\",\\"name\\":\\"((?:[^"\\]|\\.)*?)\\",\\"videoCount\\"')

    @classmethod
    def _parse_tags(cls, soup: BeautifulSoup) -> List[str]:
        """从 Next.js RSC payload 中提取影片标签。

        标签数据不在可见 DOM 中，而是序列化在 ``self.__next_f.push(...)`` 的
        转义 JSON 里，形如 ``\"tag\":{\"name\":\"中出し\",...}``。
        """
        html = str(soup)
        tags: List[str] = []
        for name in cls._TAG_PATTERN.findall(html):
            name = name.strip()
            if name and name not in tags:
                tags.append(name)
        return tags

    @staticmethod
    def _parse_samples(soup: BeautifulSoup, movie_id: str) -> List[str]:
        """从页面中提取样品图（``/samples/{id}/NNN.webp``）作为背景图。"""
        html = str(soup)
        pattern = re.compile(r"https://[^\"'\s\\]+/samples/\d+/" + re.escape(movie_id) + r"/\d+\.webp")
        return sorted(set(pattern.findall(html)))

    @staticmethod
    def _parse_plot(soup: BeautifulSoup) -> Optional[str]:
        """从「商品説明」区域提取影片简介。

        结构: ``<h2>...商品説明</h2>`` 后跟一个
        ``<p class="whitespace-pre-wrap ...">`` 段落，保留原始换行。
        """
        for h2 in soup.find_all("h2"):
            if "商品説明" in h2.get_text():
                parent = h2.parent
                p = parent.select_one("p.whitespace-pre-wrap") if parent else None
                if p is None:
                    p = soup.select_one("p.whitespace-pre-wrap")
                if p:
                    text = p.get_text("\n", strip=True)
                    return text or None
                break
        return None

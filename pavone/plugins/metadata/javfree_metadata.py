"""
JAVFREE 元数据提取器插件

参考: D:\\code\\metatube-sdk-go-main\\provider\\javfree\\javfree.go
支持的 URL 模式: https://javfree.me/{id}/fc2-ppv-{number}
ID 格式: FC2-{number} (FC2 内容专用)
通过 HTML 页面解析获取元数据。
"""

import re
from typing import List, Optional
from urllib.parse import urlparse

from bs4 import BeautifulSoup

from ...models import MovieMetadata
from ...utils.metadata_builder import MetadataBuilder
from .base import HtmlMetadataPlugin

PLUGIN_NAME = "JavfreeMetadata"
PLUGIN_VERSION = "1.0.0"
PLUGIN_DESCRIPTION = "提取 javfree.me/javfree.sh 的视频元数据 (FC2 内容)"
PLUGIN_AUTHOR = "PAVOne"
PLUGIN_PRIORITY = 50

SUPPORTED_DOMAINS = ["javfree.me", "javfree.sh", "www.javfree.me", "www.javfree.sh"]
SITE_NAME = "JAVFREE"

MOVIE_URL_TEMPLATE = "https://javfree.me/{post_id}/fc2-ppv-{number}"


class JavfreeMetadata(HtmlMetadataPlugin):
    """javfree.me/javfree.sh 元数据提取器 (FC2 内容)，通过 HTML 解析获取数据。"""

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
        # ID format: {post_id}-{fc2_number} (dual ID)
        return bool(re.match(r"^\d+-\d+$", identifier.strip()))

    def _resolve(self, identifier: str):
        if identifier.startswith("http://") or identifier.startswith("https://"):
            parsed = urlparse(identifier)
            # Match /post_id/slug format
            m = re.search(r"/(\d+)/(.+?)/?$", parsed.path)
            if m:
                movie_id = m.group(2)
                return movie_id, identifier
            return None, None
        parts = identifier.strip().split("-")
        if len(parts) == 2 and parts[0].isdigit() and parts[1].isdigit():
            return identifier.strip(), MOVIE_URL_TEMPLATE.format(post_id=parts[0], number=parts[1])
        return None, None

    def _parse(self, soup: BeautifulSoup, movie_id: str, page_url: str) -> Optional[MovieMetadata]:
        fc2_number: Optional[str] = None
        code: Optional[str] = None
        title: Optional[str] = None
        director: Optional[str] = None
        premiered: Optional[str] = None

        # Title from h1
        h1 = soup.select_one("header.entry-header h1")
        if not h1:
            h1 = soup.select_one("h1.entry-title")
        if h1:
            raw_title = h1.get_text(strip=True)
            # Try FC2 number
            m = re.search(r"FC2[-_]?(?:PPV[-_]?)?(\d+)", raw_title, re.IGNORECASE)
            if m:
                fc2_number = f"FC2-{m.group(1)}"
                title = re.sub(r"(?i)FC2[-_]?(?:PPV[-_]?)?\d+\s*", "", raw_title).strip()
            else:
                # Try [CODE-123] bracket format
                m = re.search(r"\[([A-Z]+-\d+)\]", raw_title)
                if m:
                    code = m.group(1)
                    title = re.sub(r"\[" + re.escape(code) + r"\]\s*", "", raw_title).strip()
                else:
                    title = raw_title

        # Fallback FC2 number from URL
        if not fc2_number and not code:
            slug = page_url.rstrip("/").split("/")[-1]
            m = re.search(r"fc2-ppv-(\d+)", slug, re.IGNORECASE)
            if m:
                fc2_number = f"FC2-{m.group(1)}"

        # Director + Release date from post-author
        author_el = soup.select_one("span.post-author strong")
        if author_el:
            director = author_el.get_text(strip=True)
            next_sib = author_el.next_sibling
            if next_sib and isinstance(next_sib, str):
                premiered = self._parse_date(next_sib.strip())

        # Preview images
        backdrops: List[str] = []
        for img in soup.select("div.entry-content p img"):
            src = img.get("src")
            if src:
                backdrops.append(str(src))

        # Cover: first preview image
        cover: Optional[str] = None
        if backdrops:
            cover = backdrops[0]
            backdrops = backdrops[1:]

        display_code = code or fc2_number or movie_id.upper()

        metadata = (
            MetadataBuilder()
            .set_title(title or "", display_code)
            .set_identifier(SITE_NAME, display_code, page_url)
            .set_actors([])
            .set_studio(None)
            .set_tags([])
            .set_release_date(premiered)
            .set_cover(cover)
            .set_thumbnail(cover)
            .set_backdrops(backdrops)
            .build()
        )
        if director:
            metadata.director = director
        metadata.official_rating = "JP-18+"
        self.logger.info(f"成功提取元数据: {display_code}")
        return metadata

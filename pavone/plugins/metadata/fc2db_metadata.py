"""FC2DB 元数据提取器，使用持久化浏览器复用年龄确认和 Cloudflare 验证状态。"""

import re
from pathlib import Path
from typing import Optional, Tuple
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup, Tag

from ...models import BaseMetadata
from ...utils.http_utils import HttpUtils
from ...utils.metadata_builder import MetadataBuilder
from .fc2_base import FC2BaseMetadata

PLUGIN_NAME = "FC2DBMetadata"
PLUGIN_VERSION = "1.0.0"
PLUGIN_DESCRIPTION = "提取 fc2db.net 的 FC2 视频元数据"
PLUGIN_AUTHOR = "PAVOne"
PLUGIN_PRIORITY = 21

SUPPORTED_DOMAINS = ["fc2db.net", "www.fc2db.net"]
SITE_NAME = "FC2DB"
MOVIE_URL_TEMPLATE = "https://fc2db.net/work/{movie_id}/"


class FC2DBMetadata(FC2BaseMetadata):
    """从 FC2DB 作品详情页提取元数据。"""

    def __init__(self) -> None:
        super().__init__(
            name=PLUGIN_NAME,
            version=PLUGIN_VERSION,
            description=PLUGIN_DESCRIPTION,
            author=PLUGIN_AUTHOR,
            priority=PLUGIN_PRIORITY,
        )
        self.supported_domains = SUPPORTED_DOMAINS

    def can_extract(self, identifier: str) -> bool:
        movie_id, _ = self._resolve(identifier)
        return movie_id is not None

    def _resolve(self, identifier: str) -> Tuple[Optional[str], Optional[str]]:
        identifier = identifier.strip()
        if "://" in identifier:
            if not self.can_handle_domain(identifier, self.supported_domains):
                return None, None
            match = re.fullmatch(r"/work/([0-9]+)/?", urlparse(identifier).path)
            movie_id = match.group(1) if match else None
        else:
            movie_id = self._extract_fc2_id(identifier)
        if not movie_id:
            return None, None
        return movie_id, MOVIE_URL_TEMPLATE.format(movie_id=movie_id)

    def _browser_user_data_path(self) -> Path:
        configured = self.config.download.cache_dir
        cache_dir = Path(configured).expanduser() if configured else Path.home() / ".cache" / "pavone"
        return cache_dir / "browser" / "fc2db-profile"

    def _fetch_page(self, url: str) -> requests.Response:
        movie_id = url.rstrip("/").split("/")[-1]
        self.logger.info("首次访问 FC2DB 时，请在浏览器窗口中完成验证并确认年龄；后续将复用验证状态")
        response = HttpUtils.fetch_with_browser(
            url=url,
            proxy_config=self.config.proxy,
            logger=self.logger,
            wait_for_content=[f"[FC2-PPV-{movie_id}]"],
            reject_content=['action="/__verify_age__"'],
            max_wait=300,
            browser_user_data_path=str(self._browser_user_data_path()),
            browser_load_mode="normal",
        )
        response.raise_for_status()
        return response

    def _parse(self, soup: BeautifulSoup, movie_id: str, page_url: str) -> Optional[BaseMetadata]:
        main = soup.find("main")
        heading = main.find("h1") if main else None
        heading_text = heading.get_text(" ", strip=True) if heading else ""
        match = re.fullmatch(rf"\[FC2-PPV-{re.escape(movie_id)}\]\s*(.+)", heading_text)
        if not main or not match:
            self.logger.error(f"FC2DB 页面缺少目标作品标题，可能未通过验证或作品不存在: {page_url}")
            return None

        details = main.find("dl")
        info = details.parent if details else main
        if not isinstance(info, Tag):
            self.logger.error(f"FC2DB 作品详情结构无效: {page_url}")
            return None

        fields: dict[str, str] = {}
        if details:
            for label in details.find_all("dt"):
                value = label.find_next_sibling("dd")
                if value:
                    fields[label.get_text(strip=True)] = value.get_text(" ", strip=True)
        if fields.get("商品ID", movie_id) != movie_id:
            self.logger.error(f"FC2DB 页面商品 ID 与请求不一致: {page_url}")
            return None

        actors = self._link_names(info, "/actress/")
        tags = self._link_names(info, "/work-tags/")
        description = info.select_one(".prose")
        plot = description.get_text("\n", strip=True) if description else None
        image = soup.find("meta", property="og:image")
        cover = self._get_tag_attr(image, "content")
        if not cover:
            cover = self._get_tag_attr(main.select_one("img.wp-post-image"), "src")
        if cover:
            cover = urljoin(page_url, cover)
        code = self._build_fc2_code(movie_id)
        metadata = (
            MetadataBuilder()
            .set_title(match.group(1).strip(), code)
            .set_identifier(SITE_NAME, code, page_url)
            .set_actors(actors)
            .set_studio(fields.get("作品販売者"))
            .set_release_date(self._parse_date(fields.get("販売日", "")))
            .set_runtime(self._parse_runtime(fields.get("収録時間", "")))
            .set_tags(tags)
            .set_plot(plot)
            .set_cover(cover)
            .set_poster(cover)
            .set_thumbnail(cover)
            .build()
        )
        metadata.official_rating = "JP-18+"
        self.logger.info(f"成功提取元数据: {code}")
        return metadata

    @staticmethod
    def _link_names(info: Tag, path_prefix: str) -> list[str]:
        names: list[str] = []
        for link in info.find_all("a", href=True):
            href = link.get("href")
            if not isinstance(href, str) or not urlparse(href).path.startswith(path_prefix):
                continue
            name = link.get_text(" ", strip=True)
            if name and name not in names:
                names.append(name)
        return names

"""
Javrate复合型插件

支持从 javrate.com 网站提取视频下载链接和元数据。
通过 HttpUtils.fetch_with_browser() 绕过 Cloudflare Turnstile 保护。
"""

import json
import re
from typing import Any, Dict, List, Optional, cast

import requests

from ..models import MovieMetadata, OperationItem, Quality
from ..utils import CodeExtractUtils
from ..utils.html_metadata_utils import HTMLMetadataExtractor
from ..utils.http_utils import HttpUtils
from ..utils.metadata_builder import MetadataBuilder
from ..utils.operation_item_builder import OperationItemBuilder
from .extractors.base import ExtractorPlugin
from .metadata.base import MetadataPlugin

# 定义插件名称和版本
PLUGIN_NAME = "Javrate"
PLUGIN_VERSION = "2.1.0"
PLUGIN_DESCRIPTION = "提取 javrate.com 的视频下载链接和元数据（使用浏览器自动化绕过 Cloudflare）"
PLUGIN_AUTHOR = "PAVOne"

# 定义插件优先级
PLUGIN_PRIORITY = 30

# 定义支持的域名
SUPPORTED_DOMAINS = ["javrate.com", "www.javrate.com"]

SITE_NAME = "Javrate"


class JavratePlugin(ExtractorPlugin, MetadataPlugin):
    """
    Javrate复合型插件，支持视频下载和元数据提取

    由于 javrate.com 使用了 Cloudflare Turnstile 保护，
    通过 HttpUtils.fetch_with_browser() 使用真实浏览器自动化来获取页面内容，
    浏览器会在获取完成后自动关闭。
    页面包含 JSON-LD 结构化数据（schema.org VideoObject），
    可直接从中提取大部分所需信息。
    """

    def __init__(self):
        super().__init__(
            name=PLUGIN_NAME,
            version=PLUGIN_VERSION,
            description=PLUGIN_DESCRIPTION,
            author=PLUGIN_AUTHOR,
            priority=PLUGIN_PRIORITY,
        )
        self.supported_domains = SUPPORTED_DOMAINS
        self.site_name = SITE_NAME

    def fetch(
        self,
        url: str,
        headers: Optional[Dict[str, str]] = None,
        timeout: int = 30,
        verify_ssl: bool = False,
        no_exceptions: bool = False,
        max_retry: Optional[int] = None,
    ) -> requests.Response:
        """使用浏览器自动化绕过 Cloudflare 保护获取网页内容

        通过 HttpUtils.fetch_with_browser() 获取页面，
        浏览器会在获取完成后自动关闭。
        """
        proxy_config = self.config.proxy
        resp = HttpUtils.fetch_with_browser(
            url=url,
            proxy_config=proxy_config,
            logger=self.logger,
            max_wait=timeout,
        )

        if resp.status_code != 200 and not no_exceptions:
            resp.raise_for_status()

        return resp

    # ==================== JSON-LD 解析 ====================

    @staticmethod
    def _parse_json_ld(html: str) -> Optional[Dict[str, Any]]:
        """从 HTML 中解析 JSON-LD 结构化数据（schema.org VideoObject）

        javrate.com 页面包含如下结构：
        <script type="application/ld+json">
        {
          "@type": "VideoObject",
          "name": "MDL-0003 ...",
          "contentUrl": "https://cloud.avking.xyz/.../index.m3u8",
          "thumbnailUrl": "https://picture.avking.xyz/...",
          "duration": "PT1H17M35S",
          "uploadDate": "2023-05-30",
          "actor": [{"@type": "Person", "name": "...", "url": "..."}],
          "identifier": {"@type": "PropertyValue", "name": "code", "Value": "MDL-0003"}
        }
        </script>
        """
        pattern = r'<script[^>]+type=["\']application/ld\+json["\'][^>]*>(.*?)</script>'
        matches = re.findall(pattern, html, re.DOTALL | re.IGNORECASE)
        for match in matches:
            try:
                data: Any = json.loads(match.strip())
                # 可能是单个对象或数组
                if isinstance(data, list):
                    for item in cast(List[Any], data):
                        if isinstance(item, dict):
                            item_dict = cast(Dict[str, Any], item)
                            if item_dict.get("@type") == "VideoObject":
                                return item_dict
                elif isinstance(data, dict):
                    data_dict = cast(Dict[str, Any], data)
                    if data_dict.get("@type") == "VideoObject":
                        return data_dict
            except (json.JSONDecodeError, ValueError):
                continue
        return None

    # ==================== ExtractorPlugin 接口 ====================

    def can_handle(self, url: str) -> bool:
        """检查是否能处理给定的URL"""
        return self.can_handle_domain(url, self.supported_domains)

    def _build_metadata(self, url: str, html: str) -> Optional[MovieMetadata]:
        """从 HTML 中提取所有元数据并构建 MovieMetadata 对象

        extract 和 extract_metadata 的共享逻辑。

        Args:
            url: 页面 URL
            html: 页面 HTML 内容

        Returns:
            构建好的 MovieMetadata 对象，提取失败返回 None
        """
        # 解析 JSON-LD 结构化数据
        json_ld = self._parse_json_ld(html)

        # 提取必要字段
        code = self._extract_code(html, json_ld)
        if not code:
            self.logger.error("未找到视频代码")
            return None
        code = code.upper()

        title = self._extract_title(html, json_ld)
        if not title:
            self.logger.error("未能提取视频标题")
            return None

        # 提取可选字段
        cover_url = self._extract_cover(html, json_ld)
        release_date = self._extract_release_date(html, json_ld)
        studio = self._extract_studio(html)
        actors = self._extract_actors(html, json_ld)
        description = self._extract_description(html, json_ld)
        genres = self._extract_genres(html)

        # 使用 MetadataBuilder 构建元数据
        builder = MetadataBuilder()
        builder.set_title(title, code)
        builder.set_code(code)
        builder.set_site(self.site_name)
        builder.set_url(url)
        builder.set_identifier(self.site_name, code, url)
        if cover_url:
            builder.set_cover(cover_url)
        if release_date:
            builder.set_release_date(release_date)
        if studio:
            builder.set_studio(studio)
        if actors:
            builder.set_actors(actors)
        if description:
            builder.set_plot(description)
        if genres:
            builder.set_genres(genres)

        return builder.build()

    def extract(self, url: str) -> List[OperationItem]:
        """从给定的URL提取下载选项"""
        if not self.can_handle(url):
            return []
        try:
            response = self.fetch(url)
            html = response.text
            if not html:
                self.logger.error("无法获取网页内容")
                return []

            # 提取元数据
            metadata = self._build_metadata(url, html)
            if not metadata or not metadata.code:
                return []

            # 提取 m3u8 链接
            json_ld = self._parse_json_ld(html)
            m3u8_url = self._extract_m3u8(html, json_ld)
            if not m3u8_url:
                self.logger.error("未找到m3u8链接")
                return []

            # 构建操作项
            builder = OperationItemBuilder(SITE_NAME, metadata.title, metadata.code)
            builder.add_stream(url=m3u8_url, quality=Quality.UNKNOWN)
            builder.set_metadata(metadata)
            if metadata.cover:
                builder.set_cover(metadata.cover)
            if metadata.actors:
                builder.set_actors(metadata.actors)
            if metadata.studio:
                builder.set_studio(metadata.studio)
            if metadata.year:
                builder.set_year(metadata.year)
            return builder.build()

        except Exception as e:
            self.logger.error(f"提取视频信息失败: {e}")
            return []

    # ==================== MetadataPlugin 接口 ====================

    def can_extract(self, identifier: str) -> bool:
        """检查是否能提取给定identifier的元数据"""
        return self.can_handle(identifier)

    def extract_metadata(self, identifier: str) -> Optional[MovieMetadata]:
        """从给定的URL提取元数据"""
        if not self.can_extract(identifier):
            return None

        try:
            response = self.fetch(identifier)
            html = response.text
            if not html:
                self.logger.error("无法获取网页内容")
                return None

            return self._build_metadata(identifier, html)

        except Exception as e:
            self.logger.error(f"提取元数据失败: {e}")
            return None

    # ==================== 私有辅助方法 ====================

    def _extract_m3u8(self, html: str, json_ld: Optional[Dict[str, Any]] = None) -> Optional[str]:
        """从HTML中提取m3u8链接

        优先从 JSON-LD 的 contentUrl 字段提取，回退到 HTML 正则匹配。
        """
        # 优先从 JSON-LD 提取
        if json_ld:
            content_url = json_ld.get("contentUrl")
            if content_url and ".m3u8" in content_url:
                return content_url

        # 回退: 尝试匹配各种m3u8链接模式
        patterns = [
            # 匹配source标签中的m3u8链接
            r'<source[^>]+src=["\']([^"\']+\.m3u8[^"\']*)["\']',
            # 匹配video标签中的m3u8链接
            r'<video[^>]+src=["\']([^"\']+\.m3u8[^"\']*)["\']',
            # 匹配JavaScript中的m3u8链接
            r'["\']?(https?://[^"\'<>\s]+\.m3u8[^"\'<>\s]*)["\']?',
            # 匹配data-src属性
            r'data-src=["\']([^"\']+\.m3u8[^"\']*)["\']',
            # 匹配HLS播放器配置
            r'src\s*[:=]\s*["\']([^"\']+\.m3u8[^"\']*)["\']',
            # 匹配file参数
            r'file\s*[:=]\s*["\']([^"\']+\.m3u8[^"\']*)["\']',
        ]

        for pattern in patterns:
            match = re.search(pattern, html, re.IGNORECASE)
            if match:
                return match.group(1)

        return None

    def _extract_cover(self, html: str, json_ld: Optional[Dict[str, Any]] = None) -> Optional[str]:
        """从HTML中提取封面图片链接

        优先从 JSON-LD 的 thumbnailUrl 字段提取。
        """
        # 优先从 JSON-LD 提取
        if json_ld:
            thumbnail = json_ld.get("thumbnailUrl")
            if thumbnail:
                return thumbnail

        # 回退: 尝试提取og:image
        cover_url = HTMLMetadataExtractor.extract_og_image(html)
        if cover_url:
            return cover_url

        # 尝试从特定的图片标签提取
        patterns = [
            r'<img[^>]+src=["\']([^"\']*avking\.xyz[^"\']*)["\']',
            r'background-image:\s*url\(["\']?([^"\')\s]+)["\']?\)',
            r'poster=["\']([^"\']+)["\']',
        ]

        for pattern in patterns:
            match = re.search(pattern, html, re.IGNORECASE)
            if match:
                return match.group(1)

        return None

    def _extract_title(self, html: str, json_ld: Optional[Dict[str, Any]] = None) -> Optional[str]:
        """从HTML中提取视频标题

        优先从 JSON-LD 的 name 字段提取（并去除开头的代码部分）。
        """
        # 优先从 JSON-LD 提取
        if json_ld:
            name = json_ld.get("name")
            if name:
                # JSON-LD name 通常格式为 "CODE 标题"，去除开头的代码部分
                if " " in name:
                    parts = name.split(" ", 1)
                    if len(parts) > 1 and CodeExtractUtils.extract_code_from_text(parts[0]):
                        return parts[1].strip()
                return name

        # 回退: 尝试从og:title提取
        title = HTMLMetadataExtractor.extract_og_title(html)
        if title:
            if " " in title:
                parts = title.split(" ", 1)
                if len(parts) > 1 and CodeExtractUtils.extract_code_from_text(parts[0]):
                    return parts[1].strip()
            return title

        # 尝试从<title>标签提取
        match = re.search(r"<title>([^<]+)</title>", html, re.IGNORECASE)
        if match:
            title = match.group(1).strip()
            title = re.sub(r"\s*[-|]\s*(JAVRATE|鑒黃師).*$", "", title, flags=re.IGNORECASE)
            return title

        # 尝试从h1标签提取
        match = re.search(r"<h1[^>]*>([^<]+)</h1>", html, re.IGNORECASE)
        if match:
            return match.group(1).strip()

        return None

    def _extract_code(self, html: str, json_ld: Optional[Dict[str, Any]] = None) -> Optional[str]:
        """从HTML中提取视频代码

        优先从 JSON-LD 的 identifier.Value 字段提取。
        """
        # 优先从 JSON-LD 提取
        if json_ld:
            identifier = json_ld.get("identifier")
            if isinstance(identifier, dict):
                id_dict = cast(Dict[str, Any], identifier)
                code_val = str(id_dict.get("Value") or id_dict.get("value") or "")
                if code_val:
                    return code_val.upper()

        # 回退: 尝试从番號區塊提取
        patterns = [
            r"番號[^<]*:\s*</h4>\s*<[^>]*>\s*</[^>]*>\s*<h4[^>]*>([A-Z0-9]+-[A-Z0-9]+)</h4>",
            r"番號\s*:\s*</?\w+>\s*<[^>]*>([A-Z0-9]+-[A-Z0-9]+)",
            r"<title>\s*([A-Z0-9]+-[A-Z0-9]+)\s+",
            r'og:title"[^>]+content="([A-Z0-9]+-[A-Z0-9]+)\s+',
            r"<h[12][^>]*>\s*([A-Z0-9]+-[A-Z0-9]+)\s+",
        ]

        for pattern in patterns:
            match = re.search(pattern, html, re.IGNORECASE)
            if match:
                return match.group(1).upper()

        # 尝试从标题或URL中提取代码
        title = self._extract_title(html)
        if title:
            code = CodeExtractUtils.extract_code_from_text(title)
            if code:
                return code.upper()

        return None

    def _extract_release_date(self, html: str, json_ld: Optional[Dict[str, Any]] = None) -> Optional[str]:
        """从HTML中提取发行日期

        优先从 JSON-LD 的 uploadDate 字段提取。
        """
        # 优先从 JSON-LD 提取
        if json_ld:
            upload_date = json_ld.get("uploadDate")
            if upload_date:
                # 格式可能是 "2023-05-30" 或 "2023-05-30T00:00:00"
                date_match = re.match(r"(\d{4}-\d{2}-\d{2})", upload_date)
                if date_match:
                    return date_match.group(1)

        # 回退: 从 HTML 中提取
        patterns = [
            r"發片日期[^<]*:\s*</h4>\s*<[^>]*>\s*</[^>]*>\s*<h4[^>]*>(\d{4}年\d{1,2}月\d{1,2}日)",
            r"發片日期\s*:\s*</?\w+>\s*<[^>]*>(\d{4}[-/]\d{1,2}[-/]\d{1,2})",
            r"(\d{4})年(\d{1,2})月(\d{1,2})日",
        ]

        for pattern in patterns:
            match = re.search(pattern, html)
            if match:
                if len(match.groups()) == 3:
                    year, month, day = match.groups()
                    return f"{year}-{int(month):02d}-{int(day):02d}"
                else:
                    date_str = match.group(1)
                    date_match = re.search(r"(\d{4})年(\d{1,2})月(\d{1,2})日", date_str)
                    if date_match:
                        year, month, day = date_match.groups()
                        return f"{year}-{int(month):02d}-{int(day):02d}"
                    return date_str

        return None

    def _extract_studio(self, html: str) -> Optional[str]:
        """从HTML中提取出品厂商

        javrate.com 的厂商区域结构：
        <a href="/issuer/麻豆傳媒" class="issuer-link" data-issuer-name="麻豆傳媒">
            <h4>麻豆傳媒</h4>
        </a>
        <span class="company-tag-abi">
            <a href="/issuer/麻豆傳媒" ...>417部</a>  <!-- 这是作品数量，不是厂商名 -->
        </span>
        """
        patterns = [
            # 优先从 data-issuer-name 属性提取（最可靠）
            r'data-issuer-name=["\']([^"\']+)["\']',
            # 从出品廠商区域内的 issuer 链接的 <h4> 子标签提取
            r'出品廠商[^<]*:</h4>.*?<a[^>]+href="[^"]*issuer[^"]*"[^>]*>\s*<h4[^>]*>([^<]+)</h4>',
            # 从 issuer 链接的 title 属性提取
            r'<a[^>]+href="[^"]*(?:/issuer/)[^"]*"[^>]+title=["\']([^"\']+)["\']',
        ]

        for pattern in patterns:
            match = re.search(pattern, html, re.IGNORECASE | re.DOTALL)
            if match:
                return match.group(1).strip()

        return None

    def _extract_actors(self, html: str, json_ld: Optional[Dict[str, Any]] = None) -> Optional[List[str]]:
        """从HTML中提取演员列表

        优先从 JSON-LD 的 actor 数组提取。
        """
        # 优先从 JSON-LD 提取
        if json_ld:
            actors_data = json_ld.get("actor")
            if isinstance(actors_data, list) and actors_data:
                actors: List[str] = []
                for actor_item in cast(List[Any], actors_data):
                    if isinstance(actor_item, dict):
                        actor_dict = cast(Dict[str, Any], actor_item)
                        name = str(actor_dict.get("name") or "")
                        if name.strip():
                            actors.append(name.strip())
                    elif isinstance(actor_item, str) and actor_item.strip():
                        actors.append(actor_item.strip())
                if actors:
                    return actors

        # 回退: 从 data-actress-name 属性提取
        pattern_data_attr = r'data-actress-name=["\']([^"\']+)["\']'
        matches = re.findall(pattern_data_attr, html, re.IGNORECASE)
        if matches:
            actors = [m.strip() for m in matches if m.strip()]
            seen: set[str] = set()
            unique_actors: List[str] = []
            for actor in actors:
                if actor not in seen:
                    seen.add(actor)
                    unique_actors.append(actor)
            if unique_actors:
                return unique_actors

        # 回退: 从演员链接提取
        pattern = r'<a[^>]+href="[^"]*actor[^"]*"[^>]*>([^<]+)</a>'
        matches = re.findall(pattern, html, re.IGNORECASE)

        if matches:
            actors = [m.strip() for m in matches if m.strip() and m.strip() != "更多"]
            seen_set: set[str] = set()
            unique_actors_list: List[str] = []
            for actor in actors:
                if actor not in seen_set:
                    seen_set.add(actor)
                    unique_actors_list.append(actor)
            return unique_actors_list if unique_actors_list else None

        return None

    def _extract_description(self, html: str, json_ld: Optional[Dict[str, Any]] = None) -> Optional[str]:
        """从HTML中提取影片剧情描述

        优先从 JSON-LD 的 description 字段提取。
        """
        # 优先从 JSON-LD 提取
        if json_ld:
            description = json_ld.get("description")
            if description and len(description.strip()) > 10:
                return description.strip()

        # 回退: 从 HTML 中提取
        patterns = [
            r"影片(?:剧情|劇情)[^<]*:\s*</h4>\s*(?:<[^>]*>\s*)*([^<]+)",
            r'<meta[^>]+name="description"[^>]+content="([^"]+)"',
        ]

        for pattern in patterns:
            match = re.search(pattern, html, re.IGNORECASE)
            if match:
                desc = match.group(1).strip()
                desc = re.sub(r"\s+", " ", desc)
                if len(desc) > 10:
                    return desc

        return HTMLMetadataExtractor.extract_og_description(html)

    def _extract_genres(self, html: str) -> Optional[List[str]]:
        """从HTML中提取影片分类/标签"""
        pattern = r'<a[^>]+href="[^"]*keywords[^"]*"[^>]*>([^<]+)</a>'
        matches = re.findall(pattern, html, re.IGNORECASE)

        if matches:
            genres = [m.strip() for m in matches if m.strip()]
            seen: set[str] = set()
            unique_genres: List[str] = []
            for genre in genres:
                if genre not in seen:
                    seen.add(genre)
                    unique_genres.append(genre)
            return unique_genres if unique_genres else None

        return None


def register_plugin():
    """注册Javrate复合型插件"""
    return JavratePlugin()

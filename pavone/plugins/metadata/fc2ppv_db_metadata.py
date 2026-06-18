"""
FC2PPV-DB 元数据提取器插件

站点: https://fc2ppv-db.com
URL 模式: https://fc2ppv-db.com/ja/videos/{id}
ID 格式: 纯数字 FC2 PPV 编号

注意: 该站点同时受 Cloudflare Turnstile 与年龄确认页保护。
- Cloudflare: 需要真实浏览器（DrissionPage）解决挑战。
- 年龄确认: 设置 cookie ``age-verified=true`` 即可绕过，无需点击按钮。

数据来源: 该站点是 Next.js 应用，影片的全部元数据以一个结构化 JSON 对象
序列化在 RSC flight payload（``self.__next_f.push([1,"..."])``）中。本插件
直接解析该对象，而非拼凑 og meta / DOM，字段更全也更准确。
"""

import json
import re
from typing import Any, Dict, List, Optional, Tuple, cast
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
# FC2 编号兜底首选: 解析结构化 JSON，字段最全最准（fc2ppv-db → ppvdatabank → supfc2）
PLUGIN_PRIORITY = 18

SUPPORTED_DOMAINS = ["fc2ppv-db.com", "www.fc2ppv-db.com"]
SITE_NAME = "FC2PPV-DB"

MOVIE_URL_TEMPLATE = "https://fc2ppv-db.com/ja/videos/{movie_id}"
ROOT_URL = "https://fc2ppv-db.com/ja"
AGE_COOKIE = {"name": "age-verified", "value": "true", "domain": "fc2ppv-db.com", "path": "/"}

# 图片托管 CDN（thumbnailLocal / imageLocal 均为相对此根的路径）
CDN_BASE = "https://d39jz7pbpqkw9s.cloudfront.net"

# 匹配 RSC flight chunk: self.__next_f.push([1,"<js-string>"])
_FLIGHT_CHUNK = re.compile(r'self\.__next_f\.push\(\[1,"((?:[^"\\]|\\.)*)"\]\)')

# 匹配 RSC 字段引用值（纯小写 hex id，如 ``$44``）；
# ``$undefined`` / ``$D...`` / ``$L...`` 等因含非 hex 字符不会被匹配
_REF_PATTERN = re.compile(r"\$[0-9a-f]+")


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
        return self._validate_fc2_identifier(identifier)

    def _fetch_page(self, url: str) -> requests.Response:
        """使用浏览器获取页面：先过 Cloudflare，再以 age-verified cookie 绕过年龄确认页。

        注意: 不能用 "年齢確認" 作为 reject 标记——该站点是 Next.js 应用，年龄确认
        文案作为 i18n 数据常驻于真实页面 HTML 中。改用番号 ``FC2-PPV-{id}`` 作为
        真实页已加载的正向标记（年龄确认页不含番号）。
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
        video = self._extract_video_object(str(soup), movie_id)
        if not video:
            self.logger.error(f"未能解析到影片数据对象（可能未通过年龄确认或影片不存在）: {page_url}")
            return None

        code = self._build_fc2_code(movie_id)
        cover = self._cdn(video.get("thumbnailLocal"))
        images = [self._as_dict(img) for img in self._as_list(video.get("images"))]
        backdrops = [
            url for img in sorted(images, key=lambda i: i.get("sortOrder", 0)) if (url := self._cdn(img.get("imageLocal")))
        ]
        # 缩略图优先用背景图第一张（与封面区分），无背景图时回退到封面
        thumbnail = backdrops[0] if backdrops else cover

        metadata = (
            MetadataBuilder()
            .set_title(self._str(video.get("title")) or "Unknown", code)
            .set_identifier(SITE_NAME, code, page_url)
            .set_actors(self._actors(video))
            .set_studio(self._seller_name(video))
            .set_tags(self._tags(video))
            .set_plot(self._str(video.get("description")))
            .set_release_date(self._date(self._str(video.get("releaseDate"))))
            .set_runtime(self._runtime(video.get("duration")))
            .set_rating(self._rating(video))
            .set_cover(cover)
            .set_thumbnail(thumbnail)
            .set_poster(cover)
            .set_backdrops(backdrops)
            .build()
        )
        metadata.official_rating = "JP-18+"
        self.logger.info(f"成功提取元数据: {code}")
        return metadata

    # ── RSC payload 解析 ──

    @classmethod
    def _extract_video_object(cls, html: str, movie_id: str) -> Optional[Dict[str, Any]]:
        """从 RSC flight payload 中抠出当前番号的影片主对象。

        步骤: 拼接所有 flight chunk 并按 JS 字符串解码 → 以主对象起始
        ``{"id":"<movie_id>","title":`` 为锚点 → 括号配平截取 → ``json.loads``
        → 解析 RSC 字段引用。

        锚点用主对象自身的 ``id``+``title`` 而非 ``fc2Url``，因为部分影片的 FC2 原始页
        已下架，``fc2Url`` 为 ``null``。
        """
        chunks = _FLIGHT_CHUNK.findall(html)
        if not chunks:
            return None
        try:
            flight = "".join(json.loads(f'"{c}"') for c in chunks)
        except json.JSONDecodeError:
            return None

        anchor = flight.find(f'{{"id":"{movie_id}","title":')
        if anchor < 0:
            return None
        obj_str = cls._balanced_object(flight, anchor)
        if not obj_str:
            return None
        try:
            video = json.loads(obj_str)
        except json.JSONDecodeError:
            return None
        return cls._deref_fields(video, flight)

    @classmethod
    def _deref_fields(cls, video: Dict[str, Any], flight: str) -> Dict[str, Any]:
        """解析影片对象中的 RSC 字段引用。

        RSC 会对重复出现的长文本（如 ``description``）去重，提升为单独的 flight 行，
        字段值变为 ``$<hexid>`` 引用（如 ``"description":"$44"``）。此处将这类引用
        替换回真实文本。``$undefined`` / ``$D<date>`` / ``$L<id>`` 等其他 ``$`` 标记
        因含大写或非 hex 字符不会被 ``_REF_PATTERN`` 匹配，保持原样。
        """
        for key, value in video.items():
            if isinstance(value, str) and _REF_PATTERN.fullmatch(value):
                resolved = cls._deref(value[1:], flight)
                if isinstance(resolved, str):
                    video[key] = resolved
        return video

    @staticmethod
    def _deref(ref_id: str, flight: str) -> Any:
        """取出 flight 中 ``<ref_id>:`` 行的内容并解码。

        RSC 行有两种编码:
        - ``T<hexlen>,<text>``: 文本块，``hexlen`` 为 UTF-8 **字节**长度（文本本身
          可能含真实换行，故必须按声明长度截取，不能按行分割）。
        - 其他: 直接 ``json.loads`` 的 JSON 值。
        """
        marker = f"\n{ref_id}:"
        pos = flight.find(marker)
        if pos < 0:
            if flight.startswith(f"{ref_id}:"):
                pos = -1  # 行首即文件首
            else:
                return None
        payload_start = pos + len(marker) if pos >= 0 else len(ref_id) + 1

        text_match = re.match(r"T([0-9a-f]+),", flight[payload_start:])
        if text_match:
            byte_len = int(text_match.group(1), 16)
            text_start = payload_start + text_match.end()
            raw = flight[text_start:].encode("utf-8")[:byte_len]
            return raw.decode("utf-8", "ignore")

        # 非文本块: 截取到下一个行首再 json.loads
        end = flight.find("\n", payload_start)
        chunk = flight[payload_start:] if end < 0 else flight[payload_start:end]
        try:
            return json.loads(chunk)
        except json.JSONDecodeError:
            return None

    @staticmethod
    def _balanced_object(s: str, anchor: int) -> Optional[str]:
        """从 anchor 处（或其前最近的 ``{``）开始括号配平，截取完整 JSON 对象。

        anchor 可以正好指向对象起始 ``{``，也可以是对象内部某处；后者会先向前
        回溯到最近的 ``{``。
        """
        start = s.rfind("{", 0, anchor + 1)
        if start < 0:
            return None
        depth = 0
        in_str = False
        esc = False
        for i in range(start, len(s)):
            ch = s[i]
            if esc:
                esc = False
            elif ch == "\\":
                esc = True
            elif ch == '"':
                in_str = not in_str
            elif not in_str:
                if ch == "{":
                    depth += 1
                elif ch == "}":
                    depth -= 1
                    if depth == 0:
                        return s[start : i + 1]
        return None

    # ── 字段映射辅助 ──

    @staticmethod
    def _as_dict(value: Any) -> Dict[str, Any]:
        """将任意值安全转为 ``Dict[str, Any]``（非字典返回空字典），消除 json Any 不确定性。"""
        return cast(Dict[str, Any], value) if isinstance(value, dict) else {}

    @staticmethod
    def _as_list(value: Any) -> List[Any]:
        """将任意值安全转为 ``List[Any]``（非列表返回空列表）。"""
        return cast(List[Any], value) if isinstance(value, list) else []

    @staticmethod
    def _str(value: Any) -> Optional[str]:
        """仅当值为非空字符串时返回，否则 None（消除 json Any 类型不确定性）。"""
        return value if isinstance(value, str) and value else None

    @staticmethod
    def _cdn(local_path: Any) -> Optional[str]:
        """将 ``thumbnailLocal`` / ``imageLocal`` 相对路径拼为 CDN 绝对地址。"""
        return f"{CDN_BASE}/{local_path}" if isinstance(local_path, str) and local_path else None

    @classmethod
    def _seller_name(cls, video: Dict[str, Any]) -> Optional[str]:
        return cls._str(cls._as_dict(video.get("seller")).get("name"))

    @classmethod
    def _actors(cls, video: Dict[str, Any]) -> List[str]:
        """从 ``actresses[].actress.name`` 提取女优名。"""
        actors: List[str] = []
        for rel in cls._as_list(video.get("actresses")):
            name = cls._str(cls._as_dict(cls._as_dict(rel).get("actress")).get("name"))
            if name and name not in actors:
                actors.append(name)
        return actors

    @classmethod
    def _tags(cls, video: Dict[str, Any]) -> List[str]:
        """从 ``productTags[].tag.name`` 提取标签。"""
        tags: List[str] = []
        for rel in cls._as_list(video.get("productTags")):
            name = cls._str(cls._as_dict(cls._as_dict(rel).get("tag")).get("name"))
            if name and name not in tags:
                tags.append(name)
        return tags

    @staticmethod
    def _date(release_date: Optional[str]) -> Optional[str]:
        """``$D2025-10-13T00:00:00.000Z`` -> ``YYYY-MM-DD``。"""
        if not release_date:
            return None
        m = re.search(r"(\d{4}-\d{2}-\d{2})", release_date)
        return m.group(1) if m else None

    @staticmethod
    def _runtime(duration: Any) -> Optional[int]:
        """``duration`` 为秒数 -> 分钟（四舍五入）。"""
        if isinstance(duration, (int, float)) and duration > 0:
            return round(duration / 60)
        return None

    @staticmethod
    def _rating(video: Dict[str, Any]) -> Optional[float]:
        """评分: ``avgRating`` 为字符串，仅在有评分人数（``ratingCount`` > 0）时返回。"""
        if (video.get("ratingCount") or 0) <= 0:
            return None
        try:
            value = float(video.get("avgRating") or 0)
        except (TypeError, ValueError):
            return None
        return value or None

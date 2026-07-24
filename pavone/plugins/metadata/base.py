"""
元数据提取器插件基类
"""

import json
import re
from abc import abstractmethod
from dataclasses import asdict, dataclass
from typing import Any, Dict, List, Optional, Tuple, cast
from urllib.parse import urlparse

import requests
from bs4 import BeautifulSoup

from ...models import BaseMetadata
from ..base import BasePlugin


@dataclass
class MetadataDiagnostic:
    """最近一次元数据提取的诊断上下文。"""

    stage: str = "idle"
    error: Optional[str] = None
    exception_type: Optional[str] = None
    http_status: Optional[int] = None
    final_url: Optional[str] = None


class MetadataPlugin(BasePlugin):
    """元数据提取器插件基类

    元数据提取器插件负责从指定的identifier中提取元数据，
    包括视频代码、标题、演员、导演、发行日期等信息。
    """

    def __init__(
        self,
        name: Optional[str] = None,
        version: Optional[str] = "1.0.0",
        description: Optional[str] = "",
        author: Optional[str] = "",
        priority: Optional[int] = 50,
    ):
        super().__init__(
            name=name,
            version=version,
            description=description,
            author=author,
            priority=priority,
        )
        self._last_diagnostic = MetadataDiagnostic()

    def _reset_diagnostic(self) -> None:
        self._last_diagnostic = MetadataDiagnostic(stage="resolve")

    def _set_diagnostic_stage(self, stage: str) -> None:
        self._last_diagnostic.stage = stage

    def _record_response(self, response: requests.Response) -> None:
        self._last_diagnostic.http_status = response.status_code
        self._last_diagnostic.final_url = response.url

    def _record_failure(self, error: str, exception: Optional[Exception] = None) -> None:
        self._last_diagnostic.error = error
        if exception is not None:
            self._last_diagnostic.exception_type = type(exception).__name__
            response = getattr(exception, "response", None)
            if isinstance(response, requests.Response):
                self._record_response(response)

    def get_last_diagnostic(self) -> Dict[str, Any]:
        """返回最近一次提取的诊断快照。"""
        return asdict(self._last_diagnostic)

    def initialize(self) -> bool:
        """初始化插件"""
        self.logger.info(f"初始化 {self.name} 插件")
        return True

    @abstractmethod
    def can_extract(self, identifier: str) -> bool:
        """检查是否能处理该identifier

        Args:
            identifier: 可以是URL、视频代码等标识符

        Returns:
            如果能处理返回True，否则返回False
        """
        pass

    @abstractmethod
    def extract_metadata(self, identifier: str) -> Optional[BaseMetadata]:
        """从给定的identifier提取元数据

        Args:
            identifier: 可以是URL、视频代码等标识符

        Returns:
            提取到的元数据对象，如果失败返回None
        """
        pass

    def select_portrait_image(self, image_urls: List[str], timeout: int = 15) -> Optional[str]:
        """从多张图片中选择一张竖图（宽度<高度）

        依次检查给定的图片URL列表，返回第一张宽度小于高度的图片URL。
        如果都不满足则返回None。

        Args:
            image_urls: 图片URL列表
            timeout: 请求超时时间（秒）

        Returns:
            竖图的URL，如果没有则返回None
        """
        import io

        from PIL import Image

        for url in image_urls:
            try:
                resp = self.fetch(url, timeout=timeout, no_exceptions=True)
                if resp.status_code != 200:
                    continue
                img = Image.open(io.BytesIO(resp.content))
                width, height = img.size
                if width < height:
                    self.logger.debug(f"选择竖图: {url} ({width}x{height})")
                    return url
            except Exception:
                continue
        self.logger.debug("未找到竖图")
        return None


class HtmlMetadataPlugin(MetadataPlugin):
    """HTML 解析类元数据插件的公共基类。

    子类仅需实现: can_extract, _resolve, _parse
    可选覆写: _fetch_page (自定义 HTTP 行为)
    """

    # ── 模板方法 ──

    def extract_metadata(self, identifier: str) -> Optional[BaseMetadata]:
        """模板方法: resolve → fetch → parse，统一错误处理。"""
        self._reset_diagnostic()
        try:
            movie_id, page_url = self._resolve(identifier)
            if not movie_id or not page_url:
                self._record_failure(f"无法解析 identifier: {identifier}")
                self.logger.error(f"无法解析 identifier: {identifier}")
                return None
            self._set_diagnostic_stage("fetch")
            resp = self._fetch_page(page_url)
            self._record_response(resp)
            soup = BeautifulSoup(resp.text, "lxml")
            self._set_diagnostic_stage("parse")
            metadata = self._parse(soup, movie_id, page_url)
            if metadata is None:
                self._record_failure("解析器返回空结果")
            else:
                self._set_diagnostic_stage("complete")
            return metadata
        except requests.RequestException as e:
            self._record_failure(str(e), e)
            self.logger.error(f"HTTP 请求失败: {e}")
            return None
        except Exception as e:
            self._record_failure(str(e), e)
            self.logger.error(f"提取元数据失败: {e}", exc_info=True)
            return None

    def _fetch_page(self, url: str) -> requests.Response:
        """获取页面, 子类可覆写以添加 cookies/headers/特殊超时"""
        return self.fetch(url, timeout=30)

    # ── 抽象方法 ──

    @abstractmethod
    def _resolve(self, identifier: str) -> Tuple[Optional[str], Optional[str]]:
        """将 identifier 解析为 (movie_id, page_url)"""
        ...

    @abstractmethod
    def _parse(self, soup: BeautifulSoup, movie_id: str, page_url: str) -> Optional[BaseMetadata]:
        """从 BeautifulSoup 对象解析元数据"""
        ...

    # ── 公共工具方法 (超集策略) ──

    @staticmethod
    def _abs(url: str, base: str) -> str:
        """相对 URL 转绝对 URL (统一 16 份实现)"""
        if url.startswith("http"):
            return url
        parsed = urlparse(base)
        if url.startswith("//"):
            return f"{parsed.scheme}:{url}"
        return f"{parsed.scheme}://{parsed.netloc}{url}"

    @staticmethod
    def _parse_runtime(text: str) -> Optional[int]:
        """解析时长文本 → 分钟数 (超集: 合并 3 种变体)

        支持: '120分', '1:30:00', '02:15', 'Apx. 122 Min.'
        """
        # Variant 1: Japanese minutes
        m = re.search(r"(\d+)\s*分", text)
        if m:
            return int(m.group(1))
        # Variant 3: English minutes
        m = re.search(r"(\d+)\s*[Mm]in", text)
        if m:
            return int(m.group(1))
        # Variant 2: HH:MM:SS or HH:MM
        m = re.match(r"(\d+):(\d+)(?::(\d+))?", text.strip())
        if m:
            hours = int(m.group(1))
            mins = int(m.group(2))
            return hours * 60 + mins
        return None

    @staticmethod
    def _parse_date(s: str) -> Optional[str]:
        """解析日期文本 → 'YYYY-MM-DD' (超集: 合并 4 种变体)

        支持: '2023/01/02', '2023-01-02', '2023年1月2日', '2023.01.02', '09/15/2022' (MM/DD/YYYY)
        """
        s = s.strip().split("\n")[0].split("(")[0].strip()
        # YYYY-MM-DD, YYYY/MM/DD, YYYY年M月D日, YYYY.MM.DD
        m = re.match(r"(\d{4})[年/\-.](\d{1,2})[月/\-.](\d{1,2})", s)
        if m:
            return f"{m.group(1)}-{int(m.group(2)):02d}-{int(m.group(3)):02d}"
        # MM/DD/YYYY (aventertainments 格式)
        m2 = re.match(r"(\d{1,2})/(\d{1,2})/(\d{4})", s)
        if m2:
            return f"{m2.group(3)}-{int(m2.group(1)):02d}-{int(m2.group(2)):02d}"
        return None

    @staticmethod
    def _parse_iso_duration(s: str) -> Optional[int]:
        """解析 ISO 8601 duration (PT1H30M) → 分钟数"""
        if not s:
            return None
        m = re.match(r"PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?", s)
        if m:
            h = int(m.group(1) or 0)
            mi = int(m.group(2) or 0)
            return h * 60 + mi or None
        m2 = re.search(r"(\d+)\s*分", s)
        if m2:
            return int(m2.group(1))
        return None

    @staticmethod
    def _get_tag_attr(tag: Optional[Any], attr: str) -> Optional[str]:
        """安全获取 BS4 tag 属性, 返回 Optional[str] (消除 _AttributeValue 类型问题)"""
        if tag is None:
            return None
        val = tag.get(attr)
        return str(val) if isinstance(val, str) else None


class ApiMetadataPlugin(MetadataPlugin):
    """API/JSON 类元数据插件的公共基类。

    子类仅需实现: can_extract, _resolve, _build_api_url, _parse
    可选覆写: _fetch_api (自定义 HTTP 行为)
    """

    def extract_metadata(self, identifier: str) -> Optional[BaseMetadata]:
        """模板方法: resolve → build_api_url → fetch_api → json → parse。"""
        self._reset_diagnostic()
        try:
            movie_id, page_url = self._resolve(identifier)
            if not movie_id or not page_url:
                self._record_failure(f"无法解析 identifier: {identifier}")
                self.logger.error(f"无法解析 identifier: {identifier}")
                return None
            api_url = self._build_api_url(movie_id)
            self._set_diagnostic_stage("fetch")
            resp = self._fetch_api(api_url)
            self._record_response(resp)
            self._set_diagnostic_stage("parse")
            data = resp.json()
            metadata = self._parse(data, movie_id, page_url)
            if metadata is None:
                self._record_failure("解析器返回空结果")
            else:
                self._set_diagnostic_stage("complete")
            return metadata
        except requests.RequestException as e:
            self._record_failure(str(e), e)
            self.logger.error(f"HTTP 请求失败: {e}")
            return None
        except Exception as e:
            self._record_failure(str(e), e)
            self.logger.error(f"提取元数据失败: {e}", exc_info=True)
            return None

    def _fetch_api(self, url: str) -> requests.Response:
        """获取 API 响应, 子类可覆写以添加 headers/认证"""
        return self.fetch(url, timeout=30)

    @abstractmethod
    def _build_api_url(self, movie_id: str) -> str:
        """构建 API 请求 URL"""
        ...

    @abstractmethod
    def _resolve(self, identifier: str) -> Tuple[Optional[str], Optional[str]]:
        """将 identifier 解析为 (movie_id, page_url)"""
        ...

    @abstractmethod
    def _parse(self, data: Dict[str, Any], movie_id: str, page_url: str) -> Optional[BaseMetadata]:
        """从 JSON 响应数据解析元数据"""
        ...


class JsonLdMetadataPlugin(HtmlMetadataPlugin):
    """JSON-LD 解析类元数据插件的公共基类。

    继承 HtmlMetadataPlugin, 在 HTML 解析基础上增加 JSON-LD 自动提取。
    子类仅需实现: can_extract, _resolve, _parse_with_jsonld
    """

    def extract_metadata(self, identifier: str) -> Optional[BaseMetadata]:
        """模板方法: resolve → fetch → BS4 → extract_jsonld → parse_with_jsonld。"""
        self._reset_diagnostic()
        try:
            movie_id, page_url = self._resolve(identifier)
            if not movie_id or not page_url:
                self._record_failure(f"无法解析 identifier: {identifier}")
                self.logger.error(f"无法解析 identifier: {identifier}")
                return None
            self._set_diagnostic_stage("fetch")
            resp = self._fetch_page(page_url)
            self._record_response(resp)
            soup = BeautifulSoup(resp.text, "lxml")
            jsonld_data = self._extract_jsonld(soup)
            self._set_diagnostic_stage("parse")
            metadata = self._parse_with_jsonld(soup, jsonld_data, movie_id, page_url)
            if metadata is None:
                self._record_failure("JSON-LD 解析器返回空结果")
            else:
                self._set_diagnostic_stage("complete")
            return metadata
        except requests.RequestException as e:
            self._record_failure(str(e), e)
            self.logger.error(f"HTTP 请求失败: {e}")
            return None
        except Exception as e:
            self._record_failure(str(e), e)
            self.logger.error(f"提取元数据失败: {e}", exc_info=True)
            return None

    def _extract_jsonld(self, soup: BeautifulSoup) -> Optional[Dict[str, Any]]:
        """从 HTML 中提取 JSON-LD 数据"""
        for script in soup.find_all("script", type="application/ld+json"):
            try:
                text = (script.string or "").replace("\n", "")
                data: object = json.loads(text)
                if isinstance(data, list):
                    items = cast(List[object], data)
                    data = items[0] if items else None
                if isinstance(data, dict):
                    return cast(Dict[str, Any], data)
            except Exception:
                continue
        return None

    @abstractmethod
    def _parse_with_jsonld(
        self,
        soup: BeautifulSoup,
        jsonld: Optional[Dict[str, Any]],
        movie_id: str,
        page_url: str,
    ) -> Optional[BaseMetadata]:
        """从 JSON-LD + HTML soup 解析元数据"""
        ...

    def _parse(self, soup: BeautifulSoup, movie_id: str, page_url: str) -> Optional[BaseMetadata]:
        """重定向到 _parse_with_jsonld, 保持 HtmlMetadataPlugin 兼容"""
        jsonld_data = self._extract_jsonld(soup)
        return self._parse_with_jsonld(soup, jsonld_data, movie_id, page_url)

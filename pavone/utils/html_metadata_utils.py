"""
HTML Metadata Extraction Utilities - HTML元数据提取工具

提供统一的HTML元数据提取方法，消除插件中的重复代码。
"""

import re
from typing import Optional


class HTMLMetadataExtractor:
    """HTML元数据提取器 - 提供统一的HTML元数据提取方法"""

    # Open Graph 元数据模式
    OG_TITLE_PATTERN = r'<meta\s+property="og:title"\s+content="([^"]+)"'
    OG_IMAGE_PATTERN = r'<meta\s+property="og:image"\s+content="([^"]+)"'
    OG_DESCRIPTION_PATTERN = r'<meta\s+property="og:description"\s+content="([^"]+)"'
    OG_URL_PATTERN = r'<meta\s+property="og:url"\s+content="([^"]+)"'
    OG_TYPE_PATTERN = r'<meta\s+property="og:type"\s+content="([^"]+)"'
    OG_VIDEO_PATTERN = r'<meta\s+property="og:video"\s+content="([^"]+)"'
    OG_VIDEO_URL_PATTERN = r'<meta\s+property="og:video:url"\s+content="([^"]+)"'

    @staticmethod
    def extract_og_title(html: str) -> Optional[str]:
        """
        提取 Open Graph title 元数据

        Args:
            html: HTML内容

        Returns:
            提取的标题，如果未找到则返回 None
        """
        match = re.search(HTMLMetadataExtractor.OG_TITLE_PATTERN, html, re.IGNORECASE)
        if match:
            return match.group(1).strip()
        return None

    @staticmethod
    def extract_og_image(html: str) -> Optional[str]:
        """
        提取 Open Graph image 元数据

        Args:
            html: HTML内容

        Returns:
            提取的图片URL，如果未找到则返回 None
        """
        match = re.search(HTMLMetadataExtractor.OG_IMAGE_PATTERN, html, re.IGNORECASE)
        if match:
            return match.group(1).strip()
        return None

    @staticmethod
    def extract_og_description(html: str) -> Optional[str]:
        """
        提取 Open Graph description 元数据

        Args:
            html: HTML内容

        Returns:
            提取的描述，如果未找到则返回 None
        """
        match = re.search(HTMLMetadataExtractor.OG_DESCRIPTION_PATTERN, html, re.IGNORECASE)
        if match:
            return match.group(1).strip()
        return None

    @staticmethod
    def extract_og_url(html: str) -> Optional[str]:
        """
        提取 Open Graph URL 元数据

        Args:
            html: HTML内容

        Returns:
            提取的URL，如果未找到则返回 None
        """
        match = re.search(HTMLMetadataExtractor.OG_URL_PATTERN, html, re.IGNORECASE)
        if match:
            return match.group(1).strip()
        return None

    @staticmethod
    def extract_og_type(html: str) -> Optional[str]:
        """
        提取 Open Graph type 元数据

        Args:
            html: HTML内容

        Returns:
            提取的类型，如果未找到则返回 None
        """
        match = re.search(HTMLMetadataExtractor.OG_TYPE_PATTERN, html, re.IGNORECASE)
        if match:
            return match.group(1).strip()
        return None

    @staticmethod
    def extract_og_video(html: str) -> Optional[str]:
        """
        提取 Open Graph video 元数据

        Args:
            html: HTML内容

        Returns:
            提取的视频URL，如果未找到则返回 None
        """
        match = re.search(HTMLMetadataExtractor.OG_VIDEO_PATTERN, html, re.IGNORECASE)
        if match:
            return match.group(1).strip()
        return None

    @staticmethod
    def extract_og_video_url(html: str) -> Optional[str]:
        """
        提取 Open Graph video:url 元数据

        Args:
            html: HTML内容

        Returns:
            提取的视频URL，如果未找到则返回 None
        """
        match = re.search(HTMLMetadataExtractor.OG_VIDEO_URL_PATTERN, html, re.IGNORECASE)
        if match:
            return match.group(1).strip()
        return None

    @staticmethod
    def extract_meta_tag(html: str, property_name: str, attribute: str = "content") -> Optional[str]:
        """
        通用 meta 标签提取方法

        Args:
            html: HTML内容
            property_name: meta 标签的 property 或 name 属性值
            attribute: 要提取的属性名，默认为 "content"

        Returns:
            提取的属性值，如果未找到则返回 None

        Examples:
            >>> extract_meta_tag(html, "og:title")
            "示例标题"
            >>> extract_meta_tag(html, "description", "content")
            "示例描述"
        """
        # 尝试 property 属性
        pattern = rf'<meta\s+property="{re.escape(property_name)}"\s+{re.escape(attribute)}="([^"]+)"'
        match = re.search(pattern, html, re.IGNORECASE)
        if match:
            return match.group(1).strip()

        # 尝试 name 属性
        pattern = rf'<meta\s+name="{re.escape(property_name)}"\s+{re.escape(attribute)}="([^"]+)"'
        match = re.search(pattern, html, re.IGNORECASE)
        if match:
            return match.group(1).strip()

        # 尝试反向顺序 (attribute 在前)
        pattern = rf'<meta\s+{re.escape(attribute)}="([^"]+)"\s+property="{re.escape(property_name)}"'
        match = re.search(pattern, html, re.IGNORECASE)
        if match:
            return match.group(1).strip()

        pattern = rf'<meta\s+{re.escape(attribute)}="([^"]+)"\s+name="{re.escape(property_name)}"'
        match = re.search(pattern, html, re.IGNORECASE)
        if match:
            return match.group(1).strip()

        return None

    @staticmethod
    def extract_with_pattern(html: str, pattern: str, group: int = 1) -> Optional[str]:
        """
        使用自定义正则表达式提取内容

        Args:
            html: HTML内容
            pattern: 正则表达式模式
            group: 要提取的分组编号，默认为 1

        Returns:
            提取的内容，如果未找到则返回 None
        """
        match = re.search(pattern, html, re.IGNORECASE | re.DOTALL)
        if match:
            return match.group(group).strip()
        return None

    @staticmethod
    def extract_all_with_pattern(html: str, pattern: str, group: int = 1) -> list[str]:
        """
        使用自定义正则表达式提取所有匹配的内容

        Args:
            html: HTML内容
            pattern: 正则表达式模式
            group: 要提取的分组编号，默认为 1

        Returns:
            提取的内容列表
        """
        matches = re.finditer(pattern, html, re.IGNORECASE | re.DOTALL)
        return [match.group(group).strip() for match in matches]


# ============================================================================
# T028: 独立提取函数 — 插件按需调用, 通过参数适配不同站点
# ============================================================================

_extractor = HTMLMetadataExtractor


def extract_title(
    html: str,
    selectors: Optional[list[str]] = None,
    patterns: Optional[list[str]] = None,
) -> Optional[str]:
    """提取标题: 先尝试 OG 标签, 再尝试自定义选择器/正则.

    Args:
        html: HTML 内容
        selectors: CSS 选择器列表 (需要 BeautifulSoup, 暂不使用)
        patterns: 自定义正则列表, 每个应包含一个捕获组
    """
    # 1. OG 标签
    result = _extractor.extract_og_title(html)
    if result:
        return result

    # 2. 自定义正则
    if patterns:
        for pattern in patterns:
            result = _extractor.extract_with_pattern(html, pattern)
            if result:
                return result

    # 3. <title> 标签 fallback
    result = _extractor.extract_with_pattern(html, r"<title[^>]*>([^<]+)</title>")
    return result


def extract_code(
    html: str,
    patterns: Optional[list[str]] = None,
) -> Optional[str]:
    """提取番号/识别码.

    Args:
        html: HTML 内容
        patterns: 自定义正则列表
    """
    if patterns:
        for pattern in patterns:
            result = _extractor.extract_with_pattern(html, pattern)
            if result:
                return result.strip().upper()
    return None


def extract_cover(
    html: str,
    selectors: Optional[list[str]] = None,
    patterns: Optional[list[str]] = None,
) -> Optional[str]:
    """提取封面图 URL: 先尝试 OG image, 再尝试自定义.

    Args:
        html: HTML 内容
        selectors: 未使用 (预留)
        patterns: 自定义正则列表
    """
    result = _extractor.extract_og_image(html)
    if result:
        return result

    if patterns:
        for pattern in patterns:
            result = _extractor.extract_with_pattern(html, pattern)
            if result:
                return result
    return None


def extract_date(
    html: str,
    patterns: Optional[list[str]] = None,
    formats: Optional[list[str]] = None,
) -> Optional[str]:
    """提取日期字符串.

    Args:
        html: HTML 内容
        patterns: 自定义正则列表
        formats: 日期格式列表 (预留, 当前仅返回原始匹配)
    """
    # 通用日期模式
    default_patterns = [
        r"(\d{4}-\d{2}-\d{2})",  # ISO: 2024-01-15
        r"(\d{4}/\d{2}/\d{2})",  # Slash: 2024/01/15
        r"(\d{4}\u5e74\d{1,2}\u6708\d{1,2}\u65e5)",  # JP: 2024年1月15日
    ]

    all_patterns = (patterns or []) + default_patterns
    for pattern in all_patterns:
        result = _extractor.extract_with_pattern(html, pattern)
        if result:
            return result
    return None


def extract_actors(
    html: str,
    selectors: Optional[list[str]] = None,
    patterns: Optional[list[str]] = None,
) -> list[str]:
    """提取演员列表.

    Args:
        html: HTML 内容
        selectors: 未使用 (预留)
        patterns: 自定义正则, 每个应匹配单个演员名
    """
    if patterns:
        for pattern in patterns:
            results = _extractor.extract_all_with_pattern(html, pattern)
            if results:
                return [r.strip() for r in results if r.strip()]
    return []


def extract_genres(
    html: str,
    selectors: Optional[list[str]] = None,
    patterns: Optional[list[str]] = None,
) -> list[str]:
    """提取类型/标签列表.

    Args:
        html: HTML 内容
        selectors: 未使用 (预留)
        patterns: 自定义正则
    """
    if patterns:
        for pattern in patterns:
            results = _extractor.extract_all_with_pattern(html, pattern)
            if results:
                return [r.strip() for r in results if r.strip()]
    return []


def extract_m3u8_url(
    html: str,
    patterns: Optional[list[str]] = None,
) -> Optional[str]:
    """提取 M3U8 播放列表 URL.

    Args:
        html: HTML 内容
        patterns: 自定义正则列表
    """
    default_patterns = [
        r'(https?://[^\s"\'<>]+\.m3u8[^\s"\'<>]*)',
    ]
    all_patterns = (patterns or []) + default_patterns
    for pattern in all_patterns:
        result = _extractor.extract_with_pattern(html, pattern)
        if result:
            return result
    return None

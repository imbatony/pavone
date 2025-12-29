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

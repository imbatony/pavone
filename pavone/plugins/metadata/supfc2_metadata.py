"""
SupFC2元数据提取器插件

支持从 supfc2.com 网站提取FC2视频元数据。
"""

import re
from typing import List, Optional, Tuple

import requests
from bs4 import BeautifulSoup

from ...models import BaseMetadata
from ...utils.html_metadata_utils import HTMLMetadataExtractor
from ...utils.metadata_builder import MetadataBuilder
from .fc2_base import FC2BaseMetadata

# 定义插件名称和版本
PLUGIN_NAME = "SupFC2Metadata"
PLUGIN_VERSION = "1.0.0"
PLUGIN_DESCRIPTION = "提取 supfc2.com 的FC2视频元数据"
PLUGIN_AUTHOR = "PAVOne"

# 定义插件优先级
PLUGIN_PRIORITY = 25

# 定义支持的域名
SUPPORTED_DOMAINS = ["supfc2.com", "www.supfc2.com"]

SITE_NAME = "SupFC2"


class SupFC2Metadata(FC2BaseMetadata):
    """
    SupFC2元数据提取器
    继承自 FC2BaseMetadata，提供从 supfc2.com 提取FC2视频元数据的功能。
    """

    def __init__(self):
        """初始化SupFC2元数据提取器"""
        super().__init__()
        self.name = PLUGIN_NAME
        self.version = PLUGIN_VERSION
        self.description = PLUGIN_DESCRIPTION
        self.priority = PLUGIN_PRIORITY
        self.supported_domains = SUPPORTED_DOMAINS
        self.author = PLUGIN_AUTHOR

    def can_extract(self, identifier: str) -> bool:
        """检查是否能处理给定的identifier

        支持两种格式：
        1. URL: https://supfc2.com/detail/FC2-PPV-1482027/...
        2. FC2代码: FC2-1482027, 1482027 等格式
        """
        # 检查是否为URL
        if identifier.startswith("http://") or identifier.startswith("https://"):
            return self.can_handle_domain(identifier, self.supported_domains)

        # 检查是否为FC2代码
        identifier_stripped = identifier.strip().upper()
        fc2_pattern = r"^(FC2[-_]?)?(?:PPV[-_]?)?(\d+)$"
        return bool(re.match(fc2_pattern, identifier_stripped))

    def _fetch_page(self, url: str) -> requests.Response:
        """获取页面, verify_ssl=False: supfc2 站点 SSL 证书配置不标准，需跳过验证"""
        return self.fetch(url, timeout=30, verify_ssl=False, max_retry=2)

    def _resolve(self, identifier: str) -> Tuple[Optional[str], Optional[str]]:
        """将 identifier 解析为 (fc2_id, page_url)"""
        if identifier.startswith("http://") or identifier.startswith("https://"):
            fc2_id = self._extract_fc2_id_from_url(identifier)
            if not fc2_id:
                return None, None
            return fc2_id, identifier

        fc2_id = self._extract_fc2_id(identifier)
        if not fc2_id:
            return None, None
        url = f"https://supfc2.com/detail/FC2-PPV-{fc2_id}/detail"
        return fc2_id, url

    def extract_metadata(self, identifier: str) -> Optional[BaseMetadata]:
        """覆写模板方法，额外保存原始 HTML 供正则提取使用。

        lxml 解析器会重组 <head>/<body> 等文档结构标签，导致 str(soup) 与原始 HTML
        不一致，正则在 str(soup) 上匹配 og:image 等 meta 标签会失败。
        """
        try:
            movie_id, page_url = self._resolve(identifier)
            if not movie_id or not page_url:
                self.logger.error(f"无法解析 identifier: {identifier}")
                return None
            resp = self._fetch_page(page_url)
            self._raw_html = resp.text
            soup = BeautifulSoup(resp.text, "lxml")
            return self._parse(soup, movie_id, page_url)
        except Exception as e:
            self.logger.error(f"提取元数据失败: {e}", exc_info=True)
            return None

    def _parse(self, soup: BeautifulSoup, movie_id: str, page_url: str) -> Optional[BaseMetadata]:
        """从 BeautifulSoup 对象解析元数据"""
        # 优先使用原始 HTML 做正则提取（避免 lxml DOM 重组导致的匹配失败）
        html_content = getattr(self, "_raw_html", None) or str(soup)

        title = self._extract_title(html_content)
        fc2_id_from_page = self._extract_fc2_id_from_page(html_content)
        release_date = self._extract_release_date(html_content)
        maker = self._extract_maker(html_content)
        duration = self._extract_duration(html_content)
        tags = self._extract_tags(html_content)
        genres = self._extract_genres(html_content)
        rating = self._extract_rating(html_content)
        description = self._extract_description(html_content, soup)
        cover_image, background_image = self._extract_images(html_content)

        # 使用从页面提取的FC2 ID（如果有）
        fc2_id = fc2_id_from_page if fc2_id_from_page else movie_id

        video_code = f"FC2-{fc2_id}"

        metadata = (
            MetadataBuilder()
            .set_title(title or "Unknown", video_code)
            .set_identifier(SITE_NAME, video_code, page_url)
            .set_director(maker)
            .set_runtime(duration)
            .set_release_date(release_date)
            .set_genres(genres)
            .set_tags(tags)
            .set_studio(maker)
            .set_cover(cover_image)
            .set_backdrop(background_image)
            .set_plot(description)
            .set_rating(rating)
            .build()
        )
        metadata.official_rating = "JP-18+"

        self.logger.info(f"成功提取元数据: {video_code}")
        return metadata

    def _extract_fc2_id_from_url(self, url: str) -> Optional[str]:
        """从URL中提取FC2 ID"""
        # URL格式: https://supfc2.com/detail/FC2-PPV-1482027/...
        pattern = r"/detail/FC2-PPV-(\d+)/"
        match = re.search(pattern, url, re.IGNORECASE)
        return match.group(1) if match else None

    def _extract_title(self, html_content: str) -> Optional[str]:
        """提取标题"""
        try:
            # 从页面标题中提取
            title_pattern = r"<title>\[FC2-PPV-\d+\](.+?)\s*-\s*SupFC2\.com</title>"
            match = re.search(title_pattern, html_content)
            if match:
                return match.group(1).strip()
            return None
        except Exception as e:
            self.logger.error(f"提取标题失败: {str(e)}")
            return None

    def _extract_fc2_id_from_page(self, html_content: str) -> Optional[str]:
        """从页面中提取FC2 ID"""
        try:
            # 查找 <label>FC2's ID: </label> 后的内容
            pattern = r'<label>FC2&#039;s ID:\s*</label>\s*<span class="detail">(\d+)</span>'
            match = re.search(pattern, html_content)
            if match:
                return match.group(1)
            return None
        except Exception as e:
            self.logger.error(f"提取FC2 ID失败: {str(e)}")
            return None

    def _extract_release_date(self, html_content: str) -> Optional[str]:
        """提取发行日期"""
        try:
            pattern = r'<label>Release Date:\s*</label>\s*<span class="detail">(\d{4}-\d{2}-\d{2})</span>'
            match = re.search(pattern, html_content)
            if match:
                return match.group(1)
            return None
        except Exception as e:
            self.logger.error(f"提取发行日期失败: {str(e)}")
            return None

    def _extract_maker(self, html_content: str) -> Optional[str]:
        """提取制作商"""
        try:
            pattern = r"<label>Maker:\s*</label>\s*<a[^>]*>([^<]+)</a>"
            match = re.search(pattern, html_content)
            if match:
                return match.group(1).strip()
            return None
        except Exception as e:
            self.logger.error(f"提取制作商失败: {str(e)}")
            return None

    def _extract_duration(self, html_content: str) -> Optional[int]:
        """提取时长（分钟）"""
        try:
            # 格式: 01:02:12
            pattern = r'<label>Duration:\s*</label>\s*<span class="detail">(\d{2}):(\d{2}):(\d{2})</span>'
            match = re.search(pattern, html_content)
            if match:
                hours = int(match.group(1))
                minutes = int(match.group(2))
                seconds = int(match.group(3))
                total_minutes = hours * 60 + minutes + (1 if seconds >= 30 else 0)
                return total_minutes
            return None
        except Exception as e:
            self.logger.error(f"提取时长失败: {str(e)}")
            return None

    def _extract_tags(self, html_content: str) -> List[str]:
        """提取标签"""
        try:
            tags: List[str] = []
            # 查找 <label>Tag: </label> 后的所有链接
            # 首先找到Tag标签的位置
            tag_section_pattern = r"<label>Tag:\s*</label>(.*?)</li>"
            match = re.search(tag_section_pattern, html_content, re.DOTALL)
            if match:
                tag_section = match.group(1)
                # 提取所有标签链接
                tag_pattern = r"<a[^>]*>([^<]+)</a>"
                tag_matches = re.findall(tag_pattern, tag_section)
                for tag in tag_matches:
                    tag = tag.strip()
                    if tag and tag != "UNKNOWN":
                        tags.append(tag)
            return tags
        except Exception as e:
            self.logger.error(f"提取标签失败: {str(e)}")
            return []

    def _extract_genres(self, html_content: str) -> List[str]:
        """提取类型"""
        try:
            genres: List[str] = []
            # 查找 <label>Genre: </label> 后的链接
            pattern = r"<label>Genre:\s*</label>.*?<a[^>]*>([^<]+)</a>"
            matches = re.finditer(pattern, html_content, re.DOTALL)
            for match in matches:
                genre = match.group(1).strip()
                if genre:
                    genres.append(genre)
            return genres
        except Exception as e:
            self.logger.error(f"提取类型失败: {str(e)}")
            return []

    def _extract_rating(self, html_content: str) -> Optional[float]:
        """提取评分"""
        try:
            # 从 ratings style width 提取百分比
            pattern = r'<span class="ratings" style="width:\s*(\d+)%'
            match = re.search(pattern, html_content)
            if match:
                percentage = int(match.group(1))
                # 转换为10分制
                return round(percentage / 10.0, 1)
            return None
        except Exception as e:
            self.logger.error(f"提取评分失败: {str(e)}")
            return None

    def _extract_description(self, html_content: str, soup: Optional[BeautifulSoup] = None) -> Optional[str]:
        """提取描述（去除图片）

        优先使用 BeautifulSoup 解析，回退到正则匹配原始 HTML。
        注意: supfc2 页面的描述区域包含嵌套 <body> 标签，lxml 解析器会重组 DOM，
        导致 str(soup) 后正则无法匹配，因此需要用 soup 的 API 直接定位。
        """
        try:
            desc_html = None

            # 方式 1: 用 BeautifulSoup 定位描述区域
            if soup is not None:
                for heading_text in ["映画の説明", "Movie Description"]:
                    h4 = soup.find("h4", string=re.compile(re.escape(heading_text)))  # type: ignore[call-overload]
                    if h4:
                        desc_div = h4.find_next_sibling("div", class_="mb-4")
                        if desc_div:
                            desc_html = desc_div.decode_contents()
                            break

            # 方式 2: 回退到原始 HTML 正则（适用于未传入 soup 的场景）
            if not desc_html:
                patterns = [
                    r'<h4[^>]*>映画の説明</h4>\s*<div class="mb-4">[^<]*<body><p>(.*?)</p>',
                    r'<h4[^>]*>Movie Description</h4>\s*<div class="mb-4">[^<]*<body><p>(.*?)</p>',
                ]
                for pattern in patterns:
                    match = re.search(pattern, html_content, re.DOTALL)
                    if match:
                        desc_html = match.group(1)
                        break

            if desc_html:
                # 移除所有图片链接
                desc_html = re.sub(r"<a[^>]*data-fancybox[^>]*>.*?</a>", "", desc_html, flags=re.DOTALL)
                # <br> 转换为换行
                desc_html = re.sub(r"<br\s*/?>", "\n", desc_html)
                # 移除其他 HTML 标签
                desc_html = re.sub(r"<[^>]+>", "", desc_html)
                # 清理多余空白
                desc_text = re.sub(r"\n\s*\n", "\n\n", desc_html)
                return desc_text.strip() or None
            return None
        except Exception as e:
            self.logger.error(f"提取描述失败: {str(e)}")
            return None

    def _extract_images(self, html_content: str) -> tuple[Optional[str], Optional[str]]:
        """提取缩略图和背景图

        Returns:
            tuple: (cover_image, background_image)
                - cover_image: 第一张图片作为缩略图
                - background_image: 第二张图片作为背景图
        """
        try:
            # 从 og:image 提取图片
            cover = HTMLMetadataExtractor.extract_og_image(html_content)

            # 提取所有 og:image
            pattern = r'<meta property="og:image" content="([^"]+)"'
            matches = re.findall(pattern, html_content)

            # 过滤掉网站logo
            images = [img for img in matches if "supfc2.png" not in img]

            cover = images[0] if len(images) > 0 else None
            background = images[1] if len(images) > 1 else cover

            return cover, background
        except Exception as e:
            self.logger.error(f"提取图片失败: {str(e)}")
            return None, None


def register_plugin():
    """注册插件"""
    return SupFC2Metadata()

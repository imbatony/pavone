"""
SupFC2元数据提取器插件

支持从 supfc2.com 网站提取FC2视频元数据。
"""

import re
from typing import List, Optional

from ...models import MovieMetadata
from ...utils.html_metadata_utils import HTMLMetadataExtractor
from ...utils.metadata_builder import MetadataBuilder
from .fc2_base import FC2BaseMetadata

# 定义插件名称和版本
PLUGIN_NAME = "SupFC2Metadata"
PLUGIN_VERSION = "1.0.0"
PLUGIN_DESCRIPTION = "提取 supfc2.com 的FC2视频元数据"
PLUGIN_AUTHOR = "PAVOne"

# 定义插件优先级
PLUGIN_PRIORITY = 30

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

    def extract_metadata(self, identifier: str) -> Optional[MovieMetadata]:
        """从给定的identifier提取元数据

        Args:
            identifier: 可以是URL或FC2代码

        Returns:
            提取到的MovieMetadata对象，如果失败返回None
        """
        try:
            # 如果是FC2代码，构建URL
            if not identifier.startswith("http"):
                fc2_id = self._extract_fc2_id(identifier)
                if not fc2_id:
                    self.logger.error(f"无法从identifier提取FC2 ID: {identifier}")
                    return None
                # 构建URL，标题部分留空，因为需要从页面获取
                url = f"https://supfc2.com/detail/FC2-PPV-{fc2_id}/"
            else:
                url = identifier
                # 从URL提取FC2 ID
                fc2_id = self._extract_fc2_id_from_url(url)
                if not fc2_id:
                    self.logger.error(f"无法从URL提取FC2 ID: {url}")
                    return None

            # 获取页面内容
            response = self.fetch(url, timeout=30, verify_ssl=False)
            html_content = response.text
            if not html_content:
                self.logger.error(f"获取页面内容失败: {url}")
                return None

            # 提取元数据
            title = self._extract_title(html_content)
            fc2_id_from_page = self._extract_fc2_id_from_page(html_content)
            release_date = self._extract_release_date(html_content)
            maker = self._extract_maker(html_content)
            duration = self._extract_duration(html_content)
            tags = self._extract_tags(html_content)
            genres = self._extract_genres(html_content)
            rating = self._extract_rating(html_content)
            description = self._extract_description(html_content)
            cover_image, background_image = self._extract_images(html_content)

            # 使用从页面提取的FC2 ID（如果有）
            if fc2_id_from_page:
                fc2_id = fc2_id_from_page

            # 生成video_code
            video_code = f"FC2-{fc2_id}"

            # 创建 MovieMetadata 对象
            metadata = (
                MetadataBuilder()
                .set_title(title or "Unknown", video_code)
                .set_identifier(SITE_NAME, video_code, url)
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
            # 直接设置 official_rating
            metadata.official_rating = "JP-18+"

            self.logger.info(f"成功提取元数据: {video_code}")
            return metadata

        except Exception as e:
            self.logger.error(f"提取元数据失败: {str(e)}", exc_info=True)
            return None

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

    def _extract_description(self, html_content: str) -> Optional[str]:
        """提取描述（去除图片）"""
        try:
            # 支持两种标题格式：日文"映画の説明"和英文"Movie Description"
            patterns = [
                r'<h4[^>]*>映画の説明</h4>\s*<div class="mb-4">\s*<body><p>(.*?)</p>',
                r'<h4[^>]*>Movie Description</h4>\s*<div class="mb-4">\s*<body><p>(.*?)</p>',
            ]

            desc_html = None
            for pattern in patterns:
                match = re.search(pattern, html_content, re.DOTALL)
                if match:
                    desc_html = match.group(1)
                    break

            if desc_html:
                # 移除所有图片链接
                desc_html = re.sub(r"<a[^>]*data-fancybox[^>]*>.*?</a>", "", desc_html, flags=re.DOTALL)
                # 移除HTML标签，保留<br>标签
                desc_html = re.sub(r"<br\s*/?>", "\n", desc_html)
                desc_html = re.sub(r"<[^>]+>", "", desc_html)
                # 清理多余的空白
                desc_text = re.sub(r"\n\s*\n", "\n\n", desc_html)
                return desc_text.strip()
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

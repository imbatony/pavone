"""
PPVDataBank元数据提取器插件

支持从 ppvdatabank.com 网站提取FC2系列视频元数据。
"""

import re
from typing import Optional

from ...models import MovieMetadata
from ...utils.html_metadata_utils import HTMLMetadataExtractor
from ...utils.metadata_builder import MetadataBuilder
from .fc2_base import FC2BaseMetadata

# 定义插件名称和版本
PLUGIN_NAME = "PPVDataBankMetadata"
PLUGIN_VERSION = "1.0.0"
PLUGIN_DESCRIPTION = "提取 ppvdatabank.com 的FC2视频元数据"
PLUGIN_AUTHOR = "PAVOne"

# 定义插件优先级
PLUGIN_PRIORITY = 30

# 定义支持的域名
SUPPORTED_DOMAINS = ["ppvdatabank.com", "www.ppvdatabank.com"]

SITE_NAME = "PPVDataBank"


class PPVDataBankMetadata(FC2BaseMetadata):
    """
    PPVDataBank元数据提取器
    继承自 FC2BaseMetadata，提供从 ppvdatabank.com 提取FC2视频元数据的功能。
    """

    def __init__(self):
        """初始化PPVDataBank元数据提取器"""
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
        1. URL: https://ppvdatabank.com/article_search.php?id=2941579
        2. 视频代码: FC2-2941579 或 FC2-PPV-2941579
        """
        # 检查是否为URL
        if identifier.startswith("http://") or identifier.startswith("https://"):
            return self.can_handle_domain(identifier, self.supported_domains)

        # 检查是否为FC2视频代码
        identifier_stripped = identifier.strip().upper()
        if identifier_stripped.startswith("FC2"):
            code_pattern = r"^FC2(-PPV)?-\d+$"
            return bool(re.match(code_pattern, identifier_stripped))

        return False

    def extract_metadata(self, identifier: str) -> Optional[MovieMetadata]:
        """从给定的identifier提取元数据

        Args:
            identifier: 可以是URL (https://ppvdatabank.com/...) 或视频代码 (FC2-XXXXXXX)

        Returns:
            提取到的MovieMetadata对象，如果失败返回None
        """
        try:
            # 如果是URL，直接使用；如果是代码，需要构建URL
            url = identifier
            video_id = None

            if identifier.startswith("http"):
                # 从URL提取视频ID
                video_id = self._extract_video_id(identifier)
                if not video_id:
                    self.logger.error(f"无法从URL提取视频ID: {identifier}")
                    return None
            else:
                # 从FC2代码提取ID
                video_id = self._extract_id_from_code(identifier)
                if not video_id:
                    self.logger.error(f"无法从代码提取视频ID: {identifier}")
                    return None
                # 构建URL
                url = f"https://ppvdatabank.com/article_search.php?id={video_id}"

            # 获取页面内容
            response = self.fetch(url, timeout=30, verify_ssl=False)
            html_content = response.text
            if not html_content:
                self.logger.error(f"获取页面内容失败: {url}")
                return None

            # 提取所有元数据
            title = self._extract_title(html_content)
            video_code = f"FC2-{video_id}"  # 构建标准的FC2代码
            studio = self._extract_studio(html_content)
            release_date = self._extract_release_date(html_content)
            runtime = self._extract_runtime(html_content)
            cover_image = self._extract_cover_image(html_content, video_id)
            backdrop_image = self._extract_backdrop_image(html_content, video_id)

            # 创建 MovieMetadata 对象
            metadata = (
                MetadataBuilder()
                .set_title(title, video_code)
                .set_identifier(SITE_NAME, video_code, url)
                .set_studio(studio)
                .set_runtime(runtime)
                .set_release_date(release_date)
                .set_cover(cover_image)
                .set_backdrop(backdrop_image)
                .build()
            )
            # 直接设置 official_rating （MetadataBuilder 暂不支持）
            metadata.official_rating = "JP-18+"

            self.logger.info(f"成功提取元数据: {video_code} - {title}")
            return metadata

        except Exception as e:
            self.logger.error(f"提取元数据失败: {e}", exc_info=True)
            return None

    def _extract_video_id(self, url: str) -> Optional[str]:
        """从URL中提取视频ID

        Args:
            url: PPVDataBank视频页面URL

        Returns:
            视频ID，如果提取失败返回None
        """
        try:
            # URL格式1: https://ppvdatabank.com/article_search.php?id=2941579
            match = re.search(r"[?&]id=(\d+)", url)
            if match:
                return match.group(1)

            # URL格式2: https://ppvdatabank.com/article/4802082/
            match = re.search(r"/article/(\d+)/?", url)
            if match:
                return match.group(1)

            return None
        except Exception as e:
            self.logger.debug(f"提取视频ID异常: {str(e)}")
            return None

    def _extract_id_from_code(self, code: str) -> Optional[str]:
        """从FC2代码中提取数字ID

        Args:
            code: FC2代码 (FC2-2941579 或 FC2-PPV-2941579)

        Returns:
            数字ID，如果提取失败返回None
        """
        return self._extract_fc2_id(code)

    def _extract_title(self, html: str) -> str:
        """从HTML中提取视频标题

        Args:
            html: HTML页面内容

        Returns:
            视频标题
        """
        default_title = "PPVDataBank Video"
        try:
            # 从 og:title 提取
            title = HTMLMetadataExtractor.extract_og_title(html)
            if title:
                return title

            # 备选：从<title>标签提取
            title_match = re.search(r"<title>([^<]+)</title>", html)
            if title_match:
                return title_match.group(1).strip()

            # 备选：从article_title提取
            article_title_match = re.search(r'<div class="article_title[^"]*"><a[^>]*>([^<]+)</a>', html)
            if article_title_match:
                return article_title_match.group(1).strip()

            return default_title
        except Exception as e:
            self.logger.error(f"提取标题异常: {str(e)}")
            return default_title

    def _extract_studio(self, html: str) -> Optional[str]:
        """从HTML中提取制作人/销售者

        Args:
            html: HTML页面内容

        Returns:
            制作人名称
        """
        try:
            # 示例: <li>販売者 : <a href="...">レッド・D・キング</a></li>
            studio_match = re.search(r"<li>販売者\s*:\s*<a[^>]*>([^<]+)</a></li>", html)
            if studio_match:
                return studio_match.group(1).strip()
            return None
        except Exception as e:
            self.logger.debug(f"提取制作人异常: {str(e)}")
            return None

    def _extract_release_date(self, html: str) -> Optional[str]:
        """从HTML中提取发布日期（格式为YYYY-MM-DD）

        Args:
            html: HTML页面内容

        Returns:
            发布日期
        """
        try:
            # 示例: <li>販売日 : 2022/6/5</li>
            date_match = re.search(r"<li>販売日\s*:\s*(\d{4})/(\d{1,2})/(\d{1,2})</li>", html)
            if date_match:
                year = date_match.group(1)
                month = date_match.group(2).zfill(2)
                day = date_match.group(3).zfill(2)
                return f"{year}-{month}-{day}"
            return None
        except Exception as e:
            self.logger.debug(f"提取发布日期异常: {str(e)}")
            return None

    def _extract_runtime(self, html: str) -> Optional[int]:
        """从HTML中提取视频时长（分钟）

        Args:
            html: HTML页面内容

        Returns:
            视频时长（分钟）
        """
        try:
            # 示例: <li>再生時間 : 01:31:25</li>
            runtime_match = re.search(r"<li>再生時間\s*:\s*(\d{1,2}):(\d{2}):(\d{2})</li>", html)
            if runtime_match:
                hours = int(runtime_match.group(1))
                minutes = int(runtime_match.group(2))
                seconds = int(runtime_match.group(3))
                total_minutes = hours * 60 + minutes + (1 if seconds > 0 else 0)
                return total_minutes
            return None
        except Exception as e:
            self.logger.debug(f"提取时长异常: {str(e)}")
            return None

    def _extract_cover_image(self, html: str, video_id: str) -> Optional[str]:
        """从HTML中提取封面图片URL

        Args:
            html: HTML页面内容
            video_id: 视频ID

        Returns:
            封面图片URL
        """
        try:
            # 示例: <div class="thumb"><img src="https://ppvdatabank.com/article/2941579/img/thumb.webp" ...>
            cover_match = re.search(r'<div class="thumb"><img src="([^"]+)"', html)
            if cover_match:
                cover_url = cover_match.group(1)
                # 如果是相对路径，转换为绝对路径
                if not cover_url.startswith("http"):
                    cover_url = f"https://ppvdatabank.com{cover_url}"
                return cover_url

            # 备选方案：根据video_id构建封面URL
            return f"https://ppvdatabank.com/article/{video_id}/img/thumb.webp"
        except Exception as e:
            self.logger.debug(f"提取封面图片异常: {str(e)}")
            return None

    def _extract_backdrop_image(self, html: str, video_id: str) -> Optional[str]:
        """从HTML中提取背景图片URL（使用第一张sample图片）

        Args:
            html: HTML页面内容
            video_id: 视频ID

        Returns:
            背景图片URL
        """
        try:
            # 示例: <li><a href="https://ppvdatabank.com/article/2941579/img/pl1.webp" ...>
            # 我们提取第一个大图片链接（pl1.webp）
            backdrop_match = re.search(r'<li><a href="([^"]+/pl1\.webp)"', html)
            if backdrop_match:
                backdrop_url = backdrop_match.group(1)
                # 如果是相对路径，转换为绝对路径
                if not backdrop_url.startswith("http"):
                    backdrop_url = f"https://ppvdatabank.com{backdrop_url}"
                return backdrop_url

            # 备选方案：根据video_id构建背景图URL
            return f"https://ppvdatabank.com/article/{video_id}/img/pl1.webp"
        except Exception as e:
            self.logger.debug(f"提取背景图片异常: {str(e)}")
            return None

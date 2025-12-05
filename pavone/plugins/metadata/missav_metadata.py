"""
Missav元数据提取器插件

支持从 missav.ai 和 missav.com 网站提取元数据。
"""

import re
from datetime import datetime
from typing import Optional, Tuple
from urllib.parse import urlparse

from ...models import MovieMetadata
from ...utils import CodeExtractUtils, StringUtils
from .base import MetadataPlugin

# 定义插件名称和版本
PLUGIN_NAME = "MissavMetadata"
PLUGIN_VERSION = "1.0.0"
PLUGIN_DESCRIPTION = "提取 missav.ai 和 missav.com 的视频元数据"
PLUGIN_AUTHOR = "PAVOne"

# 定义插件优先级
PLUGIN_PRIORITY = 30

# 定义支持的域名
SUPPORTED_DOMAINS = ["missav.ai", "www.missav.ai", "missav.com", "www.missav.com"]

SITE_NAME = "MissAV"


class MissavMetadata(MetadataPlugin):
    """
    Missav元数据提取器
    继承自MetadataPlugin，提供从 missav.ai 和 missav.com 提取元数据的功能。
    """

    def __init__(self):
        """初始化Missav元数据提取器"""
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
        1. URL: https://missav.ai/ja/xxxxx-xxx
        2. 视频代码: XXXXX-XXX 或 xxxxx-xxx (字母-数字 或 数字-数字 格式)
           例如: SDMT-415, abc-123, JAVDB-1234 等
        """
        # 检查是否为URL
        if identifier.startswith("http://") or identifier.startswith("https://"):
            try:
                parsed_url = urlparse(identifier)
                # 检查协议是否为HTTP或HTTPS
                if parsed_url.scheme.lower() not in ("http", "https"):
                    return False
                # 检查域名是否在支持列表中
                return any(parsed_url.netloc.lower() == domain.lower() for domain in self.supported_domains)
            except Exception:
                return False
        
        # 检查是否为视频代码（严格的格式检查）
        # 格式：纯字母部分 + 连字符 + 数字部分
        # 例如: SDMT-415, ABC-123, sdmt-415
        identifier_stripped = identifier.strip()
        code_pattern = r"^[a-zA-Z]+(-|\d)[a-zA-Z0-9]*$"
        if re.match(code_pattern, identifier_stripped):
            # 确保只有一个连字符，且左边是字母，右边是数字
            if "-" in identifier_stripped:
                parts = identifier_stripped.split("-")
                if len(parts) == 2 and len(parts[0]) > 0 and len(parts[1]) > 0:
                    # 左边必须是字母
                    if parts[0][0].isalpha() and parts[1][0].isdigit():
                        return True
            else:
                # 没有连字符，纯字母代码（不支持）
                return False
        
        return False

    def extract_metadata(self, identifier: str) -> Optional[MovieMetadata]:
        """从给定的identifier提取元数据
        
        Args:
            identifier: 可以是URL (https://missav.ai/...) 或视频代码 (XXXXX-XXX)
            
        Returns:
            提取到的MovieMetadata对象，如果失败返回None
        """
        try:
            # 如果是URL，直接使用；如果是代码，需要构建URL
            url = identifier
            if not identifier.startswith("http"):
                # 尝试从代码构建URL
                # 这里我们需要先搜索获取真实的URL
                # 为了简化实现，我们先假设识别为代码时返回None
                # 实际应用中可以集成搜索功能来获取URL
                self.logger.warning(f"代码格式identifier暂不直接支持: {identifier}，请使用URL")
                return None
            
            # 获取页面内容
            response = self.fetch(url, timeout=30, verify_ssl=False)
            html_content = response.text
            if not html_content:
                self.logger.error(f"获取页面内容失败: {url}")
                return None

            # 提取所有元数据
            title_with_code, original_title, video_code = self._extract_title_and_code(html_content)
            actors = self._extract_actors(html_content)
            director = self._extract_director(html_content)
            duration = self._extract_duration(html_content)
            release_date = self._extract_release_date(html_content)
            genres = self._extract_genres(html_content)
            tags = self._extract_tags(html_content)
            studio = self._extract_studio(html_content)
            series = self._extract_series(html_content)
            cover_image = self._extract_cover_image(html_content)
            description = self._extract_description(html_content)
            tagline = self._extract_tagline(html_content)
            
            release_year = int(release_date.split("-")[0]) if release_date else datetime.now().year
            
            # 创建identifier
            identifier_str = StringUtils.create_identifier(site=SITE_NAME, code=video_code, url=url)
            
            # 创建MovieMetadata对象
            metadata = MovieMetadata(
                title=title_with_code,  # 完整标题包含代码前缀
                original_title=original_title,  # 原始标题不包含代码前缀
                identifier=identifier_str,
                site=SITE_NAME,
                url=url,
                code=video_code,
                actors=actors,
                director=director,
                runtime=duration,  # 注意这里convert秒到分钟
                premiered=release_date,
                genres=genres,
                tags=tags,
                studio=studio,
                serial=series,
                cover=cover_image,
                plot=description,
                tagline=tagline,
                year=release_year,
            )
            
            self.logger.info(f"成功提取元数据: {video_code} - {original_title}")
            return metadata

        except Exception as e:
            self.logger.error(f"提取元数据失败: {e}")
            return None

    def _extract_title_and_code(self, html: str) -> Tuple[str, str, str]:
        """
        从HTML中提取视频标题和代码
        返回 (title_with_code, original_title, video_code)
        - title_with_code: 包含代码前缀的完整标题（例如 "SDMT-415 日焼け跡の残る..."）
        - original_title: 不包含代码的原始标题（例如 "日焼け跡の残る..."）
        - video_code: 视频代码（例如 "SDMT-415"）

        Args:
            html: HTML页面内容
        Returns:
            (title_with_code, original_title, video_code)
        """
        default_title = "MissAV Video"
        default_code = self._extract_uuid(html) or "Unknown"
        try:
            title_match = re.search(r'<meta property="og:title" content="([^"]+)"', html)
            if title_match:
                matched = title_match.group(1).strip()
                # 分离代码和标题
                parts = matched.split(" ", maxsplit=1)
                # 正规化代码和标题
                video_code = CodeExtractUtils.extract_code_from_text(parts[0]) if len(parts) > 0 else default_code
                if not video_code:
                    video_code = default_code
                # 原始标题不含代码前缀
                original_title = parts[1] if len(parts) > 1 else default_title
                # 完整标题包含代码前缀
                title_with_code = f"{video_code} {original_title}"
            else:
                original_title = default_title
                video_code = default_code
                title_with_code = f"{video_code} {original_title}"
            self.logger.debug(f"提取到视频标题: {original_title}, 代码: {video_code}")
            if not video_code:
                video_code = default_code
            return (title_with_code, original_title, video_code)
        except Exception as e:
            self.logger.error(f"提取标题和代码异常: {str(e)}")
            return (f"{default_code} {default_title}", default_title, default_code)

    def _extract_uuid(self, html: str) -> Optional[str]:
        """提取UUID，用于后备的代码识别"""
        try:
            if match := re.search(r"m3u8\|([a-f0-9\|]+)\|com\|surrit\|https\|video", html):
                return "-".join(match.group(1).split("|")[::-1])
            return None
        except Exception as e:
            self.logger.debug(f"UUID提取异常: {str(e)}")
            return None

    def _extract_actors(self, html: str) -> list[str]:
        """从HTML中提取演员列表"""
        try:
            # 演员信息在 <meta property="og:video:actor" content="演员名" />
            return re.findall(r'<meta property="og:video:actor" content="([^"]+)"', html)
        except Exception as e:
            self.logger.debug(f"提取演员异常: {str(e)}")
            return []

    def _extract_director(self, html: str) -> Optional[str]:
        """从HTML中提取导演，有多个只取第一个"""
        try:
            # 导演信息在 <meta property="og:video:director" content="导演名" />
            directors = re.findall(r'<meta property="og:video:director" content="([^"]+)"', html)
            return directors[0] if directors and directors[0] else None
        except Exception as e:
            self.logger.debug(f"提取导演异常: {str(e)}")
            return None

    def _extract_duration(self, html: str) -> Optional[int]:
        """从HTML中提取视频时长（秒）"""
        try:
            # 时长信息在 <meta property="og:video:duration" content="时长（秒）" />
            duration_match = re.search(r'<meta property="og:video:duration" content="(\d+)"', html)
            if duration_match:
                # 转换为分钟
                seconds = int(duration_match.group(1))
                return seconds // 60 if seconds > 0 else None
            return None
        except Exception as e:
            self.logger.debug(f"提取时长异常: {str(e)}")
            return None

    def _extract_release_date(self, html: str) -> Optional[str]:
        """从HTML中提取发布日期（格式为YYYY-MM-DD）"""
        try:
            # 发布日期信息在 <meta property="og:video:release_date" content="YYYY-MM-DD" />
            date_match = re.search(r'<meta property="og:video:release_date" content="([^"]+)"', html)
            return date_match.group(1) if date_match else None
        except Exception as e:
            self.logger.debug(f"提取发布日期异常: {str(e)}")
            return None

    def _extract_genres(self, html: str) -> list[str]:
        """从HTML中提取视频类型"""
        try:
            # 定义多语言的类型标签模式
            genre_labels = [
                r"ジャンル:",  # 日语
                r"类型:",  # 中文简体
                r"類型:",  # 中文繁体
                r"分类:",  # 中文简体
                r"分類:",  # 中文繁体
                r"种类:",  # 中文简体
                r"種類:",  # 中文繁体
                r"Genre:",  # 英语
                r"Category:",  # 英语
                r"장르:",  # 韩语
                r"Thể loại:",  # 越南语
                r"Kategori:",  # 印尼语
                r"หมวดหมู่:",  # 泰语
            ]

            # 尝试使用任何一个语言标签找到genres部分
            for label_pattern in genre_labels:
                pattern = label_pattern + r".*?</div>"
                match = re.search(pattern, html, re.DOTALL)
                if match:
                    self.logger.debug(f"找到类型部分，使用标签: {label_pattern}")
                    # 在genres部分寻找所有类型链接
                    genre_names = re.findall(r'class="text-nord13 font-medium">([^<]+)</a>', match.group(0))
                    # 去重并返回
                    return list(dict.fromkeys(genre_names))  # 保持顺序的去重

            return []

        except Exception as e:
            self.logger.debug(f"提取类型异常: {str(e)}")
            return []

    def _extract_tags(self, html: str) -> list[str]:
        """从HTML中提取视频标签"""
        try:
            # 定义多语言的标签模式
            tag_labels = [
                r"タグ:",  # 日语
                r"标签:",  # 中文简体
                r"標籤:",  # 中文繁体
                r"Tags:",  # 英语
                r"Label:",  # 英语
                r"Tag:",  # 英语
            ]

            # 尝试使用任何一个语言标签找到tags部分
            for label_pattern in tag_labels:
                pattern = label_pattern + r".*?</div>"
                match = re.search(pattern, html, re.DOTALL)
                if match:
                    self.logger.debug(f"找到标签部分，使用标签: {label_pattern}")
                    # 在tags部分寻找所有标签链接
                    tag_names = re.findall(r'class="text-nord13 font-medium">([^<]+)</a>', match.group(0))
                    # 去重并返回
                    return list(dict.fromkeys(tag_names))  # 保持顺序的去重

            # 如果没有找到任何语言标签的tags部分, 则尝试找keywords
            keywords_match = re.search(r'<meta name="keywords" content="([^"]+)"', html)
            if keywords_match:
                keywords = keywords_match.group(1).split(",")
                # 清理标签，去除空格和多余字符，并去重
                cleaned = [tag.strip() for tag in keywords if tag.strip()]
                return list(dict.fromkeys(cleaned))  # 保持顺序的去重
            
            return []

        except Exception as e:
            self.logger.debug(f"提取标签异常: {str(e)}")
            return []

    def _extract_studio(self, html: str) -> Optional[str]:
        """从HTML中提取制作公司"""
        try:
            # 定义多语言的制作公司模式
            studio_labels = [
                r"发行商:",  # 中文简体
                r"發行商:",  # 中文繁体
                r"制作公司:",  # 中文简体
                r"製作公司:",  # 中文繁体
                r"制作商:",  # 中文简体
                r"製作商:",  # 中文繁体
                r"メーカー:",  # 日语
                r"Maker:",  # 英语
            ]

            # 尝试使用任何一个语言标签找到studio部分
            for label_pattern in studio_labels:
                pattern = label_pattern + r".*?</div>"
                match = re.search(pattern, html, re.DOTALL)
                if match:
                    self.logger.debug(f"找到制作公司部分，使用标签: {label_pattern}")
                    # 在studio部分寻找制作公司名称
                    studio_name = re.search(r'class="text-nord13 font-medium">([^<]+)</a>', match.group(0))
                    return studio_name.group(1) if studio_name else None

            return None
        except Exception as e:
            self.logger.debug(f"提取制作公司异常: {str(e)}")
            return None

    def _extract_series(self, html: str) -> Optional[str]:
        """从HTML中提取系列名称"""
        try:
            # 定义多语言的系列名称模式
            series_labels = [
                r"シリーズ:",  # 日语
                r"系列:",  # 中文简体
                r"系列:",  # 中文繁体
                r"Series:",  # 英语
            ]

            # 尝试使用任何一个语言标签找到series部分
            for label_pattern in series_labels:
                pattern = label_pattern + r".*?</div>"
                match = re.search(pattern, html, re.DOTALL)
                if match:
                    self.logger.debug(f"找到系列部分，使用标签: {label_pattern}")
                    # 在series部分寻找所有系列链接
                    series_names = re.findall(r'class="text-nord13 font-medium">([^<]+)</a>', match.group(0))
                    return series_names[0] if series_names else None

            return None

        except Exception as e:
            self.logger.debug(f"提取系列异常: {str(e)}")
            return None

    def _extract_cover_image(self, html: str) -> Optional[str]:
        """从HTML中提取封面图片链接"""
        try:
            # 封面图片在<meta property="og:image" content="封面图片链接" />
            cover_match = re.search(r'<meta property="og:image" content="([^"]+)"', html)
            return cover_match.group(1) if cover_match else None
        except Exception as e:
            self.logger.debug(f"提取封面图片异常: {str(e)}")
            return None

    def _extract_description(self, html: str) -> Optional[str]:
        """从HTML中提取视频描述"""
        try:
            # 描述信息在<meta property="og:description" content="视频描述" />
            description_match = re.search(r'<meta property="og:description" content="([^"]+)"', html)
            return description_match.group(1) if description_match else None
        except Exception as e:
            self.logger.debug(f"提取描述异常: {str(e)}")
            return None

    def _extract_tagline(self, html: str) -> Optional[str]:
        """从HTML中提取视频标语"""
        try:
            # 标语信息在<meta property="og:title" content="视频标语" />
            tagline_match = re.search(r'<meta property="og:title" content="([^"]+)"', html)
            return tagline_match.group(1) if tagline_match else None
        except Exception as e:
            self.logger.debug(f"提取标语异常: {str(e)}")
            return None

"""
MissAV视频提取器插件

支持从 missav.ai 和 missav.com 网站提取视频下载链接。
"""

import re
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from urllib.parse import urlparse

from ...models import (
    MovieMetadata,
    OperationItem,
    Quality,
    create_cover_item,
    create_landscape_item,
    create_metadata_item,
    create_stream_item,
)
from ...utils import CodeExtractUtils, StringUtils
from .base import ExtractorPlugin

# 定义插件名称和版本
PLUGIN_NAME = "MissAVExtractor"
PLUGIN_VERSION = "1.0.0"
PLUGIN_DESCRIPTION = "提取 missav.ai 和 missav.com 的视频下载链接"
PLUGIN_AUTHOR = "PAVOne"

# 定义插件优先级
PLUGIN_PRIORITY = 30

# 定义支持的域名
SUPPORTED_DOMAINS = ["missav.ai", "www.missav.ai", "missav.com", "www.missav.com"]

SITE_NAME = "MissAV"


class MissAVExtractor(ExtractorPlugin):
    """
    MissAV提取器
    继承自ExtractorPlugin，提供从 missav.ai 和 missav.com 提取视频下载链接的功能。
    """

    def __init__(self):
        """初始化MissAV提取器"""
        super().__init__()
        self.name = PLUGIN_NAME
        self.version = PLUGIN_VERSION
        self.description = PLUGIN_DESCRIPTION
        self.priority = PLUGIN_PRIORITY
        self.supported_domains = SUPPORTED_DOMAINS
        self.author = PLUGIN_AUTHOR

    def can_handle(self, url: str) -> bool:
        """检查是否能处理给定的URL"""
        try:
            parsed_url = urlparse(url)
            # 检查协议是否为HTTP或HTTPS
            if parsed_url.scheme.lower() not in ("http", "https"):
                return False
            # 检查域名是否在支持列表中
            return any(parsed_url.netloc.lower() == domain.lower() for domain in self.supported_domains)
        except Exception:
            return False

    def extract(self, url: str) -> List[OperationItem]:
        """从 MissAV 页面提取视频下载选项"""
        try:
            # 使用基类的统一网页获取方法，自动处理代理和SSL
            response = self.fetch(url, timeout=30, verify_ssl=False)
            html_content = response.text
            if not html_content:
                self.logger.error(f"获取页面内容失败: {url}")
                return []

            # 提取混淆的JavaScript代码
            video_urls = self._extract_obfuscated_urls(html_content)
            if not video_urls:
                self.logger.error(f"未能从页面提取视频链接: {url}")
                return []
            # 提取视频标题和代码
            video_title, video_code = self._extract_title_and_code(html_content)
            actors = self._extract_actors(html_content)
            director = self._extract_director(html_content)
            duration = self._extract_duration(html_content)
            release_date = self._extract_release_date(html_content)
            genres = self._extract_genres(html_content)
            tags = self._extract_tags(html_content)
            studio = self._extract_studio(html_content)
            series = self._extract_series(html_content)
            cover_image = self._extract_cover_image(html_content)
            landscape = cover_image  # 假设封面图片也是横幅图片
            description = self._extract_description(html_content)
            tagline = self._extract_tagline(html_content)
            cover_item: Optional[OperationItem] = None
            landscape_item: Optional[OperationItem] = None
            release_year = int(release_date.split("-")[0]) if release_date else datetime.now().year
            # 如果有封面图片，创建封面图片项
            if cover_image and landscape:
                cover_item = create_cover_item(url=cover_image, title=video_title)
                landscape_item = create_landscape_item(url=cover_image, title=video_title)
            identifier = StringUtils.create_identifier(site=SITE_NAME, code=video_code, url=url)
            matadata = MovieMetadata(
                title=f"{video_code} {video_title}",
                identifier=identifier,
                site=SITE_NAME,
                url=url,
                code=video_code,
                actors=actors,
                director=director,
                duration=duration,
                release_date=release_date,
                genres=genres,
                tags=tags,
                studio=studio,
                series=series,
                cover=cover_image,
                description=description,
                tagline=tagline,
            )
            # 创建元数据项
            metadata_item = create_metadata_item(
                title=video_title,
                meta_data=matadata,
            )
            # 生成下载选项
            download_items: List[OperationItem] = []
            for _, video_url in video_urls.items():
                if not video_url:
                    continue

                quality = Quality.guess(video_url)
                download_item = create_stream_item(
                    site=SITE_NAME,
                    url=video_url,
                    title=video_title,
                    code=video_code,
                    quality=quality,
                    actors=actors,
                    studio=studio,
                    year=release_year,
                )
                # 如果有封面图片，添加到为子项
                if cover_item:
                    download_item.append_child(cover_item)
                if landscape_item:
                    download_item.append_child(landscape_item)
                # 添加元数据项
                download_item.append_child(metadata_item)
                # 添加到下载选项列表
                download_items.append(download_item)

            return download_items

        except Exception as e:
            self.logger.error(f"获取页面失败: {e}")
            return []

    def _extract_obfuscated_urls(self, html_content: str) -> Dict[str, str]:
        """
        从JavaScript混淆代码中提取视频URL - 只依赖dukpy执行JavaScript
        如果dukpy执行失败，直接返回空结果
        Args:
            html_content: HTML页面内容

        Returns:
            包含video URLs的字典，失败时返回空字典
        """
        # 首先尝试从HTML中提取UUID
        # 这个UUID通常用于构建主播放列表链接
        uuid = self._extract_uuid(html_content)
        if uuid:
            master_url = f"https://surrit.com/{uuid}/playlist.m3u8"
            self.logger.debug(f"提取到UUID: {uuid}, 构建的主播放列表链接: {master_url}")
            return self._extract_master_playlist(master_url)
        # 如果没有UUID，直接返回空字典
        else:
            self.logger.error("未能从页面中提取UUID，无法获取视频链接")
            return {}

    def _extract_master_playlist(self, master_url: str) -> Dict[str, str]:
        """
        从大师链接中提取所有子链接
        主要用于处理.m3u8链接，获取所有可用的子链接
        """
        try:
            # 获取大师链接内容
            response = self.fetch(master_url, timeout=30, verify_ssl=False)
            if response.status_code != 200:
                self.logger.info(f"获取大师链接失败: {master_url} - 状态码: {response.status_code}")
                return {}
            # 基准为去除playlist.m3u8的一部分
            base_url = master_url.rsplit("/", 1)[0] + "/"
            # 解析.m3u8内容，提取所有子链接
            m3u8_content = response.text
            self.logger.debug(f"处理大师链接内容: {m3u8_content}...")  # 仅打印前100个字符
            lines = m3u8_content.splitlines()
            sub_urls = {}
            for line in lines:
                line = line.strip()
                if line and not line.startswith("#"):
                    # 找到以m3u8结尾的链接
                    if line.endswith("m3u8"):
                        # 如果是绝对链接，直接使用
                        if line.startswith("http"):
                            key = self._get_key_for_url(line)
                            if key:
                                sub_urls[key] = line

                        # 如果是相对链接，拼接基准URL
                        else:
                            full_url = base_url + line
                            key = self._get_key_for_url(full_url)
                            if key:
                                sub_urls[key] = full_url

            self.logger.debug(f"从大师链接提取到 {len(sub_urls)} 个子链接")
            return sub_urls

        except Exception as e:
            self.logger.error(f"处理大师链接时出错: {e}")
            return {}

    def _get_key_for_url(self, url: str) -> str:
        """
        获取视频URL的唯一键
        通过视频质量生成一个键
        Args:
            url: 视频URL
        """
        return Quality.guess(url)

    def _extract_uuid(self, html: str) -> Optional[str]:
        try:
            if match := re.search(r"m3u8\|([a-f0-9\|]+)\|com\|surrit\|https\|video", html):
                return "-".join(match.group(1).split("|")[::-1])
            return None
        except Exception as e:
            self.logger.error(f"UUID提取异常: {str(e)}")
            return None

    def _extract_title_and_code(self, html: str) -> Tuple[str, str]:
        """
        从HTML中提取视频标题和代码
        返回 (video_title, video_code)，其中 video_title 不包含代码前缀
        
        Args:
            html: HTML页面内容
        Returns:
            (video_title, video_code)
        """
        # 从<meta property="og:title" content="{code} {title}" />
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
                # 返回纯标题（不含代码前缀）
                video_title = parts[1] if len(parts) > 1 else default_title
            else:
                video_title = default_title
                video_code = default_code
            self.logger.debug(f"提取到视频标题: {video_title}, 代码: {video_code}")
            if not video_code:
                video_code = default_code
            return (video_title, video_code)
        except Exception as e:
            self.logger.error(f"提取标题和代码异常: {str(e)}")
            return (default_title, default_code)

    def _extract_actors(self, html: str) -> List[str]:
        """
        从HTML中提取演员列表
        Args:
            html: HTML页面内容
        Returns:
            演员名称列表
        """
        try:
            # 演员信息在 <meta property="og:video:actor" content="演员名" />
            return re.findall(r'<meta property="og:video:actor" content="([^"]+)"', html)
        except Exception as e:
            self.logger.info(f"提取演员异常: {str(e)}")
            return []

    def _extract_director(self, html: str) -> Optional[str]:
        """
        从HTML中提取导演列表, 有多个只取第一个
        Args:
            html: HTML页面内容
        Returns:
            导演名称列表
        """
        try:
            # 导演信息在 <meta property="og:video:director" content="导演名" />
            directors = re.findall(r'<meta property="og:video:director" content="([^"]+)"', html)
            return directors[0] if directors and directors[0] else None
        except Exception as e:
            self.logger.info(f"提取导演异常: {str(e)}")
            return None

    def _extract_duration(self, html: str) -> Optional[int]:
        """
        从HTML中提取视频时长
        Args:
            html: HTML页面内容
        Returns:
            视频时长（秒）
        """
        try:
            # 时长信息在 <meta property="og:video:duration" content="时长（秒）" />
            duration_match = re.search(r'<meta property="og:video:duration" content="(\d+)"', html)
            if duration_match:
                return int(duration_match.group(1))
            return None
        except Exception as e:
            self.logger.info(f"提取时长异常: {str(e)}")
            return None

    def _extract_release_date(self, html: str) -> Optional[str]:
        """
        从HTML中提取发布日期
        Args:
            html: HTML页面内容
        Returns:
            发布日期（格式为YYYY-MM-DD）
        """
        try:
            # 发布日期信息在 <meta property="og:video:release_date" content="YYYY-MM-DD" />
            date_match = re.search(r'<meta property="og:video:release_date" content="([^"]+)"', html)
            return date_match.group(1) if date_match else None
        except Exception as e:
            self.logger.info(f"提取发布日期异常: {str(e)}")
            return None

    def _extract_genres(self, html: str) -> List[str]:
        """
        从HTML中提取视频类型
        支持多语言的类型标签匹配
        Args:
            html: HTML页面内容
        Returns:
            视频类型列表，如果没有匹配到返回空列表
        """
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
                    return genre_names

            # 如果没有找到任何语言标签的genres部分，返回空列表
            return []

        except Exception as e:
            self.logger.info(f"提取类型异常: {str(e)}")
            return []

    def _extract_tags(self, html: str) -> List[str]:
        """
        从HTML中提取视频标签
        支持多语言的标签匹配
        Args:
            html: HTML页面内容
        Returns:
            视频标签列表，如果没有匹配到返回空列表
        """
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
                    return tag_names

            # 如果没有找到任何语言标签的tags部分, 则尝试找keywords
            keywords_match = re.search(r'<meta name="keywords" content="([^"]+)"', html)
            if keywords_match:
                keywords = keywords_match.group(1).split(",")
                # 清理标签，去除空格和多余字符
                return [tag.strip() for tag in keywords if tag.strip()]
            # 如果没有找到任何标签部分，返回空列表
            return []

        except Exception as e:
            self.logger.info(f"提取标签异常: {str(e)}")
            return []

    def _extract_studio(self, html: str) -> Optional[str]:
        """
        从HTML中提取制作公司
        支持多语言的制作公司匹配
        Args:
            html: HTML页面内容
        Returns:
            制作公司名称，如果没有匹配到返回None
        """
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

            # 如果没有找到任何语言标签的studio部分，返回None
            return None
        except Exception as e:
            self.logger.info(f"提取制作公司异常: {str(e)}")
            return None

    def _extract_series(self, html: str) -> Optional[str]:
        """
        从HTML中提取系列名称
        支持多语言的系列名称匹配
        Args:
            html: HTML页面内容
        Returns:
            系列名称，如果没有匹配到返回空
        """
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

            # 如果没有找到任何语言标签的series部分，返回空
            return None

        except Exception as e:
            self.logger.info(f"提取系列异常: {str(e)}")
            return None

    def _extract_cover_image(self, html: str) -> Optional[str]:
        """
        从HTML中提取封面图片链接
        Args:
            html: HTML页面内容
        Returns:
            封面图片链接，如果没有匹配到返回None
        """
        try:
            # 封面图片在<meta property="og:image" content="封面图片链接" />
            cover_match = re.search(r'<meta property="og:image" content="([^"]+)"', html)
            return cover_match.group(1) if cover_match else None
        except Exception as e:
            self.logger.info(f"提取封面图片异常: {str(e)}")
            return None

    def _extract_description(self, html: str) -> Optional[str]:
        """
        从HTML中提取视频描述
        Args:
            html: HTML页面内容
        Returns:
            视频描述，如果没有匹配到返回None
        """
        try:
            # 描述信息在<meta property="og:description" content="视频描述" />
            description_match = re.search(r'<meta property="og:description" content="([^"]+)"', html)
            return description_match.group(1) if description_match else None
        except Exception as e:
            self.logger.info(f"提取描述异常: {str(e)}")
            return None

    def _extract_tagline(self, html: str) -> Optional[str]:
        """
        从HTML中提取视频标语
        Args:
            html: HTML页面内容
        Returns:
            视频标语，如果没有匹配到返回None
        """
        try:
            # 标语信息在<meta property="og:title" content="视频标语" />
            tagline_match = re.search(r'<meta property="og:title" content="([^"]+)"', html)
            return tagline_match.group(1) if tagline_match else None
        except Exception as e:
            self.logger.info(f"提取标语异常: {str(e)}")
            return None

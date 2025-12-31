"""
MissAV统一插件

一个类同时实现搜索、元数据提取和视频下载三种功能，最大程度复用代码。
"""

import re
from re import findall
from typing import Any, Dict, List, Optional, Tuple

from ..config.logging_config import get_logger
from ..models import MovieMetadata, OperationItem, Quality, SearchResult
from ..utils import CodeExtractUtils
from ..utils.html_metadata_utils import HTMLMetadataExtractor
from ..utils.metadata_builder import MetadataBuilder
from ..utils.operation_item_builder import OperationItemBuilder
from .extractors.base import ExtractorPlugin
from .metadata.base import MetadataPlugin
from .search.base import SearchPlugin

# 定义插件名称和版本
PLUGIN_NAME = "MissAV"
PLUGIN_VERSION = "2.0.0"
PLUGIN_DESCRIPTION = "MissAV统一插件：支持搜索、元数据提取和视频下载"
PLUGIN_AUTHOR = "PAVOne"

# 定义插件优先级
PLUGIN_PRIORITY = 30

# 定义支持的域名
SUPPORTED_DOMAINS = ["missav.ai", "www.missav.ai", "missav.com", "www.missav.com"]

SITE_NAME = "MissAV"

# Missav 网站的基础 URL
MISSAV_BASE_URL = "https://missav.ai"


class MissAVPlugin(ExtractorPlugin, MetadataPlugin, SearchPlugin):
    """
    MissAV统一插件
    同时实现搜索、元数据提取和视频下载三种功能（通过多继承）
    """

    def __init__(self):
        """初始化MissAV插件"""
        # 多继承时，由于 SearchPlugin 有不同的 __init__ 签名，
        # 我们直接调用 BasePlugin 的初始化，避免 MRO 链的问题
        from .base import BasePlugin

        BasePlugin.__init__(
            self,
            name=PLUGIN_NAME,
            version=PLUGIN_VERSION,
            description=PLUGIN_DESCRIPTION,
            author=PLUGIN_AUTHOR,
            priority=PLUGIN_PRIORITY,
        )
        # 设置 SearchPlugin 需要的属性
        self.site = SITE_NAME
        # 其他属性
        self.supported_domains = SUPPORTED_DOMAINS
        self.site_name = SITE_NAME
        self.base_url = MISSAV_BASE_URL
        self.logger = get_logger(__name__)

    def initialize(self) -> bool:
        """初始化插件"""
        return True

    # ==================== 搜索功能接口 ====================

    def search(self, keyword: str, limit: int = 20) -> List[SearchResult]:
        """执行搜索操作"""
        code = CodeExtractUtils.extract_code_from_text(keyword)
        if code:
            # 如果是FC2编号，转换格式
            if code.startswith("FC2") or code.startswith("fc2"):
                code = code[:3] + "-PPV" + code[3:]
            code = code.lower()
            url = f"{self.base_url}/ja/{code}"
            res = self.fetch(url)
            if res and res.status_code == 200:
                result = self._parse_video_page(res.text, code)
                if result:
                    return [result]

        # 使用搜索功能
        search_url = f"{self.base_url}/ja/search/{keyword}"
        res = self.fetch(search_url)
        if res and res.status_code == 200:
            results = self._parse_search_results(res.text, limit, keyword)
            return results
        else:
            self.logger.error(
                "Failed to fetch search results for " f"{keyword}. Status code: {res.status_code if res else 'No response'}"
            )
            return []

    def _parse_video_page(self, html: str, code: str) -> SearchResult:
        """解析视频页面，提取视频信息"""
        return SearchResult(
            site=self.site_name,
            keyword=code,
            title=f"{self.site_name} Video Result for {code}",
            description=f"Video result for {code} on {self.site_name}",
            url=f"{self.base_url}/ja/{code}",
            code=code,
        )

    def _parse_search_results(self, html: str, limit: int, keyword: str) -> List[SearchResult]:
        """解析搜索结果页面，提取视频信息"""
        results: List[SearchResult] = []
        regex = r'<a\s+class="text-secondary group-hover:text-primary"\s+href="([^"]+)"\s+alt="([^"]+)"[^>]*>\s*(.*?)\s*</a>'
        matches = findall(regex, html)
        if not matches:
            self.logger.warning(f"No search results found for keyword: {keyword}")
            return results

        matches = matches[:limit]
        for match in matches:
            url, alt, title = match
            result = SearchResult(
                site=self.site_name,
                keyword=keyword,
                title=title,
                description=f"Search result for {title} on {self.site_name}",
                url=url,
                code=alt.upper(),
            )
            results.append(result)
        return results

    # ==================== 元数据提取功能接口 ====================

    def can_extract(self, identifier: str) -> bool:
        """检查是否能处理给定的identifier"""
        if identifier.startswith("http://") or identifier.startswith("https://"):
            return self.can_handle_domain(identifier, self.supported_domains)

        # 检查是否为视频代码
        identifier_stripped = identifier.strip()
        code_pattern = r"^[a-zA-Z]+(-|\d)[a-zA-Z0-9]*$"
        if re.match(code_pattern, identifier_stripped):
            if "-" in identifier_stripped:
                parts = identifier_stripped.split("-")
                if len(parts) == 2 and len(parts[0]) > 0 and len(parts[1]) > 0:
                    if parts[0][0].isalpha() and parts[1][0].isdigit():
                        return True

        return False

    def extract_metadata(self, identifier: str) -> Optional[MovieMetadata]:
        """从给定的identifier提取元数据"""
        try:
            url = identifier
            if not identifier.startswith("http"):
                self.logger.warning(f"代码格式identifier暂不直接支持: {identifier}，请使用URL")
                return None

            response = self.fetch(url, timeout=30, verify_ssl=False)
            html_content = response.text
            if not html_content:
                self.logger.error(f"获取页面内容失败: {url}")
                return None

            # 使用共享方法提取所有元数据
            metadata_dict = self._extract_all_metadata(html_content)

            # 使用 MetadataBuilder 构建元数据
            builder = MetadataBuilder()
            metadata = (
                builder.set_title(metadata_dict["original_title"], metadata_dict["video_code"])
                .set_code(metadata_dict["video_code"])
                .set_site(self.site_name)
                .set_url(url)
                .set_identifier(self.site_name, metadata_dict["video_code"], url)
                .set_release_date(metadata_dict["release_date"])
                .set_cover(metadata_dict["cover_image"])
                .set_plot(metadata_dict["description"])
                .set_actors(metadata_dict["actors"])
                .set_director(metadata_dict["director"])
                .set_runtime(metadata_dict["duration"])
                .set_genres(metadata_dict["genres"])
                .set_tags(metadata_dict["tags"])
                .set_studio(metadata_dict["studio"])
                .set_serial(metadata_dict["series"])
                .build()
            )

            # 手动设置 MetadataBuilder 不支持的字段
            metadata.tagline = metadata_dict["tagline"]
            metadata.official_rating = "JP-18+"

            self.logger.info(f"成功提取元数据: {metadata_dict['video_code']} - {metadata_dict['original_title']}")
            return metadata

        except Exception as e:
            self.logger.error(f"提取元数据失败: {e}")
            return None

    # ==================== 视频提取功能接口 ====================

    def can_handle(self, url: str) -> bool:
        """检查是否能处理给定的URL"""
        return self.can_handle_domain(url, self.supported_domains)

    def extract(self, url: str) -> List[OperationItem]:
        """从 MissAV 页面提取视频下载选项"""
        try:
            response = self.fetch(url, timeout=30, verify_ssl=False)
            html_content = response.text
            if not html_content:
                self.logger.error(f"获取页面内容失败: {url}")
                return []

            # 提取视频URL
            video_urls = self._extract_obfuscated_urls(html_content)
            if not video_urls:
                self.logger.error(f"未能从页面提取视频链接: {url}")
                return []

            # 使用共享方法提取所有元数据
            metadata_dict = self._extract_all_metadata(html_content)

            # 使用 MetadataBuilder 构建元数据
            builder = MetadataBuilder()
            metadata = (
                builder.set_title(metadata_dict["original_title"], metadata_dict["video_code"])
                .set_code(metadata_dict["video_code"])
                .set_site(self.site_name)
                .set_url(url)
                .set_identifier(self.site_name, metadata_dict["video_code"], url)
                .set_release_date(metadata_dict["release_date"])
                .set_cover(metadata_dict["cover_image"])
                .set_plot(metadata_dict["description"])
                .set_actors(metadata_dict["actors"])
                .set_director(metadata_dict["director"])
                .set_runtime(metadata_dict["duration"])
                .set_genres(metadata_dict["genres"])
                .set_tags(metadata_dict["tags"])
                .set_studio(metadata_dict["studio"])
                .set_serial(metadata_dict["series"])
                .build()
            )

            # 手动设置 MetadataBuilder 不支持的字段
            metadata.tagline = metadata_dict["tagline"]
            metadata.official_rating = "JP-18+"

            # 使用 OperationItemBuilder 构建下载项
            op_builder = OperationItemBuilder(self.site_name, metadata_dict["original_title"], metadata_dict["video_code"])
            op_builder.set_cover(metadata_dict["cover_image"]).set_landscape(metadata_dict["cover_image"]).set_metadata(
                metadata
            ).set_actors(metadata_dict["actors"]).set_studio(metadata_dict["studio"]).set_year(metadata.year)

            # 添加所有质量的视频流
            for _, video_url in video_urls.items():
                if video_url:
                    quality = Quality.guess(video_url)
                    op_builder.add_stream(video_url, quality)

            return op_builder.build()

        except Exception as e:
            self.logger.error(f"获取页面失败: {e}")
            return []

    def _extract_obfuscated_urls(self, html_content: str) -> Dict[str, str]:
        """从JavaScript混淆代码中提取视频URL"""
        uuid = self._extract_uuid(html_content)
        if uuid:
            master_url = f"https://surrit.com/{uuid}/playlist.m3u8"
            self.logger.debug(f"提取到UUID: {uuid}, 构建的主播放列表链接: {master_url}")
            return self._extract_master_playlist(master_url)
        else:
            self.logger.error("未能从页面中提取UUID，无法获取视频链接")
            return {}

    def _extract_master_playlist(self, master_url: str) -> Dict[str, str]:
        """从大师链接中提取所有子链接"""
        try:
            response = self.fetch(master_url, timeout=30, verify_ssl=False)
            if response.status_code != 200:
                self.logger.info(f"获取大师链接失败: {master_url} - 状态码: {response.status_code}")
                return {}

            base_url = master_url.rsplit("/", 1)[0] + "/"
            m3u8_content = response.text
            self.logger.debug(f"处理大师链接内容: {m3u8_content[:100]}...")

            lines = m3u8_content.splitlines()
            sub_urls: Dict[str, str] = {}
            for line in lines:
                line = line.strip()
                if line and not line.startswith("#"):
                    if line.endswith("m3u8"):
                        if line.startswith("http"):
                            key = self._get_key_for_url(line)
                            if key:
                                sub_urls[key] = line
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
        """获取视频URL的唯一键"""
        return Quality.guess(url)

    # ==================== 共享的元数据提取方法 ====================

    def _extract_all_metadata(self, html: str) -> Dict[str, Any]:
        """提取所有元数据并返回字典"""
        title_with_code, original_title, video_code = self._extract_title_and_code(html)

        return {
            "title_with_code": title_with_code,
            "original_title": original_title,
            "video_code": video_code,
            "actors": self._extract_actors(html),
            "director": self._extract_director(html),
            "duration": self._extract_duration(html),
            "release_date": self._extract_release_date(html),
            "genres": self._extract_genres(html),
            "tags": self._extract_tags(html),
            "studio": self._extract_studio(html),
            "series": self._extract_series(html),
            "cover_image": self._extract_cover_image(html),
            "description": self._extract_description(html),
            "tagline": self._extract_tagline(html),
        }

    def _extract_title_and_code(self, html: str) -> Tuple[str, str, str]:
        """从HTML中提取视频标题和代码"""
        default_title = "MissAV Video"
        default_code = self._extract_uuid(html) or "Unknown"
        try:
            title_match = re.search(r'<meta property="og:title" content="([^"]+)"', html)
            if title_match:
                matched = title_match.group(1).strip()
                parts = matched.split(" ", maxsplit=1)
                video_code = CodeExtractUtils.extract_code_from_text(parts[0]) if len(parts) > 0 else default_code
                if not video_code:
                    video_code = default_code
                original_title = parts[1] if len(parts) > 1 else default_title
                title_with_code = f"{video_code} {original_title}"
            else:
                original_title = default_title
                video_code = default_code
                title_with_code = f"{video_code} {original_title}"

            if not video_code:
                video_code = default_code
            return (title_with_code, original_title, video_code)
        except Exception as e:
            self.logger.error(f"提取标题和代码异常: {str(e)}")
            return (f"{default_code} {default_title}", default_title, default_code)

    def _extract_uuid(self, html: str) -> Optional[str]:
        """提取UUID"""
        try:
            if match := re.search(r"m3u8\|([a-f0-9\|]+)\|com\|surrit\|https\|video", html):
                return "-".join(match.group(1).split("|")[::-1])
            return None
        except Exception as e:
            self.logger.debug(f"UUID提取异常: {str(e)}")
            return None

    def _extract_actors(self, html: str) -> List[str]:
        """从HTML中提取演员列表"""
        try:
            return re.findall(r'<meta property="og:video:actor" content="([^"]+)"', html)
        except Exception as e:
            self.logger.debug(f"提取演员异常: {str(e)}")
            return []

    def _extract_director(self, html: str) -> Optional[str]:
        """从HTML中提取导演"""
        try:
            directors = re.findall(r'<meta property="og:video:director" content="([^"]+)"', html)
            return directors[0] if directors and directors[0] else None
        except Exception as e:
            self.logger.debug(f"提取导演异常: {str(e)}")
            return None

    def _extract_duration(self, html: str) -> Optional[int]:
        """从HTML中提取视频时长（分钟）"""
        try:
            duration_match = re.search(r'<meta property="og:video:duration" content="(\d+)"', html)
            if duration_match:
                seconds = int(duration_match.group(1))
                return seconds // 60 if seconds > 0 else None
            return None
        except Exception as e:
            self.logger.debug(f"提取时长异常: {str(e)}")
            return None

    def _extract_release_date(self, html: str) -> Optional[str]:
        """从HTML中提取发布日期"""
        try:
            date_match = re.search(r'<meta property="og:video:release_date" content="([^"]+)"', html)
            return date_match.group(1) if date_match else None
        except Exception as e:
            self.logger.debug(f"提取发布日期异常: {str(e)}")
            return None

    def _extract_genres(self, html: str) -> List[str]:
        """从HTML中提取视频类型"""
        try:
            genre_labels = [
                r"ジャンル:",
                r"类型:",
                r"類型:",
                r"分类:",
                r"分類:",
                r"种类:",
                r"種類:",
                r"Genre:",
                r"Category:",
                r"장르:",
                r"Thể loại:",
                r"Kategori:",
                r"หมวดหมู่:",
            ]

            for label_pattern in genre_labels:
                pattern = label_pattern + r".*?</div>"
                match = re.search(pattern, html, re.DOTALL)
                if match:
                    self.logger.debug(f"找到类型部分，使用标签: {label_pattern}")
                    genre_names = re.findall(r'class="text-nord13 font-medium">([^<]+)</a>', match.group(0))
                    return list(dict.fromkeys(genre_names))

            return []
        except Exception as e:
            self.logger.debug(f"提取类型异常: {str(e)}")
            return []

    def _extract_tags(self, html: str) -> List[str]:
        """从HTML中提取视频标签"""
        try:
            tag_labels = [r"タグ:", r"标签:", r"標籤:", r"Tags:", r"Label:", r"Tag:"]

            for label_pattern in tag_labels:
                pattern = label_pattern + r".*?</div>"
                match = re.search(pattern, html, re.DOTALL)
                if match:
                    self.logger.debug(f"找到标签部分，使用标签: {label_pattern}")
                    tag_names = re.findall(r'class="text-nord13 font-medium">([^<]+)</a>', match.group(0))
                    return list(dict.fromkeys(tag_names))

            keywords_match = re.search(r'<meta name="keywords" content="([^"]+)"', html)
            if keywords_match:
                keywords = keywords_match.group(1).split(",")
                cleaned = [tag.strip() for tag in keywords if tag.strip()]
                return list(dict.fromkeys(cleaned))

            return []
        except Exception as e:
            self.logger.debug(f"提取标签异常: {str(e)}")
            return []

    def _extract_studio(self, html: str) -> Optional[str]:
        """从HTML中提取制作公司"""
        try:
            studio_labels = [
                r"发行商:",
                r"發行商:",
                r"制作公司:",
                r"製作公司:",
                r"制作商:",
                r"製作商:",
                r"メーカー:",
                r"Maker:",
            ]

            for label_pattern in studio_labels:
                pattern = label_pattern + r".*?</div>"
                match = re.search(pattern, html, re.DOTALL)
                if match:
                    self.logger.debug(f"找到制作公司部分，使用标签: {label_pattern}")
                    studio_name = re.search(r'class="text-nord13 font-medium">([^<]+)</a>', match.group(0))
                    return studio_name.group(1) if studio_name else None

            return None
        except Exception as e:
            self.logger.debug(f"提取制作公司异常: {str(e)}")
            return None

    def _extract_series(self, html: str) -> Optional[str]:
        """从HTML中提取系列名称"""
        try:
            series_labels = [r"シリーズ:", r"系列:", r"系列:", r"Series:"]

            for label_pattern in series_labels:
                pattern = label_pattern + r".*?</div>"
                match = re.search(pattern, html, re.DOTALL)
                if match:
                    self.logger.debug(f"找到系列部分，使用标签: {label_pattern}")
                    series_names = re.findall(r'class="text-nord13 font-medium">([^<]+)</a>', match.group(0))
                    return series_names[0] if series_names else None

            return None
        except Exception as e:
            self.logger.debug(f"提取系列异常: {str(e)}")
            return None

    def _extract_cover_image(self, html: str) -> Optional[str]:
        """从HTML中提取封面图片链接"""
        return HTMLMetadataExtractor.extract_og_image(html)

    def _extract_description(self, html: str) -> Optional[str]:
        """从HTML中提取视频描述"""
        return HTMLMetadataExtractor.extract_og_description(html)

    def _extract_tagline(self, html: str) -> Optional[str]:
        """从HTML中提取视频标语"""
        return HTMLMetadataExtractor.extract_og_title(html)


def register_plugin():
    """注册MissAV统一插件"""
    return MissAVPlugin()

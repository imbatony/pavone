"""
AV01元数据提取器插件

支持从 av01.tv 和 av01.media 网站提取元数据。

该提取器基于API，不需要解析HTML：
1. 从 geo API 获取 token
2. 从 /api/v1/videos/{id} 获取视频元数据
"""

import re
import time
from dataclasses import dataclass
from datetime import datetime
from typing import Dict, List, Optional
from urllib.parse import urlparse

from ...models import MovieMetadata
from ...utils import CodeExtractUtils, StringUtils
from .base import MetadataPlugin


@dataclass
class GeoData:
    """
    AV01 地理位置认证数据类

    用于存储从 geo API 获取的 token、IP、过期时间等信息。

    Attributes:
        token: 认证令牌
        expires: 过期时间戳（Unix timestamp）
        ip: 客户端IP地址
        asn: 自治系统号
        isp: 互联网服务提供商
        continent: 大陆代码（如 AS, EU, NA 等）
        country: 国家代码（如 SG, US, CN 等）
        ttl: 生存时间（秒），表示数据的有效期
        url: 获取此数据的 API 地址
        comp: 是否已压缩
    """

    token: str
    expires: str
    ip: str
    asn: int
    isp: str
    continent: str
    country: str
    ttl: int
    url: str
    comp: bool = False

    @classmethod
    def from_dict(cls, data: dict) -> "GeoData":
        """从字典创建 GeoData 实例"""
        required_fields = {
            "token",
            "expires",
            "ip",
            "asn",
            "isp",
            "continent",
            "country",
            "ttl",
            "url",
        }
        missing_fields = required_fields - set(data.keys())

        if missing_fields:
            raise ValueError(f"缺少必需字段: {missing_fields}")

        return cls(
            token=data["token"],
            expires=data["expires"],
            ip=data["ip"],
            asn=int(data["asn"]),
            isp=data["isp"],
            continent=data["continent"],
            country=data["country"],
            ttl=int(data["ttl"]),
            url=data["url"],
            comp=bool(data.get("comp", False)),
        )

    def is_expired(self, current_time: Optional[float] = None) -> bool:
        """检查数据是否已过期"""
        if current_time is None:
            current_time = time.time()

        try:
            expires_timestamp = float(self.expires)
            return current_time > expires_timestamp
        except (ValueError, TypeError):
            return False


@dataclass
class AV01VideoMetadata:
    """
    AV01 视频元数据类

    用于存储从视频 API 获取的视频信息。

    Attributes:
        id: 视频ID
        dvd_id: DVD ID（番号）
        dmm_id: DMM ID
        title: 视频标题
        description: 视频描述
        duration: 视频时长（秒）
        views: 浏览次数
        uploaded_time: 上传时间
        published_time: 发布时间
        original_language: 原始语言
        cover: 是否有封面
        maker: 制作商名称或字典
        director: 导演名称或字典
        actresses: 女优列表
        tags: 标签列表
        poster: 海报URL
    """

    id: int
    dvd_id: str
    dmm_id: str
    title: str
    description: str
    duration: int
    views: int
    uploaded_time: str
    published_time: str
    original_language: str
    cover: bool
    maker: Optional[str] = None
    director: Optional[str] = None
    actresses: Optional[List[Dict]] = None
    tags: Optional[List[Dict]] = None
    poster: Optional[str] = None

    @classmethod
    def from_dict(cls, data: dict) -> "AV01VideoMetadata":
        """从字典创建 AV01VideoMetadata 实例"""
        required_fields = {
            "id",
            "dvd_id",
            "dmm_id",
            "title",
            "description",
            "duration",
            "views",
            "uploaded_time",
            "published_time",
            "original_language",
            "cover",
        }
        missing_fields = required_fields - set(data.keys())

        if missing_fields:
            raise ValueError(f"缺少必需字段: {missing_fields}")

        # 处理 maker 字段 - 可能是字典或字符串
        maker = data.get("maker")
        if isinstance(maker, dict):
            maker = maker.get("name", "")
        elif not isinstance(maker, str):
            maker = None

        # 处理 director 字段 - 可能是字典或字符串
        director = data.get("director")
        if isinstance(director, dict):
            director = director.get("name", "")
        elif not isinstance(director, str):
            director = None

        return cls(
            id=int(data["id"]),
            dvd_id=data["dvd_id"],
            dmm_id=data["dmm_id"],
            title=data["title"],
            description=data["description"],
            duration=int(data["duration"]),
            views=int(data["views"]),
            uploaded_time=data["uploaded_time"],
            published_time=data["published_time"],
            original_language=data["original_language"],
            cover=bool(data["cover"]),
            maker=maker,
            director=director,
            actresses=data.get("actresses"),
            tags=data.get("tags"),
            poster=data.get("poster"),
        )

    def get_actor_names(self) -> List[str]:
        """提取所有女优名称"""
        if not self.actresses or not isinstance(self.actresses, list):
            return []

        names = []
        for actress in self.actresses:
            if isinstance(actress, dict):
                name = actress.get("name", "")
                if name:
                    names.append(name)

        return names

    def get_tag_names(self) -> List[str]:
        """提取所有标签名称"""
        if not self.tags or not isinstance(self.tags, list):
            return []

        names = []
        for tag in self.tags:
            if isinstance(tag, dict):
                name = tag.get("name", "")
                if name:
                    names.append(name)
            elif isinstance(tag, str):
                names.append(tag)

        return names

    def get_release_year(self) -> int:
        """从发布时间提取年份"""
        try:
            # 处理 ISO 8601 格式 (2025-11-27T00:00:00Z)
            if "T" in self.published_time:
                return int(self.published_time.split("T")[0].split("-")[0])
            else:
                return int(self.published_time.split("-")[0])
        except (ValueError, IndexError):
            return datetime.now().year

    def get_runtime_minutes(self) -> Optional[int]:
        """获取视频时长（分钟）"""
        if self.duration and self.duration > 0:
            return int(self.duration // 60)
        return None


# 定义插件名称和版本
PLUGIN_NAME = "AV01Metadata"
PLUGIN_VERSION = "1.0.0"
PLUGIN_DESCRIPTION = "提取 av01.tv 和 av01.media 的视频元数据（基于API）"
PLUGIN_AUTHOR = "PAVOne"

# 定义插件优先级
PLUGIN_PRIORITY = 30

# 定义支持的域名
SUPPORTED_DOMAINS = ["av01.media", "www.av01.media", "av01.tv", "www.av01.tv"]

SITE_NAME = "AV01"

# API端点
GEO_API_URL = "https://www.av01.tv/edge/geo.js?json"
VIDEO_API_BASE = "https://www.av01.media/api/v1/videos"


class AV01Metadata(MetadataPlugin):
    """
    AV01元数据提取器
    继承自MetadataPlugin，提供从 av01.tv 和 av01.media 提取元数据的功能。

    该提取器基于API，不需要解析HTML。
    """

    def __init__(self):
        """初始化AV01元数据提取器"""
        super().__init__()
        self.name = PLUGIN_NAME
        self.version = PLUGIN_VERSION
        self.description = PLUGIN_DESCRIPTION
        self.priority = PLUGIN_PRIORITY
        self.supported_domains = SUPPORTED_DOMAINS
        self.author = PLUGIN_AUTHOR

        # 缓存geo数据
        self._geo_data: Optional[GeoData] = None
        self._geo_fetched_at: Optional[float] = None

    def can_extract(self, identifier: str) -> bool:
        """检查是否能处理给定的identifier

        支持两种格式：
        1. URL: https://av01.tv/jp/video/184522/fc2-ppv-4799119
        2. 视频代码: FC2-PPV-4799119 或类似格式
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

        # 检查是否为视频代码
        # AV01支持的代码格式比较灵活，基本上符合标准番号格式的都可以
        identifier_stripped = identifier.strip()
        code_pattern = r"^[a-zA-Z]+(-|\d)[a-zA-Z0-9\-]*$"
        if re.match(code_pattern, identifier_stripped):
            # 确保包含连字符，且左边是字母
            if "-" in identifier_stripped:
                parts = identifier_stripped.split("-", 1)
                if len(parts) >= 2 and len(parts[0]) > 0 and parts[0][0].isalpha():
                    return True

        return False

    def extract_metadata(self, identifier: str) -> Optional[MovieMetadata]:
        """从给定的identifier提取元数据

        Args:
            identifier: 可以是URL或视频代码

        Returns:
            提取到的MovieMetadata对象，如果失败返回None
        """
        try:
            # 1. 提取视频ID
            video_id = None
            url = identifier

            if identifier.startswith("http"):
                # 从URL提取视频ID
                video_id = self._extract_video_id(identifier)
                if not video_id:
                    self.logger.error(f"无法从URL提取视频ID: {identifier}")
                    return None
            else:
                # 对于视频代码，暂时不直接支持
                # 实际应用中可以集成搜索功能来获取视频ID
                self.logger.warning(f"代码格式identifier暂不直接支持: {identifier}，请使用URL")
                return None

            self.logger.info(f"提取到视频ID: {video_id}")

            # 2. 获取geo数据和token
            geo_data = self._get_geo_data()
            if not geo_data:
                self.logger.error("无法获取geo token")
                return None

            # 3. 获取视频元数据
            metadata_api_url = f"{VIDEO_API_BASE}/{video_id}"
            video_metadata = self._get_video_metadata(metadata_api_url)

            if not video_metadata:
                self.logger.error(f"无法获取视频元数据: {video_id}")
                return None

            self.logger.info(f"获取到视频元数据: {video_metadata.title}")

            # 4. 构建 MovieMetadata 对象
            return self._build_movie_metadata(video_metadata, url, geo_data, video_id)

        except Exception as e:
            self.logger.error(f"提取元数据失败: {e}", exc_info=True)
            return None

    def _build_movie_metadata(
        self,
        video_metadata: AV01VideoMetadata,
        original_url: str,
        geo_data: GeoData,
        video_id: str,
    ) -> Optional[MovieMetadata]:
        """根据视频元数据构建 MovieMetadata 对象"""
        try:
            # 提取基本信息
            title = video_metadata.title

            # 提取番号 - AV01使用 dvd_id 作为番号
            video_code = video_metadata.dvd_id
            if not video_code:
                video_code = CodeExtractUtils.extract_code_from_text(title) or "Unknown"
            else:
                # 需要对番号进行额外处理
                video_code = CodeExtractUtils.extract_code_from_text(video_code) or video_code

            # 提取演员
            actors = video_metadata.get_actor_names()

            # 提取其他信息
            runtime_minutes = video_metadata.get_runtime_minutes()

            # 提取发布时间
            release_date = video_metadata.published_time

            # 提取制作商
            studio = video_metadata.maker

            # 提取分类/标签
            genres = []
            tags = video_metadata.get_tag_names()

            # 封面图片 - 使用带认证的URL构建或 poster 字段
            cover_image = None
            if video_metadata.poster:
                cover_image = video_metadata.poster
            elif video_metadata.cover:
                # 使用geo认证构建封面URL
                cover_image = self._build_cover_url(video_id, geo_data)

            # 描述
            description = video_metadata.description

            # 导演
            director = video_metadata.director

            # 发布年份
            release_year = video_metadata.get_release_year()

            # 创建identifier
            identifier = StringUtils.create_identifier(site=SITE_NAME, code=video_code, url=original_url)

            # 创建元数据对象
            metadata = MovieMetadata(
                title=video_code + " " + title,
                original_title=title,
                identifier=identifier,
                site=SITE_NAME,
                url=original_url,
                code=video_code,
                actors=actors,
                runtime=runtime_minutes,
                premiered=release_date,
                genres=genres,
                tags=tags,
                studio=studio,
                director=director,
                cover=cover_image,
                plot=description,
                year=release_year,
            )

            self.logger.info(f"成功构建元数据: {video_code} - {title}")
            return metadata

        except Exception as e:
            self.logger.error(f"构建元数据失败: {e}")
            return None

    def _build_cover_url(self, video_id: str, geo_data: GeoData) -> Optional[str]:
        """构建封面图片URL"""
        try:
            token = geo_data.token
            expires = geo_data.expires
            ip = geo_data.ip

            if not all([token, expires, ip]):
                return None

            # AV01封面格式
            cover_url = (
                f"https://static.av01.tv/media/videos/tmb/{video_id}/1.jpg/format=webp/wlv=800"
                f"?t={token}&e={expires}&ip={ip}"
            )

            self.logger.debug(f"构建封面URL: {cover_url[:100]}...")
            return cover_url
        except Exception as e:
            self.logger.error(f"构建封面URL失败: {e}")
            return None

    def _get_geo_data(self, force_refresh: bool = False) -> Optional[GeoData]:
        """获取geo数据（包含token）"""
        # 检查缓存
        if not force_refresh and self._geo_data and self._geo_fetched_at:
            ttl = self._geo_data.ttl
            elapsed = time.time() - self._geo_fetched_at

            if elapsed < ttl:
                self.logger.debug(f"使用缓存的geo数据（剩余{int(ttl - elapsed)}秒）")
                return self._geo_data

        # 从API获取
        try:
            self.logger.info("正在从API获取geo数据...")

            response = self.fetch(GEO_API_URL, timeout=10, verify_ssl=True)

            if response.status_code == 200:
                geo_dict = response.json()
                self._geo_data = GeoData.from_dict(geo_dict)
                self._geo_fetched_at = time.time()
                self.logger.info(f"成功获取geo数据，token: {self._geo_data.token[:10]}...")
                return self._geo_data
            else:
                self.logger.error(f"获取geo数据失败，状态码: {response.status_code}")
                return None

        except Exception as e:
            self.logger.error(f"获取geo数据异常: {e}")
            return None

    def _get_video_metadata(self, metadata_url: str) -> Optional[AV01VideoMetadata]:
        """从API获取视频元数据"""
        try:
            self.logger.info(f"正在获取视频元数据: {metadata_url}")

            response = self.fetch(metadata_url, timeout=30, verify_ssl=True)

            if response.status_code != 200:
                self.logger.error(f"获取视频元数据失败，状态码: {response.status_code}")
                return None

            metadata_dict = response.json()
            self.logger.debug(f"视频元数据: {str(metadata_dict)[:200]}...")

            # 转换为 AV01VideoMetadata 实例
            metadata = AV01VideoMetadata.from_dict(metadata_dict)
            return metadata

        except Exception as e:
            self.logger.error(f"获取视频元数据异常: {e}")
            return None

    def _extract_video_id(self, url: str) -> Optional[str]:
        """从URL提取视频ID

        URL格式示例:
        - https://www.av01.media/jp/video/184522/fc2-ppv-4799119
        - https://av01.media/en/video/123456/some-title

        视频ID是 /video/ 后面的数字
        """
        try:
            # 匹配 /video/{id}/ 或 /video/{id} 模式
            match = re.search(r"/video/(\d+)", url)
            if match:
                return match.group(1)

            return None
        except Exception as e:
            self.logger.error(f"提取视频ID失败: {e}")
            return None

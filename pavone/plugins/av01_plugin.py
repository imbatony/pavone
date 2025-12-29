"""
AV01统一插件

支持从 av01.tv 和 av01.media 网站提取元数据和视频下载链接。

该插件完全基于API，不需要解析HTML：
1. 从 geo API 获取 token
2. 从 /api/v1/videos/{id} 获取视频元数据
3. 从 /api/v1/videos/{id}/playlist 获取播放列表
"""

import base64
import json
import re
import time
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List, Optional, cast
from urllib.parse import urlparse

from ..config.logging_config import get_logger
from ..models import MovieMetadata, OperationItem, Quality
from ..utils import CodeExtractUtils
from ..utils.metadata_builder import MetadataBuilder
from ..utils.operation_item_builder import OperationItemBuilder
from .extractors.base import ExtractorPlugin
from .metadata.base import MetadataPlugin


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
    def from_dict(cls, data: Dict[str, Any]) -> "GeoData":
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

    def to_dict(self) -> Dict[str, Any]:
        """将 GeoData 转换为字典"""
        return {
            "token": self.token,
            "expires": self.expires,
            "ip": self.ip,
            "asn": self.asn,
            "isp": self.isp,
            "continent": self.continent,
            "country": self.country,
            "ttl": self.ttl,
            "url": self.url,
            "comp": self.comp,
        }

    def is_expired(self, current_time: Optional[float] = None) -> bool:
        """检查数据是否已过期"""
        if current_time is None:
            current_time = time.time()

        try:
            expires_timestamp = float(self.expires)
            return current_time > expires_timestamp
        except (ValueError, TypeError):
            return False

    def __repr__(self) -> str:
        """返回对象的字符串表示"""
        token_preview = self.token[:10] + "..." if len(self.token) > 10 else self.token
        return f"GeoData(token={token_preview}, ip={self.ip}, country={self.country}, expires={self.expires})"


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
    actresses: Optional[List[Dict[str, str]]] = None
    tags: Optional[List[Dict[str, str]]] = None
    poster: Optional[str] = None

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "AV01VideoMetadata":
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
        maker_raw = data.get("maker")
        maker: Optional[str] = None
        if isinstance(maker_raw, dict):
            maker_dict = cast(Dict[str, Any], maker_raw)
            name_value = maker_dict.get("name", "")
            maker = str(name_value) if name_value else None
        elif isinstance(maker_raw, str):
            maker = maker_raw

        # 处理 director 字段 - 可能是字典或字符串
        director_raw = data.get("director")
        director: Optional[str] = None
        if isinstance(director_raw, dict):
            director_dict = cast(Dict[str, Any], director_raw)
            name_value = director_dict.get("name", "")
            director = str(name_value) if name_value else None
        elif isinstance(director_raw, str):
            director = director_raw

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

    def to_dict(self) -> Dict[str, Any]:
        """将 AV01VideoMetadata 转换为字典"""
        return {
            "id": self.id,
            "dvd_id": self.dvd_id,
            "dmm_id": self.dmm_id,
            "title": self.title,
            "description": self.description,
            "duration": self.duration,
            "views": self.views,
            "uploaded_time": self.uploaded_time,
            "published_time": self.published_time,
            "original_language": self.original_language,
            "cover": self.cover,
            "maker": self.maker,
            "director": self.director,
            "actresses": self.actresses,
            "tags": self.tags,
            "poster": self.poster,
        }

    def get_actor_names(self) -> List[str]:
        """提取所有女优名称"""
        if not self.actresses or not isinstance(self.actresses, list):
            return []

        names: List[str] = []
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

        names: List[str] = []
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

    def __repr__(self) -> str:
        """返回对象的字符串表示"""
        return f"AV01VideoMetadata(id={self.id}, dvd_id={self.dvd_id}, title={self.title[:50]}...)"


# 定义插件名称和版本
PLUGIN_NAME = "AV01"
PLUGIN_VERSION = "2.0.0"
PLUGIN_DESCRIPTION = "AV01统一插件：支持元数据提取和视频下载"
PLUGIN_AUTHOR = "PAVOne"

# 定义插件优先级
PLUGIN_PRIORITY = 30

# 定义支持的域名
SUPPORTED_DOMAINS = ["av01.media", "www.av01.media", "av01.tv", "www.av01.tv"]

SITE_NAME = "AV01"

# API端点
GEO_API_URL = "https://www.av01.tv/edge/geo.js?json"
VIDEO_API_BASE = "https://www.av01.media/api/v1/videos"


class AV01Plugin(ExtractorPlugin, MetadataPlugin):
    """
    AV01统一插件
    同时实现元数据提取和视频下载两种功能（通过多继承）
    """

    def __init__(self):
        """初始化AV01插件"""
        # 多继承情况下，使用 super() 会按照 MRO 顺序调用
        super().__init__(
            name=PLUGIN_NAME,
            version=PLUGIN_VERSION,
            description=PLUGIN_DESCRIPTION,
            author=PLUGIN_AUTHOR,
            priority=PLUGIN_PRIORITY,
        )
        self.supported_domains = SUPPORTED_DOMAINS
        self.site_name = SITE_NAME
        self.logger = get_logger(__name__)

        # 缓存geo数据
        self._geo_data: Optional[GeoData] = None
        self._geo_fetched_at: Optional[float] = None

    def initialize(self) -> bool:
        """初始化插件"""
        return True

    # ==================== 元数据提取功能接口 ====================

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

    # ==================== 视频提取功能接口 ====================

    def can_handle(self, url: str) -> bool:
        """检查是否能处理给定的URL"""
        return self.can_handle_domain(url, self.supported_domains)

    def extract(self, url: str) -> List[OperationItem]:
        """
        从 AV01 API提取视频下载选项

        工作流程：
        1. 从URL提取视频ID
        2. 获取geo token
        3. 调用视频元数据API
        4. 调用播放列表API
        5. 构建下载选项
        """
        try:
            # 1. 提取视频ID
            video_id = self._extract_video_id(url)
            if not video_id:
                self.logger.error(f"无法从URL提取视频ID: {url}")
                return []

            self.logger.info(f"提取到视频ID: {video_id}")

            # 2. 获取geo数据和token
            geo_data = self._get_geo_data()
            if not geo_data:
                self.logger.error("无法获取geo token")
                return []

            token = geo_data.token
            expires = geo_data.expires
            ip = geo_data.ip

            self.logger.info(f"获取到token: {token[:10]}... IP: {ip}")

            # 3. 获取视频元数据
            metadata_api_url = f"{VIDEO_API_BASE}/{video_id}"
            video_metadata = self._get_video_metadata(metadata_api_url)

            if not video_metadata:
                self.logger.error(f"无法获取视频元数据: {video_id}")
                return []

            self.logger.info(f"获取到视频元数据: {video_metadata.title}")

            # 4. 获取播放列表
            playlist_api_url = f"{VIDEO_API_BASE}/{video_id}/playlist?token={token}&expires={expires}&ip={ip}"
            video_urls = self._get_video_playlist(playlist_api_url)

            if not video_urls:
                self.logger.error(f"无法获取视频播放列表: {video_id}")
                return []

            self.logger.info(f"找到 {len(video_urls)} 个视频链接")

            # 5. 解析元数据并构建下载选项
            return self._build_download_items(video_metadata, video_urls, url, geo_data, video_id)

        except Exception as e:
            self.logger.error(f"提取视频信息失败: {e}", exc_info=True)
            return []

    # ==================== 共享辅助方法 ====================

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
            genres: list[str] = []
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

            # 使用 MetadataBuilder 构建元数据
            builder = MetadataBuilder()
            metadata = (
                builder.set_title(title, video_code)
                .set_code(video_code)
                .set_site(SITE_NAME)
                .set_url(original_url)
                .set_identifier(SITE_NAME, video_code, original_url)
                .set_release_date(release_date)
                .set_cover(cover_image)
                .set_plot(description)
                .set_actors(actors)
                .set_director(director)
                .set_runtime(runtime_minutes)
                .set_genres(genres)
                .set_tags(tags)
                .set_studio(studio)
                .build()
            )

            # 手动设置 MetadataBuilder 不支持的字段
            metadata.official_rating = "JP-18+"

            self.logger.info(f"成功构建元数据: {video_code} - {title}")
            return metadata

        except Exception as e:
            self.logger.error(f"构建元数据失败: {e}")
            return None

    def _build_download_items(
        self,
        video_metadata: AV01VideoMetadata,
        video_urls: Dict[str, str],
        original_url: str,
        geo_data: GeoData,
        video_id: str,
    ) -> List[OperationItem]:
        """根据视频元数据和URL列表构建下载选项"""
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
            genres: list[str] = []
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

            # 使用 MetadataBuilder 构建元数据
            builder = MetadataBuilder()
            metadata = (
                builder.set_title(title, video_code)
                .set_code(video_code)
                .set_site(SITE_NAME)
                .set_url(original_url)
                .set_identifier(SITE_NAME, video_code, original_url)
                .set_release_date(release_date)
                .set_cover(cover_image)
                .set_plot(description)
                .set_actors(actors)
                .set_director(director)
                .set_runtime(runtime_minutes)
                .set_genres(genres)
                .set_tags(tags)
                .set_studio(studio)
                .build()
            )

            # 使用 OperationItemBuilder 构建下载项
            op_builder = OperationItemBuilder(SITE_NAME, title, video_code)
            op_builder.set_cover(cover_image).set_landscape(cover_image).set_metadata(metadata).set_actors(actors).set_studio(
                studio
            ).set_year(release_year)

            # 构建下载选项
            for quality_key, video_url in video_urls.items():
                if not video_url:
                    continue

                # 使用已解析的质量，如果无法识别再猜测
                quality = (
                    quality_key
                    if quality_key
                    in [
                        Quality.UHD,
                        Quality.QHD,
                        Quality.FHD,
                        Quality.HD,
                        Quality.SD,
                        Quality.LOW,
                    ]
                    else Quality.guess(video_url)
                )

                op_builder.add_stream(video_url, quality)

            return op_builder.build()

        except Exception as e:
            self.logger.error(f"构建下载选项失败: {e}")
            return []

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
            self.logger.debug(f"视频元数据: {json.dumps(metadata_dict, ensure_ascii=False)[:200]}...")

            # 转换为 AV01VideoMetadata 实例
            metadata = AV01VideoMetadata.from_dict(metadata_dict)
            return metadata

        except Exception as e:
            self.logger.error(f"获取视频元数据异常: {e}")
            return None

    def _get_video_playlist(self, playlist_url: str) -> Dict[str, str]:
        """从API获取视频播放列表"""
        try:
            self.logger.info(f"正在获取播放列表: {playlist_url}")

            response = self.fetch(playlist_url, timeout=30, verify_ssl=True)

            if response.status_code != 200:
                self.logger.error(f"获取播放列表失败，状态码: {response.status_code}")
                return {}

            # 尝试解析响应
            content_type = response.headers.get("Content-Type", "")

            if "application/json" in content_type:
                # JSON响应
                playlist_data = response.json()
                return self._parse_playlist_json(playlist_data)
            else:
                # 可能是m3u8格式
                return self._parse_m3u8_playlist(response.text, playlist_url)

        except Exception as e:
            self.logger.error(f"获取播放列表异常: {e}")
            return {}

    def _parse_playlist_json(self, data: Dict[str, Any]) -> Dict[str, str]:
        """解析JSON格式的播放列表响应"""
        result: Dict[str, str] = {}

        try:
            # AV01 API返回的是 {src: "data:application/x-mpegurl;charset=utf-8;base64,..."} 格式
            if "src" in data and isinstance(data["src"], str):
                src = data["src"]

                # 检查是否是base64编码的m3u8
                if "base64," in src:
                    # 提取base64部分
                    base64_data = src.split("base64,")[1]
                    # 解码
                    try:
                        m3u8_content = base64.b64decode(base64_data).decode("utf-8")
                        self.logger.debug(f"解码base64 m3u8内容: {len(m3u8_content)} 字符")
                        # 解析m3u8内容
                        return self._parse_m3u8_playlist(m3u8_content, "")
                    except Exception as e:
                        self.logger.error(f"解码base64失败: {e}")
                        return {}
                elif src.startswith("http"):
                    # 直接是URL
                    result["default"] = src
                    return result

            # 尝试其他可能的数据结构
            # 情况1: {data: {quality: url}}
            playlist: Dict[str, Any]
            if "data" in data and isinstance(data["data"], dict):
                playlist = cast(Dict[str, Any], data["data"])
            # 情况2: {playlist: {quality: url}}
            elif "playlist" in data:
                playlist = cast(Dict[str, Any], data["playlist"])
            # 情况3: 直接是 {quality: url}
            else:
                playlist = data

            # 提取URL
            for key, value in playlist.items():
                if isinstance(value, str) and ("http" in value or "m3u8" in value or "mp4" in value):
                    result[key] = value
                elif isinstance(value, dict) and "url" in value:
                    result[key] = value["url"]

            self.logger.info(f"从JSON解析到 {len(result)} 个播放链接")
            return result

        except Exception as e:
            self.logger.error(f"解析JSON播放列表失败: {e}")
            return {}

    def _parse_m3u8_playlist(self, m3u8_content: str, base_url: str) -> Dict[str, str]:
        """解析m3u8格式的播放列表"""
        result: Dict[str, str] = {}

        try:
            lines = m3u8_content.splitlines()

            current_quality: Optional[str] = None
            for _i, line in enumerate(lines):
                line = line.strip()

                # 解析 #EXT-X-STREAM-INF 标签以获取分辨率
                if line.startswith("#EXT-X-STREAM-INF:"):
                    # 提取分辨率信息
                    if "RESOLUTION=" in line:
                        resolution_match = re.search(r"RESOLUTION=(\d+)x(\d+)", line)
                        if resolution_match:
                            width = resolution_match.group(1)
                            height = resolution_match.group(2)
                            # 根据高度确定质量
                            if int(height) >= 2160:
                                current_quality = Quality.UHD
                            elif int(height) >= 1440:
                                current_quality = Quality.QHD
                            elif int(height) >= 1080:
                                current_quality = Quality.FHD
                            elif int(height) >= 720:
                                current_quality = Quality.HD
                            elif int(height) >= 480:
                                current_quality = Quality.SD
                            else:
                                current_quality = Quality.LOW

                            self.logger.debug(f"检测到质量 {current_quality} ({width}x{height})")

                # 处理URL行（非注释行）
                elif line and not line.startswith("#"):
                    # 构建完整URL
                    if line.startswith("http"):
                        url = line
                    elif base_url:
                        # 简单拼接
                        base_path = base_url.rsplit("/", 1)[0] + "/"
                        url = base_path + line if not line.startswith("/") else "https://www.av01.tv" + line
                    else:
                        # base_url为空，说明是从base64解码的，URL应该已经完整
                        url = line

                    # 使用之前检测到的质量，或从URL猜测
                    quality = current_quality if current_quality else Quality.guess(url)
                    result[quality] = url
                    current_quality = None  # 重置

            self.logger.info(f"从m3u8解析到 {len(result)} 个播放链接")
            return result

        except Exception as e:
            self.logger.error(f"解析m3u8播放列表失败: {e}")
            return {}

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

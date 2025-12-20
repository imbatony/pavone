"""
AV01视频提取器插件

支持从 av01.tv 网站提取视频下载链接。

该提取器完全基于API，不需要解析HTML：
1. 从 geo API 获取 token
2. 从 /api/v1/videos/{id} 获取视频元数据
3. 从 /api/v1/videos/{id}/playlist 获取播放列表
"""

import json
import re
import time
from dataclasses import dataclass
from datetime import datetime
from typing import Dict, List, Optional
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


@dataclass
class GeoData:
    """
    AV01 地理位置认证数据类

    用于存储从 geo API 获取的 token、IP、过期时间等信息。
    此类仅用于 AV01 提取器。

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
        """
        从字典创建 GeoData 实例

        Args:
            data: 包含 geo 数据的字典

        Returns:
            GeoData 实例

        Raises:
            ValueError: 当缺少必需字段时
        """
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

    def to_dict(self) -> dict:
        """
        将 GeoData 转换为字典

        Returns:
            包含所有字段的字典
        """
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
        """
        检查数据是否已过期

        Args:
            current_time: 当前时间戳，如果为 None 则使用系统当前时间

        Returns:
            如果已过期返回 True，否则返回 False
        """
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
        return f"GeoData(token={token_preview}, ip={self.ip}, " f"country={self.country}, expires={self.expires})"


@dataclass
class AV01VideoMetadata:
    """
    AV01 视频元数据类

    用于存储从视频 API 获取的视频信息。
    此类仅用于 AV01 提取器。

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
        """
        从字典创建 AV01VideoMetadata 实例

        Args:
            data: 包含视频元数据的字典

        Returns:
            AV01VideoMetadata 实例

        Raises:
            ValueError: 当缺少必需字段时
        """
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

    def to_dict(self) -> dict:
        """
        将 AV01VideoMetadata 转换为字典

        Returns:
            包含所有字段的字典
        """
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
        """
        提取所有女优名称

        Returns:
            女优名称列表
        """
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
        """
        提取所有标签名称

        Returns:
            标签名称列表
        """
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
        """
        从发布时间提取年份

        Returns:
            发布年份
        """
        try:
            # 处理 ISO 8601 格式 (2025-11-27T00:00:00Z)
            if "T" in self.published_time:
                return int(self.published_time.split("T")[0].split("-")[0])
            else:
                return int(self.published_time.split("-")[0])
        except (ValueError, IndexError):
            return datetime.now().year

    def get_runtime_minutes(self) -> Optional[int]:
        """
        获取视频时长（分钟）

        Returns:
            视频时长（分钟）或 None
        """
        if self.duration and self.duration > 0:
            return int(self.duration // 60)
        return None

    def __repr__(self) -> str:
        """返回对象的字符串表示"""
        return f"AV01VideoMetadata(id={self.id}, dvd_id={self.dvd_id}, title={self.title[:50]}...)"


# 定义插件名称和版本
PLUGIN_NAME = "AV01Extractor"
PLUGIN_VERSION = "1.0.0"
PLUGIN_DESCRIPTION = "提取 av01.tv 的视频下载链接（基于API）"
PLUGIN_AUTHOR = "PAVOne"

# 定义插件优先级
PLUGIN_PRIORITY = 30

# 定义支持的域名
SUPPORTED_DOMAINS = ["av01.media", "www.av01.media", "av01.tv", "www.av01.tv"]

SITE_NAME = "AV01"

# API端点
GEO_API_URL = "https://www.av01.tv/edge/geo.js?json"
VIDEO_API_BASE = "https://www.av01.media/api/v1/videos"


class AV01Extractor(ExtractorPlugin):
    """
    AV01提取器
    继承自ExtractorPlugin，提供从 av01.tv 提取视频下载链接的功能。

    该网站使用基于geo API的token认证系统来获取视频资源。
    """

    def __init__(self):
        """初始化AV01提取器"""
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

    def _build_cover_url(self, video_id: str, geo_data: GeoData) -> Optional[str]:
        """
        构建封面图片URL

        Args:
            video_id: 视频ID
            geo_data: geo认证数据

        Returns:
            封面图片URL
        """
        try:
            token = geo_data.token
            expires = geo_data.expires
            ip = geo_data.ip

            if not all([token, expires, ip]):
                return None

            # AV01封面格式: https://static.av01.tv/media/videos/tmb/{video_id}/1.jpg/format=webp/wlv=800?t={token}&e={expires}&ip={ip}
            cover_url = (
                f"https://static.av01.tv/media/videos/tmb/{video_id}/1.jpg/format=webp/wlv=800?t={token}&e={expires}&ip={ip}"
            )

            self.logger.debug(f"构建封面URL: {cover_url[:100]}...")
            return cover_url
        except Exception as e:
            self.logger.error(f"构建封面URL失败: {e}")
            return None

    def _build_download_items(
        self,
        video_metadata: AV01VideoMetadata,
        video_urls: Dict[str, str],
        original_url: str,
        geo_data: GeoData,
        video_id: str,
    ) -> List[OperationItem]:
        """
        根据视频元数据和URL列表构建下载选项

        Args:
            video_metadata: AV01VideoMetadata 实例
            video_urls: 视频URL字典（质量 -> URL）
            original_url: 原始页面URL
            geo_data: geo认证数据
            video_id: 视频ID

        Returns:
            下载选项列表
        """
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

            # 创建封面项
            cover_item: Optional[OperationItem] = None
            landscape_item: Optional[OperationItem] = None
            if cover_image:
                cover_item = create_cover_item(url=cover_image, title=title)
                landscape_item = create_landscape_item(url=cover_image, title=title)

            # 创建元数据对象
            identifier = StringUtils.create_identifier(site=SITE_NAME, code=video_code, url=original_url)
            metadata = MovieMetadata(
                title=video_code + " " + title,
                identifier=identifier,
                site=SITE_NAME,
                url=original_url,
                code=video_code,
                actors=actors,
                runtime=runtime_minutes,
                premiered=release_date,  # 使用premiered而不是release_date
                genres=genres,
                tags=tags,
                studio=studio,
                director=director,
                cover=cover_image,
                plot=description,  # 使用plot而不是description
                year=release_year,
            )

            metadata_item = create_metadata_item(
                title=title,
                meta_data=metadata,
            )

            # 构建下载选项
            download_items: List[OperationItem] = []
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
                download_item = create_stream_item(
                    site=SITE_NAME,
                    url=video_url,
                    title=title,
                    code=video_code,
                    quality=quality,
                    actors=actors,
                    studio=studio,
                    year=release_year,
                )

                # 添加子项
                if cover_item:
                    download_item.append_child(cover_item)
                if landscape_item:
                    download_item.append_child(landscape_item)
                download_item.append_child(metadata_item)

                download_items.append(download_item)

            return download_items

        except Exception as e:
            self.logger.error(f"构建下载选项失败: {e}")
            return []

    def _get_geo_data(self, force_refresh: bool = False) -> Optional[GeoData]:
        """
        获取geo数据（包含token）

        Args:
            force_refresh: 是否强制刷新

        Returns:
            GeoData 实例或 None
        """
        # 检查缓存
        if not force_refresh and self._geo_data and self._geo_fetched_at:
            import time

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
                import time

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
        """
        从API获取视频元数据

        Args:
            metadata_url: 元数据API URL

        Returns:
            AV01VideoMetadata 实例或 None
        """
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
        """
        从API获取视频播放列表

        Args:
            playlist_url: 播放列表API URL（包含token、expires、ip参数）

        Returns:
            包含不同质量视频URL的字典
        """
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

    def _parse_playlist_json(self, data: Dict) -> Dict[str, str]:
        """
        解析JSON格式的播放列表响应

        Args:
            data: API返回的JSON数据

        Returns:
            质量 -> URL 的字典
        """
        result = {}

        try:
            # AV01 API返回的是 {src: "data:application/x-mpegurl;charset=utf-8;base64,..."} 格式
            if "src" in data and isinstance(data["src"], str):
                src = data["src"]

                # 检查是否是base64编码的m3u8
                if "base64," in src:
                    import base64

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
            if "data" in data and isinstance(data["data"], dict):
                playlist = data["data"]
            # 情况2: {playlist: {quality: url}}
            elif "playlist" in data:
                playlist = data["playlist"]
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
        """
        解析m3u8格式的播放列表

        Args:
            m3u8_content: m3u8文件内容
            base_url: 基础URL用于构建完整URL（如果为空字符串则表示URL已经完整）

        Returns:
            质量 -> URL 的字典
        """
        result = {}

        try:
            lines = m3u8_content.splitlines()

            current_quality = None
            for i, line in enumerate(lines):
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
        """
        从URL提取视频ID

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

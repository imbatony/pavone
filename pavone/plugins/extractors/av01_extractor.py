"""
AV01视频提取器插件

支持从 av01.tv 网站提取视频下载链接。

该提取器完全基于API，不需要解析HTML：
1. 从 geo API 获取 token
2. 从 /api/v1/videos/{id} 获取视频元数据
3. 从 /api/v1/videos/{id}/playlist 获取播放列表
"""

import re
import json
from typing import List, Dict, Optional, Tuple
from urllib.parse import urlparse
from datetime import datetime

from ...models import OperationItem, Quality, create_stream_item, create_cover_item, create_metadata_item
from ...models import MovieMetadata
from .base import ExtractorPlugin
from ...utils import StringUtils, CodeExtractUtils

# 定义插件名称和版本
PLUGIN_NAME = "AV01Extractor"
PLUGIN_VERSION = "1.0.0"
PLUGIN_DESCRIPTION = "提取 av01.tv 的视频下载链接（基于API）"
PLUGIN_AUTHOR = "PAVOne"

# 定义插件优先级
PLUGIN_PRIORITY = 30

# 定义支持的域名
SUPPORTED_DOMAINS = ["av01.tv", "www.av01.tv"]

SITE_NAME = "AV01"

# API端点
GEO_API_URL = "https://www.av01.tv/edge/geo.js?json"
VIDEO_API_BASE = "https://www.av01.tv/api/v1/videos"


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
        self._geo_data: Optional[Dict] = None
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
            if not geo_data or "token" not in geo_data:
                self.logger.error("无法获取geo token")
                return []

            token = geo_data["token"]
            expires = geo_data["expires"]
            ip = geo_data["ip"]

            self.logger.info(f"获取到token: {token[:10]}... IP: {ip}")

            # 3. 获取视频元数据
            metadata_api_url = f"{VIDEO_API_BASE}/{video_id}"
            video_metadata = self._get_video_metadata(metadata_api_url)

            if not video_metadata:
                self.logger.error(f"无法获取视频元数据: {video_id}")
                return []

            self.logger.info(f"获取到视频元数据: {video_metadata.get('title', 'Unknown')}")

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

    def _build_cover_url(self, video_id: str, geo_data: Dict) -> Optional[str]:
        """
        构建封面图片URL

        Args:
            video_id: 视频ID
            geo_data: geo认证数据

        Returns:
            封面图片URL
        """
        try:
            token = geo_data.get("token", "")
            expires = geo_data.get("expires", "")
            ip = geo_data.get("ip", "")

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
        self, video_metadata: Dict, video_urls: Dict[str, str], original_url: str, geo_data: Dict, video_id: str
    ) -> List[OperationItem]:
        """
        根据视频元数据和URL列表构建下载选项

        Args:
            video_metadata: 视频元数据字典
            video_urls: 视频URL字典（质量 -> URL）
            original_url: 原始页面URL
            geo_data: geo认证数据
            video_id: 视频ID

        Returns:
            下载选项列表
        """
        try:
            # 提取基本信息
            title = video_metadata.get("title", "Unknown Video")

            # 提取番号 - AV01使用 dvd_id 作为番号
            video_code: str = video_metadata.get("dvd_id", "") or video_metadata.get("number", "") or video_metadata.get("code", "")

            # 如果没有code，尝试从title提取
            if not video_code:
                video_code = CodeExtractUtils.extract_code_from_text(title) or "Unknown"
            else:
                # 需要对番号进行额外处理
                video_code = CodeExtractUtils.extract_code_from_text(video_code) or video_code

            # 提取演员 - AV01使用 actresses 字段
            actors = []
            if "actresses" in video_metadata and isinstance(video_metadata["actresses"], list):
                actors = [actress.get("name", "") for actress in video_metadata["actresses"] if actress.get("name")]
            elif "actors" in video_metadata and isinstance(video_metadata["actors"], list):
                actors = [actor.get("name", "") for actor in video_metadata["actors"] if actor.get("name")]

            # 提取其他信息
            duration_seconds = video_metadata.get("duration")  # 秒
            runtime_minutes = None
            if duration_seconds and isinstance(duration_seconds, (int, float)):
                runtime_minutes = int(duration_seconds // 60)  # 转换为分钟

            # 提取发布时间 - AV01使用 published_time 而非 published_at
            release_date = video_metadata.get("published_time", "") or video_metadata.get("published_at", "")

            # 提取制作商 - AV01使用 maker 字段
            studio = None
            if "maker" in video_metadata:
                if isinstance(video_metadata["maker"], dict):
                    studio = video_metadata["maker"].get("name")
                elif isinstance(video_metadata["maker"], str):
                    studio = video_metadata["maker"]

            # 如果没有maker，尝试studio字段
            if not studio and "studio" in video_metadata:
                if isinstance(video_metadata["studio"], dict):
                    studio = video_metadata["studio"].get("name")
                elif isinstance(video_metadata["studio"], str):
                    studio = video_metadata["studio"]

            # 提取分类/标签 - AV01主要使用 tags，genres较少
            genres = []
            if "genres" in video_metadata and isinstance(video_metadata["genres"], list):
                for g in video_metadata["genres"]:
                    if isinstance(g, dict):
                        name = g.get("name", "")
                        if name:
                            genres.append(name)
                    elif isinstance(g, str):
                        genres.append(g)

            tags = []
            if "tags" in video_metadata and isinstance(video_metadata["tags"], list):
                for t in video_metadata["tags"]:
                    if isinstance(t, dict):
                        name = t.get("name", "")
                        if name:
                            tags.append(name)
                    elif isinstance(t, str):
                        tags.append(t)

            # 封面图片 - 使用带认证的URL构建
            cover_image = None
            if "poster" in video_metadata and isinstance(video_metadata["poster"], str):
                cover_image = video_metadata["poster"]
            elif "cover" in video_metadata and video_metadata["cover"] is True:
                # 使用geo认证构建封面URL
                cover_image = self._build_cover_url(video_id, geo_data)
            elif "cover" in video_metadata and isinstance(video_metadata["cover"], str):
                cover_image = video_metadata["cover"]

            # 描述
            description = video_metadata.get("description", "")

            # 导演
            director = None
            if "director" in video_metadata:
                if isinstance(video_metadata["director"], dict):
                    director = video_metadata["director"].get("name")
                elif isinstance(video_metadata["director"], str) and video_metadata["director"]:
                    director = video_metadata["director"]

            # 发布年份
            release_year = datetime.now().year
            if release_date:
                try:
                    # 处理 ISO 8601 格式 (2025-11-17T00:00:00Z)
                    if "T" in release_date:
                        release_year = int(release_date.split("T")[0].split("-")[0])
                    else:
                        release_year = int(release_date.split("-")[0])
                except:
                    pass

            # 创建封面项
            cover_item: Optional[OperationItem] = None
            if cover_image:
                cover_item = create_cover_item(url=cover_image, title=title)

            # 创建元数据对象
            identifier = StringUtils.create_identifier(site=SITE_NAME, code=video_code, url=original_url)
            metadata = MovieMetadata(
                title= video_code + " " + title,
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
                    if quality_key in [Quality.UHD, Quality.QHD, Quality.FHD, Quality.HD, Quality.SD, Quality.LOW]
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
                download_item.append_child(metadata_item)

                download_items.append(download_item)

            return download_items

        except Exception as e:
            self.logger.error(f"构建下载选项失败: {e}")
            return []

    def _get_geo_data(self, force_refresh: bool = False) -> Optional[Dict]:
        """
        获取geo数据（包含token）

        Args:
            force_refresh: 是否强制刷新

        Returns:
            包含token、ip、expires等信息的字典
        """
        # 检查缓存
        if not force_refresh and self._geo_data and self._geo_fetched_at:
            import time

            ttl = self._geo_data.get("ttl", 1800)
            elapsed = time.time() - self._geo_fetched_at

            if elapsed < ttl:
                self.logger.debug(f"使用缓存的geo数据（剩余{int(ttl - elapsed)}秒）")
                return self._geo_data

        # 从API获取
        try:
            self.logger.info("正在从API获取geo数据...")
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                "Accept": "application/json, */*",
                "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8,ja;q=0.7",
                "Referer": "https://www.av01.tv/",
            }

            response = self.fetch(GEO_API_URL, headers=headers, timeout=10, verify_ssl=True)

            if response.status_code == 200:
                import time

                self._geo_data = response.json()
                self._geo_fetched_at = time.time()
                token_preview = self._geo_data.get("token", "")[:10] if self._geo_data else ""
                self.logger.info(f"成功获取geo数据，token: {token_preview}...")
                return self._geo_data
            else:
                self.logger.error(f"获取geo数据失败，状态码: {response.status_code}")
                return None

        except Exception as e:
            self.logger.error(f"获取geo数据异常: {e}")
            return None

    def _get_video_metadata(self, metadata_url: str) -> Optional[Dict]:
        """
        从API获取视频元数据

        Args:
            metadata_url: 元数据API URL

        Returns:
            视频元数据字典
        """
        try:
            self.logger.info(f"正在获取视频元数据: {metadata_url}")
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                "Accept": "application/json, */*",
                "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8,ja;q=0.7",
                "Referer": "https://www.av01.tv/",
            }

            response = self.fetch(metadata_url, headers=headers, timeout=30, verify_ssl=True)

            if response.status_code != 200:
                self.logger.error(f"获取视频元数据失败，状态码: {response.status_code}")
                return None

            metadata = response.json()
            self.logger.debug(f"视频元数据: {json.dumps(metadata, ensure_ascii=False)[:200]}...")
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
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                "Accept": "application/json, */*",
                "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8,ja;q=0.7",
                "Referer": "https://www.av01.tv/",
            }

            response = self.fetch(playlist_url, headers=headers, timeout=30, verify_ssl=True)

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
        - https://www.av01.tv/jp/video/184522/fc2-ppv-4799119
        - https://av01.tv/en/video/123456/some-title

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

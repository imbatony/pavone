"""
Jellyfin API 客户端包装器

基于 jellyfin-apiclient-python 库，提供简化的 API 接口和错误处理。
"""

import logging
from typing import Any, Dict, List, Optional

from jellyfin_apiclient_python import JellyfinClient

from ..config.configs import JellyfinConfig
from .exceptions import (
    JellyfinAPIError,
    JellyfinAuthenticationError,
    JellyfinConnectionError,
)
from .models import JellyfinItem, LibraryInfo


class JellyfinClientWrapper:
    """
    Jellyfin API 客户端包装器

    对 jellyfin-apiclient-python 的轻量包装，提供：
    - 简化的认证流程
    - 错误处理和日志记录
    - 常用 API 方法的封装
    """

    def __init__(self, config: JellyfinConfig):
        """
        初始化 Jellyfin 客户端

        Args:
            config: Jellyfin 配置对象

        Raises:
            ValueError: 配置无效时
        """
        self.config = config
        self.logger = logging.getLogger(__name__)

        if not config.server_url:
            raise ValueError("Jellyfin server_url 不能为空")

        self.client = JellyfinClient()
        self._setup_client_config()
        self._authenticated = False
        self.user_id: Optional[str] = None

    def _setup_client_config(self) -> None:
        """配置 Jellyfin 客户端基本信息"""
        # 需要设置设备信息才能获取有效的用户令牌
        self.client.config.app("PAVOne", "0.2.0", "pavone-client", "pavone-unique-id-client")
        self.client.config.http(user_agent="PAVOne/0.2.0")

        # 设置 SSL 验证
        self.client.config.data["auth.ssl"] = "https" in self.config.server_url
        if not self.config.verify_ssl:
            # 禁用 SSL 验证警告
            import urllib3

            urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

    def authenticate(self) -> bool:
        """
        认证到 Jellyfin 服务器

        支持两种认证方式：
        1. API Key 认证（优先使用）
        2. 用户名/密码认证

        Returns:
            认证成功返回 True

        Raises:
            JellyfinAuthenticationError: 认证失败
            JellyfinConnectionError: 连接失败
        """
        try:
            self.logger.info(f"正在连接 Jellyfin 服务器: {self.config.server_url}")

            if self.config.api_key:
                # 使用 API Key 认证
                self._authenticate_with_api_key()
            elif self.config.username and self.config.password:
                # 使用用户名密码认证
                self._authenticate_with_credentials()
            else:
                raise JellyfinAuthenticationError("未提供有效的认证信息（API Key 或用户名密码）")

            self._authenticated = True
            self.logger.info("✓ Jellyfin 认证成功")
            return True

        except JellyfinAuthenticationError:
            raise
        except Exception as e:
            self.logger.error(f"Jellyfin 连接错误: {e}")
            raise JellyfinConnectionError(f"无法连接到 Jellyfin 服务器: {e}")

    def _authenticate_with_api_key(self) -> None:
        """使用 API Key 进行认证"""
        try:
            self.client.authenticate(
                {
                    "Servers": [
                        {
                            "AccessToken": self.config.api_key,
                            "address": self.config.server_url,
                        }
                    ]
                },
                discover=False,
            )

            # 从认证结果中获取用户 ID
            try:
                # 尝试从 ConnectionManager 的凭证中获取用户 ID
                creds = self.client.get_credentials()
                if creds and "Servers" in creds and len(creds["Servers"]) > 0:
                    server_creds = creds["Servers"][0]
                    if "UserId" in server_creds:
                        self.user_id = server_creds["UserId"]
                        self.client.config.data["auth.user_id"] = self.user_id
                        self.logger.debug(f"从认证结果获取用户 ID: {self.user_id}")

                # 如果仍未获得用户 ID，调用 API 获取当前用户信息
                if not self.user_id:
                    users = self.client.jellyfin.get_users()
                    if isinstance(users, list) and len(users) > 0:
                        self.user_id = users[0].get("Id")
                        self.client.config.data["auth.user_id"] = self.user_id
                        self.logger.debug(f"从 API 获取用户 ID: {self.user_id}")

            except Exception as e:
                self.logger.warning(f"无法获取用户 ID: {e}")

            self.logger.debug("使用 API Key 认证成功")
        except Exception as e:
            raise JellyfinAuthenticationError(f"API Key 认证失败: {e}")

    def _authenticate_with_credentials(self) -> None:
        """使用用户名密码进行认证"""
        try:
            # 连接到服务器地址
            self.client.auth.connect_to_address(self.config.server_url)

            # 使用用户名密码登录
            self.client.auth.login(self.config.server_url, self.config.username, self.config.password)

            # 获取用户 ID 用于后续 API 调用
            try:
                creds = self.client.get_credentials()
                if creds and "Servers" in creds and len(creds["Servers"]) > 0:
                    server_creds = creds["Servers"][0]
                    if "UserId" in server_creds:
                        self.user_id = server_creds["UserId"]
                        self.client.config.data["auth.user_id"] = self.user_id
                        self.logger.debug(f"从认证结果获取用户 ID: {self.user_id}")
            except Exception as e:
                self.logger.warning(f"无法从认证结果获取用户 ID: {e}")

            self.logger.debug(f"用户 {self.config.username} 认证成功")
        except Exception as e:
            raise JellyfinAuthenticationError(f"用户名密码认证失败: {e}")

    def is_authenticated(self) -> bool:
        """
        检查是否已认证

        Returns:
            已认证返回 True
        """
        return self._authenticated

    def get_server_info(self) -> Dict[str, Any]:
        """
        获取服务器信息

        Returns:
            服务器信息字典

        Raises:
            JellyfinAPIError: API 调用失败
        """
        try:
            info = self.client.jellyfin.get_system_info()
            self.logger.debug(f"获取到服务器信息: {info.get('ServerName', 'Unknown')}")
            return info
        except Exception as e:
            self.logger.error(f"获取服务器信息失败: {e}")
            raise JellyfinAPIError(f"获取服务器信息失败: {e}")

    def get_libraries(self) -> List[LibraryInfo]:
        """
        获取所有库列表

        Returns:
            LibraryInfo 对象列表

        Raises:
            JellyfinAPIError: API 调用失败
        """
        try:
            # 使用 media_folders() 直接获取库列表（不需要 UserId）
            result = self.client.jellyfin.media_folders()
            libraries = []

            for item in result.get("Items", []):
                lib_id = item.get("Id", "")
                lib_name = item.get("Name", "")
                lib_type = item.get("CollectionType", "")

                # 排除 playlists 类型的库（内建库）
                if lib_type == "playlists":
                    self.logger.debug(f"跳过内建库: {lib_name}")
                    continue

                # 获取库中的项目数
                item_count = self._get_library_item_count(lib_id)

                lib_info = LibraryInfo(
                    name=lib_name,
                    id=lib_id,
                    type=lib_type,
                    item_count=item_count,
                )
                libraries.append(lib_info)

            self.logger.info(f"获取到 {len(libraries)} 个库")
            return libraries

        except Exception as e:
            self.logger.error(f"获取库列表失败: {e}")
            raise JellyfinAPIError(f"获取库列表失败: {e}")

    def get_library_physical_locations(self) -> Dict[str, List[str]]:
        """
        获取所有库的物理文件夹位置

        Returns:
            {库名: 物理路径列表} 的字典

        Raises:
            JellyfinAPIError: API 调用失败
        """
        try:
            locations = {}

            # 方法 1: 尝试使用 virtual_folders API
            try:
                virtual_folders_result = self.client.jellyfin.virtual_folders()
                if virtual_folders_result and isinstance(virtual_folders_result, list):
                    for vf in virtual_folders_result:
                        lib_name = vf.get("Name", "")
                        locations_list = vf.get("Locations", [])
                        if lib_name and locations_list:
                            locations[lib_name] = locations_list
                            self.logger.debug(f"从 virtual_folders 获取 {lib_name}: {locations_list}")
            except Exception as e:
                self.logger.debug(f"virtual_folders API 失败: {e}")

            # 如果 virtual_folders 成功返回了结果，则直接返回
            if locations:
                return locations

            # 方法 2: 尝试从 media_folders 获取 PhysicalLocations 或 CollectionFolders
            result = self.client.jellyfin.media_folders()
            for item in result.get("Items", []):
                lib_name = item.get("Name", "")
                lib_type = item.get("CollectionType", "")

                # 排除 playlists 类型的库（内建库）
                if lib_type == "playlists":
                    continue

                # 尝试获取物理位置
                paths = item.get("PhysicalLocations", [])
                if paths:
                    locations[lib_name] = paths
                    self.logger.debug(f"从 media_folders PhysicalLocations 获取 {lib_name}: {paths}")
                    continue

                # 尝试从 CollectionFolders 获取
                collection_folders = item.get("CollectionFolders", [])
                if collection_folders:
                    folder_paths = [f.get("Path", "") for f in collection_folders if f.get("Path")]
                    if folder_paths:
                        locations[lib_name] = folder_paths
                        self.logger.debug(f"从 media_folders CollectionFolders 获取 {lib_name}: {folder_paths}")
                        continue

                # 尝试从 Folders 获取
                folders = item.get("Folders", [])
                if folders:
                    folder_paths = [f.get("Path", "") for f in folders if f.get("Path")]
                    if folder_paths:
                        locations[lib_name] = folder_paths
                        self.logger.debug(f"从 media_folders Folders 获取 {lib_name}: {folder_paths}")

            self.logger.debug(f"获取到库物理位置: {locations}")
            return locations

        except Exception as e:
            self.logger.error(f"获取库物理位置失败: {e}")
            raise JellyfinAPIError(f"获取库物理位置失败: {e}")

    def _get_library_item_count(self, library_id: str) -> int:
        """
        获取库中的项目数

        Args:
            library_id: 库 ID

        Returns:
            项目数
        """
        try:
            # 查询库中的项目总数
            result = self.client.jellyfin.user_items(
                handler="",
                params={
                    "ParentId": library_id,
                    "Recursive": True,
                },
            )
            count = result.get("TotalRecordCount", 0)
            self.logger.debug(f"库 {library_id} 包含 {count} 个项目")
            return count
        except Exception as e:
            self.logger.warning(f"获取库 {library_id} 的项目数失败: {e}")
            return 0

    def get_library_items(
        self,
        library_ids: Optional[List[str]] = None,
        limit: int = 100,
        start_index: int = 0,
    ) -> List[JellyfinItem]:
        """
        获取库中的所有项

        Args:
            library_ids: 库 ID 列表，如果为 None 则获取所有库
            limit: 单次查询的项数限制
            start_index: 起始索引（用于分页）

        Returns:
            JellyfinItem 对象列表

        Raises:
            JellyfinAPIError: API 调用失败
        """
        try:
            items = []

            # 如果未指定库，获取所有库
            if not library_ids:
                libraries = self.get_libraries()
                library_ids = [lib.id for lib in libraries if lib.type == "movies"]

            for lib_id in library_ids:
                try:
                    # 使用 user_items 方法获取库中的项
                    result = self.client.jellyfin.user_items(
                        handler="",
                        params={
                            "ParentId": lib_id,
                            "Filters": "IsNotFolder",
                            "IncludeItemTypes": "Movie,Video",
                            "Limit": limit,
                            "StartIndex": start_index,
                            "Recursive": True,
                        },
                    )

                    for item_data in result.get("Items", []):
                        item = self._parse_item(item_data)
                        items.append(item)

                    self.logger.debug(f"从库 {lib_id} 获取了 {len(result.get('Items', []))} 个项")

                except Exception as e:
                    self.logger.warning(f"获取库 {lib_id} 的项失败: {e}")
                    continue

            self.logger.info(f"共获取了 {len(items)} 个库项")
            return items

        except Exception as e:
            self.logger.error(f"获取库项失败: {e}")
            raise JellyfinAPIError(f"获取库项失败: {e}")

    def search_items(self, keyword: str, limit: int = 20, media_type: str = "Videos") -> List[JellyfinItem]:
        """
        搜索视频项

        Args:
            keyword: 搜索关键词
            limit: 结果数量限制
            media_type: 媒体类型（默认 "Videos"）

        Returns:
            JellyfinItem 对象列表

        Raises:
            JellyfinAPIError: API 调用失败
        """
        try:
            self.logger.info(f"搜索: '{keyword}' (限制: {limit})")

            # 临时设置用户 ID 来进行搜索（某些 API 需要它）
            old_user_id = None
            if self.user_id:
                old_user_id = self.client.config.data.get("auth.user_id")
                self.client.config.data["auth.user_id"] = self.user_id

            result = self.client.jellyfin.search_media_items(term=keyword, media=media_type, limit=limit)

            if self.user_id:
                self.client.config.data["auth.user_id"] = old_user_id

            items = []
            for item_data in result.get("Items", []):
                item = self._parse_item(item_data)
                items.append(item)

            self.logger.info(f"搜索到 {len(items)} 个结果")
            return items

        except Exception as e:
            self.logger.error(f"搜索失败: {e}")
            raise JellyfinAPIError(f"搜索失败: {e}")

    def get_item(self, item_id: str) -> JellyfinItem:
        """
        获取单个项的详细信息

        Args:
            item_id: 项 ID

        Returns:
            JellyfinItem 对象

        Raises:
            JellyfinAPIError: API 调用失败
        """
        try:
            item_data = self.client.jellyfin.get_item(item_id)
            item = self._parse_item(item_data)
            self.logger.debug(f"获取项信息: {item.name}")
            return item

        except Exception as e:
            self.logger.error(f"获取项 {item_id} 失败: {e}")
            raise JellyfinAPIError(f"获取项失败: {e}")

    def update_item_metadata(self, item_id: str, metadata: Dict[str, Any]) -> bool:
        """
        更新项的元数据

        Args:
            item_id: 项 ID
            metadata: 要更新的元数据字典

        Returns:
            成功返回 True

        Raises:
            JellyfinAPIError: API 调用失败
        """
        try:
            self.client.jellyfin.update_item(item_id, metadata)
            self.logger.info(f"更新项 {item_id} 的元数据成功")
            return True

        except Exception as e:
            self.logger.error(f"更新项 {item_id} 的元数据失败: {e}")
            raise JellyfinAPIError(f"更新元数据失败: {e}")

    def mark_item_played(self, item_id: str, user_id: Optional[str] = None) -> bool:
        """
        标记项为已观看

        Args:
            item_id: 项 ID
            user_id: 用户 ID（可选）

        Returns:
            成功返回 True

        Raises:
            JellyfinAPIError: API 调用失败
        """
        try:
            # 如果提供了 user_id，临时切换
            old_user_id = None
            target_user_id = user_id or self.user_id

            if target_user_id:
                old_user_id = self.client.config.data.get("auth.user_id")
                self.client.config.data["auth.user_id"] = target_user_id

            self.client.jellyfin.item_played(item_id, watched=True)

            if target_user_id:
                self.client.config.data["auth.user_id"] = old_user_id

            self.logger.debug(f"标记项 {item_id} 为已观看")
            return True

        except Exception as e:
            self.logger.error(f"标记项 {item_id} 为已观看失败: {e}")
            raise JellyfinAPIError(f"标记为已观看失败: {e}")

    def refresh_library(self, library_id: Optional[str] = None) -> bool:
        """
        增量刷新库元数据

        扫描库目录中的新增和修改文件，仅更新新项和修改项的元数据

        Args:
            library_id: 库 ID（如果为 None 则刷新所有库）

        Returns:
            成功返回 True

        Raises:
            JellyfinAPIError: API 调用失败
        """
        try:
            if library_id:
                # 增量刷新特定库
                # 使用 jellyfin 库的 _post 方法调用 API，传递增量刷新参数
                self.client.jellyfin._post(
                    f"Items/{library_id}/Refresh",
                    params={
                        "Recursive": True,
                        "ImageRefreshMode": "Default",
                        "MetadataRefreshMode": "Default",
                        "ReplaceAllImages": False,
                        "RegenerateTrickplay": False,
                        "ReplaceAllMetadata": False,  # 关键：不替换所有元数据，进行增量更新
                    },
                )
                self.logger.info(f"增量刷新库 {library_id} 成功")
            else:
                # 增量刷新所有库
                libraries = self.get_libraries()
                for lib in libraries:
                    self.client.jellyfin._post(
                        f"Items/{lib.id}/Refresh",
                        params={
                            "Recursive": True,
                            "ImageRefreshMode": "Default",
                            "MetadataRefreshMode": "Default",
                            "ReplaceAllImages": False,
                            "RegenerateTrickplay": False,
                            "ReplaceAllMetadata": False,
                        },
                    )

                self.logger.info("增量刷新所有库完成")

            return True

        except Exception as e:
            self.logger.error(f"刷新库失败: {e}")
            raise JellyfinAPIError(f"刷新库失败: {e}")

    def _parse_item(self, item_data: Dict[str, Any]) -> JellyfinItem:
        """
        解析 API 返回的项数据

        Args:
            item_data: API 返回的项数据字典

        Returns:
            JellyfinItem 对象
        """
        return JellyfinItem(
            id=item_data.get("Id", ""),
            name=item_data.get("Name", ""),
            type=item_data.get("Type", ""),
            container=item_data.get("Container"),
            path=item_data.get("Path"),
            metadata=item_data,
        )

    def upload_image(self, item_id: str, image_path: str, image_type: str = "Primary") -> bool:
        """
        上传图片到 Jellyfin 项目

        Args:
            item_id: 项目 ID
            image_path: 本地图片文件路径
            image_type: 图片类型 (Primary, Backdrop, Thumb 等)

        Returns:
            上传成功返回 True

        Raises:
            JellyfinAPIError: API 调用失败
        """
        try:
            from pathlib import Path

            import requests
            from PIL import Image

            image_file = Path(image_path)
            if not image_file.exists():
                raise FileNotFoundError(f"图片文件不存在: {image_path}")

            # 如果是 webp 格式，转换为 jpeg
            suffix = image_file.suffix.lower()
            if suffix == ".webp":
                self.logger.debug(f"检测到 webp 格式，转换为 jpeg: {image_path}")
                img = Image.open(image_file)
                # 转换为 RGB 模式（webp 可能是 RGBA）
                if img.mode in ("RGBA", "LA", "P"):
                    background = Image.new("RGB", img.size, (255, 255, 255))
                    if img.mode == "P":
                        img = img.convert("RGBA")
                    background.paste(img, mask=img.split()[-1] if img.mode == "RGBA" else None)
                    img = background
                elif img.mode != "RGB":
                    img = img.convert("RGB")
                
                # 保存为临时 jpeg 文件
                temp_path = image_file.with_suffix(".jpg")
                img.save(temp_path, "JPEG", quality=95)
                image_file = temp_path
                content_type = "image/jpeg"
            else:
                # 确定 MIME 类型
                mime_types = {
                    ".jpg": "image/jpeg",
                    ".jpeg": "image/jpeg",
                    ".png": "image/png",
                    ".gif": "image/gif",
                }
                content_type = mime_types.get(suffix, "image/jpeg")

            # 读取图片文件
            with open(image_file, "rb") as f:
                image_data = f.read()

            # 获取访问令牌
            access_token = self.config.api_key
            if not access_token:
                # 尝试从客户端凭证获取
                creds = self.client.get_credentials()
                if creds and "Servers" in creds and len(creds["Servers"]) > 0:
                    access_token = creds["Servers"][0].get("AccessToken")

            if not access_token:
                raise JellyfinAPIError("无法获取访问令牌")

            # 构建完整的 API URL
            base_url = self.config.server_url.rstrip("/")
            
            # Jellyfin 10.8+ 使用这个端点上传图片
            # 对于 Backdrop，可能需要索引
            if image_type == "Backdrop":
                endpoint = f"{base_url}/Items/{item_id}/Images/{image_type}/0"
            else:
                endpoint = f"{base_url}/Items/{item_id}/Images/{image_type}"
            
            # 准备请求头 - 参考实际请求案例，直接设置 Content-Type
            headers = {
                "X-Emby-Token": access_token,
                "Content-Type": content_type,
            }
            
            self.logger.debug(f"上传图片到: {endpoint}")
            self.logger.debug(f"Content-Type: {content_type}")
            self.logger.debug(f"图片大小: {len(image_data)} bytes")
            
            # 参考实际请求案例，直接 POST 二进制数据
            response = requests.post(
                endpoint,
                data=image_data,
                headers=headers,
                verify=self.config.verify_ssl,
                timeout=30,
            )

            # 检查响应
            if response.status_code >= 400:
                # 记录详细的错误信息
                self.logger.error(f"上传图片失败，状态码: {response.status_code}")
                self.logger.error(f"响应内容: {response.text}")
                self.logger.error(f"请求 URL: {endpoint}")
            
            response.raise_for_status()

            self.logger.debug(f"上传图片成功: {image_type} -> {item_id}")
            return True

        except Exception as e:
            self.logger.error(f"上传图片失败: {e}")
            raise JellyfinAPIError(f"上传图片失败: {e}")

    def delete_image(self, item_id: str, image_type: str = "Primary") -> bool:
        """
        删除 Jellyfin 项目的图片

        Args:
            item_id: 项目 ID
            image_type: 图片类型 (Primary, Backdrop, Thumb 等)

        Returns:
            删除成功返回 True

        Raises:
            JellyfinAPIError: API 调用失败
        """
        try:
            import requests

            # 构建完整的 API URL
            base_url = self.config.server_url.rstrip("/")
            endpoint = f"{base_url}/Items/{item_id}/Images/{image_type}"

            # 获取访问令牌
            access_token = self.config.api_key
            if not access_token:
                # 尝试从客户端凭证获取
                creds = self.client.get_credentials()
                if creds and "Servers" in creds and len(creds["Servers"]) > 0:
                    access_token = creds["Servers"][0].get("AccessToken")

            if not access_token:
                raise JellyfinAPIError("无法获取访问令牌")

            # 准备请求头
            headers = {
                "X-Emby-Token": access_token,
            }

            # 发送 DELETE 请求
            response = requests.delete(
                endpoint, headers=headers, verify=self.config.verify_ssl, timeout=30
            )

            # 检查响应
            response.raise_for_status()

            self.logger.debug(f"删除图片成功: {image_type} -> {item_id}")
            return True
        except Exception as e:
            self.logger.warning(f"删除图片失败（可能不存在）: {e}")
            return False

    def download_remote_image(self, item_id: str, image_url: str, image_type: str = "Primary") -> bool:
        """
        让 Jellyfin 从远程 URL 下载图片

        Args:
            item_id: 项目 ID
            image_url: 远程图片 URL
            image_type: 图片类型 (Primary, Backdrop, Thumb 等)

        Returns:
            下载成功返回 True

        Raises:
            JellyfinAPIError: API 调用失败
        """
        try:
            import requests

            # 构建完整的 API URL
            base_url = self.config.server_url.rstrip("/")
            
            # 使用 RemoteImages/Download 端点让 Jellyfin 下载图片
            endpoint = f"{base_url}/Items/{item_id}/RemoteImages/Download"

            # 获取访问令牌
            access_token = self.config.api_key
            if not access_token:
                creds = self.client.get_credentials()
                if creds and "Servers" in creds and len(creds["Servers"]) > 0:
                    access_token = creds["Servers"][0].get("AccessToken")

            if not access_token:
                raise JellyfinAPIError("无法获取访问令牌")

            # 准备请求参数
            params = {
                "Type": image_type,
                "ImageUrl": image_url,
            }

            headers = {
                "X-Emby-Token": access_token,
            }

            self.logger.debug(f"请求 Jellyfin 下载远程图片: {image_url}")
            self.logger.debug(f"目标端点: {endpoint}")

            # 发送 POST 请求
            response = requests.post(
                endpoint,
                params=params,
                headers=headers,
                verify=self.config.verify_ssl,
                timeout=30,
            )

            # 检查响应
            if response.status_code >= 400:
                self.logger.error(f"远程图片下载失败，状态码: {response.status_code}")
                self.logger.error(f"响应内容: {response.text}")
            
            response.raise_for_status()

            self.logger.debug(f"远程图片下载成功: {image_type} -> {item_id}")
            return True

        except Exception as e:
            self.logger.error(f"远程图片下载失败: {e}")
            raise JellyfinAPIError(f"远程图片下载失败: {e}")

    def __repr__(self) -> str:
        return f"JellyfinClientWrapper(server={self.config.server_url}, authenticated={self._authenticated})"


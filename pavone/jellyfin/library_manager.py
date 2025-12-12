"""
Jellyfin 库管理模块

提供库管理功能，包括扫描、匹配、文件管理等
"""

import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from .client import JellyfinClientWrapper
from .exceptions import JellyfinLibraryError
from .models import JellyfinItem, LibraryInfo


class LibraryManager:
    """Jellyfin 库管理器"""

    def __init__(self, client_wrapper: JellyfinClientWrapper):
        """
        初始化库管理器

        Args:
            client_wrapper: Jellyfin 客户端包装器
        """
        self.client = client_wrapper
        self.logger = logging.getLogger(__name__)
        self._cache: Dict[str, List[JellyfinItem]] = {}

    def initialize(self) -> bool:
        """
        初始化并验证连接

        Returns:
            成功返回 True

        Raises:
            JellyfinLibraryError: 初始化失败
        """
        try:
            if not self.client.is_authenticated():
                self.client.authenticate()

            self.logger.info("库管理器初始化成功")
            return True
        except Exception as e:
            raise JellyfinLibraryError(f"库管理器初始化失败: {e}")

    def get_monitored_libraries(self) -> List[str]:
        """
        获取要监控的库列表

        Returns:
            库名称列表
        """
        return self.client.config.libraries or []

    def scan_library(self, force_refresh: bool = False) -> Dict[str, List[JellyfinItem]]:
        """
        扫描库中的所有视频

        Args:
            force_refresh: 是否强制刷新缓存

        Returns:
            {库名: 项列表} 的字典
        """
        if not force_refresh and self._cache:
            self.logger.debug("使用缓存的库数据")
            return self._cache

        try:
            libraries = self.client.get_libraries()
            result = {}

            for lib in libraries:
                self.logger.info(f"扫描库: {lib.name}")
                items = self.client.get_library_items([lib.id])
                result[lib.name] = items

            self._cache = result
            self.logger.info(f"扫描完成，共获取 {sum(len(v) for v in result.values())} 个项")
            return result

        except Exception as e:
            raise JellyfinLibraryError(f"扫描库失败: {e}")

    def find_item_by_title(
        self, title: str, threshold: float = 0.8, library_names: Optional[List[str]] = None
    ) -> Optional[JellyfinItem]:
        """
        按标题查找项（模糊匹配）

        Args:
            title: 要查找的标题
            threshold: 匹配阈值（0-1）
            library_names: 要搜索的库名称列表

        Returns:
            匹配的 JellyfinItem 或 None
        """
        try:
            from difflib import SequenceMatcher

            libraries_to_scan = library_names or self.get_monitored_libraries()
            scanned = self.scan_library()

            best_match: Optional[Tuple[JellyfinItem, float]] = None

            for lib_name, items in scanned.items():
                if library_names and lib_name not in library_names:
                    continue

                for item in items:
                    # 计算相似度
                    ratio = SequenceMatcher(None, title.lower(), item.name.lower()).ratio()

                    if ratio >= threshold:
                        if best_match is None or ratio > best_match[1]:
                            best_match = (item, ratio)

            if best_match:
                self.logger.info(
                    f"找到匹配项: {best_match[0].name} (相似度: {best_match[1]:.2%})"
                )
                return best_match[0]

            self.logger.debug(f"未找到与 '{title}' 相匹配的项")
            return None

        except Exception as e:
            self.logger.error(f"按标题查找项失败: {e}")
            raise JellyfinLibraryError(f"查找项失败: {e}")

    def find_item_by_code(self, code: str) -> Optional[JellyfinItem]:
        """
        按视频番号查找项

        尝试在项的名称或元数据中查找视频番号

        Args:
            code: 视频番号（如 "FC2-3751072"）

        Returns:
            匹配的 JellyfinItem 或 None
        """
        try:
            items = self.client.search_items(code, limit=20)

            if items:
                self.logger.info(f"按番号搜索到 {len(items)} 个结果")
                # 返回第一个搜索结果（通常是最相关的）
                return items[0]

            self.logger.debug(f"未找到番号 '{code}' 的项")
            return None

        except Exception as e:
            self.logger.error(f"按番号查找项失败: {e}")
            raise JellyfinLibraryError(f"查找项失败: {e}")

    def get_library_folders(self) -> Dict[str, List[str]]:
        """
        获取所有库及其对应的本地文件夹

        Returns:
            {库名: 文件夹路径列表} 的字典
        """
        try:
            # 首先尝试从 API 直接获取物理位置
            locations = self.client.get_library_physical_locations()
            
            if locations:
                self.logger.info(f"从 API 获取到 {len(locations)} 个库的物理位置")
                return locations
            
            # 如果 API 返回为空，则回退到从库项获取路径
            self.logger.info("API 返回的物理位置为空，尝试从库项获取路径")
            libraries = self.client.get_libraries()
            result = {}

            for lib in libraries:
                folders = []

                # 尝试从库项中获取路径
                # 获取多个项目来增加找到路径的可能性
                items = self.client.get_library_items([lib.id], limit=10)
                
                if items:
                    # 从所有项中收集唯一的父路径
                    parent_paths = set()
                    for item in items:
                        if item.path:
                            parent_path = str(Path(item.path).parent)
                            parent_paths.add(parent_path)
                    
                    if parent_paths:
                        folders = list(parent_paths)
                        self.logger.debug(f"从库项获取 {lib.name} 的路径: {folders}")

                if folders:
                    result[lib.name] = folders
                else:
                    result[lib.name] = []

            return result

        except Exception as e:
            self.logger.error(f"获取库文件夹失败: {e}")
            raise JellyfinLibraryError(f"获取库文件夹失败: {e}")

    def refresh_library_metadata(self, library_id: str) -> bool:
        """
        刷新库的元数据

        Args:
            library_id: 库 ID

        Returns:
            成功返回 True
        """
        try:
            self.client.refresh_library(library_id)
            self.logger.info(f"刷新库 {library_id} 的元数据成功")
            # 清除缓存
            self._cache.clear()
            return True
        except Exception as e:
            self.logger.error(f"刷新库元数据失败: {e}")
            raise JellyfinLibraryError(f"刷新库元数据失败: {e}")

    def clear_cache(self) -> None:
        """清除缓存"""
        self._cache.clear()
        self.logger.debug("已清除库缓存")

    def __repr__(self) -> str:
        return f"LibraryManager(server={self.client.config.server_url})"

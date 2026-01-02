"""元数据管理器

负责元数据的获取、处理、缓存等业务逻辑。
将原有散落在 CLI 命令中的元数据处理逻辑统一管理。
"""

from typing import TYPE_CHECKING, Callable, Dict, List, Optional, cast

from ..config.logging_config import get_logger
from ..models import MovieMetadata, SearchResult

if TYPE_CHECKING:
    from ..plugins.metadata.base import MetadataPlugin

from .plugin_manager import PluginManager, get_plugin_manager


class MetadataManager:
    """元数据管理器

    负责元数据的获取、处理、缓存等业务逻辑。
    将原有散落在 CLI 命令中的元数据处理逻辑统一管理。

    主要功能:
    1. 元数据获取 - 支持 URL、代码等多种标识符
    2. 缓存机制 - 避免重复请求，提高性能
    3. 批量处理 - 支持批量获取元数据
    4. 搜索结果转换 - 从 SearchResult 获取完整元数据
    """

    def __init__(self, plugin_manager: Optional["PluginManager"] = None):
        """初始化元数据管理器

        Args:
            plugin_manager: 插件管理器实例。如果为 None，将使用全局实例
        """
        if plugin_manager is None:
            plugin_manager = get_plugin_manager()

        self.plugin_manager = plugin_manager
        self.logger = get_logger(__name__)
        self._cache: Dict[str, MovieMetadata] = {}

    def get_metadata(self, identifier: str) -> Optional[MovieMetadata]:
        """获取元数据（从 CLI metadata.py 迁移）

        支持多种标识符类型:
        - URL: https://missav.ai/ja/xxxxx-xxx
        - 视频代码: XXXXX-XXX

        Args:
            identifier: 标识符（URL 或代码）

        Returns:
            元数据对象，失败返回 None
        """
        # 1. 检查缓存
        if identifier in self._cache:
            self.logger.debug(f"从缓存获取元数据: {identifier}")
            return self._cache[identifier]

        # 2. 查找元数据提取器
        metadata_extractor = self.plugin_manager.get_metadata_extractor(identifier)

        if not metadata_extractor:
            self.logger.warning(f"未找到能处理该标识符的元数据插件: {identifier}")
            return None

        # 3. 提取元数据
        self.logger.info(f"正在提取元数据: {identifier}")
        try:
            metadata = metadata_extractor.extract_metadata(identifier)

            # 4. 缓存结果
            if metadata:
                # 所有实际的元数据插件都应该返回 MovieMetadata
                # 这里进行类型转换以满足类型检查
                movie_metadata = cast(MovieMetadata, metadata)
                self._cache[identifier] = movie_metadata
                # 如果有 code，也缓存到 code 键
                if movie_metadata.code and movie_metadata.code != identifier:
                    self._cache[movie_metadata.code] = movie_metadata
                return movie_metadata

            return None

        except Exception as e:
            self.logger.error(f"元数据提取失败 ({identifier}): {e}")
            return None

    def get_metadata_from_search_result(self, search_result: SearchResult) -> Optional[MovieMetadata]:
        """从搜索结果获取元数据

        流程:
        1. 优先使用 URL 提取元数据（如果有 extractor）
        2. 尝试使用 code 提取元数据
        3. 如果都失败，返回 None

        Args:
            search_result: 搜索结果对象

        Returns:
            元数据对象，失败返回 None
        """
        # 1. 尝试使用 URL
        if search_result.url:
            metadata = self.get_metadata(search_result.url)
            if metadata:
                return metadata

        # 2. 尝试使用 code
        if search_result.code:
            metadata = self.get_metadata(search_result.code)
            if metadata:
                return metadata

        # 3. 都失败
        self.logger.warning(f"无法从搜索结果获取元数据: {search_result.title or search_result.code}")
        return None

    def batch_get_metadata(
        self,
        identifiers: List[str],
        callback: Optional[Callable[[int, int, str], None]] = None,
    ) -> List[Optional[MovieMetadata]]:
        """批量获取元数据

        Args:
            identifiers: 标识符列表
            callback: 进度回调函数 callback(current, total, identifier)

        Returns:
            元数据对象列表（保持顺序，失败的为 None）
        """
        results: List[Optional[MovieMetadata]] = []
        total = len(identifiers)

        for idx, identifier in enumerate(identifiers, 1):
            # 进度回调
            if callback:
                try:
                    callback(idx, total, identifier)
                except Exception as e:
                    self.logger.warning(f"进度回调异常: {e}")

            # 获取元数据
            metadata = self.get_metadata(identifier)
            results.append(metadata)

        return results

    def batch_get_metadata_from_search_results(
        self,
        search_results: List[SearchResult],
        callback: Optional[Callable[[int, int, SearchResult], None]] = None,
    ) -> List[Optional[MovieMetadata]]:
        """批量从搜索结果获取元数据

        Args:
            search_results: 搜索结果列表
            callback: 进度回调函数 callback(current, total, search_result)

        Returns:
            元数据对象列表（保持顺序，失败的为 None）
        """
        results: List[Optional[MovieMetadata]] = []
        total = len(search_results)

        for idx, search_result in enumerate(search_results, 1):
            # 进度回调
            if callback:
                try:
                    callback(idx, total, search_result)
                except Exception as e:
                    self.logger.warning(f"进度回调异常: {e}")

            # 获取元数据
            metadata = self.get_metadata_from_search_result(search_result)
            results.append(metadata)

        return results

    def clear_cache(self) -> None:
        """清空缓存"""
        self._cache.clear()
        self.logger.info("元数据缓存已清空")

    def get_cache_size(self) -> int:
        """获取缓存大小

        Returns:
            缓存中的元数据数量
        """
        return len(self._cache)

    def get_available_plugins(self) -> List[str]:
        """获取可用的元数据插件列表（从 CLI 迁移）

        Returns:
            插件名称列表
        """
        return [plugin.name for plugin in self.plugin_manager.metadata_plugins]

    def get_plugin_for_identifier(self, identifier: str) -> "Optional[MetadataPlugin]":
        """获取能处理指定标识符的元数据插件

        Args:
            identifier: 标识符（URL 或代码）

        Returns:
            元数据插件，如果没有找到返回 None
        """
        return self.plugin_manager.get_metadata_extractor(identifier)


# 全局实例（单例模式）
_metadata_manager_instance: Optional[MetadataManager] = None


def get_metadata_manager(
    plugin_manager: Optional["PluginManager"] = None,
) -> MetadataManager:
    """获取元数据管理器全局实例

    Args:
        plugin_manager: 插件管理器实例。仅在首次调用时使用

    Returns:
        MetadataManager 实例
    """
    global _metadata_manager_instance
    if _metadata_manager_instance is None:
        _metadata_manager_instance = MetadataManager(plugin_manager)
    return _metadata_manager_instance

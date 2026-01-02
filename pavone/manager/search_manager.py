"""
搜索管理器

负责管理和执行搜索操作,从 PluginManager 迁移搜索业务逻辑。
"""

from typing import TYPE_CHECKING, List, Optional

from ..config.logging_config import get_logger
from ..models import SearchResult

if TYPE_CHECKING:
    from .plugin_manager import PluginManager


class SearchManager:
    """搜索管理器

    负责管理和执行搜索操作，提供搜索、去重、排序和最佳匹配功能。
    """

    def __init__(self, plugin_manager: "PluginManager"):
        """初始化搜索管理器

        Args:
            plugin_manager: 插件管理器实例
        """
        self.plugin_manager = plugin_manager
        self.logger = get_logger(__name__)

    def search(self, keyword: str, limit: int = 20, enable_sites: Optional[List[str]] = None) -> List[SearchResult]:
        """在所有搜索插件中执行搜索

        从 PluginManager.search() 迁移的核心搜索功能。

        Args:
            keyword: 搜索关键词（通常是视频代码）
            limit: 每个插件的结果数量限制
            enable_sites: 启用的站点列表（None则使用所有，["All"]表示所有）

        Returns:
            合并后的搜索结果列表
        """
        search_plugins = self.plugin_manager.get_all_search_plugins()

        if not search_plugins:
            self.logger.warning("没有可用的搜索插件")
            return []

        results: List[SearchResult] = []
        is_all_enabled = enable_sites and len(enable_sites) == 1 and enable_sites[0] == "All"

        # 如果未指定站点，使用所有搜索插件
        if enable_sites is None:
            enable_sites = [plugin.get_site_name() for plugin in search_plugins]

        # 遍历所有搜索插件
        for plugin in search_plugins:
            # 检查插件是否在启用列表中
            if not is_all_enabled and plugin.get_site_name() not in enable_sites:
                continue

            try:
                self.logger.debug(f"使用插件 {plugin.name} 搜索关键词: {keyword}")
                plugin_results = plugin.search(keyword, limit)
                results.extend(plugin_results)
                self.logger.debug(f"插件 {plugin.name} 返回 {len(plugin_results)} 个结果")
            except Exception as e:
                self.logger.error(f"搜索插件 {plugin.name} 执行失败: {e}", exc_info=True)

        self.logger.info(f"搜索关键词 '{keyword}' 共返回 {len(results)} 个结果")
        return results

    def search_with_dedup(self, keyword: str, limit: int = 20, enable_sites: Optional[List[str]] = None) -> List[SearchResult]:
        """执行搜索并去重

        增强功能：对搜索结果进行去重处理，避免重复的URL或代码。

        Args:
            keyword: 搜索关键词
            limit: 每个插件的结果数量限制
            enable_sites: 启用的站点列表

        Returns:
            去重后的搜索结果列表
        """
        results = self.search(keyword, limit, enable_sites)

        if not results:
            return []

        # 去重逻辑：基于URL和代码
        seen_urls: set[str] = set()
        seen_codes: set[str] = set()
        deduped_results: List[SearchResult] = []

        for result in results:
            # 检查URL去重
            if result.url and result.url in seen_urls:
                self.logger.debug(f"跳过重复URL: {result.url}")
                continue

            # 检查代码去重
            if result.code and result.code in seen_codes:
                self.logger.debug(f"跳过重复代码: {result.code}")
                continue

            # 记录已见的URL和代码
            if result.url:
                seen_urls.add(result.url)
            if result.code:
                seen_codes.add(result.code)

            deduped_results.append(result)

        removed_count = len(results) - len(deduped_results)
        if removed_count > 0:
            self.logger.info(f"去重：移除 {removed_count} 个重复结果，剩余 {len(deduped_results)} 个")

        return deduped_results

    def get_best_match(self, keyword: str, enable_sites: Optional[List[str]] = None) -> Optional[SearchResult]:
        """获取最佳匹配结果

        增强功能：从搜索结果中选择最佳匹配项（通常是第一个结果）。

        Args:
            keyword: 搜索关键词
            enable_sites: 启用的站点列表

        Returns:
            最佳匹配的搜索结果，如果没有结果则返回 None
        """
        # 限制搜索数量以提高性能
        results = self.search_with_dedup(keyword, limit=5, enable_sites=enable_sites)

        if not results:
            self.logger.warning(f"未找到关键词 '{keyword}' 的任何匹配结果")
            return None

        # 返回第一个结果作为最佳匹配
        best_match = results[0]
        self.logger.info(f"找到最佳匹配: {best_match.title} ({best_match.code})")
        return best_match

    def search_by_code(self, code: str, enable_sites: Optional[List[str]] = None) -> List[SearchResult]:
        """使用标准化的代码进行搜索

        便捷方法：使用视频代码进行搜索并去重。

        Args:
            code: 视频代码（如 "SSIS-123"）
            enable_sites: 启用的站点列表

        Returns:
            去重后的搜索结果列表
        """
        self.logger.info(f"使用代码搜索: {code}")
        return self.search_with_dedup(code, enable_sites=enable_sites)

    def get_available_sites(self) -> List[str]:
        """获取所有可用的搜索站点列表

        Returns:
            可用搜索站点名称列表
        """
        search_plugins = self.plugin_manager.get_all_search_plugins()
        sites = [plugin.get_site_name() for plugin in search_plugins]
        self.logger.debug(f"可用搜索站点: {sites}")
        return sites


# 全局搜索管理器实例（延迟初始化）
_search_manager: Optional[SearchManager] = None


def get_search_manager(plugin_manager: Optional["PluginManager"] = None) -> SearchManager:
    """获取全局搜索管理器实例

    Args:
        plugin_manager: 插件管理器实例（首次调用时必须提供）

    Returns:
        全局搜索管理器实例

    Raises:
        ValueError: 如果首次调用时未提供 plugin_manager
    """
    global _search_manager

    if _search_manager is None:
        if plugin_manager is None:
            raise ValueError("首次初始化 SearchManager 时必须提供 plugin_manager")
        _search_manager = SearchManager(plugin_manager)

    return _search_manager

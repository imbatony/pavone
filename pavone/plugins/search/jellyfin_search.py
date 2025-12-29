"""
Jellyfin 搜索插件

在 Jellyfin 库中搜索视频
"""

from typing import List, Optional

from pavone.jellyfin.models import JellyfinItem

from ...config.logging_config import get_logger
from ...jellyfin import JellyfinClientWrapper, LibraryManager
from ...models import SearchResult
from .base import SearchPlugin

# 定义插件名称和版本
PLUGIN_NAME = "JellyfinSearch"
PLUGIN_VERSION = "1.0.0"
PLUGIN_DESCRIPTION = "在 Jellyfin 库中搜索视频"
PLUGIN_AUTHOR = "PAVOne"

SITE_NAME = "Jellyfin"


class JellyfinSearch(SearchPlugin):
    """Jellyfin 搜索插件"""

    def __init__(
        self,
        name: str = PLUGIN_NAME,
        version: str = PLUGIN_VERSION,
        description: str = PLUGIN_DESCRIPTION,
        author: str = PLUGIN_AUTHOR,
    ):
        super().__init__(
            site=SITE_NAME,
            name=name,
            version=version,
            description=description,
            author=author,
        )
        self.client: Optional[JellyfinClientWrapper] = None
        self.library_manager: Optional[LibraryManager] = None
        self.logger = get_logger(__name__)

    def initialize(self) -> bool:
        """初始化 Jellyfin 搜索插件"""
        try:
            if not self.config.jellyfin.enabled:
                self.logger.info("Jellyfin 未启用，搜索插件不可用")
                return False

            self.client = JellyfinClientWrapper(self.config.jellyfin)
            self.client.authenticate()

            self.library_manager = LibraryManager(self.client)
            self.library_manager.initialize()

            self.logger.info("Jellyfin 搜索插件初始化成功")
            return True

        except Exception as e:
            self.logger.error(f"Jellyfin 搜索插件初始化失败: {e}")
            return False

    def search(self, keyword: str, limit: int = 20) -> List[SearchResult]:
        """
        在 Jellyfin 中搜索视频

        Args:
            keyword: 搜索关键词
            limit: 结果数量限制

        Returns:
            搜索结果列表
        """
        if not self.client or not self.library_manager:
            self.logger.warning("Jellyfin 搜索插件未初始化")
            return []

        try:
            self.logger.debug(f"在 Jellyfin 中搜索: {keyword}")

            # 使用 Jellyfin 客户端搜索
            items = self.client.search_items(keyword, limit=limit)

            if not items:
                self.logger.debug(f"未在 Jellyfin 中找到与 '{keyword}' 相关的视频")
                return []

            # 将 JellyfinItem 转换为 SearchResult
            results: List[SearchResult] = []
            for item in items:
                result = SearchResult(
                    site=SITE_NAME,
                    keyword=keyword,
                    title=item.name,
                    description=f"Jellyfin 库项 - {item.type}",
                    url=f"jellyfin://{item.id}",
                    code=self._extract_code_from_item(item),
                )
                results.append(result)

            self.logger.info(f"在 Jellyfin 中找到 {len(results)} 个搜索结果")
            return results

        except Exception as e:
            self.logger.error(f"Jellyfin 搜索失败: {e}")
            return []

    def _extract_code_from_item(self, item:JellyfinItem) -> str:
        """
        从 Jellyfin 项中提取视频番号

        Args:
            item: JellyfinItem 对象

        Returns:
            视频番号或空字符串
        """
        try:
            # 尝试从项名称中提取番号
            import re

            name = item.name
            # 常见格式: FC2-3751072, ABP-123456, FC2-PPV-123456 等
            match = re.search(r"([A-Z][A-Z0-9]+-[A-Z]?[A-Z]?[A-Z]?-?\d+)", name, re.IGNORECASE)
            if match:
                return match.group(1)

            # 尝试从元数据中获取
            external_urls = item.metadata.get("ExternalUrls", {})
            if external_urls:
                return list(external_urls.values())[0] if external_urls else ""

            return ""

        except Exception:
            return ""

    def cleanup(self):
        """清理搜索插件资源"""
        if self.client:
            self.client = None
        if self.library_manager:
            self.library_manager = None

    def __repr__(self) -> str:
        status = "可用" if (self.client and self.library_manager) else "不可用"
        return f"JellyfinSearch(status={status})"

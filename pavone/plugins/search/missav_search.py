from __future__ import annotations
from re import findall
from .base import SearchPlugin
from ...models.search_result import SearchResult
from ...utils import CodeExtractUtils

# 定义插件名称和版本
PLUGIN_NAME = "MissavSearch"
PLUGIN_VERSION = "1.0.0"
PLUGIN_DESCRIPTION = "提取 missav.ai 和 missav.com 的视频下载链接"
PLUGIN_AUTHOR = "PAVOne"

SITE_NAME = "MissAV"

# Missav 网站的基础 URL,有可能未来会调整
MISSAV_BASE_URL = "https://missav.ai"


class MissavSearch(SearchPlugin):
    """
    Missav 搜索插件
    """

    def __init__(
        self,
        name: str = PLUGIN_NAME,
        version: str = PLUGIN_VERSION,
        description: str = PLUGIN_DESCRIPTION,
        author: str = PLUGIN_AUTHOR,
    ):
        super().__init__(name, version, description, author)

    def search(self, keyword: str, limit: int = 20) -> list[SearchResult]:
        """
        执行搜索操作
        :param keyword: 搜索关键词
        :param limit: 返回结果数量限制
        :return: 搜索结果列表
        """
        # 这里可以添加实际的搜索逻辑
        # 先尝试从关键词中提取编号
        code = CodeExtractUtils.extract_code_from_text(keyword)
        if code:
            # 如果是FC2或FC2的编号，转换为大写，需要中间添加ppv
            if code.startswith("FC2") or code.startswith("fc2"):
                code = code[:3] + "-PPV-" + code[3:]
            code = code.lower()
            url = f"{MISSAV_BASE_URL}/ja/{code}"
            res = self.fetch(url)
            if res and res.status_code == 200:
                # 解析视频页面，提取视频信息
                result = self._parse_video_page(res.text, code)
                if result:
                    return [result]
        # 如果没有提取到编号,使用网页的搜索功能
        search_url = f"{MISSAV_BASE_URL}/ja/search/{keyword}"

        res = self.fetch(search_url)
        if res and res.status_code == 200:
            # 解析搜索结果页面，提取视频信息
            results = self._parse_search_results(res.text, limit, keyword)
            return results
        else:
            self.logger.error(
                f"Failed to fetch search results for {keyword}. Status code: {res.status_code if res else 'No response'}"
            )
            return []

    def _parse_video_page(self, html: str, code: str) -> SearchResult:
        """
        解析视频页面，提取视频信息
        :param html: 视频页面的HTML内容
        :param code: 视频编号
        :return: 搜索结果
        """
        return SearchResult(
            site=SITE_NAME,
            keyword=code,
            title=f"{SITE_NAME} Video Result for {code}",
            description=f"Video result for {code} on {SITE_NAME}",
            url=f"{MISSAV_BASE_URL}/ja/{code}",
            code=code,
        )

    def _parse_search_results(self, html: str, limit: int, keyword: str) -> list[SearchResult]:
        """
        解析搜索结果页面，提取视频信息
        :param html: 搜索结果页面的HTML内容
        :param limit: 返回结果数量限制
        :param keyword: 搜索关键词
        :return: 搜索结果列表
        """
        results: list[SearchResult] = []
        regex = r'<a\s+class="text-secondary group-hover:text-primary"\s+href="([^"]+)"\s+alt="([^"]+)"[^>]*>\s*(.*?)\s*</a>'
        matches = findall(regex, html)
        if not matches:
            self.logger.warning(f"No search results found for keyword: {keyword}")
            return results
        # 限制返回结果数量
        matches = matches[:limit]
        for match in matches:
            url, alt, title = match
            result = SearchResult(
                site=SITE_NAME,
                keyword=keyword,
                title=title,
                description=f"Search result for {title} on {SITE_NAME}",
                url=url,
                code=alt.upper(),  # 将编号转换为大写形式
            )
            results.append(result)
        return results

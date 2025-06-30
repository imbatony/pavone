from dataclasses import dataclass
from typing import Optional


@dataclass
class SearchResult:
    def __init__(self, site: str, keyword: str, title: str, description: str, url: str, code: Optional[str] = None):
        """
        初始化搜索结果对象
        """
        self.code = code
        self.keyword = keyword
        self.title = title
        self.description = description
        self.url = url
        self.site = site

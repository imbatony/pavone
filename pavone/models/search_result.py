from dataclasses import dataclass


@dataclass
class SearchResult:
    def __init__(self, keyword: str, title: str, description: str, url: str):
        self.keyword = keyword
        self.title = title
        self.description = description
        self.url = url

    def __repr__(self):
        return f"SearchResult(keyword={self.keyword}, title={self.title}, description={self.description}, url={self.url})"
# 合同: HtmlMetadataPlugin 公共 API

**版本**: 1.0.0 | **类型**: 内部插件 API

## 类签名

```python
class HtmlMetadataPlugin(MetadataPlugin):
    """HTML 解析类元数据插件的公共基类"""
```

## 公共接口

### 模板方法 (继承, 不建议覆写)

```python
def extract_metadata(self, identifier: str) -> Optional[BaseMetadata]:
    """
    模板方法: resolve → fetch → parse，统一错误处理。

    参数:
        identifier: URL 或视频代码
    返回:
        BaseMetadata 对象, 失败返回 None (不抛出异常)
    行为保证:
        - RequestException → logger.error + return None
        - Exception → logger.error(exc_info=True) + return None
    """
```

### 钩子方法 (可覆写)

```python
def _fetch_page(self, url: str) -> requests.Response:
    """
    获取 HTML 页面。子类覆写以自定义:
    - 添加 cookies (如年龄确认)
    - 添加 headers (如 Referer, User-Agent)
    - 修改 timeout
    - 设置 verify_ssl=False

    默认行为: self.fetch(url, timeout=30)

    覆写示例:
        def _fetch_page(self, url: str) -> requests.Response:
            return self.fetch(url, headers={"Cookie": "modal=off"}, timeout=30)
    """
```

### 抽象方法 (子类必须实现)

```python
@abstractmethod
def _resolve(self, identifier: str) -> Tuple[Optional[str], Optional[str]]:
    """
    将 identifier 解析为 (movie_id, page_url)。

    参数:
        identifier: URL 或视频代码
    返回:
        (movie_id, page_url) — 成功
        (None, None) — 失败
    """

@abstractmethod
def _parse(self, soup: BeautifulSoup, movie_id: str, page_url: str) -> Optional[BaseMetadata]:
    """
    从 BeautifulSoup 对象解析元数据。

    参数:
        soup: 已解析的 HTML 文档
        movie_id: 从 _resolve 得到的影片 ID
        page_url: 原始页面 URL (用于 _abs 转换)
    返回:
        填充好的 BaseMetadata 对象, 失败返回 None
    """
```

### 静态工具方法 (直接使用, 不建议覆写)

```python
@staticmethod
def _abs(url: str, base: str) -> str:
    """相对 URL 转绝对 URL"""

@staticmethod
def _parse_runtime(text: str) -> Optional[int]:
    """解析时长文本 → 分钟数。支持: '120分', '02:15', 'Apx. 122 Min.'"""

@staticmethod
def _parse_date(s: str) -> Optional[str]:
    """解析日期文本 → 'YYYY-MM-DD'。支持: '2023/01/02', '2023年1月2日', '2023-01-02'"""

@staticmethod
def _parse_iso_duration(s: str) -> Optional[int]:
    """解析 ISO 8601 时长 → 分钟数。支持: 'PT1H30M', 'PT30M', '120分'"""

@staticmethod
def _get_tag_attr(tag: Optional[Any], attr: str) -> Optional[str]:
    """安全获取 BS4 tag 属性, 返回 Optional[str]"""
```

## 最小实现示例

```python
class ExampleMetadata(HtmlMetadataPlugin):
    def can_extract(self, identifier: str) -> bool:
        return self.can_handle_domain(identifier, ["example.com"])

    def _resolve(self, identifier: str) -> Tuple[Optional[str], Optional[str]]:
        # URL → (movie_id, page_url)
        return "EX-001", identifier

    def _parse(self, soup: BeautifulSoup, movie_id: str, page_url: str) -> Optional[BaseMetadata]:
        title = soup.select_one("h1").get_text(strip=True)
        return MetadataBuilder().set_title(title, movie_id).build()
```

## 兼容性承诺

- `MetadataPlugin.can_extract` 和 `MetadataPlugin.extract_metadata` 接口不变
- 未迁移的插件（直接继承 `MetadataPlugin`）不受影响
- `_fetch_page` 默认行为等同于现有 `self.fetch(url, timeout=30)`

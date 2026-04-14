# 合同: JsonLdMetadataPlugin 公共 API

**版本**: 1.0.0 | **类型**: 内部插件 API

## 类签名

```python
class JsonLdMetadataPlugin(HtmlMetadataPlugin):
    """JSON-LD 解析类元数据插件的公共基类。继承 HtmlMetadataPlugin。"""
```

## 公共接口

### 模板方法 (覆写 HtmlMetadataPlugin)

```python
def extract_metadata(self, identifier: str) -> Optional[BaseMetadata]:
    """
    模板方法: resolve → fetch → BS4 → extract_jsonld → parse_with_jsonld。

    与 HtmlMetadataPlugin 的区别:
        额外调用 _extract_jsonld 提取 JSON-LD 数据
        传递 JSON-LD 数据给 _parse_with_jsonld
    """
```

### 新增方法

```python
def _extract_jsonld(self, soup: BeautifulSoup) -> Optional[Dict[str, Any]]:
    """
    从 HTML 中提取 JSON-LD 结构化数据。

    行为:
        - 查找所有 <script type="application/ld+json"> 标签
        - 返回第一个成功解析的 JSON 对象
        - JSON 数组取第一个元素
        - 所有 script 解析失败返回 None
    """
```

### 抽象方法 (子类必须实现)

```python
@abstractmethod
def _parse_with_jsonld(
    self,
    soup: BeautifulSoup,
    jsonld: Optional[Dict[str, Any]],
    movie_id: str,
    page_url: str,
) -> Optional[BaseMetadata]:
    """
    从 JSON-LD + HTML 解析元数据。

    参数:
        soup: HTML 文档 (用于 fallback 字段提取)
        jsonld: JSON-LD 数据 (可能为 None)
        movie_id: 影片 ID
        page_url: 页面 URL
    """
```

### 继承的方法

- 所有 `HtmlMetadataPlugin` 的静态工具方法 (`_abs`, `_parse_runtime`, `_parse_date`, `_parse_iso_duration`, `_get_tag_attr`)
- `_fetch_page` 钩子方法

## 最小实现示例

```python
class ExampleJsonLdMetadata(JsonLdMetadataPlugin):
    def can_extract(self, identifier: str) -> bool:
        return self.can_handle_domain(identifier, ["example.com"])

    def _resolve(self, identifier: str) -> Tuple[Optional[str], Optional[str]]:
        return "EX-001", identifier

    def _parse_with_jsonld(self, soup, jsonld, movie_id, page_url):
        title = (jsonld or {}).get("name") or soup.select_one("h1").get_text(strip=True)
        runtime = self._parse_iso_duration((jsonld or {}).get("duration", ""))
        return MetadataBuilder().set_title(title, movie_id).set_runtime(runtime).build()
```

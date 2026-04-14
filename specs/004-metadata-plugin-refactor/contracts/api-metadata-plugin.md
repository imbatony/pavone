# 合同: ApiMetadataPlugin 公共 API

**版本**: 1.0.0 | **类型**: 内部插件 API

## 类签名

```python
class ApiMetadataPlugin(MetadataPlugin):
    """API/JSON 类元数据插件的公共基类"""
```

## 公共接口

### 模板方法 (继承, 不建议覆写)

```python
def extract_metadata(self, identifier: str) -> Optional[BaseMetadata]:
    """
    模板方法: resolve → build_api_url → fetch_api → json → parse。

    行为保证:
        - RequestException → logger.error + return None
        - Exception → logger.error(exc_info=True) + return None
    """
```

### 钩子方法 (可覆写)

```python
def _fetch_api(self, url: str) -> requests.Response:
    """
    获取 API 响应。子类覆写以自定义:
    - 添加 Authorization header (Bearer token)
    - 添加 Referer header
    - 修改 Content-Type

    默认行为: self.fetch(url, timeout=30)
    """
```

### 抽象方法 (子类必须实现)

```python
@abstractmethod
def _build_api_url(self, movie_id: str) -> str:
    """构建 API 请求 URL"""

@abstractmethod
def _resolve(self, identifier: str) -> Tuple[Optional[str], Optional[str]]:
    """将 identifier 解析为 (movie_id, page_url)"""

@abstractmethod
def _parse(self, data: Dict[str, Any], movie_id: str, page_url: str) -> Optional[BaseMetadata]:
    """从 JSON 响应数据解析元数据"""
```

## 最小实现示例

```python
class ExampleApiMetadata(ApiMetadataPlugin):
    def can_extract(self, identifier: str) -> bool:
        return bool(re.match(r"^[a-zA-Z]+-\d+$", identifier))

    def _build_api_url(self, movie_id: str) -> str:
        return f"https://api.example.com/v1/videos/{movie_id}"

    def _resolve(self, identifier: str) -> Tuple[Optional[str], Optional[str]]:
        return identifier, f"https://example.com/videos/{identifier}"

    def _parse(self, data: Dict[str, Any], movie_id: str, page_url: str) -> Optional[BaseMetadata]:
        return MetadataBuilder().set_title(data.get("title", ""), movie_id).build()
```

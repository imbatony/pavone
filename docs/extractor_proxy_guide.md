# ExtractorPlugin 代理集成指南

## 概述

`ExtractorPlugin` 基类现在提供了统一的网页获取方法 `fetch_webpage()`，该方法自动处理：

- **代理配置**: 自动读取并应用全局代理设置
- **SSL验证**: 默认忽略SSL证书错误，避免连接问题
- **请求头部**: 提供默认的浏览器请求头
- **异常处理**: 统一的错误处理和警告管理

## 主要功能

### 1. 统一的网页获取方法

```python
def fetch_webpage(self, url: str, headers: Optional[Dict[str, str]] = None, 
                 timeout: int = 30, verify_ssl: bool = False) -> requests.Response
```

**参数说明:**
- `url`: 要获取的URL
- `headers`: 自定义HTTP头部（可选，默认使用浏览器头部）
- `timeout`: 请求超时时间（默认30秒）
- `verify_ssl`: 是否验证SSL证书（默认False，忽略SSL错误）

### 2. 自动代理配置

方法会自动从 `config_manager` 获取代理设置：

```python
def _get_proxies(self) -> Optional[Dict[str, str]]
```

- 读取 `config.proxy.enabled` 状态
- 应用 `config.proxy.http_proxy` 和 `config.proxy.https_proxy`
- 如果代理未启用或配置无效，返回 `None`

## 使用方法

### 基本用法

```python
class MyExtractor(ExtractorPlugin):
    def extract(self, url: str) -> List[DownloadOpt]:
        try:
            # 使用基类方法，自动处理代理和SSL
            response = self.fetch_webpage(url)
            html_content = response.text
            # 解析HTML...
            return download_options
        except Exception as e:
            print(f"提取失败: {e}")
            return []
```

### 自定义请求头

```python
def extract_with_auth(self, url: str) -> List[DownloadOpt]:
    custom_headers = {
        'Authorization': 'Bearer token123',
        'X-Custom-Header': 'value'
    }
    
    response = self.fetch_webpage(url, headers=custom_headers)
    # 处理响应...
```

### 自定义超时和SSL设置

```python
def extract_secure(self, url: str) -> List[DownloadOpt]:
    response = self.fetch_webpage(
        url,
        timeout=60,      # 60秒超时
        verify_ssl=True  # 验证SSL证书
    )
    # 处理响应...
```

## 迁移指南

### 原有代码（需要手动处理代理）

```python
def extract(self, url: str) -> List[DownloadOpt]:
    try:
        import requests
        
        # 手动配置代理
        proxies = None
        if config.proxy.enabled:
            proxies = {'http': config.proxy.http_proxy}
        
        # 手动配置请求头
        headers = {'User-Agent': '...'}
        
        # 手动处理SSL
        response = requests.get(url, headers=headers, proxies=proxies, verify=False)
        # ...
```

### 新代码（使用统一方法）

```python
def extract(self, url: str) -> List[DownloadOpt]:
    try:
        # 一行代码，自动处理所有配置
        response = self.fetch_webpage(url)
        html_content = response.text
        # ...
```

## 优势

1. **简化代码**: 提取器无需关心代理、SSL等底层配置
2. **统一管理**: 所有提取器自动使用全局代理设置
3. **错误处理**: 统一的SSL警告抑制和异常处理
4. **易于维护**: 代理逻辑集中在基类中
5. **向后兼容**: 不影响现有代码结构

## 配置代理

使用 PAVOne 的配置系统设置代理：

```bash
# 通过CLI设置
pavone init  # 交互式配置代理

# 或直接编辑配置文件 ~/.pavone/config.json
{
  "proxy": {
    "enabled": true,
    "http_proxy": "http://127.0.0.1:7890",
    "https_proxy": "http://127.0.0.1:7890"
  }
}
```

## 故障排除

### SSL证书错误
默认情况下，`fetch_webpage()` 会忽略SSL证书错误。如果需要验证SSL：

```python
response = self.fetch_webpage(url, verify_ssl=True)
```

### 代理连接问题
检查代理配置：

```python
proxies = self._get_proxies()
print(f"当前代理配置: {proxies}")
```

### 超时问题
调整超时时间：

```python
response = self.fetch_webpage(url, timeout=60)
```

## 示例实现

参考 `examples/extractor_proxy_example.py` 获取完整的示例代码。

参考 `MissAVExtractor` 的实际迁移案例，了解如何将现有提取器升级到新的基类方法。

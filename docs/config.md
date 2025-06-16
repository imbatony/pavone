# 配置示例

## 基础配置

创建配置文件在 `~/.pavone/config.json`:

```json
{
  "download": {
    "output_dir": "./downloads",
    "max_concurrent_downloads": 3,
    "retry_times": 3,
    "timeout": 30,
    "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
  },
  "organize": {
    "auto_organize": true,
    "organize_by": "studio",
    "naming_pattern": "{studio}-{code}-{title}",
    "create_nfo": true,
    "download_cover": true
  },
  "search": {
    "max_results_per_site": 20,
    "search_timeout": 10,
    "enabled_sites": ["javbus", "javlibrary", "pornhub"]
  },
  "proxy": {
    "enabled": false,
    "http_proxy": "",
    "https_proxy": ""
  }
}
```

## 使用代理

如果需要使用代理，可以在配置中启用：

```json
{
  "proxy": {
    "enabled": true,
    "http_proxy": "http://127.0.0.1:1080",
    "https_proxy": "http://127.0.0.1:1080"
  }
}
```

## 自定义命名模式

支持的变量：
- `{studio}`: 制作商
- `{code}`: 番号/编号
- `{title}`: 标题
- `{actor}`: 演员
- `{date}`: 发布日期

示例：
- `{studio}-{code}-{title}` → `ABC-123-视频标题`
- `{code} {title} [{actor}]` → `ABC-123 视频标题 [演员名]`

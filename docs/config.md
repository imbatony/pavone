# PAVOne 配置文档

## 配置文件位置

PAVOne 的配置文件位于：
- Windows: `%USERPROFILE%\.pavone\config.json`
- Linux/macOS: `~/.pavone/config.json`

## 基础配置

创建配置文件 `~/.pavone/config.json`：

```json
{
  "output_dir": "./downloads",
  "max_concurrent_downloads": 3,
  "timeout": 30,
  "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
  "proxy": {
    "enabled": false,
    "http_proxy": "",
    "https_proxy": ""
  },
  "logging": {
    "level": "INFO",
    "file_enabled": false,
    "file_path": "~/.pavone/logs/pavone.log"
  },
  "plugins": {
    "extractors_dir": "~/.pavone/plugins/extractors",
    "auto_load": true
  }
}
```

## 配置项说明

### 下载配置

| 配置项 | 类型 | 默认值 | 说明 |
|--------|------|--------|------|
| `output_dir` | string | `"./downloads"` | 下载文件保存目录 |
| `max_concurrent_downloads` | int | `3` | 最大并发下载数量 |
| `timeout` | int | `30` | 网络请求超时时间（秒） |
| `user_agent` | string | Chrome UA | 请求时使用的User-Agent |

### 代理配置

| 配置项 | 类型 | 默认值 | 说明 |
|--------|------|--------|------|
| `proxy.enabled` | bool | `false` | 是否启用代理 |
| `proxy.http_proxy` | string | `""` | HTTP代理地址 |
| `proxy.https_proxy` | string | `""` | HTTPS代理地址 |

### 日志配置

| 配置项 | 类型 | 默认值 | 说明 |
|--------|------|--------|------|
| `logging.level` | string | `"INFO"` | 日志级别（DEBUG, INFO, WARNING, ERROR） |
| `logging.file_enabled` | bool | `false` | 是否启用文件日志 |
| `logging.file_path` | string | `"~/.pavone/logs/pavone.log"` | 日志文件路径 |

### 插件配置

| 配置项 | 类型 | 默认值 | 说明 |
|--------|------|--------|------|
| `plugins.extractors_dir` | string | `"~/.pavone/plugins/extractors"` | 外部提取器插件目录 |
| `plugins.auto_load` | bool | `true` | 是否自动加载外部插件 |

## 配置示例

### 基本下载配置

```json
{
  "output_dir": "D:\\Downloads\\Videos",
  "max_concurrent_downloads": 5,
  "timeout": 60,
  "user_agent": "Custom User Agent"
}
```

### 使用代理

```json
{
  "output_dir": "./downloads",
  "proxy": {
    "enabled": true,
    "http_proxy": "http://127.0.0.1:1080",
    "https_proxy": "http://127.0.0.1:1080"
  }
}
```

### 开发调试配置

```json
{
  "output_dir": "./test_downloads",
  "max_concurrent_downloads": 1,
  "timeout": 10,
  "logging": {
    "level": "DEBUG",
    "file_enabled": true,
    "file_path": "./debug.log"
  }
}
```

### 插件开发配置

```json
{
  "output_dir": "./downloads",
  "plugins": {
    "extractors_dir": "./custom_extractors",
    "auto_load": true
  },
  "logging": {
    "level": "DEBUG",
    "file_enabled": true
  }
}
```

## 配置管理

### 命令行配置

使用 `pavone config` 命令管理配置：

```bash
# 查看当前配置
pavone config list

# 设置配置项
pavone config set output_dir "/path/to/downloads"
pavone config set max_concurrent_downloads 5
pavone config set timeout 60

# 设置代理
pavone config set proxy.enabled true
pavone config set proxy.http_proxy "http://127.0.0.1:1080"

# 设置日志
pavone config set logging.level "DEBUG"
pavone config set logging.file_enabled true

# 重置配置为默认值
pavone config reset
```

### 编程方式配置

```python
from pavone.config.settings import Config, get_config, update_config

# 获取当前配置
config = get_config()
print(f"输出目录: {config.output_dir}")

# 修改配置
config.output_dir = "./custom_downloads"
config.max_concurrent_downloads = 10

# 保存配置
update_config(config)

# 创建临时配置
temp_config = Config(
    output_dir="./temp_downloads",
    timeout=120,
    proxy={"enabled": True, "http_proxy": "http://proxy:8080"}
)

# 在代码中使用临时配置
from pavone.manager.execution import ExecutionManager
manager = ExecutionManager(temp_config)
```

### 环境变量

可以通过环境变量覆盖配置：

```bash
# 设置输出目录
export PAVONE_OUTPUT_DIR="/path/to/downloads"

# 设置超时时间
export PAVONE_TIMEOUT="60"

# 设置代理
export PAVONE_PROXY_ENABLED="true"
export PAVONE_HTTP_PROXY="http://127.0.0.1:1080"

# 设置日志级别
export PAVONE_LOG_LEVEL="DEBUG"
```

对应的环境变量名规则：
- `PAVONE_` + 配置项的大写形式
- 嵌套配置用 `_` 分隔，如 `proxy.enabled` → `PAVONE_PROXY_ENABLED`

## 配置验证

PAVone 会在启动时自动验证配置：

```python
from pavone.config.validator import validate_config
from pavone.config.settings import get_config

config = get_config()
errors = validate_config(config)

if errors:
    print("配置验证失败：")
    for error in errors:
        print(f"  - {error}")
else:
    print("配置验证通过")
```

常见的配置错误：
- 输出目录不存在或没有写权限
- 超时时间设置为非正数
- 代理地址格式错误
- 并发下载数设置过大

## 迁移配置

从旧版本迁移配置：

```python
from pavone.config.migration import migrate_config_from_v1

# 迁移旧版本配置文件
migrate_config_from_v1("./old_config.json")
```

这会自动：
1. 读取旧版本配置
2. 转换为新格式
3. 保存到标准位置
4. 备份原始配置

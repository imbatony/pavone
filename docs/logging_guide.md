# 日志管理指南

Pavone项目集成了完整的日志管理系统，支持控制台和文件日志记录，具有日志轮转和灵活的配置选项。

## 日志配置

### 配置选项

日志配置通过 `LoggingConfig` 类进行管理，包含以下选项：

```python
@dataclass
class LoggingConfig:
    level: str = "INFO"                    # 日志级别: DEBUG, INFO, WARNING, ERROR, CRITICAL
    console_enabled: bool = True           # 是否启用控制台日志
    file_enabled: bool = True              # 是否启用文件日志
    file_path: str = "./logs/pavone.log"   # 日志文件路径
    max_file_size: int = 10 * 1024 * 1024  # 最大文件大小 (10MB)
    backup_count: int = 5                  # 备份文件数量
    format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"  # 日志格式
    date_format: str = "%Y-%m-%d %H:%M:%S" # 日期格式
```

### 默认配置

项目默认使用以下日志配置：

- **日志级别**: INFO
- **控制台日志**: 启用
- **文件日志**: 启用
- **日志文件**: `~/.pavone/logs/pavone.log`
- **文件轮转**: 10MB 每个文件，保留5个备份

## 使用方法

### 基本使用

```python
from pavone.config import get_logger

# 获取日志器
logger = get_logger("your.module.name")

# 记录不同级别的日志
logger.debug("调试信息")
logger.info("普通信息")
logger.warning("警告信息")
logger.error("错误信息")
logger.critical("严重错误")
```

### 通过配置管理器使用

```python
from pavone.config.settings import config_manager

# 获取日志器
logger = config_manager.get_logger("module.name")

# 动态修改日志配置
config_manager.set_log_level("DEBUG")
config_manager.disable_console_logging()
config_manager.enable_file_logging()
```

### 批量更新日志配置

```python
config_manager.update_logging_config(
    level="WARNING",
    max_file_size=20 * 1024 * 1024,  # 20MB
    backup_count=10,
    file_path="/custom/path/app.log"
)
```

## 配置文件

日志配置会自动保存在配置文件 `~/.pavone/config.json` 中：

```json
{
  "logging": {
    "level": "INFO",
    "console_enabled": true,
    "file_enabled": true,
    "file_path": "./logs/pavone.log",
    "max_file_size": 10485760,
    "backup_count": 5,
    "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    "date_format": "%Y-%m-%d %H:%M:%S"
  }
}
```

## 日志级别

支持的日志级别及其用途：

| 级别 | 数值 | 用途 |
|------|------|------|
| DEBUG | 10 | 详细的调试信息，通常只在开发时使用 |
| INFO | 20 | 一般信息，确认程序正常工作 |
| WARNING | 30 | 警告信息，程序仍在工作但有潜在问题 |
| ERROR | 40 | 错误信息，程序某些功能失败 |
| CRITICAL | 50 | 严重错误，程序可能无法继续运行 |

## 日志文件管理

### 文件轮转

当日志文件达到最大大小时，系统会自动创建新的日志文件：

- `pavone.log` - 当前日志文件
- `pavone.log.1` - 最近的备份
- `pavone.log.2` - 更早的备份
- ...
- `pavone.log.5` - 最早的备份（然后被删除）

### 自定义日志路径

```python
# 修改日志文件路径
config_manager.update_logging_config(
    file_path="/var/log/pavone/app.log"
)
```

## 模块化日志

为不同模块使用不同的日志器名称：

```python
# 下载模块
downloader_logger = get_logger("pavone.downloader")

# 提取器模块
extractor_logger = get_logger("pavone.extractor.missav")

# 组织器模块
organizer_logger = get_logger("pavone.organizer")
```

这样可以在日志中清楚地识别消息来源。

## 性能考虑

### 日志级别过滤

只有达到配置级别的日志才会被处理，低级别的日志会被忽略：

```python
# 当日志级别设为 INFO 时
logger.debug("这条消息不会被处理")  # 被忽略
logger.info("这条消息会被处理")     # 输出
```

### 条件日志

对于复杂的调试信息，使用条件日志：

```python
if logger.isEnabledFor(logging.DEBUG):
    expensive_debug_info = generate_debug_info()
    logger.debug(f"详细调试信息: {expensive_debug_info}")
```

## 故障排除

### 日志文件未创建

1. 检查日志目录权限
2. 确认 `file_enabled` 为 `True`
3. 检查磁盘空间

### 日志消息未显示

1. 检查日志级别设置
2. 确认相应的输出（控制台/文件）已启用
3. 验证日志器名称正确

### 配置未生效

```python
# 手动重新初始化日志系统
from pavone.config.logging_config import init_log_manager
init_log_manager(config_manager.config.logging)
```

## 最佳实践

1. **使用模块化日志器名称**: 以模块路径命名日志器
2. **合适的日志级别**: 生产环境使用 INFO，开发时使用 DEBUG
3. **避免敏感信息**: 不要在日志中记录密码、token等敏感信息
4. **结构化消息**: 使用一致的日志消息格式
5. **异常日志**: 使用 `logger.exception()` 记录异常和堆栈跟踪

```python
try:
    risky_operation()
except Exception as e:
    logger.exception("操作失败", exc_info=True)
```

# PAVOne 使用文档

## 安装

```bash
pip install -r requirements.txt
pip install -e .
```

## 基本使用

### 初始化配置

```bash
pavone init
```

### 下载视频

```bash
# 下载单个视频
pavone download "https://example.com/video.mp4"

# 自动选择第一个可用选项
pavone download "https://example.com/video.mp4" --auto-select

# 静默下载（无用户交互）
pavone download "https://example.com/video.mp4" --silent

# 指定输出目录
pavone download "https://example.com/video.mp4" --output-dir "/path/to/downloads"

# 批量下载（从文件读取URL列表）
pavone batch-download urls.txt --auto-select

# 批量下载（从命令行指定URL）
pavone batch-download "https://example1.com/video1.mp4" "https://example2.com/video2.mp4"
```

## 高级功能

### 配置管理

```bash
# 查看当前配置
pavone config list

# 设置配置项
pavone config set output_dir "/path/to/downloads"
pavone config set max_concurrent 5
pavone config set timeout 60

# 重置配置为默认值
pavone config reset
```

### 操作项管理

PAVOne 使用统一的 `OperationItem` 模型来管理下载任务：

```python
from pavone.models.operation import OperationItem, OperationType
from pavone.manager.execution import ExecutionManager

# 创建下载操作项
operation = OperationItem(
    operation_type=OperationType.DOWNLOAD,
    url="https://example.com/video.mp4",
    output_dir="/path/to/downloads"
)

# 使用执行管理器处理
manager = ExecutionManager()
result = manager.execute(operation)
print(f"操作成功: {result.success}")
```

### 插件系统

PAVOne 采用插件架构，支持提取器、元数据提取器等多种插件类型。

#### 提取器插件

```python
from pavone.plugins.manager import plugin_manager

# 自动加载所有插件
plugin_manager.load_plugins()

# 获取适合的提取器
extractor = plugin_manager.get_extractor_for_url("https://example.com/video.mp4")
if extractor:
    # 提取下载选项
    options = extractor.extract(url)
    for opt in options:
        print(f"可下载: {opt.filename}")
```

#### 创建自定义提取器

```python
from pavone.plugins.extractors.base import ExtractorPlugin
from pavone.models.operation import DownloadOption
from typing import List

class CustomExtractor(ExtractorPlugin):
    def __init__(self):
        super().__init__()
        self.name = "CustomExtractor"
        self.priority = 5  # 较高优先级
        self.description = "自定义网站提取器"
        
    def can_handle(self, url: str) -> bool:
        """检查是否能处理该URL"""
        return "mysite.com" in url
        
    def extract(self, url: str) -> List[DownloadOption]:
        """提取下载选项"""
        # 实现提取逻辑
        return [
            DownloadOption(
                url="https://real-video-url.mp4",
                filename="video.mp4",
                quality="1080p"
            )
        ]
        
    def initialize(self) -> bool:
        """初始化插件"""
        return True
        
    def execute(self, *args, **kwargs) -> List[DownloadOption]:
        """执行插件（委托给extract方法）"""
        if args:
            return self.extract(args[0])
        return []
```

#### 内置提取器

PAVOne 提供以下内置提取器：
- **DirectLinkExtractor** - 处理直接链接（.mp4, .m3u8 等）
- **MissAVExtractor** - 处理 MissAV 网站（如果配置）

### 批量操作

创建包含URL列表的文件 `urls.txt`：
```
https://example1.com/video1.mp4
https://example2.com/video2.mp4
https://example3.com/video3.mp3
```

然后执行：
```bash
pavone batch-download urls.txt --auto-select
```

### 进度监控

```python
from pavone.models.progress_info import ProgressInfo
from pavone.manager.execution import ExecutionManager

def progress_callback(progress: ProgressInfo):
    if progress.total_size > 0:
        percentage = (progress.downloaded / progress.total_size) * 100
        print(f"\r进度: {percentage:.1f}% ({progress.downloaded}/{progress.total_size})", end="")

# 创建带进度回调的操作
operation = OperationItem(
    operation_type=OperationType.DOWNLOAD,
    url="https://example.com/video.mp4",
    progress_callback=progress_callback
)

manager = ExecutionManager()
result = manager.execute(operation)
```

### 配置文件

配置文件位于 `~/.pavone/config.json`，详细配置说明请参考 [配置文档](config.md)。

### 命令行接口

PAVOne 提供了清晰的命令行接口：

```bash
# 查看帮助
pavone --help

# 查看子命令帮助
pavone download --help
pavone config --help
pavone batch-download --help

# 启用详细日志
pavone --verbose download "url"

# 指定配置文件
pavone --config-file "/path/to/config.json" download "url"
```

## 故障排除

### 常见问题

1. **下载失败**
   - 检查网络连接
   - 检查代理设置（如果配置）
   - 查看错误日志（使用 `--verbose` 参数）

2. **提取器无法识别URL**
   - 确认URL格式正确
   - 检查是否有对应的提取器插件
   - 查看插件是否正确加载

3. **配置问题**
   - 检查配置文件语法
   - 使用 `pavone config list` 查看当前配置
   - 使用 `pavone config reset` 重置配置

### 日志调试

启用详细日志：
```bash
pavone --verbose download "url"
```

查看日志文件（如果配置了日志文件）：
```bash
tail -f ~/.pavone/logs/pavone.log
```

### 开发调试

如果需要调试插件或核心功能：

```python
import logging
from pavone.config.logging_config import setup_logging

# 启用调试日志
setup_logging(level=logging.DEBUG)

# 然后执行相关操作
from pavone.manager.execution import ExecutionManager
manager = ExecutionManager()
# ...
```

## 贡献

欢迎提交问题和贡献代码！请查看项目的 GitHub 仓库。

# 提取器插件

这个文件夹包含所有与资源提取相关的插件类。

## 文件结构

- `base.py` - 包含 `ExtractorPlugin` 基类
- `mp4_direct.py` - MP4 直接链接提取器
- `m3u8_direct.py` - M3U8 直接链接提取器
- `missav_extractor.py` - MissAV 网站专用提取器
- `__init__.py` - 导出所有提取器插件类

## 什么是提取器插件

提取器插件负责分析给定的URL并提取出可下载的资源列表，而不直接进行下载操作。提取器将返回 `DownloadOption` 对象的列表，每个对象包含一个可下载资源的信息，这些 `DownloadOption` 对象随后被包装为 `OperationItem` 进行执行。

## 如何添加新的提取器

1. 在这个文件夹中创建新的 `.py` 文件
2. 继承 `ExtractorPlugin` 基类
3. 实现必需的抽象方法：
   - `can_handle(url: str) -> bool` - 检查是否能处理该URL
   - `extract(url: str) -> List[DownloadOption]` - 提取下载选项列表
   - `initialize() -> bool` - 初始化插件
   - `execute(*args, **kwargs)` - 执行插件功能

4. 在 `__init__.py` 中导出你的新插件类

## 示例

```python
from typing import List
from .base import ExtractorPlugin
from ...models.metadata import DownloadOption

class MyCustomExtractor(ExtractorPlugin):
    def __init__(self):
        super().__init__()
        self.name = "MyCustomExtractor"
        self.description = "我的自定义资源提取器"
    
    def initialize(self) -> bool:
        return True
    
    def execute(self, *args, **kwargs):
        if len(args) >= 1:
            return self.extract(args[0])
        return []
    
    def can_handle(self, url: str) -> bool:
        return "example.com" in url
    
    def extract(self, url: str) -> List[DownloadOption]:
        # 分析URL并提取资源
        download_options = []
        
        # 示例：提取视频资源
        video_url = "https://example.com/video.mp4"
        download_option = DownloadOption(
            url=video_url,
            filename="video.mp4",
            headers={"Referer": url}
        )
        download_options.append(download_option)
        
        return download_options
```

## 注册和使用插件

创建插件后，可以通过插件管理器注册并使用：

```python
from pavone.plugins import plugin_manager
from pavone.plugins.extractors import MyCustomExtractor
from pavone.manager.execution import ExecutionManager
from pavone.models.operation import OperationItem

# 创建并注册插件
extractor = MyCustomExtractor()
plugin_manager.register_plugin(extractor)

# 使用插件提取资源
extractor_plugin = plugin_manager.get_extractor_for_url("https://example.com/page")
if extractor_plugin:
    download_options = extractor_plugin.extract("https://example.com/page")  # type: ignore
    
    # 将下载选项转换为操作项并执行
    execution_manager = ExecutionManager()
    for option in download_options:
        operation = OperationItem.from_download_option(option)
        execution_manager.add_operation(operation)
    
    # 执行所有操作
    execution_manager.execute_all()
```

## 内置提取器

### MP4DirectExtractor
处理以 `.mp4` 结尾的直接视频链接。这类链接无需额外解析网站内容，直接返回对应的下载选项。

- **优先级**: 10（高优先级）
- **支持的URL格式**:
  - `https://example.com/video.mp4`
  - `https://cdn.example.com/path/to/movie.MP4`

### M3U8DirectExtractor  
处理以 `.m3u8` 结尾的直接播放列表链接。这类链接指向HLS流媒体播放列表，无需额外解析网站内容。

- **优先级**: 10（高优先级）
- **支持的URL格式**:
  - `https://example.com/playlist.m3u8`
  - `https://stream.example.com/live/stream.M3U8`

**注意**: M3U8链接提取后的文件名会自动改为 `.mp4` 扩展名。

## 优先级系统

ExtractorPlugin 支持优先级系统，用于确定当多个提取器都能处理同一URL时的选择顺序。

### 优先级规则
- 优先级用数值表示，**数值越小优先级越高**
- 默认优先级为 50
- 直接链接提取器（MP4、M3U8）使用优先级 10
- 网站解析提取器建议使用优先级 20-80
- 通用回退提取器建议使用优先级 90-100

### 设置优先级
```python
class MyExtractor(ExtractorPlugin):
    def __init__(self):
        super().__init__()
        self.priority = 20  # 在初始化时设置
        
# 或者动态修改
extractor = MyExtractor()
extractor.set_priority(15)
```

### 优先级示例
- 优先级 1-10：直接媒体链接处理器
- 优先级 11-30：专用网站提取器  
- 优先级 31-70：通用网站提取器
- 优先级 71-100：回退和通用处理器

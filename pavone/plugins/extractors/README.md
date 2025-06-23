# 提取器插件

这个文件夹包含所有与资源提取相关的插件类。提取器插件负责分析给定的URL并提取出可下载的资源列表，而不直接进行下载操作。

## 文件结构

- `base.py` - 包含 `ExtractorPlugin` 基类
- `mp4_direct.py` - MP4 直接链接提取器
- `m3u8_direct.py` - M3U8 直接链接提取器
- `missav_extractor.py` - MissAV 网站专用提取器
- `jtable.py` - JTable 网站专用提取器
- `__init__.py` - 导出所有提取器插件类

## 提取器插件基本概念

提取器插件的主要职责：
- 分析URL并确定是否能够处理
- 提取媒体资源的下载链接
- 收集媒体的元数据信息
- 创建操作项（`OperationItem`）以供执行管理器处理

提取器插件按优先级进行排序，优先级值越低优先级越高，当多个提取器能处理同一URL时，将使用优先级最高的提取器。

## 如何添加新的提取器

### 基本步骤

1. 在这个文件夹中创建新的 `.py` 文件
2. 继承 `ExtractorPlugin` 基类
3. 定义插件元数据常量（可选但推荐）
4. 实现必需的抽象方法
5. 在 `__init__.py` 中导出你的新插件类

### 必须实现的方法

每个提取器插件必须实现以下方法：

- `can_handle(url: str) -> bool`  
  检查插件是否能处理给定的URL

- `extract(url: str) -> List[OperationItem]`  
  提取URL中的资源并返回操作项列表
  
- `initialize() -> bool`  
  初始化插件（可以进行资源加载或验证）

- `execute(*args, **kwargs)`  
  执行插件功能（通常是调用extract方法）

### 定义插件元数据

推荐在插件文件开始处定义以下常量：

```python
# 定义插件名称和版本
PLUGIN_NAME = "MyExtractor"
PLUGIN_VERSION = "1.0.0"
PLUGIN_DESCRIPTION = "我的自定义提取器"
PLUGIN_AUTHOR = "Your Name"

# 定义插件优先级（越低优先级越高）
PLUGIN_PRIORITY = 50

# 定义支持的域名
SUPPORTED_DOMAINS = ["example.com", "www.example.com"]
```

## 最新提取器插件示例

下面是一个遵循当前最佳实践的提取器插件示例：

```python
from typing import List, Optional
from urllib.parse import urlparse
from .base import ExtractorPlugin
from ...models import OperationItem, Quality
from ...models import MovieMetadata
from ...utils.stringutils import StringUtils

# 定义插件元数据
PLUGIN_NAME = "MyCustomExtractor"
PLUGIN_VERSION = "1.0.0"
PLUGIN_DESCRIPTION = "我的自定义资源提取器"
PLUGIN_AUTHOR = "Your Name"
PLUGIN_PRIORITY = 50
SUPPORTED_DOMAINS = ["example.com", "www.example.com"]

class MyCustomExtractor(ExtractorPlugin):
    """
    自定义提取器的详细说明
    """
    def __init__(self):
        super().__init__(
            name=PLUGIN_NAME, 
            version=PLUGIN_VERSION, 
            description=PLUGIN_DESCRIPTION, 
            author=PLUGIN_AUTHOR, 
            priority=PLUGIN_PRIORITY
        )
    
    def initialize(self) -> bool:
        """初始化插件"""
        self.logger.info(f"{self.name} 初始化")
        return True
    
    def can_handle(self, url: str) -> bool:
        """
        判断是否能处理该URL
        
        Args:
            url: 要处理的URL
            
        Returns:
            能否处理
        """
        try:
            parsed_url = urlparse(url)
            return parsed_url.netloc.lower() in SUPPORTED_DOMAINS
        except:
            return False
    
    def extract(self, url: str) -> List[OperationItem]:
        """
        提取URL中的资源
        
        Args:
            url: 要提取资源的URL
            
        Returns:
            操作项列表
        """
        self.logger.info(f"从 {url} 提取资源")
        operations = []
        
        # 获取页面内容
        response = self.session.get(url, headers=self.headers)
        if response.status_code != 200:
            self.logger.error(f"获取页面失败: {response.status_code}")
            return operations
            
        # 创建元数据
        metadata = MovieMetadata()
        metadata.title = "示例视频"
        metadata.code = "ABC-123"
        metadata.set_source_site("Example")
        metadata.set_source_url(url)
        
        # 创建视频流操作项
        video_url = "https://example.com/video.mp4"
        stream_item = create_stream_item(
            url=video_url,
            filename="ABC-123.mp4",
            referrer=url,
            quality=Quality.FHD,
            metadata=metadata
        )
        operations.append(stream_item)
        
        # 创建封面图片操作项
        cover_url = "https://example.com/cover.jpg"
        cover_item = create_cover_item(
            url=cover_url,
            filename="ABC-123.jpg",
            referrer=url,
            metadata=metadata
        )
        operations.append(cover_item)
        
        # 创建元数据操作项
        metadata_item = create_metadata_item(
            metadata=metadata,
            filename="ABC-123.nfo"
        )
        operations.append(metadata_item)
        
        return operations
        
    def execute(self, *args, **kwargs):
        """
        执行插件功能
        
        Args:
            args: 位置参数，第一个参数通常是URL
            kwargs: 关键字参数
            
        Returns:
            操作项列表
        """
        if len(args) >= 1:
            return self.extract(args[0])
        return []
```

## 现有提取器插件

### 1. MP4DirectExtractor

直接处理MP4链接的提取器，能够获取直链视频资源。

### 2. M3U8DirectExtractor

处理M3U8流媒体链接的提取器，能够解析HLS流并提取片段。

### 3. MissAVExtractor

MissAV网站的专用提取器，能够从该网站获取视频资源和元数据。

### 4. JTableExtractor

JTable网站的专用提取器，能够从jp.jable.tv提取视频资源和元数据。

## 提取器插件的使用

提取器插件通过插件管理器进行注册和使用：

```python
from pavone.plugins import plugin_manager
from pavone.manager.execution import ExecutionManager

# 获取适合URL的提取器
extractor_plugin = plugin_manager.get_extractor_for_url("https://example.com/video/123")

if extractor_plugin:
    # 提取操作项
    operation_items = extractor_plugin.extract("https://example.com/video/123")
    
    # 使用执行管理器执行操作
    execution_manager = ExecutionManager()
    for item in operation_items:
        execution_manager.add_operation(item)
    
    # 执行所有操作
    execution_manager.execute_all()
```
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

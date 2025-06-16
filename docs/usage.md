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

# 下载并自动整理
pavone download "https://example.com/video.mp4" --organize
```

### 搜索视频

```bash
# 搜索关键词
pavone search "关键词"

# 在特定网站搜索
pavone search "关键词" --site javbus

# 按演员搜索
pavone search "演员名" --type actor
```

### 整理视频文件

```bash
# 整理指定目录
pavone organize "/path/to/videos"

# 按制作商整理
pavone organize "/path/to/videos" --by studio

# 按演员整理
pavone organize "/path/to/videos" --by actor

# 查找重复文件
pavone organize "/path/to/videos" --find-duplicates
```

## 高级功能

### 批量下载

创建包含URL列表的文件 `urls.txt`：
```
https://example1.com/video1.mp4
https://example2.com/video2.mp4
https://example3.com/video3.mp4
```

然后执行：
```bash
pavone download --batch urls.txt
```

### 自定义插件

PAVOne 支持插件扩展，你可以创建自己的提取器、元数据提取器或搜索插件。

#### 自动插件加载

PAVOne 的插件管理器提供了自动插件加载功能：

```python
from pavone.plugins.manager import plugin_manager

# 自动加载所有插件（内置 + 外部）
plugin_manager.load_plugins()

# 自动加载指定目录的插件
plugin_manager.load_plugins("/path/to/custom/plugins")
```

自动加载功能会：
1. **自动加载内置插件**：系统启动时自动加载所有内置提取器
2. **自动发现外部插件**：扫描插件目录并自动注册符合规范的插件类
3. **优先级管理**：根据插件优先级自动排序和选择

#### 插件优先级机制

提取器插件支持优先级设置，数值越小优先级越高：

```python
class MyCustomExtractor(ExtractorPlugin):
    def __init__(self):
        super().__init__()
        self.priority = 5  # 高优先级，将优先于内置插件（优先级 10）
        
    def can_handle(self, url: str) -> bool:
        return "mysite.com" in url
        
    def extract(self, url: str) -> List[DownloadOpt]:
        # 提取逻辑
        return [DownloadOpt(url=real_url, filename="video.mp4")]
```

#### 内置提取器

PAVOne 提供以下内置提取器：
- **MP4DirectExtractor** (优先级: 10) - 处理直接的 .mp4 链接
- **M3U8DirectExtractor** (优先级: 10) - 处理直接的 .m3u8 链接

#### 提取器使用

```python
from pavone.plugins.manager import plugin_manager

# 获取适合的提取器（最高优先级）
extractor = plugin_manager.get_extractor_for_url("https://example.com/video.mp4")
if extractor:
    options = extractor.extract(url)
    for opt in options:
        print(f"可下载: {opt.filename}")

# 获取所有匹配的提取器（按优先级排序）
all_extractors = plugin_manager.get_all_extractors_for_url(url)
for extractor in all_extractors:
    priority = getattr(extractor, 'priority', 'N/A')
    print(f"提取器: {extractor.name} (优先级: {priority})")
```

### 插件文件结构

提取器插件位于 `pavone/plugins/extractors/` 子文件夹中，这样可以更好地组织相关的插件类。

#### 创建自定义插件

要创建自定义提取器插件：

1. 继承 `ExtractorPlugin` 基类
2. 实现必需的方法：`initialize()`, `execute()`, `can_handle()`, `extract()`
3. 设置适当的优先级

示例提取器插件：
```python
from pavone.plugins.extractors.base import ExtractorPlugin
from pavone.core.downloader.options import DownloadOpt, LinkType
from typing import List, Any

class YouTubeExtractor(ExtractorPlugin):
    def __init__(self):
        super().__init__()
        self.name = "YouTubeExtractor"
        self.priority = 15  # 中等优先级
        self.description = "YouTube 视频提取器"
        
    def initialize(self) -> bool:
        """初始化插件，检查依赖项等"""
        return True
        
    def execute(self, *args, **kwargs) -> Any:
        """执行插件功能（委托给 extract 方法）"""
        if args:
            return self.extract(args[0])
        return []
        
    def can_handle(self, url: str) -> bool:
        """检查是否能处理该URL"""
        return "youtube.com" in url or "youtu.be" in url
        
    def extract(self, url: str) -> List[DownloadOpt]:
        """提取下载选项"""
        # 使用 yt-dlp 或其他工具提取真实下载链接
        return [
            DownloadOpt(
                url="https://real-video-url.mp4",
                filename="youtube_video.mp4",
                link_type=LinkType.VIDEO
            )
        ]
```

#### 插件管理

```python
from pavone.plugins.manager import plugin_manager

# 手动注册插件
extractor = YouTubeExtractor()
if extractor.initialize():
    plugin_manager.register_plugin(extractor)

# 注销插件
plugin_manager.unregister_plugin("YouTubeExtractor")

# 查看已注册的插件
for name, plugin in plugin_manager.plugins.items():
    print(f"插件: {name}")
```

参考 `examples/custom_extractors_example.py` 查看完整的自定义插件示例。

### 配置文件

配置文件位于 `~/.pavone/config.json`，详细配置说明请参考 [配置文档](config.md)。

## 故障排除

### 常见问题

1. **下载失败**
   - 检查网络连接
   - 检查代理设置
   - 查看错误日志

2. **元数据获取失败**
   - 确认网站可访问
   - 检查代理配置
   - 更新用户代理字符串

3. **文件整理问题**
   - 检查文件权限
   - 确认目录路径正确
   - 查看命名模式配置

### 日志调试

启用详细日志：
```bash
pavone --verbose download "url"
```

## 贡献

欢迎提交问题和贡献代码！请查看项目的 GitHub 仓库。

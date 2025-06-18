# DownloadManager 使用指南

## 概述

`DownloadManager` 是一个门面类，提供了统一的下载接口。它会自动：

1. 使用 `PluginManager` 的 `get_extractor_for_url` 方法查找合适的提取器
2. 提取对应的 `DownloadOpt` 列表
3. 要求用户进行选择（如果有多个选项）
4. 根据 `link_type` 判断调用 `M3U8Downloader` 或 `HTTPDownloader`

## 下载器选择规则

- **M3U8Downloader**: 仅适用于 `LinkType.STREAM` 类型
- **HTTPDownloader**: 适用于其他所有类型（VIDEO, IMAGE, SUBTITLE, METADATA等）

## 基本使用

### 1. 创建下载管理器

```python
from pavone.config.settings import DownloadConfig
from pavone.core.downloader import DownloadManager, create_download_manager

# 创建配置
config = DownloadConfig(
    output_dir="./downloads",
    max_concurrent_downloads=3,
    timeout=30
)

# 创建下载管理器
manager = create_download_manager(config)
```

### 2. 单个URL下载

```python
# 完整的下载流程（包含用户选择）
success = manager.download_from_url("https://example.com/video.mp4")

# 自动选择第一个选项（适用于自动化场景）
success = manager.download_from_url(
    "https://example.com/video.mp4", 
    auto_select=True
)
```

### 3. 手动选择下载选项

```python
# 1. 提取下载选项
options = manager.extract_download_options("https://example.com/video.mp4")

# 2. 显示选项让用户选择
selected = manager.select_download_option(options)

# 3. 下载选中的选项
success = manager.download_option(selected)
```

### 4. 批量下载

```python
urls = [
    "https://example.com/video1.mp4",
    "https://example.com/video2.mp4",
    "https://example.com/stream.m3u8"
]

results = manager.batch_download(urls, auto_select=True)

# 查看结果
for url, success in results:
    print(f"{url}: {'成功' if success else '失败'}")
```

### 5. 带进度回调的下载

```python
from pavone.core.downloader.progress import ProgressInfo

def progress_callback(progress: ProgressInfo):
    if progress.total_size > 0:
        percentage = progress.percentage
        print(f"\r进度: {percentage:.1f}% ({progress.downloaded}/{progress.total_size})", end="")

success = manager.download_from_url(
    "https://example.com/video.mp4",
    progress_callback=progress_callback
)
```

## API 参考

### DownloadManager 类

#### 构造函数

```python
DownloadManager(config: DownloadConfig, plugin_manager: Optional[PluginManager] = None)
```

- `config`: 下载配置
- `plugin_manager`: 可选的插件管理器实例

#### 主要方法

##### extract_download_options(url: str) -> List[DownloadOpt]
从URL提取下载选项列表。

- **参数**: `url` - 要处理的URL
- **返回**: 可用的下载选项列表
- **异常**: `ValueError` - 如果找不到合适的提取器

##### select_download_option(options: List[DownloadOpt]) -> DownloadOpt
让用户选择下载选项。

- **参数**: `options` - 可用的下载选项列表
- **返回**: 用户选择的下载选项
- **异常**: `ValueError` - 如果用户取消选择

##### get_downloader_for_option(option: DownloadOpt) -> Tuple[str, BaseDownloader]
根据下载选项选择合适的下载器。

- **参数**: `option` - 下载选项
- **返回**: (下载器类型, 下载器实例)

##### download_from_url(url: str, progress_callback: Optional[ProgressCallback] = None, auto_select: bool = False) -> bool
完整的下载流程。

- **参数**:
  - `url` - 要下载的URL
  - `progress_callback` - 进度回调函数
  - `auto_select` - 是否自动选择第一个选项
- **返回**: 下载是否成功

##### download_option(option: DownloadOpt, progress_callback: Optional[ProgressCallback] = None) -> bool
直接下载指定的选项。

- **参数**:
  - `option` - 要下载的选项
  - `progress_callback` - 进度回调函数
- **返回**: 下载是否成功

##### batch_download(urls: List[str], progress_callback: Optional[ProgressCallback] = None, auto_select: bool = True) -> List[Tuple[str, bool]]
批量下载多个URL。

- **参数**:
  - `urls` - URL列表
  - `progress_callback` - 进度回调函数
  - `auto_select` - 是否自动选择第一个选项
- **返回**: (URL, 成功状态) 的列表

## 使用场景

### 场景1: 命令行工具

```python
def main():
    import sys
    if len(sys.argv) < 2:
        print("用法: python script.py <URL>")
        return
    
    config = DownloadConfig()
    manager = create_download_manager(config)
    
    url = sys.argv[1]
    success = manager.download_from_url(url)
    
    if success:
        print("下载成功!")
    else:
        print("下载失败!")

if __name__ == "__main__":
    main()
```

### 场景2: GUI应用程序

```python
class DownloadApp:
    def __init__(self):
        self.config = DownloadConfig()
        self.manager = create_download_manager(self.config)
    
    def start_download(self, url: str):
        try:
            # 提取选项
            options = self.manager.extract_download_options(url)
            
            # 显示选项给用户选择（GUI界面）
            selected_option = self.show_options_dialog(options)
            
            # 开始下载
            success = self.manager.download_option(
                selected_option, 
                self.update_progress
            )
            
            self.show_result(success)
            
        except Exception as e:
            print(f"下载失败: {e}")
    
    def update_progress(self, progress):
        # 更新GUI进度条
        pass
```

### 场景3: Web服务

```python
from flask import Flask, request, jsonify

app = Flask(__name__)
manager = create_download_manager(DownloadConfig())

@app.route('/download', methods=['POST'])
def download():
    url = request.json.get('url')
    if not url:
        return jsonify({'error': '缺少URL参数'}), 400
    
    try:
        # 提取选项
        options = manager.extract_download_options(url)
        
        # 返回选项给前端
        return jsonify({
            'options': [
                {
                    'id': i,
                    'display_name': opt.get_display_name(),
                    'quality': opt.get_quality_info(),
                    'description': opt.get_full_description()
                }
                for i, opt in enumerate(options)
            ]
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@app.route('/download/<int:option_id>', methods=['POST'])
def download_option(option_id):
    # 实现下载指定选项的逻辑
    pass
```

## 错误处理

### 常见异常

- `ValueError`: 
  - 找不到合适的提取器
  - 提取器没有找到下载选项
  - 用户取消选择
- `ImportError`: 缺少必要的依赖
- `ConnectionError`: 网络连接问题
- `TimeoutError`: 请求超时

### 错误处理示例

```python
try:
    success = manager.download_from_url(url)
except ValueError as e:
    if "用户取消" in str(e):
        print("用户取消了下载")
    else:
        print(f"配置错误: {e}")
except ConnectionError:
    print("网络连接失败，请检查网络设置")
except TimeoutError:
    print("请求超时，请稍后重试")
except Exception as e:
    print(f"未知错误: {e}")
```

## 扩展和自定义

### 自定义提取器

要让DownloadManager支持新的网站，只需要创建自定义提取器并确保它被插件管理器加载：

```python
from pavone.plugins.extractors.base import ExtractorPlugin
from pavone.core.downloader.options import DownloadOpt, LinkType

class CustomExtractor(ExtractorPlugin):
    def can_handle(self, url: str) -> bool:
        return "mysite.com" in url
    
    def extract(self, url: str) -> List[DownloadOpt]:
        # 实现提取逻辑
        return [
            DownloadOpt(
                url="https://mysite.com/video.mp4",
                display_name="自定义视频",
                quality="1080p",
                link_type=LinkType.VIDEO
            )
        ]
```

### 自定义进度回调

```python
def custom_progress_callback(progress: ProgressInfo):
    # 自定义进度显示逻辑
    if progress.total_size > 0:
        print(f"已下载: {progress.percentage:.1f}%")
        print(f"速度: {progress.speed/1024:.1f} KB/s")
        if progress.remaining_time < float('inf'):
            print(f"剩余时间: {progress.remaining_time:.0f}秒")
```

这个下载管理器提供了一个简洁而强大的接口，使得下载各种类型的内容变得非常简单。

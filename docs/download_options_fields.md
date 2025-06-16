# DownloadOpt 新增字段说明

## 概述

在 `DownloadOpt` 类中新增了两个字段：`display_name` 和 `quality`，用于改善当extractor返回多个下载选项时的用户体验。

## 新增字段

### display_name (str, 可选)
- **用途**: 提供一个用户友好的显示名称，用于在用户选择下载选项时显示
- **默认值**: None
- **回退机制**: 如果未设置，`get_display_name()` 方法会依次尝试使用 `filename` 或 `url`

### quality (str, 可选)
- **用途**: 描述下载选项的质量信息，如分辨率、清晰度、格式等
- **默认值**: None
- **常见值**: "1080p", "720p", "480p", "高清", "标清", "音频", "原画质" 等

## 使用示例

### 基本用法

```python
from pavone.core.downloader.options import DownloadOpt

# 创建带有显示名称和质量的下载选项
opt = DownloadOpt(
    url="https://example.com/video.mp4",
    filename="video.mp4",
    display_name="示例视频",
    quality="1080p"
)

# 获取显示名称
print(opt.get_display_name())  # 输出: 示例视频

# 获取质量信息
print(opt.get_quality_info())  # 输出: 1080p

# 获取完整描述
print(opt.get_full_description())  # 输出: 未指定类型 | 质量: 1080p | 名称: 示例视频
```

### 在提取器中使用

```python
from pavone.plugins.extractors.base import ExtractorPlugin
from pavone.core.downloader.options import DownloadOpt, LinkType

class CustomExtractor(ExtractorPlugin):
    def extract(self, url: str) -> List[DownloadOpt]:
        # 返回多个质量选项供用户选择
        return [
            DownloadOpt(
                url="https://example.com/video_1080p.mp4",
                filename="video_1080p.mp4",
                link_type=LinkType.VIDEO,
                display_name="高清视频",
                quality="1080p"
            ),
            DownloadOpt(
                url="https://example.com/video_720p.mp4",
                filename="video_720p.mp4",
                link_type=LinkType.VIDEO,
                display_name="标清视频",
                quality="720p"
            ),
            DownloadOpt(
                url="https://example.com/audio.m4a",
                filename="audio.m4a",
                link_type=LinkType.OTHER,
                display_name="音频文件",
                quality="音频"
            )
        ]
```

### 使用便利函数

```python
from pavone.core.downloader.options import create_download_opt, LinkType

# 使用 create_download_opt 函数创建
opt = create_download_opt(
    url="https://example.com/video.mp4",
    filename="video.mp4",
    link_type=LinkType.VIDEO,
    display_name="示例视频",
    quality="1080p",
    Authorization="Bearer token"  # 自定义头部
)
```

## 新增的方法

### get_display_name() -> str
返回显示名称，按以下优先级：
1. `display_name` 字段（如果设置）
2. `filename` 字段（如果设置）
3. `url` 字段

### get_quality_info() -> Optional[str]
返回质量信息，如果未设置则返回 None。

### get_full_description() -> str
返回包含类型、质量和显示名称的完整描述，格式为：
`类型 | 质量: xxx | 名称: xxx`

## 向后兼容性

- 所有新字段都是可选的，现有代码无需修改即可继续工作
- 现有的 `DownloadOpt` 初始化不会被影响
- `create_download_opt` 函数的现有参数顺序保持不变

## 最佳实践

1. **显示名称**: 使用描述性的名称，帮助用户识别内容
2. **质量信息**: 使用标准化的质量描述，如 "1080p", "720p" 等
3. **多选项**: 当提取器能提供多种质量或格式时，为每个选项设置明确的显示名称和质量信息
4. **一致性**: 在同一个提取器中保持命名风格的一致性

## 示例场景

### 场景1: 视频网站多清晰度
```python
# YouTube提取器返回多个清晰度选项
[
    DownloadOpt(url="...", display_name="YouTube视频 - 标题", quality="1080p"),
    DownloadOpt(url="...", display_name="YouTube视频 - 标题", quality="720p"),
    DownloadOpt(url="...", display_name="YouTube视频 - 标题", quality="480p")
]
```

### 场景2: 不同格式选项
```python
# Bilibili提取器返回视频和音频选项
[
    DownloadOpt(url="...", display_name="Bilibili视频", quality="1080p"),
    DownloadOpt(url="...", display_name="Bilibili音频", quality="音频"),
    DownloadOpt(url="...", display_name="Bilibili字幕", quality="字幕")
]
```

这些改进使得用户在面对多个下载选项时能够更好地理解和选择合适的内容。

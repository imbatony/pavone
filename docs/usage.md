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

PAVOne 支持插件扩展，你可以创建自己的下载器、元数据提取器或搜索插件。

示例插件结构：
```python
from pavone.plugins.base import DownloaderPlugin

class MyDownloader(DownloaderPlugin):
    def can_handle(self, url: str) -> bool:
        return "mysite.com" in url
    
    def download(self, url: str, output_dir: str) -> bool:
        # 实现下载逻辑
        pass
```

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

"""
示例：自定义提取器插件

这个文件展示了如何创建自定义提取器插件，并演示插件系统的自动发现功能。
"""

from typing import List, Any
from pavone.core.downloader.options import DownloadOpt, LinkType
from pavone.plugins.extractors.base import ExtractorPlugin


class CustomYouTubeExtractor(ExtractorPlugin):
    """自定义 YouTube 提取器示例"""
    
    def __init__(self):
        super().__init__()
        self.name = "CustomYouTubeExtractor"
        self.priority = 20  # 较低优先级
        self.description = "自定义 YouTube 视频提取器"
    
    def initialize(self) -> bool:
        """初始化插件"""
        return True
    
    def execute(self, *args, **kwargs) -> Any:
        """执行插件功能（这里委托给 extract 方法）"""
        if args:
            return self.extract(args[0])
        return []    
    def can_handle(self, url: str) -> bool:
        """检查是否能处理该URL"""
        return "youtube.com" in url or "youtu.be" in url
    
    def extract(self, url: str) -> List[DownloadOpt]:
        """提取下载选项"""
        # 这里只是示例，实际实现需要调用 yt-dlp 等工具
        # 模拟YouTube返回多个质量选项
        video_id = url.split("v=")[-1] if "v=" in url else "video"
        return [
            DownloadOpt(
                url="https://example.com/extracted_video_1080p.mp4",
                filename=f"{video_id}_1080p.mp4",
                link_type=LinkType.VIDEO,
                display_name=f"YouTube视频 - {video_id}",
                quality="1080p"
            ),
            DownloadOpt(
                url="https://example.com/extracted_video_720p.mp4",
                filename=f"{video_id}_720p.mp4",
                link_type=LinkType.VIDEO,
                display_name=f"YouTube视频 - {video_id}",
                quality="720p"
            ),
            DownloadOpt(
                url="https://example.com/extracted_video_480p.mp4",
                filename=f"{video_id}_480p.mp4",
                link_type=LinkType.VIDEO,
                display_name=f"YouTube视频 - {video_id}",
                quality="480p"
            )
        ]


class CustomBilibiliExtractor(ExtractorPlugin):
    """自定义 Bilibili 提取器示例"""
    
    def __init__(self):
        super().__init__()
        self.name = "CustomBilibiliExtractor"
        self.priority = 15  # 中等优先级
        self.description = "自定义 Bilibili 视频提取器"
    
    def initialize(self) -> bool:
        """初始化插件"""
        return True
    
    def execute(self, *args, **kwargs) -> Any:
        """执行插件功能（这里委托给 extract 方法）"""
        if args:
            return self.extract(args[0])
        return []    
    def can_handle(self, url: str) -> bool:
        """检查是否能处理该URL"""
        return "bilibili.com" in url
    
    def extract(self, url: str) -> List[DownloadOpt]:
        """提取下载选项"""
        # 这里只是示例，实际实现需要调用相应的API
        # 模拟Bilibili返回多个质量和格式选项
        video_id = url.split("/")[-1] if "/" in url else "BV123456"
        return [
            DownloadOpt(
                url="https://example.com/extracted_bilibili_video_1080p.mp4",
                filename=f"{video_id}_1080p.mp4",
                link_type=LinkType.VIDEO,
                display_name=f"Bilibili视频 - {video_id}",
                quality="1080p 高清"
            ),
            DownloadOpt(
                url="https://example.com/extracted_bilibili_video_720p.mp4",
                filename=f"{video_id}_720p.mp4",
                link_type=LinkType.VIDEO,
                display_name=f"Bilibili视频 - {video_id}",
                quality="720p 清晰"
            ),
            DownloadOpt(
                url="https://example.com/extracted_bilibili_audio.m4a",
                filename=f"{video_id}_audio.m4a",
                link_type=LinkType.OTHER,
                display_name=f"Bilibili音频 - {video_id}",
                quality="音频"
            )
        ]


class HighPriorityMp4Extractor(ExtractorPlugin):
    """高优先级 MP4 提取器示例"""
    
    def __init__(self):
        super().__init__()
        self.name = "HighPriorityMp4Extractor"
        self.priority = 5  # 高优先级，会排在内置提取器前面
        self.description = "高优先级 MP4 直链提取器"
    
    def initialize(self) -> bool:
        """初始化插件"""
        return True
    
    def execute(self, *args, **kwargs) -> Any:
        """执行插件功能（这里委托给 extract 方法）"""
        if args:
            return self.extract(args[0])
        return []    
    def can_handle(self, url: str) -> bool:
        """检查是否能处理该URL"""
        return url.endswith('.mp4')
    
    def extract(self, url: str) -> List[DownloadOpt]:
        """提取下载选项"""
        # 提供额外的处理逻辑，比如添加更多的质量选项
        filename = url.split('/')[-1]
        base_name = filename.rsplit('.', 1)[0] if '.' in filename else filename
        
        # 提供多个处理选项
        options = [
            DownloadOpt(
                url=url,
                filename=filename,
                link_type=LinkType.VIDEO,
                display_name=f"原始文件 - {base_name}",
                quality="原画质"
            ),
            DownloadOpt(
                url=url,
                filename=f"720p_{filename}",
                link_type=LinkType.VIDEO,
                custom_headers={"Quality": "720p"},
                display_name=f"720p版本 - {base_name}",
                quality="720p"
            ),
            DownloadOpt(
                url=url,
                filename=f"480p_{filename}",
                link_type=LinkType.VIDEO,
                custom_headers={"Quality": "480p"},
                display_name=f"480p版本 - {base_name}",
                quality="480p"
            )
        ]
        
        return options


if __name__ == "__main__":
    # 演示插件使用
    print("=== 自定义插件演示 ===")
    
    # 创建插件实例
    youtube_extractor = CustomYouTubeExtractor()
    bilibili_extractor = CustomBilibiliExtractor()
    high_priority_extractor = HighPriorityMp4Extractor()
    
    # 初始化插件
    extractors = [youtube_extractor, bilibili_extractor, high_priority_extractor]
    for extractor in extractors:
        if not extractor.initialize():
            print(f"插件 {extractor.name} 初始化失败")
            continue
      # 测试URL
    test_urls = [
        "https://youtube.com/watch?v=abc123",
        "https://bilibili.com/video/BV123456",
        "https://example.com/video.mp4"
    ]
    
    for url in test_urls:
        print(f"\n测试URL: {url}")
        for extractor in extractors:
            if extractor.can_handle(url):
                options = extractor.extract(url)
                print(f"  {extractor.name} (优先级: {extractor.priority}) 找到 {len(options)} 个选项:")
                for i, opt in enumerate(options, 1):
                    print(f"    {i}. {opt.get_full_description()}")
                    print(f"       - 显示名称: {opt.get_display_name()}")
                    print(f"       - 质量: {opt.get_quality_info() or '未指定'}")
                    print(f"       - 文件名: {opt.filename}")

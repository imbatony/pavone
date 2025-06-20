"""
MP4 直接链接提取器
处理以 .mp4 结尾的直接视频链接
"""

from typing import List
from urllib.parse import urlparse
from pathlib import Path
from .base import ExtractorPlugin
from ...core.downloader.options import DownloadOpt, LinkType


class MP4DirectExtractor(ExtractorPlugin):
    """MP4 直接链接提取器    
    处理以 .mp4 结尾的直接视频链接，无需额外解析网站内容
    """
    
    def __init__(self):
        super().__init__()
        self.name = "MP4DirectExtractor"
        self.version = "1.0.0"
        self.description = "处理 .mp4 直接链接的提取器"
        self.author = "PAVOne Team"
        self.priority = 10  # 高优先级，因为是直接链接
    
    def initialize(self) -> bool:
        """初始化插件"""
        return True
    
    def execute(self, *args, **kwargs):
        """执行插件功能"""
        if len(args) >= 1:
            return self.extract(args[0])
        return []
    
    def can_handle(self, url: str) -> bool:
        """检查是否能处理该URL"""
        try:
            parsed_url = urlparse(url)
            path = parsed_url.path.lower()
            return path.endswith('.mp4')
        except Exception:
            return False
    
    def extract(self, url: str) -> List[DownloadOpt]:
        """从 MP4 直接链接提取下载选项"""
        try:
            parsed_url = urlparse(url)
            
            # 从URL路径中提取文件名
            filename = Path(parsed_url.path).name
            if not filename or not filename.endswith('.mp4'):
                filename = "video.mp4"            # 创建下载选项
            download_opt = DownloadOpt(
                url=url,
                filename=filename,
                custom_headers={
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                    "Accept": "video/mp4,video/*;q=0.9,*/*;q=0.8"
                },
                link_type=LinkType.VIDEO,
                display_name=f"MP4视频 - {Path(filename).stem}",
                quality="原画质"            )
            
            return [download_opt]
            
        except Exception as e:
            self.logger.error(f"MP4提取器错误: {e}")
            return []

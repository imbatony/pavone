"""
M3U8 直接链接提取器
处理以 .m3u8 结尾的直接播放列表链接
"""

from typing import List
from urllib.parse import urlparse
from pathlib import Path
from .base import ExtractorPlugin
from ...core.downloader.options import DownloadOpt, LinkType
from ...config.logging_config import get_logger


class M3U8DirectExtractor(ExtractorPlugin):
    """M3U8 直接链接提取器    
    处理以 .m3u8 结尾的直接播放列表链接，无需额外解析网站内容
    """
    
    def __init__(self):
        super().__init__()
        self.name = "M3U8DirectExtractor"
        self.version = "1.0.0"
        self.description = "处理 .m3u8 直接链接的提取器"
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
            return path.endswith('.m3u8')
        except Exception:
            return False
    
    def extract(self, url: str) -> List[DownloadOpt]:
        """从 M3U8 直接链接提取下载选项"""
        try:
            parsed_url = urlparse(url)
            
            # 从URL路径中提取文件名（去掉.m3u8扩展名，改为.mp4）
            path_name = Path(parsed_url.path).stem
            if not path_name:
                path_name = "video"
            filename = f"{path_name}.mp4"            # 创建下载选项
            download_opt = DownloadOpt(
                url=url,
                filename=filename,
                custom_headers={
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                    "Accept": "application/vnd.apple.mpegurl,application/x-mpegurl,video/*;q=0.9,*/*;q=0.8"
                },
                link_type=LinkType.STREAM,
                display_name=f"M3U8流媒体 - {path_name}",                quality="流媒体"
            )
            
            return [download_opt]
            
        except Exception as e:
            logger = get_logger(__name__)
            logger.error(f"M3U8提取器错误: {e}")
            return []

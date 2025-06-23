"""
MP4 直接链接提取器
处理以 .mp4 结尾的直接视频链接
"""

from datetime import datetime
from typing import List
from urllib.parse import urlparse
from pathlib import Path
from .base import ExtractorPlugin
from ...models import OpertionItem, Quality, create_video_item
from ...config.settings import get_download_config

# 定义插件名称和版本
PLUGIN_NAME = "MP4DirectExtractor"
PLUGIN_VERSION = "1.0.0"
PLUGIN_DESCRIPTION = "提取 MP4 直接链接的插件"
PLUGIN_AUTHOR = "PAVOne"
# 定义插件优先级
# 低优先级，无法确定是否一定为视频, 优先使用其他提取器
PLUGIN_PRIORITY = 999

SITE_NAME = "Unknown"


class MP4DirectExtractor(ExtractorPlugin):
    """
    MP4 直接链接提取器
    处理以 .mp4 结尾的直接视频链接，无需额外解析网站内容
    """

    def __init__(self):
        super().__init__()
        self.name = PLUGIN_NAME
        self.version = PLUGIN_VERSION
        self.description = PLUGIN_DESCRIPTION
        self.author = PLUGIN_AUTHOR
        self.priority = PLUGIN_PRIORITY
        self.download_config = get_download_config()

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
            return path.endswith(".mp4")
        except Exception:
            return False

    def extract(self, url: str) -> List[OpertionItem]:
        """从 MP4 直接链接提取下载选项"""
        try:
            parsed_url = urlparse(url)

            # 从URL路径中提取文件名
            title = Path(parsed_url.path).name
            if not title:
                title = "video-" + str(datetime.now().timestamp())

            quality = Quality.guess(url)
            # 创建下载选项
            download_opt = create_video_item(
                url=url,
                site=SITE_NAME,
                title=f"{title}",
                quality=quality,
                custom_headers={"Accept": "video/mp4,video/*;q=0.9,*/*;q=0.8"},
            )
            return [download_opt]

        except Exception as e:
            self.logger.error(f"MP4提取器错误: {e}")
            return []

"""
元数据提取器插件基类
"""

from abc import abstractmethod
from typing import List, Optional

from ...models import BaseMetadata
from ..base import BasePlugin


class MetadataPlugin(BasePlugin):
    """元数据提取器插件基类

    元数据提取器插件负责从指定的identifier中提取元数据，
    包括视频代码、标题、演员、导演、发行日期等信息。
    """

    def __init__(
        self,
        name: Optional[str] = None,
        version: Optional[str] = "1.0.0",
        description: Optional[str] = "",
        author: Optional[str] = "",
        priority: Optional[int] = 50,
    ):
        super().__init__(
            name=name,
            version=version,
            description=description,
            author=author,
            priority=priority,
        )

    def initialize(self) -> bool:
        """初始化插件"""
        self.logger.info(f"初始化 {self.name} 插件")
        return True

    @abstractmethod
    def can_extract(self, identifier: str) -> bool:
        """检查是否能处理该identifier

        Args:
            identifier: 可以是URL、视频代码等标识符

        Returns:
            如果能处理返回True，否则返回False
        """
        pass

    @abstractmethod
    def extract_metadata(self, identifier: str) -> Optional[BaseMetadata]:
        """从给定的identifier提取元数据

        Args:
            identifier: 可以是URL、视频代码等标识符

        Returns:
            提取到的元数据对象，如果失败返回None
        """
        pass

    def select_portrait_image(self, image_urls: List[str], timeout: int = 15) -> Optional[str]:
        """从多张图片中选择一张竖图（宽度<高度）

        依次检查给定的图片URL列表，返回第一张宽度小于高度的图片URL。
        如果都不满足则返回None。

        Args:
            image_urls: 图片URL列表
            timeout: 请求超时时间（秒）

        Returns:
            竖图的URL，如果没有则返回None
        """
        import io

        from PIL import Image

        for url in image_urls:
            try:
                resp = self.fetch(url, timeout=timeout, no_exceptions=True)
                if resp.status_code != 200:
                    continue
                img = Image.open(io.BytesIO(resp.content))
                width, height = img.size
                if width < height:
                    self.logger.debug(f"选择竖图: {url} ({width}x{height})")
                    return url
            except Exception:
                continue
        self.logger.debug("未找到竖图")
        return None

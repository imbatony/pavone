"""
下载进度相关模块
"""

from typing import Callable


class ProgressInfo:
    """下载进度信息"""

    def __init__(self, total_size: int = 0, downloaded: int = 0, speed: float = 0.0):
        self.total_size = total_size  # 总大小（字节）
        self.downloaded = downloaded  # 已下载大小（字节）
        self.speed = speed  # 下载速度（字节/秒）

    @property
    def percentage(self) -> float:
        """下载百分比"""
        if self.total_size <= 0:
            return 0.0
        return (self.downloaded / self.total_size) * 100

    @property
    def remaining_time(self) -> float:
        """预计剩余时间（秒）"""
        if self.speed <= 0:
            return float("inf")
        remaining_bytes = self.total_size - self.downloaded
        return remaining_bytes / self.speed


# 进度回调函数类型
ProgressCallback = Callable[[ProgressInfo], None]

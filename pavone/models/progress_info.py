"""
下载进度相关模块
"""

from dataclasses import dataclass
from typing import Callable, Optional


class ProgressInfo:
    """下载进度信息"""

    def __init__(
        self,
        total_size: int = 0,
        downloaded: int = 0,
        speed: float = 0.0,
        status_message: str = "",
        total_segments: int = 0,
        completed_segments: int = 0,
        segment_speed: float = 0.0,
    ):
        self.total_size = total_size  # 总大小（字节）
        self.downloaded = downloaded  # 已下载大小（字节）
        self.speed = speed  # 下载速度（字节/秒）
        self.status_message = status_message  # 状态消息（用于显示当前操作状态）
        self.total_segments = total_segments  # M3U8 总分片数
        self.completed_segments = completed_segments  # M3U8 已完成分片数
        self.segment_speed = segment_speed  # M3U8 分片下载速度（分片/秒）

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


@dataclass
class SegmentResult:
    """M3U8 分片下载结果"""

    index: int
    success: bool
    error_message: Optional[str] = None

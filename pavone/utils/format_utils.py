"""
格式化工具类

提供通用的格式化功能
"""


class FormatUtils:
    """格式化工具类"""

    @staticmethod
    def format_size(bytes_size: int) -> str:
        """
        格式化文件大小

        Args:
            bytes_size: 字节大小

        Returns:
            格式化后的字符串，如 "1.23 MB"
        """
        size = float(bytes_size)
        for unit in ["B", "KB", "MB", "GB"]:
            if size < 1024:
                return f"{size:.2f} {unit}"
            size /= 1024
        return f"{size:.2f} TB"

    @staticmethod
    def format_bitrate(bitrate: int) -> str:
        """
        格式化比特率

        Args:
            bitrate: 比特率（bps）

        Returns:
            格式化后的字符串，如 "5 Mbps"，如果为0则返回"未知"
        """
        if bitrate == 0:
            return "未知"
        return f"{bitrate // 1000000} Mbps"

"""
下载选项相关模块
"""

from typing import Optional, Dict


class DownloadOpt:
    """下载选项类"""
    
    def __init__(self, url: str, filename: Optional[str] = None, 
                 custom_headers: Optional[Dict[str, str]] = None):
        self.url = url
        self.filename = filename
        self.custom_headers = custom_headers or {}
    
    def get_effective_headers(self, default_headers: Optional[Dict[str, str]] = None) -> Dict[str, str]:
        """获取有效的HTTP头部，合并默认头部和自定义头部"""
        headers = default_headers.copy() if default_headers else {}
        headers.update(self.custom_headers)
        return headers


def create_download_opt(url: str, filename: Optional[str] = None, **headers) -> DownloadOpt:
    """
    便利的DownloadOpt创建函数
    
    Args:
        url: 下载URL
        filename: 可选的文件名
        **headers: 自定义HTTP头部作为关键字参数
    
    Returns:
        DownloadOpt: 配置好的下载选项
    """
    return DownloadOpt(url, filename, headers)

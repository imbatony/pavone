"""
下载选项相关模块
"""

from typing import Optional, Dict


# 常用链接类型常量
class LinkType:
    """链接类型常量"""
    VIDEO = "video"          # 视频文件
    IMAGE = "image"          # 图片文件（封面、截图等）
    SUBTITLE = "subtitle"    # 字幕文件
    METADATA = "metadata"    # 元数据文件（NFO等）
    THUMBNAIL = "thumbnail"  # 缩略图
    COVER = "cover"         # 封面图
    TORRENT = "torrent"     # 种子文件
    STREAM = "stream"       # 流媒体
    OTHER = "other"         # 其他类型


class DownloadOpt:
    """下载选项类"""
    
    def __init__(self, url: str, filename: Optional[str] = None, 
                 custom_headers: Optional[Dict[str, str]] = None,
                 link_type: Optional[str] = None,
                 display_name: Optional[str] = None,
                 quality: Optional[str] = None):
        self.url = url
        self.filename = filename
        self.custom_headers = custom_headers or {}
        self.link_type = link_type
        self.display_name = display_name
        self.quality = quality
    
    def get_effective_headers(self, default_headers: Optional[Dict[str, str]] = None) -> Dict[str, str]:
        """获取有效的HTTP头部，合并默认头部和自定义头部"""
        headers = default_headers.copy() if default_headers else {}
        headers.update(self.custom_headers)
        return headers
    
    def is_video(self) -> bool:
        """判断是否为视频类型链接"""
        return self.link_type == LinkType.VIDEO
    
    def is_image(self) -> bool:
        """判断是否为图片类型链接"""
        return self.link_type in (LinkType.IMAGE, LinkType.COVER, LinkType.THUMBNAIL)
    
    def is_metadata(self) -> bool:
        """判断是否为元数据类型链接"""
        return self.link_type in (LinkType.METADATA, LinkType.SUBTITLE)
    
    def is_stream(self) -> bool:
        """判断是否为流媒体类型链接"""
        return self.link_type == LinkType.STREAM
    
    def get_type_description(self) -> str:
        """获取链接类型的描述"""
        if self.link_type is None:
            return "未指定类型"
            
        type_descriptions = {
            LinkType.VIDEO: "视频文件",
            LinkType.IMAGE: "图片文件", 
            LinkType.SUBTITLE: "字幕文件",
            LinkType.METADATA: "元数据文件",
            LinkType.THUMBNAIL: "缩略图",
            LinkType.COVER: "封面图",
            LinkType.TORRENT: "种子文件",
            LinkType.STREAM: "流媒体",
            LinkType.OTHER: "其他文件"
        }
        return type_descriptions.get(self.link_type, "未知类型")
    
    def get_display_name(self) -> str:
        """获取显示名称，如果未设置则返回文件名或URL"""
        if self.display_name:
            return self.display_name
        if self.filename:
            return self.filename
        return self.url
    
    def get_quality_info(self) -> Optional[str]:
        """获取质量信息"""
        return self.quality
    
    def get_full_description(self) -> str:
        """获取包含类型、质量和显示名称的完整描述"""
        parts = []
        
        # 添加类型描述
        parts.append(self.get_type_description())
        
        # 添加质量信息
        if self.quality:
            parts.append(f"质量: {self.quality}")
        
        # 添加显示名称
        display_name = self.get_display_name()
        if display_name and display_name not in (self.url, ""):
            parts.append(f"名称: {display_name}")
        
        return " | ".join(parts)


def create_download_opt(url: str, filename: Optional[str] = None, 
                       link_type: Optional[str] = None,
                       display_name: Optional[str] = None,
                       quality: Optional[str] = None, **headers) -> DownloadOpt:
    """
    便利的DownloadOpt创建函数
    
    Args:
        url: 下载URL
        filename: 可选的文件名
        link_type: 可选的链接类型（如 'video', 'image', 'subtitle', 'metadata', 'stream'等）
        display_name: 可选的显示名称，用于用户选择时显示
        quality: 可选的质量信息，如 '1080p', '720p', '高清', '标清' 等
        **headers: 自定义HTTP头部作为关键字参数
    
    Returns:
        DownloadOpt: 配置好的下载选项
    """
    return DownloadOpt(url, filename, headers, link_type, display_name, quality)

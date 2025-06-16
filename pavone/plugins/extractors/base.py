"""
提取器插件基类
"""

from abc import abstractmethod
from typing import List
from ..base import BasePlugin
from ...core.downloader.options import DownloadOpt


class ExtractorPlugin(BasePlugin):
    """提取器插件基类
    
    提取器插件负责分析给定的URL并提取出可下载的资源列表，
    而不直接进行下载操作
    """
    
    def __init__(self):
        super().__init__()
        self.priority = 50  # 默认优先级，数值越小优先级越高
    
    @property
    def priority_level(self) -> int:
        """获取插件优先级
        
        Returns:
            优先级数值，越小优先级越高
        """
        return self.priority
    
    def set_priority(self, priority: int):
        """设置插件优先级
        
        Args:
            priority: 优先级数值，越小优先级越高
        """
        self.priority = priority
    
    @abstractmethod
    def can_handle(self, url: str) -> bool:
        """检查是否能处理该URL"""
        pass
    
    @abstractmethod
    def extract(self, url: str) -> List[DownloadOpt]:
        """从URL中提取下载选项列表
        
        Args:
            url: 要分析的URL
            
        Returns:
            包含所有可下载资源的DownloadOpt列表
        """
        pass

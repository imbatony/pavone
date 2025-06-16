"""
插件基类和插件管理器
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from pathlib import Path


class BasePlugin(ABC):
    """插件基类"""
    
    def __init__(self):
        self.name = self.__class__.__name__
        self.version = "1.0.0"
        self.description = ""
        self.author = ""
    
    @abstractmethod
    def initialize(self) -> bool:
        """初始化插件"""
        pass
    
    @abstractmethod
    def execute(self, *args, **kwargs) -> Any:
        """执行插件功能"""
        pass
    
    def cleanup(self):
        """清理插件资源"""
        pass


class DownloaderPlugin(BasePlugin):
    """下载器插件基类"""
    
    @abstractmethod
    def can_handle(self, url: str) -> bool:
        """检查是否能处理该URL"""
        pass
    
    @abstractmethod
    def download(self, url: str, output_dir: str) -> bool:
        """下载视频"""
        pass


class MetadataPlugin(BasePlugin):
    """元数据插件基类"""
    
    @abstractmethod
    def can_extract(self, identifier: str) -> bool:
        """检查是否能提取该标识符的元数据"""
        pass
    
    @abstractmethod
    def extract_metadata(self, identifier: str) -> Dict[str, Any]:
        """提取元数据"""
        pass


class SearchPlugin(BasePlugin):
    """搜索插件基类"""
    
    @abstractmethod
    def search(self, keyword: str, limit: int = 20) -> List[Dict[str, Any]]:
        """搜索功能"""
        pass


class PluginManager:
    """插件管理器"""
    
    def __init__(self):
        self.plugins: Dict[str, BasePlugin] = {}
        self.downloader_plugins: List[DownloaderPlugin] = []
        self.metadata_plugins: List[MetadataPlugin] = []
        self.search_plugins: List[SearchPlugin] = []
    
    def load_plugins(self, plugin_dir: Optional[str] = None):
        """加载插件"""
        if plugin_dir is None:
            plugin_dir = str(Path(__file__).parent)
        
        # TODO: 实现插件自动发现和加载
        pass
    
    def register_plugin(self, plugin: BasePlugin):
        """注册插件"""
        if plugin.initialize():
            self.plugins[plugin.name] = plugin
            
            if isinstance(plugin, DownloaderPlugin):
                self.downloader_plugins.append(plugin)
            elif isinstance(plugin, MetadataPlugin):
                self.metadata_plugins.append(plugin)
            elif isinstance(plugin, SearchPlugin):
                self.search_plugins.append(plugin)
    
    def unregister_plugin(self, plugin_name: str):
        """注销插件"""
        if plugin_name in self.plugins:
            plugin = self.plugins[plugin_name]
            plugin.cleanup()
            
            # 从各类型列表中移除
            if isinstance(plugin, DownloaderPlugin):
                self.downloader_plugins.remove(plugin)
            elif isinstance(plugin, MetadataPlugin):
                self.metadata_plugins.remove(plugin)
            elif isinstance(plugin, SearchPlugin):
                self.search_plugins.remove(plugin)
            
            del self.plugins[plugin_name]
    
    def get_downloader_for_url(self, url: str) -> Optional[DownloaderPlugin]:
        """获取适合的下载器插件"""
        for plugin in self.downloader_plugins:
            if plugin.can_handle(url):
                return plugin
        return None
    
    def get_metadata_extractor(self, identifier: str) -> Optional[MetadataPlugin]:
        """获取适合的元数据提取插件"""
        for plugin in self.metadata_plugins:
            if plugin.can_extract(identifier):
                return plugin
        return None
    
    def get_all_search_plugins(self) -> List[SearchPlugin]:
        """获取所有搜索插件"""
        return self.search_plugins.copy()


# 全局插件管理器实例
plugin_manager = PluginManager()

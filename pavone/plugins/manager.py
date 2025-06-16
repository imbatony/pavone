"""
插件管理器
"""

import importlib
import inspect
import pkgutil
from typing import Dict, List, Optional, Type
from pathlib import Path
from .base import BasePlugin


class PluginManager:
    """插件管理器"""    
    def __init__(self):
        self.plugins: Dict[str, BasePlugin] = {}
        self.extractor_plugins: List[BasePlugin] = []
        self.metadata_plugins: List[BasePlugin] = []
        self.search_plugins: List[BasePlugin] = []
    
    def load_plugins(self, plugin_dir: Optional[str] = None):
        """加载插件"""
        if plugin_dir is None:
            plugin_dir = str(Path(__file__).parent)        
        # 加载内置提取器插件
        self._load_builtin_extractors()
        
        # 加载外部插件目录中的插件（跳过 extractors 目录避免重复加载）
        if plugin_dir and Path(plugin_dir).exists():
            self._load_plugins_from_directory(plugin_dir, skip_dirs={'extractors', '__pycache__'})
    
    def _load_builtin_extractors(self):
        """加载内置提取器插件"""
        try:
            from .extractors import MP4DirectExtractor, M3U8DirectExtractor, MissAVExtractor
            
            # 注册内置提取器
            mp4_extractor = MP4DirectExtractor()
            m3u8_extractor = M3U8DirectExtractor()
            missav_extractor = MissAVExtractor()
            
            self.register_plugin(mp4_extractor)
            self.register_plugin(m3u8_extractor)
            self.register_plugin(missav_extractor)
            
            print(f"已加载内置提取器: {mp4_extractor.name}, {m3u8_extractor.name}, {missav_extractor.name}")
            
        except ImportError as e:
            print(f"加载内置提取器失败: {e}")
    
    def _load_plugins_from_directory(self, plugin_dir: str, skip_dirs: Optional[set] = None):
        """从指定目录加载插件"""
        if skip_dirs is None:
            skip_dirs = set()
            
        plugin_path = Path(plugin_dir)
        
        # 遍历插件目录中的子目录
        for subdir in plugin_path.iterdir():
            if (subdir.is_dir() and 
                not subdir.name.startswith('_') and 
                subdir.name not in skip_dirs):
                self._load_plugins_from_package(subdir)
    
    def _load_plugins_from_package(self, package_path: Path):
        """从包中加载插件"""
        try:
            # 构建模块路径
            relative_path = package_path.relative_to(Path(__file__).parent.parent.parent)
            module_path = str(relative_path).replace('/', '.').replace('\\', '.')
            
            # 导入包
            package = importlib.import_module(module_path)
            
            # 遍历包中的模块
            for finder, name, ispkg in pkgutil.iter_modules(package.__path__, package.__name__ + "."):
                if not ispkg:
                    try:
                        module = importlib.import_module(name)
                        self._discover_plugins_in_module(module)
                    except Exception as e:
                        print(f"加载模块 {name} 失败: {e}")
                        
        except Exception as e:
            print(f"加载包 {package_path} 失败: {e}")
    
    def _discover_plugins_in_module(self, module):
        """在模块中发现并加载插件类"""
        for name, obj in inspect.getmembers(module, inspect.isclass):
            # 检查是否是插件类
            if (self._is_plugin_class(obj) and 
                obj.__module__ == module.__name__ and
                not inspect.isabstract(obj)):
                
                try:
                    # 创建插件实例并注册
                    plugin_instance = obj()
                    self.register_plugin(plugin_instance)
                    print(f"自动加载插件: {plugin_instance.name}")
                except Exception as e:
                    print(f"实例化插件 {name} 失败: {e}")
    
    def _is_plugin_class(self, cls: Type) -> bool:
        """检查类是否是有效的插件类"""
        from .extractors import ExtractorPlugin
        from .metadata import MetadataPlugin
        from .search import SearchPlugin
        
        return (issubclass(cls, (ExtractorPlugin, MetadataPlugin, SearchPlugin)) and
                cls not in (ExtractorPlugin, MetadataPlugin, SearchPlugin, BasePlugin))
    
    def register_plugin(self, plugin: BasePlugin):
        """注册插件"""
        if plugin.initialize():
            self.plugins[plugin.name] = plugin
            
            # 检查插件类型并分类
            from .extractors import ExtractorPlugin
            from .metadata import MetadataPlugin  
            from .search import SearchPlugin
            
            if isinstance(plugin, ExtractorPlugin):
                self.extractor_plugins.append(plugin)
                # 按优先级排序（数值越小优先级越高）
                self.extractor_plugins.sort(key=lambda p: getattr(p, 'priority', 50))
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
            from .extractors import ExtractorPlugin
            from .metadata import MetadataPlugin
            from .search import SearchPlugin
            
            if isinstance(plugin, ExtractorPlugin):
                self.extractor_plugins.remove(plugin)
            elif isinstance(plugin, MetadataPlugin):
                self.metadata_plugins.remove(plugin)
            elif isinstance(plugin, SearchPlugin):
                self.search_plugins.remove(plugin)
            
            del self.plugins[plugin_name]
    
    def get_extractor_for_url(self, url: str) -> Optional[BasePlugin]:
        """获取适合的提取器插件（按优先级排序）"""
        for plugin in self.extractor_plugins:
            # 运行时类型检查
            if hasattr(plugin, 'can_handle') and callable(getattr(plugin, 'can_handle')):
                if plugin.can_handle(url):  # type: ignore
                    return plugin
        return None
    
    def get_all_extractors_for_url(self, url: str) -> List[BasePlugin]:
        """获取所有能处理该URL的提取器插件（按优先级排序）"""
        matching_extractors = []
        for plugin in self.extractor_plugins:
            # 运行时类型检查
            if hasattr(plugin, 'can_handle') and callable(getattr(plugin, 'can_handle')):
                if plugin.can_handle(url):  # type: ignore
                    matching_extractors.append(plugin)
        return matching_extractors
    
    def get_metadata_extractor(self, identifier: str) -> Optional[BasePlugin]:
        """获取适合的元数据提取插件"""
        for plugin in self.metadata_plugins:
            # 运行时类型检查
            if hasattr(plugin, 'can_extract') and callable(getattr(plugin, 'can_extract')):
                if plugin.can_extract(identifier):  # type: ignore
                    return plugin
        return None
    
    def get_all_search_plugins(self) -> List[BasePlugin]:
        """获取所有搜索插件"""
        return self.search_plugins.copy()


# 全局插件管理器实例
plugin_manager = PluginManager()

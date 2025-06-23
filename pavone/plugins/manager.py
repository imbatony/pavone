"""
插件管理器
"""

from __future__ import annotations
import importlib
import inspect
import pkgutil
from types import ModuleType
from typing import Any, Dict, List, Optional, Type
from pathlib import Path
from .base import BasePlugin
from ..config.settings import config_manager
from .extractors import ExtractorPlugin
from .metadata import MetadataPlugin
from .search import SearchPlugin

class PluginManager:
    """插件管理器"""

    def __init__(self) -> None:
        """初始化插件管理器"""
        self.plugins: Dict[str, BasePlugin] = {}
        self.extractor_plugins: List[ExtractorPlugin] = []
        self.metadata_plugins: List[MetadataPlugin] = []
        self.search_plugins: List[SearchPlugin] = []
        self.config = config_manager.get_config().plugin
        self.logger = config_manager.get_logger(__name__)

    def load_plugins(self, plugin_dir: Optional[str] = None):
        """加载插件"""
        if plugin_dir is None:
            plugin_dir = self.config.plugin_dir

        # 确保插件相关目录存在
        config_manager.ensure_plugin_dirs()

        self.logger.info(f"开始加载插件，目录: {plugin_dir}")

        # 加载内置提取器插件
        self._load_builtin_extractors()

        # 加载外部插件目录中的插件（跳过 extractors 目录避免重复加载）
        if plugin_dir and Path(plugin_dir).exists():
            if self.config.auto_discovery:
                self._load_plugins_from_directory(plugin_dir, skip_dirs={"extractors", "__pycache__"})
            else:
                self.logger.info("插件自动发现已禁用")
        else:
            self.logger.warning(f"插件目录不存在: {plugin_dir}")

    def _load_builtin_extractors(self):
        """加载内置提取器插件"""
        try:
            from .extractors import MP4DirectExtractor, M3U8DirectExtractor, MissAVExtractor

            # 定义内置提取器映射
            builtin_extractors: dict[str, type[ExtractorPlugin]] = {
                "MP4DirectExtractor": MP4DirectExtractor,
                "M3U8DirectExtractor": M3U8DirectExtractor,
                "MissAVExtractor": MissAVExtractor,
            }

            loaded_extractors: list[str] = []

            for name, extractor_class in builtin_extractors.items():
                # 检查插件是否被禁用
                if config_manager.is_plugin_disabled(name):
                    self.logger.info(f"跳过禁用的内置提取器: {name}")
                    continue

                try:
                    extractor = extractor_class()

                    # 应用配置中的优先级设置
                    priority = config_manager.get_plugin_priority(name, extractor.priority)
                    extractor.set_priority(priority)

                    self.register_plugin(extractor)
                    loaded_extractors.append(extractor.name)
                    self.logger.info(f"已加载内置提取器: {extractor.name} (优先级: {priority})")

                except Exception as e:
                    self.logger.error(f"加载内置提取器 {name} 失败: {e}")

            if loaded_extractors:
                self.logger.info(f"成功加载 {len(loaded_extractors)} 个内置提取器")

        except ImportError as e:
            self.logger.error(f"导入内置提取器失败: {e}")

    def _load_plugins_from_directory(self, plugin_dir: str, skip_dirs: Optional[set[str]] = None):
        """从指定目录加载插件"""
        if skip_dirs is None:
            skip_dirs = set()

        plugin_path = Path(plugin_dir)

        # 遍历插件目录中的子目录
        for subdir in plugin_path.iterdir():
            if subdir.is_dir() and not subdir.name.startswith("_") and subdir.name not in skip_dirs:
                self._load_plugins_from_package(subdir)

    def _load_plugins_from_package(self, package_path: Path):
        """从包中加载插件"""
        try:
            # 构建模块路径
            relative_path = package_path.relative_to(Path(__file__).parent.parent.parent)
            module_path = str(relative_path).replace("/", ".").replace("\\", ".")

            # 导入包
            package = importlib.import_module(module_path)

            # 遍历包中的模块
            for _, name, ispkg in pkgutil.iter_modules(package.__path__, package.__name__ + "."):
                if not ispkg:
                    try:
                        module: ModuleType = importlib.import_module(name)
                        self._discover_plugins_in_module(module)
                    except Exception as e:
                        self.logger.error(f"加载模块 {name} 失败: {e}")

        except Exception as e:
            self.logger.error(f"加载包 {package_path} 失败: {e}")

    def _discover_plugins_in_module(self, module: ModuleType):
        """在模块中发现并加载插件类"""
        for name, obj in inspect.getmembers(module, inspect.isclass):
            # 检查是否是插件类
            if self._is_plugin_class(obj) and obj.__module__ == module.__name__ and not inspect.isabstract(obj):

                # 检查插件是否被禁用
                plugin_name = getattr(obj, "name", name)
                if config_manager.is_plugin_disabled(plugin_name):
                    self.logger.info(f"跳过禁用的插件: {plugin_name}")
                    continue

                try:
                    # 创建插件实例
                    plugin_instance = obj()

                    # 应用配置中的优先级设置
                    if hasattr(plugin_instance, "set_priority"):
                        priority = config_manager.get_plugin_priority(
                            plugin_instance.name, getattr(plugin_instance, "priority", 50)
                        )
                        plugin_instance.set_priority(priority)

                    self.register_plugin(plugin_instance)
                    self.logger.info(f"自动加载插件: {plugin_instance.name}")
                except Exception as e:
                    self.logger.error(f"实例化插件 {name} 失败: {e}")

    def _is_plugin_class(self, cls: Type[Any]) -> bool:
        return issubclass(cls, (ExtractorPlugin, MetadataPlugin, SearchPlugin)) and cls not in (
            ExtractorPlugin,
            MetadataPlugin,
            SearchPlugin,
            BasePlugin,
        )

    def register_plugin(self, plugin: BasePlugin):
        """注册插件"""
        # 检查插件是否被禁用
        if config_manager.is_plugin_disabled(plugin.name):
            self.logger.info(f"插件 {plugin.name} 已被禁用，跳过注册")
            return False

        if plugin.initialize():
            self.plugins[plugin.name] = plugin

            # 检查插件类型并分类
            from .extractors import ExtractorPlugin
            from .metadata import MetadataPlugin
            from .search import SearchPlugin

            if isinstance(plugin, ExtractorPlugin):
                self.extractor_plugins.append(plugin)
                # 按优先级排序（数值越小优先级越高）
                self.extractor_plugins.sort(key=lambda p: getattr(p, "priority", 50))
            elif isinstance(plugin, MetadataPlugin):
                self.metadata_plugins.append(plugin)
            elif isinstance(plugin, SearchPlugin):
                self.search_plugins.append(plugin)

            self.logger.info(f"成功注册插件: {plugin.name}")
            return True
        else:
            self.logger.warning(f"插件 {plugin.name} 初始化失败")
            return False

    def unregister_plugin(self, plugin_name: str):
        """注销插件"""
        if plugin_name in self.plugins:
            plugin = self.plugins[plugin_name]
            plugin.cleanup()

            if isinstance(plugin, ExtractorPlugin):
                self.extractor_plugins.remove(plugin)
            elif isinstance(plugin, MetadataPlugin):
                self.metadata_plugins.remove(plugin)
            elif isinstance(plugin, SearchPlugin):
                self.search_plugins.remove(plugin)

            del self.plugins[plugin_name]

    def get_extractor_for_url(self, url: str) -> Optional[ExtractorPlugin]:
        """获取适合的提取器插件（按优先级排序）"""
        for plugin in self.extractor_plugins:
            # 运行时类型检查
            if hasattr(plugin, "can_handle") and callable(getattr(plugin, "can_handle")):
                if plugin.can_handle(url):  # type: ignore
                    return plugin
        return None

    def get_all_extractors_for_url(self, url: str) -> List[ExtractorPlugin]:
        """获取所有能处理该URL的提取器插件（按优先级排序）"""
        matching_extractors:List[ExtractorPlugin] = []
        for plugin in self.extractor_plugins:
            # 运行时类型检查
            if hasattr(plugin, "can_handle") and callable(getattr(plugin, "can_handle")):
                if plugin.can_handle(url):  # type: ignore
                    matching_extractors.append(plugin)
        return matching_extractors

    def get_metadata_extractor(self, identifier: str) -> Optional[MetadataPlugin]:
        """获取适合的元数据提取插件"""
        for plugin in self.metadata_plugins:
            # 运行时类型检查
            if hasattr(plugin, "can_extract") and callable(getattr(plugin, "can_extract")):
                if plugin.can_extract(identifier):  # type: ignore
                    return plugin
        return None

    def get_all_search_plugins(self) -> List[SearchPlugin]:
        """获取所有搜索插件"""
        return self.search_plugins.copy()

    def reload_plugins(self):
        """重新加载所有插件"""
        self.logger.info("开始重新加载插件")

        # 清理现有插件
        for plugin in list(self.plugins.values()):
            plugin.cleanup()

        # 重置插件列表
        self.plugins.clear()
        self.extractor_plugins.clear()
        self.metadata_plugins.clear()
        self.search_plugins.clear()

        # 重新加载配置
        self.config = config_manager.get_config().plugin

        # 重新加载插件
        self.load_plugins()

        self.logger.info(f"重新加载完成，共加载 {len(self.plugins)} 个插件")

    def enable_plugin_by_name(self, plugin_name: str):
        """启用指定名称的插件"""
        config_manager.enable_plugin(plugin_name)
        # 重新加载插件以应用更改
        self.reload_plugins()

    def disable_plugin_by_name(self, plugin_name: str):
        """禁用指定名称的插件"""
        config_manager.disable_plugin(plugin_name)

        # 如果插件当前已加载，则注销它
        if plugin_name in self.plugins:
            self.unregister_plugin(plugin_name)
            self.logger.info(f"已禁用并注销插件: {plugin_name}")

    def set_plugin_priority_by_name(self, plugin_name: str, priority: int):
        """设置插件优先级"""
        config_manager.set_plugin_priority(plugin_name, priority)

        # 如果插件当前已加载，更新其优先级
        if plugin_name in self.plugins:
            plugin = self.plugins[plugin_name]
            if hasattr(plugin, "set_priority"):
                plugin.set_priority(priority)  # type: ignore

                # 如果是提取器插件，重新排序
                from .extractors import ExtractorPlugin

                if isinstance(plugin, ExtractorPlugin):
                    self.extractor_plugins.sort(key=lambda p: getattr(p, "priority", 50))

            self.logger.info(f"已更新插件 {plugin_name} 的优先级为 {priority}")

    def get_plugin_info(self) -> Dict[str, Any]:
        """获取插件信息统计"""
        disabled_plugins = self.config.disabled_plugins

        info:Dict[str, Any] = {
            "total_plugins": len(self.plugins),
            "extractor_plugins": len(self.extractor_plugins),
            "metadata_plugins": len(self.metadata_plugins),
            "search_plugins": len(self.search_plugins),
            "disabled_plugins": len(disabled_plugins),
            "plugin_list": {
                name: {
                    "type": type(plugin).__name__,
                    "priority": getattr(plugin, "priority", 50),
                    "enabled": not config_manager.is_plugin_disabled(name),
                }
                for name, plugin in self.plugins.items()
            },
            "disabled_plugin_list": disabled_plugins,
        }

        return info

    def get_plugins_by_type(self, plugin_type: str) -> List[ExtractorPlugin] | List[MetadataPlugin] | List[SearchPlugin]:
        """根据类型获取插件列表"""
        if plugin_type.lower() == "extractor":
            return self.extractor_plugins.copy()
        elif plugin_type.lower() == "metadata":
            return self.metadata_plugins.copy()
        elif plugin_type.lower() == "search":
            return self.search_plugins.copy()
        else:
            return []


# 全局插件管理器实例
plugin_manager = PluginManager()


def get_plugin_manager() -> PluginManager:
    """获取全局插件管理器实例"""
    return plugin_manager

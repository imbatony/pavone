"""插件自动发现测试"""

import unittest

from pavone.config.settings import config_manager
from pavone.manager.plugin_manager import PluginManager


class TestPluginAutoDiscovery(unittest.TestCase):
    """插件自动发现机制测试"""

    def test_auto_discovery_loads_all_builtin_plugins(self) -> None:
        """自动发现应加载所有内置插件"""
        pm = PluginManager()
        pm.load_plugins()

        # 验证核心插件被加载
        plugin_names = list(pm.plugins.keys())
        self.assertGreater(len(plugin_names), 0)
        # 检查关键插件 (使用插件的 name 属性, 非类名)
        self.assertIn("MissAV", plugin_names)
        self.assertIn("Javrate", plugin_names)
        self.assertIn("MP4DirectExtractor", plugin_names)
        self.assertIn("M3U8DirectExtractor", plugin_names)

    def test_extractor_plugins_loaded(self) -> None:
        """ExtractorPlugin 子类应被自动发现"""
        pm = PluginManager()
        pm.load_plugins()
        self.assertGreater(len(pm.extractor_plugins), 0)

    def test_metadata_plugins_loaded(self) -> None:
        """MetadataPlugin 子类应被自动发现"""
        pm = PluginManager()
        pm.load_plugins()
        self.assertGreater(len(pm.metadata_plugins), 0)
        # 确保至少 34 个元数据提取器被发现 (4 原有 + 30 新增)
        self.assertGreaterEqual(
            len(pm.metadata_plugins),
            34,
            f"Expected ≥34 metadata plugins, got {len(pm.metadata_plugins)}: " f"{[p.name for p in pm.metadata_plugins]}",
        )

    def test_search_plugins_loaded(self) -> None:
        """SearchPlugin 子类应被自动发现"""
        pm = PluginManager()
        pm.load_plugins()
        self.assertGreater(len(pm.search_plugins), 0)

    def test_disabled_plugin_skipped(self) -> None:
        """禁用列表中的插件应被跳过"""
        pm = PluginManager()
        # 获取当前禁用列表
        original_disabled = config_manager.get_config().plugin.disabled_plugins.copy()

        # 添加一个插件到禁用列表
        config = config_manager.get_config()
        config.plugin.disabled_plugins = ["MissAV"]

        pm.load_plugins()
        self.assertNotIn("MissAV", pm.plugins)

        # 恢复
        config.plugin.disabled_plugins = original_disabled

    def test_plugin_load_failure_isolated(self) -> None:
        """单个插件加载失败不应影响其他插件"""
        pm = PluginManager()
        pm.load_plugins()

        # 验证即使有错误的模块, 其他插件仍然加载
        self.assertGreater(len(pm.plugins), 0)

    def test_no_hardcoded_imports_in_plugin_manager(self) -> None:
        """plugin_manager.py 不应包含硬编码的插件导入"""
        import inspect

        from pavone.manager import plugin_manager as pm_module

        source = inspect.getsource(pm_module)
        # 不应有具体插件类的导入
        self.assertNotIn("from ..plugins.av01_plugin import", source)
        self.assertNotIn("from ..plugins.missav_plugin import", source)
        self.assertNotIn("from ..plugins.javrate_plugin import", source)
        self.assertNotIn("from ..plugins.jtable_plugin import", source)
        self.assertNotIn("from ..plugins.memojav_plugin import", source)


if __name__ == "__main__":
    unittest.main()

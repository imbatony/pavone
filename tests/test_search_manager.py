"""
SearchManager 单元测试
"""

from unittest.mock import Mock

import pytest

from pavone.manager.search_manager import SearchManager, get_search_manager
from pavone.models import SearchResult


def create_result(code, title=None, site="TestSite", url=None):
    """创建测试用 SearchResult 对象的辅助函数"""
    if title is None:
        title = f"Result {code}"
    if url is None:
        url = f"https://{site.lower()}.com/{code.lower().replace('-', '')}"

    return SearchResult(site=site, keyword="ABC", title=title, description=f"Test desc for {code}", url=url, code=code)


class TestSearchManager:
    """SearchManager 基本功能测试"""

    def test_init(self):
        """测试初始化"""
        mock_pm = Mock()
        manager = SearchManager(mock_pm)

        assert manager.plugin_manager is mock_pm
        assert manager.logger is not None

    def test_search_no_plugins(self):
        """测试无可用搜索插件时的行为"""
        mock_pm = Mock()
        mock_pm.get_all_search_plugins.return_value = []
        manager = SearchManager(mock_pm)

        results = manager.search("test")

        assert results == []

    def test_search_with_plugins(self):
        """测试基本搜索功能"""
        mock_plugin1 = Mock()
        mock_plugin1.name = "Plugin1"
        mock_plugin1.get_site_name.return_value = "Site1"
        mock_plugin1.search.return_value = [
            create_result("ABC-001", site="Site1"),
            create_result("ABC-002", site="Site1"),
        ]

        mock_plugin2 = Mock()
        mock_plugin2.name = "Plugin2"
        mock_plugin2.get_site_name.return_value = "Site2"
        mock_plugin2.search.return_value = [
            create_result("ABC-003", site="Site2"),
        ]

        mock_pm = Mock()
        mock_pm.get_all_search_plugins.return_value = [mock_plugin1, mock_plugin2]

        manager = SearchManager(mock_pm)
        results = manager.search("ABC", limit=10)

        assert len(results) == 3
        assert results[0].code == "ABC-001"
        assert results[1].code == "ABC-002"
        assert results[2].code == "ABC-003"

        mock_plugin1.search.assert_called_once_with("ABC", 10)
        mock_plugin2.search.assert_called_once_with("ABC", 10)

    def test_search_with_enable_sites(self):
        """测试使用 enable_sites 过滤"""
        mock_plugin1 = Mock()
        mock_plugin1.name = "Plugin1"
        mock_plugin1.get_site_name.return_value = "Site1"
        mock_plugin1.search.return_value = [
            create_result("ABC-001", site="Site1"),
        ]

        mock_plugin2 = Mock()
        mock_plugin2.name = "Plugin2"
        mock_plugin2.get_site_name.return_value = "Site2"
        mock_plugin2.search.return_value = [
            create_result("ABC-002", site="Site2"),
        ]

        mock_pm = Mock()
        mock_pm.get_all_search_plugins.return_value = [mock_plugin1, mock_plugin2]

        manager = SearchManager(mock_pm)

        # 只启用 Site1
        results = manager.search("ABC", enable_sites=["Site1"])

        assert len(results) == 1
        assert results[0].code == "ABC-001"

        mock_plugin1.search.assert_called_once()
        mock_plugin2.search.assert_not_called()

    def test_search_with_all_sites(self):
        """测试使用 ['All'] 启用所有站点"""
        mock_plugin1 = Mock()
        mock_plugin1.name = "Plugin1"
        mock_plugin1.get_site_name.return_value = "Site1"
        mock_plugin1.search.return_value = []

        mock_plugin2 = Mock()
        mock_plugin2.name = "Plugin2"
        mock_plugin2.get_site_name.return_value = "Site2"
        mock_plugin2.search.return_value = []

        mock_pm = Mock()
        mock_pm.get_all_search_plugins.return_value = [mock_plugin1, mock_plugin2]

        manager = SearchManager(mock_pm)
        manager.search("ABC", enable_sites=["All"])

        mock_plugin1.search.assert_called_once()
        mock_plugin2.search.assert_called_once()

    def test_search_plugin_error(self):
        """测试插件执行失败时的错误处理"""
        mock_plugin1 = Mock()
        mock_plugin1.name = "Plugin1"
        mock_plugin1.get_site_name.return_value = "Site1"
        mock_plugin1.search.side_effect = Exception("Network error")

        mock_plugin2 = Mock()
        mock_plugin2.name = "Plugin2"
        mock_plugin2.get_site_name.return_value = "Site2"
        mock_plugin2.search.return_value = [
            create_result("ABC-001", site="Site2"),
        ]

        mock_pm = Mock()
        mock_pm.get_all_search_plugins.return_value = [mock_plugin1, mock_plugin2]

        manager = SearchManager(mock_pm)
        results = manager.search("ABC")

        # 应该只返回成功插件的结果
        assert len(results) == 1
        assert results[0].code == "ABC-001"


class TestSearchManagerDedup:
    """SearchManager 去重功能测试"""

    def test_search_with_dedup_duplicate_urls(self):
        """测试URL去重"""
        mock_plugin = Mock()
        mock_plugin.name = "Plugin1"
        mock_plugin.get_site_name.return_value = "Site1"
        mock_plugin.search.return_value = [
            create_result("ABC-001", site="Site1", url="https://site1.com/1"),
            create_result("ABC-002", site="Site1", url="https://site1.com/1"),  # 重复URL
            create_result("ABC-003", site="Site1", url="https://site1.com/3"),
        ]

        mock_pm = Mock()
        mock_pm.get_all_search_plugins.return_value = [mock_plugin]

        manager = SearchManager(mock_pm)
        results = manager.search_with_dedup("ABC")

        assert len(results) == 2
        assert results[0].code == "ABC-001"
        assert results[1].code == "ABC-003"

    def test_search_with_dedup_duplicate_codes(self):
        """测试代码去重"""
        mock_plugin = Mock()
        mock_plugin.name = "Plugin1"
        mock_plugin.get_site_name.return_value = "Site1"
        mock_plugin.search.return_value = [
            create_result("ABC-001", site="Site1", url="https://site1.com/1"),
            create_result("ABC-001", site="Site1", url="https://site1.com/2"),  # 重复代码
            create_result("ABC-003", site="Site1", url="https://site1.com/3"),
        ]

        mock_pm = Mock()
        mock_pm.get_all_search_plugins.return_value = [mock_plugin]

        manager = SearchManager(mock_pm)
        results = manager.search_with_dedup("ABC")

        assert len(results) == 2
        assert results[0].code == "ABC-001"
        assert results[1].code == "ABC-003"

    def test_search_with_dedup_no_duplicates(self):
        """测试无重复时的行为"""
        mock_plugin = Mock()
        mock_plugin.name = "Plugin1"
        mock_plugin.get_site_name.return_value = "Site1"
        mock_plugin.search.return_value = [
            create_result("ABC-001", site="Site1"),
            create_result("ABC-002", site="Site1"),
            create_result("ABC-003", site="Site1"),
        ]

        mock_pm = Mock()
        mock_pm.get_all_search_plugins.return_value = [mock_plugin]

        manager = SearchManager(mock_pm)
        results = manager.search_with_dedup("ABC")

        assert len(results) == 3

    def test_search_with_dedup_empty_results(self):
        """测试空结果时的去重"""
        mock_pm = Mock()
        mock_pm.get_all_search_plugins.return_value = []

        manager = SearchManager(mock_pm)
        results = manager.search_with_dedup("ABC")

        assert results == []


class TestSearchManagerBestMatch:
    """SearchManager 最佳匹配功能测试"""

    def test_get_best_match(self):
        """测试获取最佳匹配结果"""
        mock_plugin = Mock()
        mock_plugin.name = "Plugin1"
        mock_plugin.get_site_name.return_value = "Site1"
        mock_plugin.search.return_value = [
            create_result("ABC-001", site="Site1"),
            create_result("ABC-002", site="Site1"),
            create_result("ABC-003", site="Site1"),
        ]

        mock_pm = Mock()
        mock_pm.get_all_search_plugins.return_value = [mock_plugin]

        manager = SearchManager(mock_pm)
        result = manager.get_best_match("ABC")

        assert result is not None
        assert result.code == "ABC-001"
        assert result.title == "Result ABC-001"

    def test_get_best_match_no_results(self):
        """测试无结果时的最佳匹配"""
        mock_pm = Mock()
        mock_pm.get_all_search_plugins.return_value = []

        manager = SearchManager(mock_pm)
        result = manager.get_best_match("ABC")

        assert result is None

    def test_get_best_match_with_enable_sites(self):
        """测试指定站点时的最佳匹配"""
        mock_plugin1 = Mock()
        mock_plugin1.name = "Plugin1"
        mock_plugin1.get_site_name.return_value = "Site1"
        mock_plugin1.search.return_value = [
            create_result("ABC-001", site="Site1"),
        ]

        mock_plugin2 = Mock()
        mock_plugin2.name = "Plugin2"
        mock_plugin2.get_site_name.return_value = "Site2"
        mock_plugin2.search.return_value = [
            create_result("ABC-002", site="Site2"),
        ]

        mock_pm = Mock()
        mock_pm.get_all_search_plugins.return_value = [mock_plugin1, mock_plugin2]

        manager = SearchManager(mock_pm)
        result = manager.get_best_match("ABC", enable_sites=["Site2"])

        assert result is not None
        assert result.code == "ABC-002"


class TestSearchManagerConvenience:
    """SearchManager 便捷方法测试"""

    def test_search_by_code(self):
        """测试使用代码搜索"""
        mock_plugin = Mock()
        mock_plugin.name = "Plugin1"
        mock_plugin.get_site_name.return_value = "Site1"
        mock_plugin.search.return_value = [
            create_result("ABC-001", site="Site1"),
        ]

        mock_pm = Mock()
        mock_pm.get_all_search_plugins.return_value = [mock_plugin]

        manager = SearchManager(mock_pm)
        results = manager.search_by_code("ABC-001")

        assert len(results) == 1
        assert results[0].code == "ABC-001"
        mock_plugin.search.assert_called_once()

    def test_get_available_sites(self):
        """测试获取可用站点列表"""
        mock_plugin1 = Mock()
        mock_plugin1.get_site_name.return_value = "Site1"

        mock_plugin2 = Mock()
        mock_plugin2.get_site_name.return_value = "Site2"

        mock_pm = Mock()
        mock_pm.get_all_search_plugins.return_value = [mock_plugin1, mock_plugin2]

        manager = SearchManager(mock_pm)
        sites = manager.get_available_sites()

        assert len(sites) == 2
        assert "Site1" in sites
        assert "Site2" in sites

    def test_get_available_sites_empty(self):
        """测试无可用站点时的行为"""
        mock_pm = Mock()
        mock_pm.get_all_search_plugins.return_value = []

        manager = SearchManager(mock_pm)
        sites = manager.get_available_sites()

        assert sites == []


class TestSearchManagerGlobal:
    """SearchManager 全局实例测试"""

    def test_get_search_manager_first_call(self):
        """测试首次调用 get_search_manager"""
        from pavone.manager import search_manager

        # 重置全局实例
        search_manager._search_manager = None

        mock_pm = Mock()
        manager = search_manager.get_search_manager(mock_pm)

        assert manager is not None
        assert manager.plugin_manager is mock_pm

    def test_get_search_manager_without_plugin_manager(self):
        """测试首次调用时未提供 plugin_manager 会抛出异常"""
        from pavone.manager import search_manager

        # 重置全局实例
        search_manager._search_manager = None

        with pytest.raises(ValueError, match="首次初始化 SearchManager 时必须提供 plugin_manager"):
            search_manager.get_search_manager()

    def test_get_search_manager_subsequent_calls(self):
        """测试后续调用 get_search_manager 返回相同实例"""
        from pavone.manager import search_manager

        # 重置全局实例
        search_manager._search_manager = None

        mock_pm = Mock()
        manager1 = search_manager.get_search_manager(mock_pm)
        manager2 = search_manager.get_search_manager()

        assert manager1 is manager2

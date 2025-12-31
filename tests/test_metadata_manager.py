"""MetadataManager 测试"""

from unittest.mock import MagicMock, Mock, patch

import pytest

from pavone.manager.metadata_manager import MetadataManager, get_metadata_manager
from pavone.models import MovieMetadata, SearchResult


def create_test_metadata(code="TEST-123", title="Test Movie", site="test"):
    """创建测试用的元数据对象"""
    return MovieMetadata(
        identifier=f"{site}-{code}",
        code=code,
        title=title,
        url=f"https://{site}.com/video/{code}",
        site=site,
    )


def create_test_search_result(code="TEST-123", title="Test Movie", site="test"):
    """创建测试用的搜索结果对象"""
    return SearchResult(
        code=code,
        keyword=code,
        title=title,
        description=f"Description for {title}",
        url=f"https://{site}.com/video/{code}",
        site=site,
    )


class TestMetadataManager:
    """MetadataManager 基础测试"""

    def test_init(self):
        """测试初始化"""
        plugin_manager = MagicMock()
        manager = MetadataManager(plugin_manager)

        assert manager.plugin_manager == plugin_manager
        assert manager._cache == {}
        assert manager.logger is not None

    def test_init_without_plugin_manager(self):
        """测试不提供 plugin_manager 时使用全局实例"""
        with patch("pavone.manager.plugin_manager.get_plugin_manager") as mock_get:
            mock_plugin_manager = MagicMock()
            mock_get.return_value = mock_plugin_manager

            manager = MetadataManager()

            assert manager.plugin_manager == mock_plugin_manager

    def test_get_available_plugins(self):
        """测试获取可用插件列表"""
        plugin_manager = MagicMock()
        plugin1 = Mock()
        plugin1.name = "plugin1"
        plugin2 = Mock()
        plugin2.name = "plugin2"
        plugin_manager.metadata_plugins = [plugin1, plugin2]

        manager = MetadataManager(plugin_manager)
        plugins = manager.get_available_plugins()

        assert plugins == ["plugin1", "plugin2"]

    def test_get_plugin_for_identifier(self):
        """测试获取处理特定标识符的插件"""
        plugin_manager = MagicMock()
        mock_plugin = MagicMock()
        plugin_manager.get_metadata_extractor.return_value = mock_plugin

        manager = MetadataManager(plugin_manager)
        result = manager.get_plugin_for_identifier("test-123")

        assert result == mock_plugin
        plugin_manager.get_metadata_extractor.assert_called_once_with("test-123")

    def test_clear_cache(self):
        """测试清空缓存"""
        plugin_manager = MagicMock()
        manager = MetadataManager(plugin_manager)
        manager._cache = {"key1": "value1", "key2": "value2"}

        manager.clear_cache()

        assert manager._cache == {}

    def test_get_cache_size(self):
        """测试获取缓存大小"""
        plugin_manager = MagicMock()
        manager = MetadataManager(plugin_manager)
        manager._cache = {"key1": "value1", "key2": "value2", "key3": "value3"}

        assert manager.get_cache_size() == 3


class TestMetadataManagerGetMetadata:
    """MetadataManager.get_metadata() 测试"""

    def test_get_metadata_success(self):
        """测试成功获取元数据"""
        plugin_manager = MagicMock()
        mock_plugin = MagicMock()
        mock_metadata = create_test_metadata()
        mock_plugin.extract_metadata.return_value = mock_metadata
        plugin_manager.get_metadata_extractor.return_value = mock_plugin

        manager = MetadataManager(plugin_manager)
        result = manager.get_metadata("TEST-123")

        assert result == mock_metadata
        plugin_manager.get_metadata_extractor.assert_called_once_with("TEST-123")
        mock_plugin.extract_metadata.assert_called_once_with("TEST-123")

    def test_get_metadata_from_cache(self):
        """测试从缓存获取元数据"""
        plugin_manager = MagicMock()
        mock_metadata = create_test_metadata()

        manager = MetadataManager(plugin_manager)
        manager._cache["TEST-123"] = mock_metadata

        result = manager.get_metadata("TEST-123")

        assert result == mock_metadata
        # 不应该调用 plugin_manager
        plugin_manager.get_metadata_extractor.assert_not_called()

    def test_get_metadata_cache_by_code(self):
        """测试元数据同时缓存到 identifier 和 code"""
        plugin_manager = MagicMock()
        mock_plugin = MagicMock()
        mock_metadata = create_test_metadata()
        mock_plugin.extract_metadata.return_value = mock_metadata
        plugin_manager.get_metadata_extractor.return_value = mock_plugin

        manager = MetadataManager(plugin_manager)
        # 使用 URL 获取
        result = manager.get_metadata("https://test.com/video/TEST-123")

        assert result == mock_metadata
        # 应该缓存到 URL 和 code
        assert "https://test.com/video/TEST-123" in manager._cache
        assert "TEST-123" in manager._cache

    def test_get_metadata_no_plugin(self):
        """测试没有找到合适的插件"""
        plugin_manager = MagicMock()
        plugin_manager.get_metadata_extractor.return_value = None

        manager = MetadataManager(plugin_manager)
        result = manager.get_metadata("UNKNOWN-123")

        assert result is None

    def test_get_metadata_extraction_failed(self):
        """测试元数据提取失败"""
        plugin_manager = MagicMock()
        mock_plugin = MagicMock()
        mock_plugin.extract_metadata.return_value = None
        plugin_manager.get_metadata_extractor.return_value = mock_plugin

        manager = MetadataManager(plugin_manager)
        result = manager.get_metadata("TEST-123")

        assert result is None

    def test_get_metadata_exception(self):
        """测试提取过程中抛出异常"""
        plugin_manager = MagicMock()
        mock_plugin = MagicMock()
        mock_plugin.extract_metadata.side_effect = Exception("Test error")
        plugin_manager.get_metadata_extractor.return_value = mock_plugin

        manager = MetadataManager(plugin_manager)
        result = manager.get_metadata("TEST-123")

        assert result is None


class TestMetadataManagerSearchResult:
    """MetadataManager.get_metadata_from_search_result() 测试"""

    def test_get_metadata_from_search_result_with_url(self):
        """测试从搜索结果获取元数据（使用 URL）"""
        plugin_manager = MagicMock()
        mock_plugin = MagicMock()
        mock_metadata = create_test_metadata()
        mock_plugin.extract_metadata.return_value = mock_metadata
        plugin_manager.get_metadata_extractor.return_value = mock_plugin

        search_result = create_test_search_result()

        manager = MetadataManager(plugin_manager)
        result = manager.get_metadata_from_search_result(search_result)

        assert result == mock_metadata

    def test_get_metadata_from_search_result_with_code(self):
        """测试从搜索结果获取元数据（使用 code）"""
        plugin_manager = MagicMock()
        mock_plugin = MagicMock()
        mock_metadata = create_test_metadata()
        mock_plugin.extract_metadata.return_value = mock_metadata

        # URL 失败，code 成功
        def get_extractor_side_effect(identifier):
            if identifier == "TEST-123":
                return mock_plugin
            return None

        plugin_manager.get_metadata_extractor.side_effect = get_extractor_side_effect

        search_result = create_test_search_result()

        manager = MetadataManager(plugin_manager)
        result = manager.get_metadata_from_search_result(search_result)

        assert result == mock_metadata

    def test_get_metadata_from_search_result_both_failed(self):
        """测试从搜索结果获取元数据失败"""
        plugin_manager = MagicMock()
        plugin_manager.get_metadata_extractor.return_value = None

        search_result = create_test_search_result()

        manager = MetadataManager(plugin_manager)
        result = manager.get_metadata_from_search_result(search_result)

        assert result is None


class TestMetadataManagerBatch:
    """MetadataManager 批量处理测试"""

    def test_batch_get_metadata(self):
        """测试批量获取元数据"""
        plugin_manager = MagicMock()
        mock_plugin = MagicMock()

        metadata1 = create_test_metadata("TEST-001", "Movie 1")
        metadata2 = create_test_metadata("TEST-002", "Movie 2")
        metadata3 = create_test_metadata("TEST-003", "Movie 3")

        mock_plugin.extract_metadata.side_effect = [metadata1, metadata2, metadata3]
        plugin_manager.get_metadata_extractor.return_value = mock_plugin

        manager = MetadataManager(plugin_manager)
        identifiers = ["TEST-001", "TEST-002", "TEST-003"]

        results = manager.batch_get_metadata(identifiers)

        assert len(results) == 3
        assert results[0] == metadata1
        assert results[1] == metadata2
        assert results[2] == metadata3

    def test_batch_get_metadata_with_callback(self):
        """测试批量获取元数据（带进度回调）"""
        plugin_manager = MagicMock()
        mock_plugin = MagicMock()
        mock_plugin.extract_metadata.return_value = create_test_metadata()
        plugin_manager.get_metadata_extractor.return_value = mock_plugin

        callback_calls = []

        def callback(current, total, identifier):
            callback_calls.append((current, total, identifier))

        manager = MetadataManager(plugin_manager)
        identifiers = ["TEST-001", "TEST-002", "TEST-003"]

        manager.batch_get_metadata(identifiers, callback=callback)

        assert len(callback_calls) == 3
        assert callback_calls[0] == (1, 3, "TEST-001")
        assert callback_calls[1] == (2, 3, "TEST-002")
        assert callback_calls[2] == (3, 3, "TEST-003")

    def test_batch_get_metadata_callback_exception(self):
        """测试批量获取元数据（回调异常）"""
        plugin_manager = MagicMock()
        mock_plugin = MagicMock()
        mock_plugin.extract_metadata.return_value = create_test_metadata()
        plugin_manager.get_metadata_extractor.return_value = mock_plugin

        def callback(current, total, identifier):
            raise Exception("Callback error")

        manager = MetadataManager(plugin_manager)
        identifiers = ["TEST-001", "TEST-002"]

        # 即使回调异常，也应该继续处理
        results = manager.batch_get_metadata(identifiers, callback=callback)

        assert len(results) == 2

    def test_batch_get_metadata_partial_failure(self):
        """测试批量获取元数据（部分失败）"""
        plugin_manager = MagicMock()
        mock_plugin = MagicMock()

        metadata1 = create_test_metadata("TEST-001", "Movie 1")
        # 第二个失败
        metadata3 = create_test_metadata("TEST-003", "Movie 3")

        mock_plugin.extract_metadata.side_effect = [metadata1, None, metadata3]
        plugin_manager.get_metadata_extractor.return_value = mock_plugin

        manager = MetadataManager(plugin_manager)
        identifiers = ["TEST-001", "TEST-002", "TEST-003"]

        results = manager.batch_get_metadata(identifiers)

        assert len(results) == 3
        assert results[0] == metadata1
        assert results[1] is None
        assert results[2] == metadata3

    def test_batch_get_metadata_from_search_results(self):
        """测试批量从搜索结果获取元数据"""
        plugin_manager = MagicMock()
        mock_plugin = MagicMock()

        metadata1 = create_test_metadata("TEST-001", "Movie 1")
        metadata2 = create_test_metadata("TEST-002", "Movie 2")

        mock_plugin.extract_metadata.side_effect = [metadata1, metadata2]
        plugin_manager.get_metadata_extractor.return_value = mock_plugin

        search_results = [
            create_test_search_result("TEST-001", "Movie 1"),
            create_test_search_result("TEST-002", "Movie 2"),
        ]

        manager = MetadataManager(plugin_manager)
        results = manager.batch_get_metadata_from_search_results(search_results)

        assert len(results) == 2
        assert results[0] == metadata1
        assert results[1] == metadata2


class TestMetadataManagerGlobal:
    """MetadataManager 全局实例测试"""

    def test_get_metadata_manager_with_custom_plugin_manager(self):
        """测试使用自定义 plugin_manager 获取实例"""
        # 重置全局实例
        import pavone.manager.metadata_manager as mm_module

        mm_module._metadata_manager_instance = None

        custom_plugin_manager = MagicMock()

        manager = get_metadata_manager(custom_plugin_manager)

        assert isinstance(manager, MetadataManager)
        assert manager.plugin_manager == custom_plugin_manager

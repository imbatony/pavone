"""
Jellyfin 搜索插件单元测试
"""

from unittest.mock import MagicMock, patch

from pavone.models import SearchResult
from pavone.plugins.search import JellyfinSearch


class TestJellyfinSearchPluginInit:
    """测试 Jellyfin 搜索插件初始化"""

    def test_init(self):
        """测试插件初始化"""
        plugin = JellyfinSearch()
        assert plugin.name == "JellyfinSearch"
        assert plugin.site == "Jellyfin"
        assert plugin.client is None
        assert plugin.library_manager is None

    def test_init_custom_name(self):
        """测试自定义名称初始化"""
        plugin = JellyfinSearch(name="CustomJellyfinSearch")
        assert plugin.name == "CustomJellyfinSearch"


class TestJellyfinSearchPluginInitialize:
    """测试 Jellyfin 搜索插件初始化方法"""

    @patch("pavone.plugins.search.jellyfin_search.JellyfinClientWrapper")
    @patch("pavone.plugins.search.jellyfin_search.LibraryManager")
    def test_initialize_enabled(self, mock_library_manager, mock_client_wrapper):
        """测试启用状态下的初始化"""
        plugin = JellyfinSearch()
        plugin.config.jellyfin.enabled = True

        result = plugin.initialize()

        assert result is True
        assert mock_client_wrapper.called
        assert mock_library_manager.called

    def test_initialize_disabled(self):
        """测试禁用状态下的初始化"""
        plugin = JellyfinSearch()
        plugin.config.jellyfin.enabled = False

        result = plugin.initialize()

        assert result is False

    @patch("pavone.plugins.search.jellyfin_search.JellyfinClientWrapper")
    def test_initialize_connection_error(self, mock_client_wrapper):
        """测试连接错误"""
        mock_client_wrapper.side_effect = Exception("连接失败")
        plugin = JellyfinSearch()
        plugin.config.jellyfin.enabled = True

        result = plugin.initialize()

        assert result is False


class TestJellyfinSearchPluginSearch:
    """测试 Jellyfin 搜索插件搜索功能"""

    @patch("pavone.plugins.search.jellyfin_search.LibraryManager")
    @patch("pavone.plugins.search.jellyfin_search.JellyfinClientWrapper")
    def test_search_success(self, mock_client_wrapper, mock_library_manager):
        """测试成功搜索"""
        # 模拟搜索结果
        mock_item = MagicMock()
        mock_item.name = "FC2-3751072 Test Video"
        mock_item.id = "test-id-123"
        mock_item.type = "Movie"
        mock_item.path = "/media/videos/test.mkv"
        mock_item.container = "mkv"
        mock_item.metadata = {}

        mock_client = MagicMock()
        mock_client.search_items.return_value = [mock_item]
        mock_client.get_item_web_url.return_value = "jellyfin://test-id-123"
        mock_client_wrapper.return_value = mock_client

        plugin = JellyfinSearch()
        plugin.client = mock_client
        plugin.library_manager = MagicMock()

        results = plugin.search("FC2-3751072", limit=20)

        assert len(results) == 1
        assert isinstance(results[0], SearchResult)
        assert results[0].title == "FC2-3751072 Test Video"
        assert results[0].site == "Jellyfin"
        assert results[0].url == "jellyfin://test-id-123"
        assert results[0].description == "Jellyfin 库项 - Movie"

    @patch("pavone.plugins.search.jellyfin_search.LibraryManager")
    @patch("pavone.plugins.search.jellyfin_search.JellyfinClientWrapper")
    def test_search_no_results(self, mock_client_wrapper, mock_library_manager):
        """测试无搜索结果"""
        mock_client = MagicMock()
        mock_client.search_items.return_value = []
        mock_client_wrapper.return_value = mock_client

        plugin = JellyfinSearch()
        plugin.client = mock_client
        plugin.library_manager = MagicMock()

        results = plugin.search("NonExistent", limit=20)

        assert len(results) == 0

    def test_search_not_initialized(self):
        """测试未初始化时的搜索"""
        plugin = JellyfinSearch()
        plugin.client = None

        results = plugin.search("test")

        assert len(results) == 0

    @patch("pavone.plugins.search.jellyfin_search.JellyfinClientWrapper")
    def test_search_error(self, mock_client_wrapper):
        """测试搜索错误"""
        mock_client = MagicMock()
        mock_client.search_items.side_effect = Exception("搜索失败")

        plugin = JellyfinSearch()
        plugin.client = mock_client
        plugin.library_manager = MagicMock()

        results = plugin.search("test")

        assert len(results) == 0


class TestJellyfinSearchPluginExtractCode:
    """测试代码提取功能"""

    def test_extract_code_from_name(self):
        """测试从名称中提取番号"""
        plugin = JellyfinSearch()

        mock_item = MagicMock()
        mock_item.name = "FC2-3751072 Test Video"
        mock_item.metadata = {}

        code = plugin._extract_code_from_item(mock_item)

        assert code == "FC2-3751072"

    def test_extract_code_not_found(self):
        """测试未找到番号"""
        plugin = JellyfinSearch()

        mock_item = MagicMock()
        mock_item.name = "Test Video Without Code"
        mock_item.metadata = {}

        code = plugin._extract_code_from_item(mock_item)

        assert code == ""


class TestJellyfinSearchPluginCleanup:
    """测试清理功能"""

    def test_cleanup(self):
        """测试清理方法"""
        plugin = JellyfinSearch()
        plugin.client = MagicMock()
        plugin.library_manager = MagicMock()

        plugin.cleanup()

        assert plugin.client is None
        assert plugin.library_manager is None

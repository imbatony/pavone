"""
Jellyfin 客户端单元测试
"""

from unittest.mock import Mock, patch

import pytest

from pavone.config.configs import JellyfinConfig
from pavone.jellyfin import (
    JellyfinAPIError,
    JellyfinAuthenticationError,
    JellyfinClientWrapper,
)
from pavone.jellyfin.models import JellyfinItem


@pytest.fixture
def jellyfin_config():
    """创建测试用 Jellyfin 配置"""
    return JellyfinConfig(
        enabled=True,
        server_url="http://localhost:8096",
        username="testuser",
        password="testpass",
        libraries=["Movies"],
    )


@pytest.fixture
def jellyfin_api_config():
    """创建使用 API Key 的 Jellyfin 配置"""
    return JellyfinConfig(
        enabled=True,
        server_url="http://localhost:8096",
        api_key="test-api-key",
        libraries=["Movies"],
    )


class TestJellyfinClientWrapperInit:
    """测试客户端初始化"""

    def test_init_with_valid_config(self, jellyfin_config):
        """测试使用有效配置初始化"""
        client = JellyfinClientWrapper(jellyfin_config)
        assert client.config == jellyfin_config
        assert client.is_authenticated() is False

    def test_init_without_server_url(self):
        """测试未提供服务器 URL 时的初始化"""
        config = JellyfinConfig(server_url="")
        with pytest.raises(ValueError):
            JellyfinClientWrapper(config)


class TestJellyfinClientAuthentication:
    """测试认证功能"""

    @patch("pavone.jellyfin.client.JellyfinClient")
    def test_authenticate_with_credentials(self, mock_jellyfin_client, jellyfin_config):
        """测试使用用户名密码认证"""
        client = JellyfinClientWrapper(jellyfin_config)

        # Mock 认证过程
        client.client.auth.connect_to_address = Mock()
        client.client.auth.login = Mock()

        result = client.authenticate()

        assert result is True
        assert client.is_authenticated() is True
        client.client.auth.connect_to_address.assert_called_once()
        client.client.auth.login.assert_called_once()

    @patch("pavone.jellyfin.client.JellyfinClient")
    def test_authenticate_with_api_key(self, mock_jellyfin_client, jellyfin_api_config):
        """测试使用 API Key 认证"""
        client = JellyfinClientWrapper(jellyfin_api_config)

        # Mock 认证过程
        client.client.authenticate = Mock()

        result = client.authenticate()

        assert result is True
        assert client.is_authenticated() is True
        client.client.authenticate.assert_called_once()

    @patch("pavone.jellyfin.client.JellyfinClient")
    def test_authenticate_failure(self, mock_jellyfin_client, jellyfin_config):
        """测试认证失败"""
        client = JellyfinClientWrapper(jellyfin_config)

        # Mock 认证过程失败
        client.client.auth.connect_to_address = Mock(side_effect=Exception("Connection failed"))
        client.client.auth.login = Mock()

        with pytest.raises(JellyfinAuthenticationError):
            client.authenticate()

    @patch("pavone.jellyfin.client.JellyfinClient")
    def test_authenticate_without_credentials(self, mock_jellyfin_client):
        """测试未提供认证信息"""
        config = JellyfinConfig(
            enabled=True,
            server_url="http://localhost:8096",
        )
        client = JellyfinClientWrapper(config)

        with pytest.raises(JellyfinAuthenticationError):
            client.authenticate()


class TestJellyfinClientAPIMethods:
    """测试 API 方法"""

    @pytest.fixture
    def authenticated_client(self, jellyfin_config):
        """创建已认证的客户端"""
        with patch("pavone.jellyfin.client.JellyfinClient"):
            client = JellyfinClientWrapper(jellyfin_config)
            client.client.auth.connect_to_address = Mock()
            client.client.auth.login = Mock()
            client.authenticate()
            return client

    def test_get_libraries(self, authenticated_client):
        """测试获取库列表"""
        mock_response = {
            "Items": [
                {
                    "Name": "Movies",
                    "Id": "lib1",
                    "CollectionType": "movies",
                    "ChildCount": 100,
                },
                {
                    "Name": "TV Shows",
                    "Id": "lib2",
                    "CollectionType": "tvshows",
                    "ChildCount": 50,
                },
            ]
        }

        authenticated_client.client.jellyfin.media_folders = Mock(return_value=mock_response)

        libraries = authenticated_client.get_libraries()

        assert len(libraries) == 2
        assert libraries[0].name == "Movies"
        assert libraries[0].type == "movies"
        assert libraries[1].name == "TV Shows"

    def test_get_libraries_error(self, authenticated_client):
        """测试获取库列表时出错"""
        authenticated_client.client.jellyfin.media_folders = Mock(side_effect=Exception("API Error"))

        with pytest.raises(JellyfinAPIError):
            authenticated_client.get_libraries()

    def test_search_items(self, authenticated_client):
        """测试搜索项"""
        mock_response = {
            "Items": [
                {
                    "Id": "item1",
                    "Name": "Test Movie",
                    "Type": "Movie",
                    "Container": "mkv",
                    "Path": "/movies/test.mkv",
                },
            ]
        }

        authenticated_client.client.jellyfin.search_media_items = Mock(return_value=mock_response)

        items = authenticated_client.search_items("test")

        assert len(items) == 1
        assert items[0].name == "Test Movie"
        assert items[0].type == "Movie"

    def test_get_item(self, authenticated_client):
        """测试获取单个项"""
        mock_item = {
            "Id": "item1",
            "Name": "Test Movie",
            "Type": "Movie",
            "Container": "mkv",
            "Path": "/movies/test.mkv",
        }

        authenticated_client.client.jellyfin.get_item = Mock(return_value=mock_item)

        item = authenticated_client.get_item("item1")

        assert item.id == "item1"
        assert item.name == "Test Movie"

    def test_mark_item_played(self, authenticated_client):
        """测试标记项为已观看"""
        authenticated_client.client.jellyfin.item_played = Mock()

        result = authenticated_client.mark_item_played("item1")

        assert result is True
        authenticated_client.client.jellyfin.item_played.assert_called_once()

    def test_refresh_library(self, authenticated_client):
        """测试刷新库"""
        authenticated_client.client.jellyfin._post = Mock(return_value={})

        result = authenticated_client.refresh_library("lib1")

        assert result is True
        authenticated_client.client.jellyfin._post.assert_called_once()


class TestJellyfinClientParseItem:
    """测试项解析"""

    def test_parse_item_with_all_fields(self, jellyfin_config):
        """测试解析完整的项数据"""
        with patch("pavone.jellyfin.client.JellyfinClient"):
            client = JellyfinClientWrapper(jellyfin_config)

            item_data = {
                "Id": "item1",
                "Name": "Test Movie",
                "Type": "Movie",
                "Container": "mkv",
                "Path": "/movies/test.mkv",
                "extra_field": "extra_value",
            }

            item = client._parse_item(item_data)

            assert isinstance(item, JellyfinItem)
            assert item.id == "item1"
            assert item.name == "Test Movie"
            assert item.type == "Movie"
            assert item.container == "mkv"
            assert item.path == "/movies/test.mkv"
            assert item.metadata == item_data

    def test_parse_item_with_missing_fields(self, jellyfin_config):
        """测试解析缺少字段的项数据"""
        with patch("pavone.jellyfin.client.JellyfinClient"):
            client = JellyfinClientWrapper(jellyfin_config)

            item_data = {
                "Id": "item1",
                "Name": "Test Movie",
            }

            item = client._parse_item(item_data)

            assert item.id == "item1"
            assert item.name == "Test Movie"
            assert item.type == ""
            assert item.container is None
            assert item.path is None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

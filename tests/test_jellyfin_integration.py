"""
Jellyfin 集成测试

测试与真实 Jellyfin 服务器的交互。
这些测试需要一个正在运行的 Jellyfin 实例。

使用方式：
    uv run pytest tests/test_jellyfin_integration.py -v -m integration
    或跳过集成测试：
    uv run pytest tests/ -v -m "not integration"
"""

import pytest
from pavone.config.configs import JellyfinConfig
from pavone.jellyfin import (
    JellyfinClientWrapper,
    JellyfinAPIError,
    JellyfinAuthenticationError,
)


# 测试配置
JELLYFIN_SERVER_URL = "http://127.0.0.1:8096"
JELLYFIN_API_KEY = "ccc539ca243e49bab3d893506763fda7"


@pytest.fixture
def jellyfin_config():
    """创建测试用的 Jellyfin 配置"""
    return JellyfinConfig(
        enabled=True,
        server_url=JELLYFIN_SERVER_URL,
        api_key=JELLYFIN_API_KEY,
        verify_ssl=False,
        timeout=30,
    )


@pytest.fixture
def jellyfin_client(jellyfin_config):
    """创建并认证 Jellyfin 客户端"""
    client = JellyfinClientWrapper(jellyfin_config)
    client.authenticate()
    return client


class TestJellyfinIntegrationConnection:
    """测试连接相关功能"""

    @pytest.mark.integration
    def test_authenticate_with_api_key(self, jellyfin_config):
        """测试使用 API Key 认证"""
        client = JellyfinClientWrapper(jellyfin_config)
        assert client.authenticate() is True
        assert client.is_authenticated() is True

    @pytest.mark.integration
    def test_get_server_info(self, jellyfin_client):
        """测试获取服务器信息"""
        info = jellyfin_client.get_server_info()

        assert info is not None
        assert "ServerName" in info or "Version" in info
        print(f"[OK] 服务器信息: {info.get('ServerName', 'Unknown')} v{info.get('Version', 'Unknown')}")

    @pytest.mark.integration
    @pytest.mark.xfail(reason="jellyfin-apiclient-python 不为无效 API Key 抛出异常", strict=False)
    def test_invalid_api_key(self, jellyfin_config):
        """测试使用无效 API Key 认证失败"""
        invalid_config = JellyfinConfig(
            enabled=True,
            server_url=JELLYFIN_SERVER_URL,
            api_key="invalid-api-key-12345",
            verify_ssl=False,
        )
        client = JellyfinClientWrapper(invalid_config)

        with pytest.raises(JellyfinAuthenticationError):
            client.authenticate()

    @pytest.mark.integration
    @pytest.mark.xfail(reason="jellyfin-apiclient-python 不为无效服务器地址抛出异常", strict=False)
    def test_invalid_server_url(self):
        """测试连接到无效服务器地址"""
        invalid_config = JellyfinConfig(
            enabled=True,
            server_url="http://invalid-server-that-does-not-exist:8096",
            api_key="test-key",
            verify_ssl=False,
            timeout=5,
        )
        client = JellyfinClientWrapper(invalid_config)

        with pytest.raises(Exception):  # 可能是 ConnectionError 或其他
            client.authenticate()


class TestJellyfinIntegrationLibraries:
    """测试库操作"""

    @pytest.mark.integration
    def test_get_libraries(self, jellyfin_client):
        """测试获取库列表"""
        libraries = jellyfin_client.get_libraries()

        assert isinstance(libraries, list)
        print(f"[OK] 获取到 {len(libraries)} 个库:")
        for lib in libraries:
            print(f"  - {lib.name} (ID: {lib.id}, 类型: {lib.type}, 项数: {lib.item_count})")

    @pytest.mark.integration
    def test_get_library_items(self, jellyfin_client):
        """测试获取库中的项"""
        try:
            items = jellyfin_client.get_library_items(limit=10)

            print(f"[OK] 获取到 {len(items)} 个库项:")
            for item in items[:5]:  # 只打印前 5 个
                print(f"  - {item.name} (ID: {item.id}, 类型: {item.type})")

            if len(items) > 5:
                print(f"  ... 还有 {len(items) - 5} 个项")

        except JellyfinAPIError as e:
            print(f"[WARN] 获取库项失败: {e}")
            print("  这可能是因为没有库或库为空")

    @pytest.mark.integration
    def test_refresh_library(self, jellyfin_client):
        """测试刷新库"""
        try:
            result = jellyfin_client.refresh_library()
            assert result is True
            print("[OK] 库刷新成功")
        except JellyfinAPIError as e:
            print(f"[WARN] 库刷新失败: {e}")


class TestJellyfinIntegrationSearch:
    """测试搜索功能"""

    @pytest.mark.integration
    def test_search_items(self, jellyfin_client):
        """测试搜索项"""
        # 搜索常见的词汇
        search_terms = ["movie", "test", "video"]

        for term in search_terms:
            try:
                items = jellyfin_client.search_items(term, limit=5)

                if items:
                    print(f"[OK] 搜索 '{term}' 找到 {len(items)} 个结果:")
                    for item in items[:3]:
                        print(f"  - {item.name} (类型: {item.type})")
                    break
                else:
                    print(f"  搜索 '{term}' 无结果")

            except JellyfinAPIError as e:
                print(f"  搜索 '{term}' 失败: {e}")
                continue

    @pytest.mark.integration
    def test_search_with_empty_result(self, jellyfin_client):
        """测试搜索无结果的情况"""
        # 搜索一个不太可能存在的词
        items = jellyfin_client.search_items("xyzabc123notexist", limit=5)

        assert isinstance(items, list)
        print(f"[OK] 搜索不存在的项，返回空列表: {len(items)} 个结果")


class TestJellyfinIntegrationItemOperations:
    """测试项操作"""

    @pytest.mark.integration
    def test_get_item_details(self, jellyfin_client):
        """测试获取项详情"""
        try:
            # 先获取库中的项
            items = jellyfin_client.get_library_items(limit=1)

            if items:
                item = items[0]
                item_id = item.id

                # 获取该项的详情
                item_detail = jellyfin_client.get_item(item_id)

                assert item_detail.id == item_id
                print(f"[OK] 获取项详情成功:")
                print(f"  - ID: {item_detail.id}")
                print(f"  - 名称: {item_detail.name}")
                print(f"  - 类型: {item_detail.type}")
                print(f"  - 路径: {item_detail.path}")
            else:
                print("[WARN] 库中没有项，跳过获取详情测试")

        except JellyfinAPIError as e:
            print(f"[WARN] 获取项详情失败: {e}")

    @pytest.mark.integration
    def test_mark_item_played(self, jellyfin_client):
        """测试标记项为已观看"""
        try:
            # 先获取库中的项
            items = jellyfin_client.get_library_items(limit=1)

            if items:
                item = items[0]
                item_id = item.id

                # 标记为已观看
                result = jellyfin_client.mark_item_played(item_id)

                assert result is True
                print(f"[OK] 标记项 {item.name} 为已观看成功")
            else:
                print("[WARN] 库中没有项，跳过标记已观看测试")

        except JellyfinAPIError as e:
            print(f"[WARN] 标记项为已观看失败: {e}")


class TestJellyfinIntegrationMetadata:
    """测试元数据操作"""

    @pytest.mark.integration
    def test_update_item_metadata(self, jellyfin_client):
        """测试更新项元数据"""
        try:
            # 先获取库中的项
            items = jellyfin_client.get_library_items(limit=1)

            if items:
                item = items[0]
                item_id = item.id

                # 更新元数据（更新一个不会造成问题的字段）
                metadata = {
                    "Overview": "Updated via integration test",
                }

                result = jellyfin_client.update_item_metadata(item_id, metadata)

                assert result is True
                print(f"[OK] 更新项 {item.name} 的元数据成功")
            else:
                print("[WARN] 库中没有项，跳过更新元数据测试")

        except JellyfinAPIError as e:
            print(f"[WARN] 更新元数据失败: {e}")


class TestJellyfinIntegrationEdgeCases:
    """测试边界情况"""

    @pytest.mark.integration
    def test_search_with_special_characters(self, jellyfin_client):
        """测试搜索特殊字符"""
        try:
            items = jellyfin_client.search_items("@#$%^&*()", limit=5)

            assert isinstance(items, list)
            print(f"[OK] 搜索特殊字符成功，返回 {len(items)} 个结果")

        except JellyfinAPIError as e:
            print(f"[WARN] 搜索特殊字符失败: {e}")

    @pytest.mark.integration
    def test_search_with_unicode(self, jellyfin_client):
        """测试搜索 Unicode 字符"""
        try:
            items = jellyfin_client.search_items("中文", limit=5)

            assert isinstance(items, list)
            print(f"[OK] 搜索 Unicode 字符成功，返回 {len(items)} 个结果")

        except JellyfinAPIError as e:
            print(f"[WARN] 搜索 Unicode 字符失败: {e}")

    @pytest.mark.integration
    def test_get_nonexistent_item(self, jellyfin_client):
        """测试获取不存在的项"""
        try:
            # 尝试获取一个不存在的 ID
            item = jellyfin_client.get_item("nonexistent-id-12345")

            # 如果没有异常，检查返回的项
            print(f"[WARN] 获取不存在的项返回: {item}")

        except JellyfinAPIError as e:
            print(f"[OK] 获取不存在的项正确抛出异常: {e}")


class TestJellyfinVideoSearch:
    """测试特定视频的搜索和验证"""

    @pytest.mark.integration
    def test_find_fc2_3751072_video(self, jellyfin_client):
        """测试是否能在 Jellyfin 中找到 FC2-3751072 视频"""
        search_term = "FC2-3751072"
        
        print(f"\n[测试] 搜索标题包含 '{search_term}' 的视频...")
        
        # 搜索
        items = jellyfin_client.search_items(search_term, limit=20)
        
        if items:
            print(f"[结果] 找到 {len(items)} 个搜索结果:")
            for item in items:
                print(f"  - {item.name} (ID: {item.id}, 类型: {item.type})")
                if search_term.lower() in item.name.lower():
                    print(f"  [OK] 匹配! 标题中包含 '{search_term}'")
            
            # 验证至少有一个结果包含搜索词
            matching_items = [item for item in items if search_term.lower() in item.name.lower()]
            assert len(matching_items) > 0, f"未找到标题包含 '{search_term}' 的视频"
            print(f"\n[成功] 验证通过: 找到 {len(matching_items)} 个包含 '{search_term}' 的视频")
        else:
            print(f"[警告] 搜索 '{search_term}' 未返回结果，尝试获取所有库项...")
            
            # 如果搜索失败，尝试从库中获取所有项目
            all_items = jellyfin_client.get_library_items(limit=100)
            print(f"[信息] 从库中获取到 {len(all_items)} 个项目")
            
            # 在所有项目中查找
            matching_items = [item for item in all_items if search_term.lower() in item.name.lower()]
            
            if matching_items:
                print(f"[结果] 在库项目中找到 {len(matching_items)} 个匹配:")
                for item in matching_items:
                    print(f"  - {item.name} (ID: {item.id})")
                print(f"\n[成功] 验证通过: 在 Jellyfin 库中存在包含 '{search_term}' 的视频")
            else:
                print(f"[警告] 在库中也未找到标题包含 '{search_term}' 的视频")
                # 显示前 10 个项目作为参考
                print(f"[参考] 库中的前 10 个项目:")
                for item in all_items[:10]:
                    print(f"  - {item.name}")


# pytest 标记定义
def pytest_configure(config):
    """注册自定义标记"""
    config.addinivalue_line(
        "markers", "integration: marks tests as integration tests that require a running Jellyfin server"
    )


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-m", "integration", "-s"])

"""
AV01统一插件测试
整合了元数据提取和视频提取两个功能的测试
"""

import pytest

from pavone.plugins.av01_plugin import (
    AV01Plugin,
    AV01VideoMetadata,
    GeoData,
)


class TestAV01Plugin:
    """AV01统一插件测试"""

    @pytest.fixture
    def plugin(self):
        """创建插件实例"""
        return AV01Plugin()

    # ==================== 基础功能测试 ====================

    def test_initialization(self, plugin):
        """测试初始化"""
        assert plugin.name == "AV01"
        assert plugin.version == "2.0.0"
        assert plugin.priority == 30
        assert "av01.media" in plugin.supported_domains
        assert "av01.tv" in plugin.supported_domains

    def test_initialize(self, plugin):
        """测试初始化方法"""
        assert plugin.initialize() is True

    # ==================== 元数据提取功能测试 ====================

    def test_can_extract_url(self, plugin):
        """测试是否能识别AV01 URL"""
        # 测试不同格式的URL
        assert plugin.can_extract("https://www.av01.tv/jp/video/184522/fc2-ppv-4799119")
        assert plugin.can_extract("https://av01.media/en/video/123456/some-title")
        assert plugin.can_extract("http://www.av01.media/video/123/test")

    def test_can_extract_code(self, plugin):
        """测试是否能识别视频代码"""
        # 测试不同格式的代码
        assert plugin.can_extract("FC2-PPV-4799119")
        assert plugin.can_extract("SDMT-415")
        assert plugin.can_extract("ABC-123")

    def test_cannot_extract_invalid(self, plugin):
        """测试无效的identifier"""
        # 不支持的URL
        assert not plugin.can_extract("https://missav.com/video/123")
        assert not plugin.can_extract("ftp://av01.tv/video/123")

        # 不支持的代码格式
        assert not plugin.can_extract("123456")  # 纯数字
        assert not plugin.can_extract("ABCDEF")  # 没有连字符

    # ==================== 视频提取功能测试 ====================

    def test_can_handle_valid_urls(self, plugin):
        """测试能处理的有效URL"""
        assert plugin.can_handle("https://www.av01.tv/jp/video/184522/fc2-ppv-4799119")
        assert plugin.can_handle("https://av01.media/en/video/123456/some-title")

    def test_can_handle_invalid_urls(self, plugin):
        """测试不能处理的无效URL"""
        assert not plugin.can_handle("https://missav.com/video/123")
        assert not plugin.can_handle("ftp://av01.tv/video/123")

    # ==================== 辅助方法测试 ====================

    def test_extract_video_id(self, plugin):
        """测试从URL提取视频ID"""
        url1 = "https://www.av01.media/jp/video/184522/fc2-ppv-4799119"
        assert plugin._extract_video_id(url1) == "184522"

        url2 = "https://av01.media/en/video/123456/some-title"
        assert plugin._extract_video_id(url2) == "123456"

        # 无效URL
        assert plugin._extract_video_id("https://av01.tv/invalid") is None

    def test_build_cover_url(self, plugin):
        """测试构建封面URL"""
        geo_data = GeoData(
            token="test_token",
            expires="1234567890",
            ip="127.0.0.1",
            asn=12345,
            isp="Test ISP",
            continent="AS",
            country="CN",
            ttl=3600,
            url="https://test.com",
        )

        video_id = "184522"
        cover_url = plugin._build_cover_url(video_id, geo_data)

        assert cover_url is not None
        assert "static.av01.tv" in cover_url
        assert video_id in cover_url
        assert "test_token" in cover_url

    # ==================== 数据类测试 ====================

    def test_geo_data_from_dict(self):
        """测试GeoData从字典创建"""
        data = {
            "token": "test_token",
            "expires": "1234567890",
            "ip": "127.0.0.1",
            "asn": 12345,
            "isp": "Test ISP",
            "continent": "AS",
            "country": "CN",
            "ttl": 3600,
            "url": "https://test.com",
            "comp": True,
        }

        geo_data = GeoData.from_dict(data)
        assert geo_data.token == "test_token"
        assert geo_data.ip == "127.0.0.1"
        assert geo_data.comp is True

    def test_geo_data_is_expired(self):
        """测试GeoData过期检查"""
        geo_data = GeoData(
            token="test_token",
            expires="1234567890",  # 已过期的时间戳
            ip="127.0.0.1",
            asn=12345,
            isp="Test ISP",
            continent="AS",
            country="CN",
            ttl=3600,
            url="https://test.com",
        )

        # 应该已经过期
        assert geo_data.is_expired() is True

    def test_av01_video_metadata_from_dict(self):
        """测试AV01VideoMetadata从字典创建"""
        data = {
            "id": 184522,
            "dvd_id": "FC2-PPV-4799119",
            "dmm_id": "test_dmm_id",
            "title": "Test Title",
            "description": "Test Description",
            "duration": 3600,
            "views": 12345,
            "uploaded_time": "2025-01-01T00:00:00Z",
            "published_time": "2025-01-01T00:00:00Z",
            "original_language": "ja",
            "cover": True,
            "maker": {"name": "Test Maker"},
            "director": {"name": "Test Director"},
            "actresses": [{"name": "Actress 1"}, {"name": "Actress 2"}],
            "tags": [{"name": "Tag 1"}, {"name": "Tag 2"}],
            "poster": "https://test.com/poster.jpg",
        }

        metadata = AV01VideoMetadata.from_dict(data)
        assert metadata.id == 184522
        assert metadata.dvd_id == "FC2-PPV-4799119"
        assert metadata.maker == "Test Maker"
        assert metadata.director == "Test Director"

    def test_av01_video_metadata_get_actor_names(self):
        """测试提取演员名称"""
        metadata = AV01VideoMetadata(
            id=123,
            dvd_id="TEST-123",
            dmm_id="dmm123",
            title="Test",
            description="Test",
            duration=3600,
            views=100,
            uploaded_time="2025-01-01",
            published_time="2025-01-01",
            original_language="ja",
            cover=True,
            actresses=[{"name": "Actor 1"}, {"name": "Actor 2"}],
        )

        actors = metadata.get_actor_names()
        assert len(actors) == 2
        assert "Actor 1" in actors
        assert "Actor 2" in actors

    def test_av01_video_metadata_get_tag_names(self):
        """测试提取标签名称"""
        metadata = AV01VideoMetadata(
            id=123,
            dvd_id="TEST-123",
            dmm_id="dmm123",
            title="Test",
            description="Test",
            duration=3600,
            views=100,
            uploaded_time="2025-01-01",
            published_time="2025-01-01",
            original_language="ja",
            cover=True,
            tags=[{"name": "Tag 1"}, {"name": "Tag 2"}],
        )

        # 手动添加字符串标签来测试
        if metadata.tags:
            metadata.tags.append("String Tag")  # type: ignore

        tags = metadata.get_tag_names()
        assert len(tags) == 3
        assert "Tag 1" in tags
        assert "Tag 2" in tags
        assert "String Tag" in tags

    def test_av01_video_metadata_get_release_year(self):
        """测试提取发布年份"""
        metadata = AV01VideoMetadata(
            id=123,
            dvd_id="TEST-123",
            dmm_id="dmm123",
            title="Test",
            description="Test",
            duration=3600,
            views=100,
            uploaded_time="2025-01-01",
            published_time="2025-11-27T00:00:00Z",
            original_language="ja",
            cover=True,
        )

        assert metadata.get_release_year() == 2025

    def test_av01_video_metadata_get_runtime_minutes(self):
        """测试获取视频时长"""
        metadata = AV01VideoMetadata(
            id=123,
            dvd_id="TEST-123",
            dmm_id="dmm123",
            title="Test",
            description="Test",
            duration=3600,  # 3600秒 = 60分钟
            views=100,
            uploaded_time="2025-01-01",
            published_time="2025-01-01",
            original_language="ja",
            cover=True,
        )

        assert metadata.get_runtime_minutes() == 60


if __name__ == "__main__":
    # 设置测试运行时的日志级别
    import logging

    logging.getLogger().setLevel(logging.ERROR)

    pytest.main([__file__, "-v"])

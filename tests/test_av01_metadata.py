"""
测试 AV01 元数据提取器
"""

import pytest

from pavone.plugins.metadata.av01_metadata import (
    AV01Metadata,
    AV01VideoMetadata,
    GeoData,
)


class TestAV01Metadata:
    """测试 AV01 元数据提取器"""

    @pytest.fixture
    def extractor(self):
        """创建提取器实例"""
        return AV01Metadata()

    def test_can_extract_url(self, extractor):
        """测试URL识别"""
        # 支持的URL
        assert extractor.can_extract("https://www.av01.tv/jp/video/184522/fc2-ppv-4799119")
        assert extractor.can_extract("https://av01.media/en/video/123456/some-title")
        assert extractor.can_extract("http://www.av01.media/video/123/test")

        # 不支持的URL
        assert not extractor.can_extract("https://missav.com/video/123")
        assert not extractor.can_extract("ftp://av01.tv/video/123")

    def test_can_extract_code(self, extractor):
        """测试视频代码识别"""
        # 支持的代码格式
        assert extractor.can_extract("FC2-PPV-4799119")
        assert extractor.can_extract("SDMT-415")
        assert extractor.can_extract("ABC-123")

        # 不支持的代码格式
        assert not extractor.can_extract("123456")  # 纯数字
        assert not extractor.can_extract("ABCDEF")  # 没有连字符

    def test_extract_video_id(self, extractor):
        """测试从URL提取视频ID"""
        url1 = "https://www.av01.media/jp/video/184522/fc2-ppv-4799119"
        assert extractor._extract_video_id(url1) == "184522"

        url2 = "https://av01.media/en/video/123456/some-title"
        assert extractor._extract_video_id(url2) == "123456"

        url3 = "https://av01.tv/video/789"
        assert extractor._extract_video_id(url3) == "789"

        # 无效URL
        assert extractor._extract_video_id("https://av01.tv/page/123") is None

    def test_build_cover_url(self, extractor):
        """测试构建封面URL"""
        geo_data = GeoData(
            token="test_token_12345",
            expires="1234567890",
            ip="192.168.1.1",
            asn=12345,
            isp="Test ISP",
            continent="AS",
            country="JP",
            ttl=3600,
            url="https://test.com",
        )

        video_id = "184522"
        cover_url = extractor._build_cover_url(video_id, geo_data)

        assert cover_url is not None
        assert "static.av01.tv" in cover_url
        assert video_id in cover_url
        assert "test_token_12345" in cover_url
        assert "1234567890" in cover_url
        assert "192.168.1.1" in cover_url


class TestGeoData:
    """测试 GeoData 数据类"""

    def test_from_dict(self):
        """测试从字典创建实例"""
        data = {
            "token": "abc123",
            "expires": "1234567890",
            "ip": "1.2.3.4",
            "asn": 12345,
            "isp": "Test ISP",
            "continent": "AS",
            "country": "JP",
            "ttl": 3600,
            "url": "https://test.com",
            "comp": True,
        }

        geo = GeoData.from_dict(data)
        assert geo.token == "abc123"
        assert geo.expires == "1234567890"
        assert geo.ip == "1.2.3.4"
        assert geo.asn == 12345
        assert geo.comp is True

    def test_from_dict_missing_fields(self):
        """测试缺少必需字段时抛出异常"""
        data = {"token": "abc123"}

        with pytest.raises(ValueError, match="缺少必需字段"):
            GeoData.from_dict(data)

    def test_is_expired(self):
        """测试过期检查"""
        import time

        current = time.time()

        # 未过期
        geo1 = GeoData(
            token="test",
            expires=str(current + 3600),  # 1小时后过期
            ip="1.2.3.4",
            asn=12345,
            isp="Test",
            continent="AS",
            country="JP",
            ttl=3600,
            url="https://test.com",
        )
        assert not geo1.is_expired()

        # 已过期
        geo2 = GeoData(
            token="test",
            expires=str(current - 3600),  # 1小时前过期
            ip="1.2.3.4",
            asn=12345,
            isp="Test",
            continent="AS",
            country="JP",
            ttl=3600,
            url="https://test.com",
        )
        assert geo2.is_expired()


class TestAV01VideoMetadata:
    """测试 AV01VideoMetadata 数据类"""

    def test_from_dict(self):
        """测试从字典创建实例"""
        data = {
            "id": 184522,
            "dvd_id": "FC2-PPV-4799119",
            "dmm_id": "test_dmm",
            "title": "Test Video",
            "description": "Test description",
            "duration": 3600,
            "views": 1000,
            "uploaded_time": "2025-01-01T00:00:00Z",
            "published_time": "2025-01-01T00:00:00Z",
            "original_language": "ja",
            "cover": True,
            "maker": {"name": "Test Maker"},
            "director": "Test Director",
            "actresses": [{"name": "Actor 1"}, {"name": "Actor 2"}],
            "tags": [{"name": "Tag 1"}, "Tag 2"],
            "poster": "https://test.com/poster.jpg",
        }

        metadata = AV01VideoMetadata.from_dict(data)
        assert metadata.id == 184522
        assert metadata.dvd_id == "FC2-PPV-4799119"
        assert metadata.title == "Test Video"
        assert metadata.maker == "Test Maker"
        assert metadata.director == "Test Director"

    def test_get_actor_names(self):
        """测试提取演员名称"""
        metadata = AV01VideoMetadata(
            id=1,
            dvd_id="TEST-001",
            dmm_id="test",
            title="Test",
            description="Test",
            duration=3600,
            views=1000,
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

    def test_get_tag_names(self):
        """测试提取标签名称"""
        metadata = AV01VideoMetadata(
            id=1,
            dvd_id="TEST-001",
            dmm_id="test",
            title="Test",
            description="Test",
            duration=3600,
            views=1000,
            uploaded_time="2025-01-01",
            published_time="2025-01-01",
            original_language="ja",
            cover=True,
            tags=[{"name": "Tag 1"}, {"name": "Tag 2"}],
        )

        tags = metadata.get_tag_names()
        assert len(tags) == 2
        assert "Tag 1" in tags
        assert "Tag 2" in tags

    def test_get_release_year(self):
        """测试提取发布年份"""
        # ISO 8601 格式
        metadata1 = AV01VideoMetadata(
            id=1,
            dvd_id="TEST-001",
            dmm_id="test",
            title="Test",
            description="Test",
            duration=3600,
            views=1000,
            uploaded_time="2025-01-01",
            published_time="2025-11-27T00:00:00Z",
            original_language="ja",
            cover=True,
        )
        assert metadata1.get_release_year() == 2025

        # 简单格式
        metadata2 = AV01VideoMetadata(
            id=1,
            dvd_id="TEST-001",
            dmm_id="test",
            title="Test",
            description="Test",
            duration=3600,
            views=1000,
            uploaded_time="2024-01-01",
            published_time="2024-05-10",
            original_language="ja",
            cover=True,
        )
        assert metadata2.get_release_year() == 2024

    def test_get_runtime_minutes(self):
        """测试获取时长（分钟）"""
        metadata = AV01VideoMetadata(
            id=1,
            dvd_id="TEST-001",
            dmm_id="test",
            title="Test",
            description="Test",
            duration=3600,  # 3600秒 = 60分钟
            views=1000,
            uploaded_time="2025-01-01",
            published_time="2025-01-01",
            original_language="ja",
            cover=True,
        )

        assert metadata.get_runtime_minutes() == 60

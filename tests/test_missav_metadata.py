"""
Missav元数据提取器测试
"""

import pytest

from pavone.plugins.metadata import MissavMetadata


class TestMissavMetadata:
    """测试MissavMetadata提取器"""

    def test_can_extract_url(self):
        """测试是否能识别Missav URL"""
        extractor = MissavMetadata()
        
        # 测试不同格式的URL
        assert extractor.can_extract("https://missav.ai/ja/sdmt-415")
        assert extractor.can_extract("https://www.missav.ai/ja/test-123")
        assert extractor.can_extract("https://missav.com/en/video-456")
        assert extractor.can_extract("https://www.missav.com/en/another-789")

    def test_can_extract_code(self):
        """测试是否能识别视频代码"""
        extractor = MissavMetadata()
        
        # 测试不同格式的代码
        assert extractor.can_extract("SDMT-415")
        assert extractor.can_extract("sdmt-415")
        assert extractor.can_extract("TEST-123")
        assert extractor.can_extract("test-456")

    def test_cannot_extract_invalid(self):
        """测试无效的identifier"""
        extractor = MissavMetadata()
        
        # 测试无效格式
        assert not extractor.can_extract("ftp://example.com")
        assert not extractor.can_extract("invalid string")
        assert not extractor.can_extract("123-456-789")  # 太多分隔符
        assert not extractor.can_extract("")

    def test_extract_metadata_url_requires_network(self):
        """
        测试从URL提取元数据（需要网络）
        
        这是一个集成测试，实际测试时需要网络连接
        """
        extractor = MissavMetadata()
        
        # 这个测试需要实际的网络连接
        # 可以使用mock来避免网络依赖
        url = "https://missav.ai/ja/sdmt-415"
        
        if not extractor.can_extract(url):
            pytest.skip("Invalid URL format")

    def test_extract_metadata_code_not_supported(self):
        """测试从代码提取元数据（当前不支持）"""
        extractor = MissavMetadata()
        
        # 当前实现中，直接使用代码format会返回None
        result = extractor.extract_metadata("SDMT-415")
        
        # 应该返回None，因为还需要实现搜索功能
        assert result is None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

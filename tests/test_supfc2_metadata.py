"""
SupFC2元数据提取器测试
"""

import pytest

from pavone.plugins.metadata.supfc2_metadata import SupFC2Metadata


class TestSupFC2Metadata:
    """测试SupFC2Metadata提取器"""

    def test_can_extract_url(self):
        """测试是否能识别SupFC2 URL"""
        extractor = SupFC2Metadata()

        # 测试不同格式的URL
        assert extractor.can_extract("https://supfc2.com/detail/FC2-PPV-1482027/【完全素人85】ミライ19才その３")
        assert extractor.can_extract("https://www.supfc2.com/detail/FC2-PPV-123456/test-title")
        assert extractor.can_extract("http://supfc2.com/detail/FC2-PPV-789012/title")

    def test_can_extract_fc2_code(self):
        """测试是否能识别FC2代码"""
        extractor = SupFC2Metadata()

        # 测试不同格式的FC2代码
        assert extractor.can_extract("FC2-PPV-1482027")
        assert extractor.can_extract("FC2-1482027")
        assert extractor.can_extract("1482027")
        assert extractor.can_extract("fc2-ppv-1482027")
        assert extractor.can_extract("FC2_PPV_1482027")
        assert extractor.can_extract("FC2PPV1482027")

    def test_cannot_extract_invalid(self):
        """测试无效的identifier"""
        extractor = SupFC2Metadata()

        # 测试无效格式
        assert not extractor.can_extract("ftp://example.com")
        assert not extractor.can_extract("invalid string")
        assert not extractor.can_extract("SDMT-415")  # 不是FC2格式
        assert not extractor.can_extract("")
        assert not extractor.can_extract("abc123")  # 不是纯数字

    def test_extract_fc2_id_from_code(self):
        """测试从代码提取FC2 ID"""
        extractor = SupFC2Metadata()

        assert extractor._extract_fc2_id("FC2-PPV-1482027") == "1482027"
        assert extractor._extract_fc2_id("FC2-1482027") == "1482027"
        assert extractor._extract_fc2_id("1482027") == "1482027"
        assert extractor._extract_fc2_id("fc2-ppv-1482027") == "1482027"
        assert extractor._extract_fc2_id("FC2_PPV_1482027") == "1482027"

    def test_extract_fc2_id_from_url(self):
        """测试从URL提取FC2 ID"""
        extractor = SupFC2Metadata()

        url = "https://supfc2.com/detail/FC2-PPV-1482027/【完全素人85】"
        assert extractor._extract_fc2_id_from_url(url) == "1482027"

        url2 = "https://www.supfc2.com/detail/fc2-ppv-123456/title"
        assert extractor._extract_fc2_id_from_url(url2) == "123456"

    def test_extract_metadata_from_html(self):
        """测试从HTML提取元数据"""
        extractor = SupFC2Metadata()

        # 读取测试HTML文件
        with open("tests/sites/supfc2.html", "r", encoding="utf-8") as f:
            html_content = f.read()

        # 测试各个提取方法
        title = extractor._extract_title(html_content)
        assert title == "【完全素人85】ミライ19才その３、おまたせしました大人気のちっぱいピュア美少女第三段"

        fc2_id = extractor._extract_fc2_id_from_page(html_content)
        assert fc2_id == "1482027"

        release_date = extractor._extract_release_date(html_content)
        assert release_date == "2020-08-26"

        maker = extractor._extract_maker(html_content)
        assert maker == "ヒメドウガ"

        duration = extractor._extract_duration(html_content)
        assert duration == 62  # 01:02:12 = 62分钟

        tags = extractor._extract_tags(html_content)
        assert len(tags) > 0  # 应该提取到多个标签
        assert "UNKNOWN" not in tags  # UNKNOWN应该被过滤掉

        genres = extractor._extract_genres(html_content)
        assert "素人" in genres

        rating = extractor._extract_rating(html_content)
        assert rating == 10.0  # width: 100% = 10.0分

        description = extractor._extract_description(html_content)
        assert description is not None
        assert "ヒメドウガでございます" in description
        # 确保图片链接被移除
        assert "<a" not in description
        assert "data-fancybox" not in description

        cover, background = extractor._extract_images(html_content)
        assert cover is not None
        assert "storage23000.contents.fc2.com" in cover
        assert background is not None

    def test_extract_metadata_url_mock(self):
        """测试从URL提取元数据（使用本地HTML文件模拟）"""
        # 这里应该使用mock来避免实际的网络请求
        # 实际测试时可以使用pytest-mock或unittest.mock
        pass

    def test_extract_metadata_from_code(self):
        """测试从代码提取元数据（需要构建URL）"""
        extractor = SupFC2Metadata()

        # 测试代码格式
        # 这个测试需要实际的网络连接或mock
        code = "FC2-PPV-1482027"
        assert extractor.can_extract(code)

        # 验证URL构建逻辑
        fc2_id = extractor._extract_fc2_id(code)
        expected_url = f"https://supfc2.com/detail/FC2-PPV-{fc2_id}/"
        assert expected_url == "https://supfc2.com/detail/FC2-PPV-1482027/"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

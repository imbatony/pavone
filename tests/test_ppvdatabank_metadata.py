"""
测试 PPVDataBank 元数据提取器
"""

import pytest

from pavone.plugins.metadata.ppvdatabank_metadata import PPVDataBankMetadata


class TestPPVDataBankMetadata:
    """测试 PPVDataBank 元数据提取器"""

    @pytest.fixture
    def extractor(self):
        """创建提取器实例"""
        return PPVDataBankMetadata()

    def test_can_extract_url(self, extractor):
        """测试URL识别"""
        # 支持的URL
        assert extractor.can_extract("https://ppvdatabank.com/article_search.php?id=2941579")
        assert extractor.can_extract("http://www.ppvdatabank.com/article_search.php?id=123456")
        assert extractor.can_extract("https://ppvdatabank.com/article/4802082/")
        assert extractor.can_extract("https://ppvdatabank.com/article/123456")

        # 不支持的URL
        assert not extractor.can_extract("https://missav.com/video/123")
        assert not extractor.can_extract("ftp://ppvdatabank.com/article_search.php?id=123")

    def test_can_extract_code(self, extractor):
        """测试视频代码识别"""
        # 支持的代码格式
        assert extractor.can_extract("FC2-2941579")
        assert extractor.can_extract("FC2-PPV-2941579")
        assert extractor.can_extract("fc2-1234567")
        assert extractor.can_extract("fc2-ppv-1234567")

        # 不支持的代码格式
        assert not extractor.can_extract("SDMT-415")  # 不是FC2
        assert not extractor.can_extract("123456")  # 纯数字
        assert not extractor.can_extract("FC2")  # 没有ID

    def test_extract_video_id(self, extractor):
        """测试从URL提取视频ID"""
        url1 = "https://ppvdatabank.com/article_search.php?id=2941579"
        assert extractor._extract_video_id(url1) == "2941579"

        url2 = "https://www.ppvdatabank.com/article_search.php?id=123456"
        assert extractor._extract_video_id(url2) == "123456"

        url3 = "https://ppvdatabank.com/article/4802082/"
        assert extractor._extract_video_id(url3) == "4802082"

        url4 = "https://ppvdatabank.com/article/123456"
        assert extractor._extract_video_id(url4) == "123456"

        # 无效URL
        assert extractor._extract_video_id("https://ppvdatabank.com/page/123") is None

    def test_extract_id_from_code(self, extractor):
        """测试从FC2代码提取ID"""
        assert extractor._extract_id_from_code("FC2-2941579") == "2941579"
        assert extractor._extract_id_from_code("FC2-PPV-2941579") == "2941579"
        assert extractor._extract_id_from_code("fc2-1234567") == "1234567"
        assert extractor._extract_id_from_code("fc2-ppv-1234567") == "1234567"

        # 无效代码
        assert extractor._extract_id_from_code("SDMT-415") is None

    def test_extract_title(self, extractor):
        """测试从HTML提取标题"""
        with open("tests/sites/ppvdatabank.html", "r", encoding="utf-8") as f:
            html = f.read()

        title = extractor._extract_title(html)
        assert title == "あどけない顔をした訳あり美少女。発展途上なまろやか巨乳に大量中出し！！"

    def test_extract_studio(self, extractor):
        """测试从HTML提取制作人"""
        with open("tests/sites/ppvdatabank.html", "r", encoding="utf-8") as f:
            html = f.read()

        studio = extractor._extract_studio(html)
        assert studio == "レッド・D・キング"

    def test_extract_release_date(self, extractor):
        """测试从HTML提取发布日期"""
        with open("tests/sites/ppvdatabank.html", "r", encoding="utf-8") as f:
            html = f.read()

        release_date = extractor._extract_release_date(html)
        assert release_date == "2022-06-05"

    def test_extract_runtime(self, extractor):
        """测试从HTML提取时长"""
        with open("tests/sites/ppvdatabank.html", "r", encoding="utf-8") as f:
            html = f.read()

        runtime = extractor._extract_runtime(html)
        assert runtime == 92  # 01:31:25 = 91分25秒，向上取整为92分钟

    def test_extract_cover_image(self, extractor):
        """测试从HTML提取封面图片"""
        with open("tests/sites/ppvdatabank.html", "r", encoding="utf-8") as f:
            html = f.read()

        cover = extractor._extract_cover_image(html, "2941579")
        assert cover == "https://ppvdatabank.com/article/2941579/img/thumb.webp"

    def test_extract_backdrop_image(self, extractor):
        """测试从HTML提取背景图片"""
        with open("tests/sites/ppvdatabank.html", "r", encoding="utf-8") as f:
            html = f.read()

        backdrop = extractor._extract_backdrop_image(html, "2941579")
        assert backdrop == "https://ppvdatabank.com/article/2941579/img/pl1.webp"

    def test_extract_metadata_from_url(self, extractor, mocker):
        """测试从URL提取完整元数据"""
        # 读取测试HTML文件
        with open("tests/sites/ppvdatabank.html", "r", encoding="utf-8") as f:
            html_content = f.read()

        # 模拟HTTP请求
        mock_response = mocker.Mock()
        mock_response.text = html_content
        mocker.patch.object(extractor, "fetch", return_value=mock_response)

        # 提取元数据
        url = "https://ppvdatabank.com/article_search.php?id=2941579"
        metadata = extractor.extract_metadata(url)

        # 验证元数据
        assert metadata is not None
        assert metadata.code == "FC2-2941579"
        assert metadata.title == "FC2-2941579 あどけない顔をした訳あり美少女。発展途上なまろやか巨乳に大量中出し！！"
        assert metadata.original_title == "あどけない顔をした訳あり美少女。発展途上なまろやか巨乳に大量中出し！！"
        assert metadata.studio == "レッド・D・キング"
        assert metadata.premiered == "2022-06-05"
        assert metadata.runtime == 92
        assert metadata.year == 2022
        assert metadata.cover == "https://ppvdatabank.com/article/2941579/img/thumb.webp"
        assert metadata.backdrop == "https://ppvdatabank.com/article/2941579/img/pl1.webp"
        assert metadata.site == "PPVDataBank"

    def test_extract_metadata_from_code(self, extractor, mocker):
        """测试从FC2代码提取完整元数据"""
        # 读取测试HTML文件
        with open("tests/sites/ppvdatabank.html", "r", encoding="utf-8") as f:
            html_content = f.read()

        # 模拟HTTP请求
        mock_response = mocker.Mock()
        mock_response.text = html_content
        mocker.patch.object(extractor, "fetch", return_value=mock_response)

        # 提取元数据
        code = "FC2-2941579"
        metadata = extractor.extract_metadata(code)

        # 验证元数据
        assert metadata is not None
        assert metadata.code == "FC2-2941579"
        assert metadata.title == "FC2-2941579 あどけない顔をした訳あり美少女。発展途上なまろやか巨乳に大量中出し！！"
        assert metadata.original_title == "あどけない顔をした訳あり美少女。発展途上なまろやか巨乳に大量中出し！！"

    def test_extract_metadata_from_ppv_code(self, extractor, mocker):
        """测试从FC2-PPV代码提取完整元数据"""
        # 读取测试HTML文件
        with open("tests/sites/ppvdatabank.html", "r", encoding="utf-8") as f:
            html_content = f.read()

        # 模拟HTTP请求
        mock_response = mocker.Mock()
        mock_response.text = html_content
        mocker.patch.object(extractor, "fetch", return_value=mock_response)

        # 提取元数据
        code = "FC2-PPV-2941579"
        metadata = extractor.extract_metadata(code)

        # 验证元数据
        assert metadata is not None
        assert metadata.code == "FC2-2941579"  # 标准化后的代码

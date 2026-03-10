"""
文件名解析器测试
"""

from pavone.utils.filename_parser import FilenameParser


class TestFilenameNormalization:
    """测试文件名正规化功能"""

    def test_remove_extension(self):
        """测试移除扩展名"""
        assert FilenameParser.normalize_filename("SSIS-123.mp4") == "SSIS-123"
        assert FilenameParser.normalize_filename("video.mkv") == "video"
        assert FilenameParser.normalize_filename("test.avi") == "test"

    def test_remove_brackets(self):
        """测试移除方括号内容"""
        assert FilenameParser.normalize_filename("[Jable]SSIS-123.mp4") == "SSIS-123"
        assert FilenameParser.normalize_filename("[FHD]ABC-123.mp4") == "ABC-123"
        assert FilenameParser.normalize_filename("[1080p][Jable]SSIS-123.mp4") == "SSIS-123"

    def test_remove_parentheses(self):
        """测试移除圆括号内容"""
        assert FilenameParser.normalize_filename("FC2-PPV-1234567(uncensored).mp4") == "FC2-PPV-1234567"
        assert FilenameParser.normalize_filename("ABC-123(leak).mp4") == "ABC-123"

    def test_remove_common_markers(self):
        """测试移除常见无用标记"""
        assert FilenameParser.normalize_filename("SSIS-123_uncensored.mp4") == "SSIS-123"
        assert FilenameParser.normalize_filename("ABC-123-uc.mp4") == "ABC-123"
        assert FilenameParser.normalize_filename("FC2-1234567_leak.mp4") == "FC2-1234567"
        assert FilenameParser.normalize_filename("SSIS-123-ch.mp4") == "SSIS-123"
        assert FilenameParser.normalize_filename("ABC-123_sub.mp4") == "ABC-123"

    def test_clean_separators(self):
        """测试清理多余分隔符"""
        # 下划线会被替换为连字符（多个下划线变为多个连字符）
        assert FilenameParser.normalize_filename("ABC___123.mp4") == "ABC---123"
        # 多个连字符会被保留（因为代码提取需要）
        assert FilenameParser.normalize_filename("ABC---123.mp4") == "ABC---123"
        # 多个空格会被压缩为单个空格
        assert FilenameParser.normalize_filename("ABC   123.mp4") == "ABC 123"

    def test_complex_filename(self):
        """测试复杂文件名"""
        filename = "[Jable][FHD]SSIS-123_uncensored_美少女(leak).mp4"
        normalized = FilenameParser.normalize_filename(filename)
        # 下划线会被转换为连字符
        assert "SSIS-123" in normalized
        assert "美少女" in normalized
        assert "[Jable]" not in normalized
        assert "uncensored" not in normalized
        # 预期结果: "SSIS-123-美少女"

    def test_preserve_chinese_japanese(self):
        """测试保留中文和日文字符"""
        # 下划线会被转换为连字符
        result1 = FilenameParser.normalize_filename("SSIS-123 美少女.mp4")
        assert "美少女" in result1
        assert "SSIS-123" in result1

        result2 = FilenameParser.normalize_filename("SSIS-123_美少女.mp4")
        assert "美少女" in result2
        # 下划线被转换为连字符
        assert "SSIS-123" in result2

    def test_empty_string(self):
        """测试空字符串"""
        assert FilenameParser.normalize_filename("") == ""

    def test_no_extension(self):
        """测试没有扩展名的文件名"""
        assert FilenameParser.normalize_filename("SSIS-123") == "SSIS-123"
        assert FilenameParser.normalize_filename("[Jable]SSIS-123") == "SSIS-123"


class TestCodeExtraction:
    """测试代码提取功能"""

    def test_extract_normal_code(self):
        """测试提取普通番号"""
        assert FilenameParser.extract_code("SSIS-123.mp4") == "SSIS-123"
        assert FilenameParser.extract_code("ABC-456.mkv") == "ABC-456"
        assert FilenameParser.extract_code("IPX-789.avi") == "IPX-789"

    def test_extract_code_with_brackets(self):
        """测试从带方括号的文件名提取番号"""
        assert FilenameParser.extract_code("[Jable]SSIS-123.mp4") == "SSIS-123"
        assert FilenameParser.extract_code("[FHD][1080p]ABC-456.mp4") == "ABC-456"

    def test_extract_code_with_markers(self):
        """测试从带标记的文件名提取番号"""
        assert FilenameParser.extract_code("SSIS-123_uncensored.mp4") == "SSIS-123"
        assert FilenameParser.extract_code("ABC-456-uc.mp4") == "ABC-456"
        assert FilenameParser.extract_code("FC2-PPV-1234567(leak).mp4") == "FC2-1234567"

    def test_extract_fc2_code(self):
        """测试提取FC2番号"""
        assert FilenameParser.extract_code("FC2-PPV-1234567.mp4") == "FC2-1234567"
        assert FilenameParser.extract_code("[Jable]FC2-PPV-1234567_uncensored.mp4") == "FC2-1234567"
        assert FilenameParser.extract_code("fc2ppv1234567.mp4") == "FC2-1234567"

    def test_extract_heyzo_code(self):
        """测试提取Heyzo番号"""
        assert FilenameParser.extract_code("Heyzo-1234.mp4") == "Heyzo-1234"
        assert FilenameParser.extract_code("[Jable]heyzo_1234.mp4") == "Heyzo-1234"

    def test_extract_heydouga_code(self):
        """测试提取Heydouga番号"""
        assert FilenameParser.extract_code("Heydouga-4017-123.mp4") == "Heydouga-4017-123"
        assert FilenameParser.extract_code("heydouga_4017_123.mp4") == "Heydouga-4017-123"

    def test_extract_tokyo_hot_code(self):
        """测试提取东热番号"""
        assert FilenameParser.extract_code("n1234.mp4") == "n1234"
        # k 系列番号(k+4位数字)只在包含"n"的上下文中匹配
        # 单独的 k1234 或 k5678 不会被匹配,因为 CodeExtractUtils 只检查 "n" in text
        assert FilenameParser.extract_code("k5678.mp4") is None
        assert FilenameParser.extract_code("k1234.mp4") is None
        # RED/SKY/EX 系列:
        # special_regrex_1: red[01]\d{2}|sky[0-3]\d{2}|ex0*0(?:0\d|\d0?)
        #   - 带连字符的会被 normal_regrex 匹配,保留连字符
        #   - 不带连字符的:如果首位符合(red 0-1, sky 0-3),匹配 special_regrex_1,大写且无连字符
        #   - 不带连字符的:如果首位不符合(如 sky4xx),匹配 normal_regrex_2,大写且有连字符
        assert FilenameParser.extract_code("RED-123.mp4") == "RED-123"  # normal_regrex
        assert FilenameParser.extract_code("RED123.mp4") == "RED123"  # special_regrex_1
        assert FilenameParser.extract_code("SKY-256.mp4") == "SKY-256"  # normal_regrex
        assert FilenameParser.extract_code("SKY256.mp4") == "SKY256"  # special_regrex_1 (首位2)
        assert FilenameParser.extract_code("SKY456.mp4") == "SKY-456"  # normal_regrex_2 (首位4不符合)

    def test_extract_code_from_path(self):
        """测试从完整路径提取番号"""
        assert FilenameParser.extract_code("/path/to/SSIS-123.mp4") == "SSIS-123"
        assert FilenameParser.extract_code("C:\\videos\\ABC-456.mp4") == "ABC-456"

    def test_extract_code_with_title(self):
        """测试从带标题的文件名提取番号"""
        assert FilenameParser.extract_code("SSIS-123 美少女.mp4") == "SSIS-123"
        assert FilenameParser.extract_code("ABC-456_美しい女性.mp4") == "ABC-456"

    def test_no_code_found(self):
        """测试无法提取番号的情况"""
        assert FilenameParser.extract_code("random_video.mp4") is None
        assert FilenameParser.extract_code("test.mp4") is None
        assert FilenameParser.extract_code("") is None

    def test_complex_filename(self):
        """测试复杂文件名"""
        filename = "[Jable][FHD]SSIS-123_uncensored_美少女(leak).mp4"
        assert FilenameParser.extract_code(filename) == "SSIS-123"


class TestMetadataHints:
    """测试元数据提示提取功能"""

    def test_extract_basic_hints(self):
        """测试提取基础元数据提示"""
        hints = FilenameParser.extract_metadata_hints("SSIS-123.mp4")
        assert hints["code"] == "SSIS-123"
        assert hints["normalized_name"] == "SSIS-123"
        assert hints["original_name"] == "SSIS-123"

    def test_extract_hints_with_title(self):
        """测试提取带标题的元数据提示"""
        hints = FilenameParser.extract_metadata_hints("SSIS-123 美少女.mp4")
        assert hints["code"] == "SSIS-123"
        assert "美少女" in hints["normalized_name"]
        assert "美少女" in hints["original_name"]

    def test_extract_hints_with_brackets(self):
        """测试提取带方括号的元数据提示"""
        hints = FilenameParser.extract_metadata_hints("[Jable]SSIS-123 美少女.mp4")
        assert hints["code"] == "SSIS-123"
        assert "SSIS-123" in hints["normalized_name"]
        assert "[Jable]" in hints["original_name"]
        assert "[Jable]" not in hints["normalized_name"]

    def test_extract_hints_from_path(self):
        """测试从路径提取元数据提示"""
        hints = FilenameParser.extract_metadata_hints("/path/to/SSIS-123.mp4")
        assert hints["code"] == "SSIS-123"
        assert "/path/to" not in hints["normalized_name"]
        assert "/path/to" not in hints["original_name"]

    def test_extract_hints_no_code(self):
        """测试无法提取番号的情况"""
        hints = FilenameParser.extract_metadata_hints("random_video.mp4")
        assert hints["code"] is None
        # 下划线会被转换为连字符
        assert hints["normalized_name"] == "random-video"
        assert hints["original_name"] == "random_video"


class TestVideoFileDetection:
    """测试视频文件检测功能"""

    def test_common_video_formats(self):
        """测试常见视频格式"""
        assert FilenameParser.is_video_file("video.mp4") is True
        assert FilenameParser.is_video_file("video.mkv") is True
        assert FilenameParser.is_video_file("video.avi") is True
        assert FilenameParser.is_video_file("video.mov") is True
        assert FilenameParser.is_video_file("video.wmv") is True
        assert FilenameParser.is_video_file("video.flv") is True
        assert FilenameParser.is_video_file("video.ts") is True

    def test_additional_video_formats(self):
        """测试额外的视频格式"""
        assert FilenameParser.is_video_file("video.m4v") is True
        assert FilenameParser.is_video_file("video.webm") is True
        assert FilenameParser.is_video_file("video.rmvb") is True

    def test_non_video_formats(self):
        """测试非视频格式"""
        assert FilenameParser.is_video_file("file.txt") is False
        assert FilenameParser.is_video_file("image.jpg") is False
        assert FilenameParser.is_video_file("audio.mp3") is False
        assert FilenameParser.is_video_file("document.pdf") is False

    def test_case_insensitive(self):
        """测试大小写不敏感"""
        assert FilenameParser.is_video_file("VIDEO.MP4") is True
        assert FilenameParser.is_video_file("Video.MKV") is True
        assert FilenameParser.is_video_file("video.AVI") is True

    def test_with_path(self):
        """测试带路径的文件名"""
        assert FilenameParser.is_video_file("/path/to/video.mp4") is True
        assert FilenameParser.is_video_file("C:\\videos\\test.mkv") is True

    def test_custom_extensions(self):
        """测试自定义扩展名列表"""
        custom_exts = [".mp4", ".mkv"]
        assert FilenameParser.is_video_file("video.mp4", custom_exts) is True
        assert FilenameParser.is_video_file("video.avi", custom_exts) is False

    def test_no_extension(self):
        """测试没有扩展名的文件"""
        assert FilenameParser.is_video_file("video") is False
        assert FilenameParser.is_video_file("") is False

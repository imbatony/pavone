"""
测试下载选项模块
"""

import unittest
from pavone.core.downloader.options import DownloadOpt, LinkType, create_download_opt


class TestDownloadOpt(unittest.TestCase):
    """测试下载选项类"""
    
    def test_basic_init(self):
        """测试基本初始化"""
        opt = DownloadOpt("https://example.com/video.mp4")
        self.assertEqual(opt.url, "https://example.com/video.mp4")
        self.assertIsNone(opt.filename)
        self.assertEqual(opt.custom_headers, {})
        self.assertIsNone(opt.link_type)
    
    def test_init_with_all_params(self):
        """测试带所有参数的初始化"""
        headers = {"User-Agent": "Test"}
        opt = DownloadOpt(
            url="https://example.com/video.mp4",
            filename="test.mp4",
            custom_headers=headers,
            link_type=LinkType.VIDEO
        )
        
        self.assertEqual(opt.url, "https://example.com/video.mp4")
        self.assertEqual(opt.filename, "test.mp4")
        self.assertEqual(opt.custom_headers, headers)
        self.assertEqual(opt.link_type, LinkType.VIDEO)
    
    def test_init_with_display_name_and_quality(self):
        """测试带显示名称和质量参数的初始化"""
        opt = DownloadOpt(
            url="https://example.com/video.mp4",
            filename="test.mp4",
            link_type=LinkType.VIDEO,
            display_name="测试视频",
            quality="1080p"
        )
        
        self.assertEqual(opt.url, "https://example.com/video.mp4")
        self.assertEqual(opt.filename, "test.mp4")
        self.assertEqual(opt.link_type, LinkType.VIDEO)
        self.assertEqual(opt.display_name, "测试视频")
        self.assertEqual(opt.quality, "1080p")
    
    def test_get_effective_headers(self):
        """测试获取有效头部"""
        custom_headers = {"Authorization": "Bearer token"}
        opt = DownloadOpt("https://example.com/video.mp4", custom_headers=custom_headers)
        
        default_headers = {"User-Agent": "Test Agent"}
        effective_headers = opt.get_effective_headers(default_headers)
        
        expected = {
            "User-Agent": "Test Agent",
            "Authorization": "Bearer token"
        }
        self.assertEqual(effective_headers, expected)
    
    def test_link_type_detection(self):
        """测试链接类型检测"""
        # 测试视频类型
        video_opt = DownloadOpt("https://example.com/video.mp4", link_type=LinkType.VIDEO)
        self.assertTrue(video_opt.is_video())
        self.assertFalse(video_opt.is_image())
        self.assertFalse(video_opt.is_metadata())
        
        # 测试图片类型
        image_opt = DownloadOpt("https://example.com/cover.jpg", link_type=LinkType.COVER)
        self.assertFalse(image_opt.is_video())
        self.assertTrue(image_opt.is_image())
        self.assertFalse(image_opt.is_metadata())
        
        # 测试元数据类型
        metadata_opt = DownloadOpt("https://example.com/info.nfo", link_type=LinkType.METADATA)
        self.assertFalse(metadata_opt.is_video())
        self.assertFalse(metadata_opt.is_image())
        self.assertTrue(metadata_opt.is_metadata())
        self.assertFalse(metadata_opt.is_stream())
        
        # 测试流媒体类型
        stream_opt = DownloadOpt("https://example.com/stream.m3u8", link_type=LinkType.STREAM)
        self.assertFalse(stream_opt.is_video())
        self.assertFalse(stream_opt.is_image())
        self.assertFalse(stream_opt.is_metadata())
        self.assertTrue(stream_opt.is_stream())

    def test_type_description(self):
        """测试类型描述"""
        # 测试已知类型
        video_opt = DownloadOpt("https://example.com/video.mp4", link_type=LinkType.VIDEO)
        self.assertEqual(video_opt.get_type_description(), "视频文件")
        
        cover_opt = DownloadOpt("https://example.com/cover.jpg", link_type=LinkType.COVER)
        self.assertEqual(cover_opt.get_type_description(), "封面图")
        
        # 测试流媒体类型
        stream_opt = DownloadOpt("https://example.com/stream.m3u8", link_type=LinkType.STREAM)
        self.assertEqual(stream_opt.get_type_description(), "流媒体")
        
        # 测试未指定类型
        no_type_opt = DownloadOpt("https://example.com/file", link_type=None)
        self.assertEqual(no_type_opt.get_type_description(), "未指定类型")
        
        # 测试未知类型
        unknown_opt = DownloadOpt("https://example.com/file", link_type="unknown")
        self.assertEqual(unknown_opt.get_type_description(), "未知类型")
    
    def test_get_display_name(self):
        """测试获取显示名称"""
        # 测试有显示名称的情况
        opt1 = DownloadOpt("https://example.com/video.mp4", display_name="测试视频")
        self.assertEqual(opt1.get_display_name(), "测试视频")
        
        # 测试没有显示名称但有文件名的情况
        opt2 = DownloadOpt("https://example.com/video.mp4", filename="test.mp4")
        self.assertEqual(opt2.get_display_name(), "test.mp4")
        
        # 测试都没有的情况，返回URL
        opt3 = DownloadOpt("https://example.com/video.mp4")
        self.assertEqual(opt3.get_display_name(), "https://example.com/video.mp4")
    
    def test_get_quality_info(self):
        """测试获取质量信息"""
        opt1 = DownloadOpt("https://example.com/video.mp4", quality="1080p")
        self.assertEqual(opt1.get_quality_info(), "1080p")
        
        opt2 = DownloadOpt("https://example.com/video.mp4")
        self.assertIsNone(opt2.get_quality_info())
    
    def test_get_full_description(self):
        """测试获取完整描述"""
        opt = DownloadOpt(
            url="https://example.com/video.mp4",
            filename="test.mp4",
            link_type=LinkType.VIDEO,
            display_name="测试视频",
            quality="1080p"
        )
        
        description = opt.get_full_description()
        self.assertIn("视频文件", description)
        self.assertIn("1080p", description)
        self.assertIn("测试视频", description)


class TestCreateDownloadOpt(unittest.TestCase):
    """测试创建下载选项函数"""
    
    def test_create_basic(self):
        """测试基本创建"""
        opt = create_download_opt("https://example.com/video.mp4")
        self.assertEqual(opt.url, "https://example.com/video.mp4")
        self.assertIsNone(opt.filename)
        self.assertIsNone(opt.link_type)
    
    def test_create_with_all_params(self):
        """测试带所有参数的创建"""
        opt = create_download_opt(
            url="https://example.com/video.mp4",
            filename="test.mp4",
            link_type=LinkType.VIDEO,
            Authorization="Bearer token",
            User_Agent="Test Agent"
        )
        
        self.assertEqual(opt.url, "https://example.com/video.mp4")
        self.assertEqual(opt.filename, "test.mp4")
        self.assertEqual(opt.link_type, LinkType.VIDEO)
        self.assertIn("Authorization", opt.custom_headers)
        self.assertIn("User_Agent", opt.custom_headers)
    
    def test_create_with_display_name_and_quality(self):
        """测试带显示名称和质量参数的创建"""
        opt = create_download_opt(
            url="https://example.com/video.mp4",
            filename="test.mp4",
            link_type=LinkType.VIDEO,
            display_name="测试视频",
            quality="1080p",
            Authorization="Bearer token"
        )
        
        self.assertEqual(opt.url, "https://example.com/video.mp4")
        self.assertEqual(opt.filename, "test.mp4")
        self.assertEqual(opt.link_type, LinkType.VIDEO)
        self.assertEqual(opt.display_name, "测试视频")
        self.assertEqual(opt.quality, "1080p")
        self.assertIn("Authorization", opt.custom_headers)


class TestLinkType(unittest.TestCase):
    """测试链接类型常量"""
    
    def test_link_type_constants(self):
        """测试链接类型常量值"""
        self.assertEqual(LinkType.VIDEO, "video")
        self.assertEqual(LinkType.IMAGE, "image")
        self.assertEqual(LinkType.SUBTITLE, "subtitle")
        self.assertEqual(LinkType.METADATA, "metadata")
        self.assertEqual(LinkType.THUMBNAIL, "thumbnail")
        self.assertEqual(LinkType.COVER, "cover")
        self.assertEqual(LinkType.TORRENT, "torrent")
        self.assertEqual(LinkType.STREAM, "stream")
        self.assertEqual(LinkType.OTHER, "other")


if __name__ == '__main__':
    unittest.main()

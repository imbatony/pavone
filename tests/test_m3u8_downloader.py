"""
M3U8下载器的测试
"""

import os
import tempfile
from unittest.mock import Mock, patch, mock_open

from pavone.config.settings import DownloadConfig
from pavone.core.downloader.m3u8_downloader import M3U8Downloader
from pavone.core.downloader.options import DownloadOpt
from pavone.core.downloader.progress import ProgressInfo


class TestM3U8Downloader:
    """M3U8下载器测试类"""
    
    def setup_method(self):
        """测试设置"""
        self.config = DownloadConfig(
            output_dir=tempfile.mkdtemp(),
            max_concurrent_downloads=2,
            timeout=10
        )
        self.downloader = M3U8Downloader(self.config)
    
    def test_parse_m3u8_playlist(self):
        """测试M3U8播放列表解析"""
        # 模拟M3U8文件内容
        m3u8_content = """#EXTM3U
#EXT-X-VERSION:3
#EXT-X-TARGETDURATION:10
#EXTINF:10.0,
segment001.ts
#EXTINF:10.0,
segment002.ts
#EXTINF:5.0,
segment003.ts
#EXT-X-ENDLIST"""
        
        base_url = "https://example.com/video/"
        segments = self.downloader._parse_m3u8_playlist(m3u8_content, base_url)
        
        expected_segments = [
            "https://example.com/video/segment001.ts",
            "https://example.com/video/segment002.ts", 
            "https://example.com/video/segment003.ts"
        ]
        
        assert segments == expected_segments
    
    def test_parse_m3u8_playlist_with_absolute_urls(self):
        """测试包含绝对URL的M3U8播放列表解析"""
        m3u8_content = """#EXTM3U
#EXT-X-VERSION:3
#EXTINF:10.0,
https://cdn.example.com/segment001.ts
#EXTINF:10.0,
https://cdn.example.com/segment002.ts"""
        
        base_url = "https://example.com/video/"
        segments = self.downloader._parse_m3u8_playlist(m3u8_content, base_url)
        
        expected_segments = [
            "https://cdn.example.com/segment001.ts",
            "https://cdn.example.com/segment002.ts"
        ]
        
        assert segments == expected_segments
    
    def test_get_output_filename_with_custom_filename(self):
        """测试自定义文件名"""
        download_opt = DownloadOpt(
            url="https://example.com/playlist.m3u8",
            filename="custom_video.mp4"
        )
        
        filename = self.downloader._get_output_filename(download_opt)
        expected_path = os.path.join(self.config.output_dir, "custom_video.mp4")
        
        assert filename == expected_path
    
    def test_get_output_filename_from_url(self):
        """测试从URL提取文件名"""
        download_opt = DownloadOpt(
            url="https://example.com/videos/movie.m3u8"
        )
        
        filename = self.downloader._get_output_filename(download_opt)
        expected_path = os.path.join(self.config.output_dir, "movie.mp4")
        
        assert filename == expected_path
    
    def test_get_output_filename_default(self):
        """测试默认文件名"""
        download_opt = DownloadOpt(
            url="https://example.com/api/stream"
        )
        
        filename = self.downloader._get_output_filename(download_opt)
        expected_path = os.path.join(self.config.output_dir, "video.mp4")
        
        assert filename == expected_path
    
    @patch('pavone.core.downloader.m3u8_downloader.requests.Session')
    def test_download_m3u8_playlist(self, mock_session_class):
        """测试M3U8播放列表下载"""
        # 设置mock
        mock_session = Mock()
        mock_session_class.return_value = mock_session
        mock_response = Mock()
        mock_response.text = "#EXTM3U\nsegment001.ts"
        mock_response.raise_for_status.return_value = None  # 不抛出异常
        mock_session.get.return_value = mock_response
        
        # 创建新的下载器实例以使用mock session
        downloader = M3U8Downloader(self.config)
        
        url = "https://example.com/playlist.m3u8"
        headers = {"User-Agent": "Test"}
        
        result = downloader._download_m3u8_playlist(url, headers)
        
        assert result == "#EXTM3U\nsegment001.ts"
        mock_session.get.assert_called_once_with(
            url,
            headers=headers,
            proxies=None,
            timeout=self.config.timeout
        )
    
    @patch('pavone.core.downloader.m3u8_downloader.requests.Session')
    def test_download_segment(self, mock_session_class):
        """测试视频段下载"""
        # 设置mock
        mock_session = Mock()
        mock_session_class.return_value = mock_session
        mock_response = Mock()
        mock_response.content = b"fake_video_data"
        mock_response.raise_for_status.return_value = None  # 不抛出异常
        mock_session.get.return_value = mock_response
        
        # 创建新的下载器实例以使用mock session
        downloader = M3U8Downloader(self.config)
        
        url = "https://example.com/segment001.ts"
        headers = {"User-Agent": "Test"}
        segment_index = 0
        
        result = downloader._download_segment(url, headers, segment_index)
        
        assert result == (0, b"fake_video_data")
        mock_session.get.assert_called_once_with(
            url,
            headers=headers,
            proxies=None,
            timeout=self.config.timeout
        )
    
    @patch('pavone.core.downloader.m3u8_downloader.os.makedirs')
    @patch('pavone.core.downloader.m3u8_downloader.os.path.exists')
    @patch('pavone.core.downloader.m3u8_downloader.os.remove')
    @patch('pavone.core.downloader.m3u8_downloader.os.rmdir')
    @patch('builtins.open', new_callable=mock_open)
    @patch('pavone.core.downloader.m3u8_downloader.requests.Session')
    def test_download_success(self, mock_session_class, mock_file, mock_rmdir, 
                            mock_remove, mock_exists, mock_makedirs):
        """测试完整的M3U8下载流程"""
        # 设置mock
        mock_session = Mock()
        mock_session_class.return_value = mock_session
        
        # Mock M3U8播放列表响应
        mock_playlist_response = Mock()
        mock_playlist_response.text = """#EXTM3U
#EXTINF:10.0,
segment001.ts
#EXTINF:10.0,
segment002.ts"""
        
        # Mock视频段响应
        mock_segment_response = Mock()
        mock_segment_response.content = b"fake_segment_data"
        
        mock_session.get.side_effect = [
            mock_playlist_response,  # 播放列表请求
            mock_segment_response,   # 第一个段
            mock_segment_response    # 第二个段
        ]
        
        mock_exists.return_value = True
        
        # 创建下载选项
        download_opt = DownloadOpt(
            url="https://example.com/playlist.m3u8",
            filename="test_video.mp4"
        )
        
        # 创建进度回调
        progress_calls = []
        def progress_callback(info: ProgressInfo):
            progress_calls.append(info)
        
        # 执行下载
        result = self.downloader.download(download_opt, progress_callback)
        
        # 验证结果
        assert result == True
        assert len(progress_calls) > 0  # 确保进度回调被调用
        
        # 验证文件操作
        assert mock_file.call_count >= 3  # 至少打开了段文件和输出文件
        mock_makedirs.assert_called()  # 确保创建了目录

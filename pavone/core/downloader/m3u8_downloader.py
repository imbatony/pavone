"""
M3U8视频下载器实现
"""

import os
import time
import requests
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Dict, List, Optional, Tuple
from urllib.parse import urljoin

from pavone.config.settings import Config
from .base import BaseDownloader
from ...models import OperationItem, ProgressCallback, ProgressInfo


class M3U8Downloader(BaseDownloader):
    """M3U8视频下载器"""

    def __init__(self, config: Config):
        super().__init__(config)
        self._session = requests.Session()
        self._lock = threading.Lock()

    def _download_m3u8_playlist(self, url: str, headers: Dict[str, str]) -> str:
        """
        下载M3U8播放列表文件

        Args:
            url: M3U8播放列表URL
            headers: HTTP头部

        Returns:
            str: M3U8文件内容

        Raises:
            requests.RequestException: 下载失败时抛出异常
        """
        try:
            response = self._session.get(url, headers=headers, proxies=self.proxies, timeout=self.download_config.timeout)
            response.raise_for_status()
            return response.text
        except Exception as e:
            raise requests.RequestException(f"Failed to download M3U8 playlist: {e}")

    def _parse_m3u8_playlist(self, content: str, base_url: str) -> List[str]:
        """
        解析M3U8播放列表，提取视频段URL列表

        Args:
            content: M3U8文件内容
            base_url: 基础URL，用于处理相对路径

        Returns:
            List[str]: 视频段URL列表
        """
        segment_urls: list[str] = []
        lines = content.strip().split("\n")

        for line in lines:
            line = line.strip()
            # 跳过注释行和空行
            if line.startswith("#") or not line:
                continue

            # 如果是相对URL，转换为绝对URL
            if line.startswith("http"):
                segment_urls.append(line)
            else:
                segment_urls.append(urljoin(base_url, line))

        return segment_urls

    def _download_segment(self, url: str, headers: Dict[str, str], segment_index: int) -> Tuple[int, bytes]:
        """
        下载单个视频段

        Args:
            url: 视频段URL
            headers: HTTP头部
            segment_index: 段索引

        Returns:
            Tuple[int, bytes]: (段索引, 段数据)
        """
        try:
            response = self._session.get(url, headers=headers, proxies=self.proxies, timeout=self.download_config.timeout)
            response.raise_for_status()
            return segment_index, response.content
        except Exception as e:
            raise Exception(f"Failed to download segment {segment_index}: {e}")

    def execute(self, item: OperationItem) -> bool:
        """
        下载M3U8视频

        Args:
            download_opt: 下载选项，包含M3U8播放列表URL
            progress_callback: 进度回调函数

        Returns:
            bool: 下载是否成功
        """
        target_path: Optional[str] = item.get_target_path()
        if not target_path:
            self.logger.warning("目标路径未设置，无法下载")
            return False

        progress_callback: Optional[ProgressCallback] = item.get_progress_callback()
        if not progress_callback:
            self.logger.warning("未设置进度回调函数，无法跟踪下载进度")
            progress_callback = lambda x: None

        url = item.get_url()
        if not url:
            self.logger.warning("下载链接未设置，无法下载")
            return False

        try:
            # 获取有效的HTTP头部
            headers = item.get_effective_headers(self.download_config.headers)
            # 下载M3U8播放列表
            m3u8_content = self._download_m3u8_playlist(url, headers)
            # 解析播放列表，获取视频段URL列表
            base_url = "/".join(url.split("/")[:-1]) + "/"
            segment_urls = self._parse_m3u8_playlist(m3u8_content, base_url)

            if not segment_urls:
                self.logger.warning("No video segments found in M3U8 playlist")
                return False

            total_segments = len(segment_urls)
            self.logger.info(f"Found {total_segments} video segments")

            # 获取输出文件路径
            output_file = target_path            # 创建临时目录存储视频段
            # 使用配置的缓存目录或基于输出文件创建临时目录
            cache_dir = self.download_config.cache_dir
            if cache_dir:
                # 创建唯一的临时目录路径以避免冲突
                import uuid
                temp_dir = os.path.join(cache_dir, f"m3u8_{uuid.uuid4().hex}")
            else:
                temp_dir = output_file + "_segments"
            os.makedirs(temp_dir, exist_ok=True)

            # 下载所有视频段
            downloaded_segments: dict[int, str] = {}
            failed_downloads: list[Tuple[int, str]] = []
            total_downloaded_bytes = 0
            successful_downloads = 0
            # 开始时间
            download_start_time = time.time()

            def download_with_progress(segment_info:Tuple[int, str]) -> bool:
                index, url = segment_info

                # 使用配置的重试次数进行重试
                for attempt in range(self.download_config.retry_times + 1):
                    try:
                        segment_index, segment_data = self._download_segment(url, headers, index)
                        # 更新总字节数
                        with self._lock:
                            nonlocal total_downloaded_bytes
                            nonlocal successful_downloads
                            successful_downloads += 1
                            total_downloaded_bytes += len(segment_data)
                        # 将段数据写入临时文件
                        segment_file = os.path.join(temp_dir, f"segment_{segment_index:06d}.ts")
                        with open(segment_file, "wb") as f:
                            f.write(segment_data)

                        with self._lock:
                            # 计算下载速度
                            elapsed_time = time.time() - download_start_time
                            speed = total_downloaded_bytes / elapsed_time if elapsed_time > 0 else 0.0
                            downloaded_segments[segment_index] = segment_file
                            # 更新进度

                            progress_info = ProgressInfo(
                                    total_size=0, downloaded=total_downloaded_bytes, speed=speed
                            )
                            progress_callback(progress_info)

                        return True
                    except Exception as e:
                        if attempt < self.download_config.retry_times:
                            # 如果不是最后一次尝试，等待重试间隔
                            retry_delay = self.download_config.retry_interval / 1000.0  # 转换为秒
                            self.logger.info(
                                f"Segment {index} download failed (attempt {attempt + 1}/{self.download_config.retry_times + 1}): {e}, retrying in {retry_delay}s..."
                            )
                            time.sleep(retry_delay)
                        else:
                            # 最后一次尝试失败
                            self.logger.error(
                                f"Failed to download segment {index} after {self.download_config.retry_times + 1} attempts: {e}"
                            )

                # 所有重试都失败了
                failed_downloads.append((index, url))
                return False

            # 使用线程池并发下载
            max_workers = min(self.download_config.max_concurrent_downloads, total_segments)
            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                segment_infos = list(enumerate(segment_urls))
                futures = [executor.submit(download_with_progress, info) for info in segment_infos]

                for future in as_completed(futures):
                    future.result()  # 等待完成

            # 检查是否有失败的下载
            if failed_downloads:
                self.logger.warning(f"Failed to download {len(failed_downloads)} segments")
                # 可以选择重试失败的段
                return False            # 合并所有视频段，优先使用ffmpeg
            self.logger.info("Merging video segments...")

            def _merge_using_ffmpeg(segment_files: list[str], output_path: str) -> bool:
                """使用ffmpeg合并视频段"""
                import subprocess
                import tempfile
                
                # 创建临时文件列表
                with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
                    for segment in segment_files:
                        f.write(f"file '{os.path.abspath(segment)}'\n")
                    filelist_path = f.name
                
                try:
                    # 使用ffmpeg合并视频段
                    cmd = [
                        'ffmpeg', 
                        '-f', 'concat', 
                        '-safe', '0',
                        '-i', filelist_path,
                        '-c', 'copy',
                        '-y',  # 覆盖输出文件
                        output_path
                    ]
                    
                    self.logger.info(f"Running ffmpeg command: {' '.join(cmd)}")
                    process = subprocess.Popen(
                        cmd, 
                        stdout=subprocess.PIPE, 
                        stderr=subprocess.PIPE
                    )
                    _, stderr = process.communicate()
                    
                    if process.returncode != 0:
                        self.logger.warning(f"ffmpeg failed: {stderr.decode('utf-8', errors='replace')}")
                        return False
                    return True
                except Exception as e:
                    self.logger.warning(f"ffmpeg error: {e}")
                    return False
                finally:
                    # 删除临时文件
                    try:
                        os.unlink(filelist_path)
                    except:
                        pass
            
            # 准备排序后的段文件列表
            segment_files: list[str] = []
            for i in range(total_segments):
                segment_file = downloaded_segments.get(i)
                if segment_file and os.path.exists(segment_file):
                    segment_files.append(segment_file)
                else:
                    self.logger.warning(f"Missing segment {i}")
                    
            # 尝试使用ffmpeg合并
            ffmpeg_success = False
            try:
                # 检查是否可以使用ffmpeg
                import shutil
                if shutil.which('ffmpeg'):
                    ffmpeg_success = _merge_using_ffmpeg(segment_files, output_file)
            except Exception as e:
                self.logger.warning(f"Error checking for ffmpeg: {e}")
            
            # 如果ffmpeg失败或不可用，则使用传统方法合并
            if not ffmpeg_success:
                self.logger.info("Falling back to direct file merging...")
                with open(output_file, "wb") as output:
                    for segment_file in segment_files:
                        with open(segment_file, "rb") as f:
                            output.write(f.read())
            # 清理临时文件
            try:
                for segment_file in downloaded_segments.values():
                    if os.path.exists(segment_file):
                        os.remove(segment_file)
                os.rmdir(temp_dir)
            except Exception as e:
                self.logger.warning(f"Failed to clean up temporary files: {e}")

            self.logger.info(f"M3U8 video downloaded successfully: {output_file}")

            # 最终进度更新
            progress_info = ProgressInfo(total_size=total_segments, downloaded=total_segments, speed=0.0)
            progress_callback(progress_info)

            return True

        except Exception as e:
            self.logger.error(f"M3U8 download failed: {e}")
            return False
        finally:
            self._session.close()

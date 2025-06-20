"""
HTTP下载器实现
"""

import os
import requests
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Optional, Dict, Any, Tuple
from urllib.parse import urlparse

from pavone.config.settings import DownloadConfig
from .base import BaseDownloader
from .options import DownloadOpt
from .progress import ProgressCallback, ProgressInfo


class HTTPDownloader(BaseDownloader):
    """HTTP协议下载器"""
    
    def __init__(self, config: DownloadConfig):
        super().__init__(config)
    
    def _get_proxies(self) -> Optional[Dict[str, str]]:
        """获取代理配置"""
        if not self.config.proxy_enabled:
            return None
        
        proxies = {}
        if self.config.http_proxy:
            proxies['http'] = self.config.http_proxy
        if self.config.https_proxy:
            proxies['https'] = self.config.https_proxy
        
        return proxies if proxies else None
    
    def _check_range_support(self, url: str, headers: Dict[str, str]) -> Tuple[bool, int]:
        """
        检查服务器是否支持Range请求和获取文件大小
        
        Returns:
            Tuple[bool, int]: (是否支持Range请求, 文件大小)
        """
        try:
            proxies = self._get_proxies()
            response = requests.head(
                url, 
                timeout=self.config.timeout,
                headers=headers,
                proxies=proxies
            )
            response.raise_for_status()
            
            # 检查是否支持Range请求
            accept_ranges = response.headers.get('Accept-Ranges', '').lower()
            supports_range = accept_ranges == 'bytes'
            
            # 获取文件大小
            content_length = response.headers.get('Content-Length')
            file_size = int(content_length) if content_length else 0
            
            return supports_range, file_size
            
        except Exception:
            return False, 0
    
    def _download_chunk(self, url: str, headers: Dict[str, str], 
                       start: int, end: int, filepath: str, 
                       chunk_index: int) -> Tuple[bool, int]:
        """
        下载文件块
        
        Returns:
            Tuple[bool, int]: (是否成功, 下载的字节数)
        """
        try:
            # 添加Range头部
            range_headers = headers.copy()
            range_headers['Range'] = f'bytes={start}-{end}'
            
            proxies = self._get_proxies()
            response = requests.get(
                url,
                headers=range_headers,
                stream=True,
                timeout=self.config.timeout,
                proxies=proxies
            )
            response.raise_for_status()
              # 写入临时文件
            temp_filepath = f"{filepath}.part{chunk_index}"
            downloaded = 0
            
            with open(temp_filepath, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)
            
            return True, downloaded
            
        except Exception as e:
            self.logger.error(f"下载块 {chunk_index} 失败: {e}")
            return False, 0
    
    def _merge_chunks(self, filepath: str, num_chunks: int) -> bool:
        """
        合并所有下载的文件块
        """
        try:
            with open(filepath, 'wb') as output_file:
                for i in range(num_chunks):
                    chunk_filepath = f"{filepath}.part{i}"
                    if os.path.exists(chunk_filepath):
                        with open(chunk_filepath, 'rb') as chunk_file:
                            output_file.write(chunk_file.read())
                        os.remove(chunk_filepath)
                    else:                        return False
            
            return True
        except Exception as e:
            self.logger.error(f"合并文件块失败: {e}")
            return False
    
    def _should_use_multithreading(self, supports_range: bool, file_size: int) -> bool:
        """
        判断是否应该使用多线程下载
        """
        # 文件大小小于1MB或不支持Range请求时使用单线程
        min_size_for_multithreading = 1024 * 1024  # 1MB
        return supports_range and file_size > min_size_for_multithreading and self.config.max_concurrent_downloads > 1
    
    def download(self, download_opt: DownloadOpt, 
                 progress_callback: Optional[ProgressCallback] = None) -> bool:
        """
        下载文件（支持多线程）
        
        Args:
            download_opt: 下载选项，包含URL、文件名和自定义HTTP头部
            progress_callback: 进度回调函数，接收ProgressInfo对象
            
        Returns:
            bool: 下载是否成功
        """
        try:
            # 准备HTTP头部，合并默认和自定义头部
            default_headers = {'User-Agent': self.config.user_agent}
            headers = download_opt.get_effective_headers(default_headers)
            
            # 检查Range支持和文件大小
            supports_range, file_size = self._check_range_support(download_opt.url, headers)
            
            # 确定文件名
            filename = download_opt.filename
            if not filename:
                parsed_url = urlparse(download_opt.url)
                filename = os.path.basename(parsed_url.path) or "download"
            
            filepath = os.path.join(self.config.output_dir, filename)
            
            # 判断是否使用多线程
            use_multithreading = self._should_use_multithreading(supports_range, file_size)
            
            if use_multithreading:
                return self._download_multithreaded(download_opt.url, headers, filepath, 
                                                  file_size, progress_callback)
            else:
                return self._download_single_threaded(download_opt.url, headers, filepath,                                                    progress_callback)
                
        except Exception as e:
            self.logger.warning(f"下载失败: {e}")
            return False
    
    def _download_single_threaded(self, url: str, headers: Dict[str, str], 
                                filepath: str, progress_callback: Optional[ProgressCallback] = None) -> bool:
        """单线程下载"""
        try:
            proxies = self._get_proxies()
            response = requests.get(
                url, 
                stream=True, 
                timeout=self.config.timeout,
                headers=headers,
                proxies=proxies
            )
            response.raise_for_status()
            
            total_size = int(response.headers.get('Content-Length', 0))
            downloaded = 0
            start_time = time.time()
            
            # 初始化进度信息
            if progress_callback:
                progress_info = ProgressInfo(total_size, 0, 0.0)
                progress_callback(progress_info)
            
            with open(filepath, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)
                        
                        # 更新进度信息
                        if progress_callback:
                            elapsed_time = time.time() - start_time
                            speed = downloaded / elapsed_time if elapsed_time > 0 else 0.0
                            progress_info = ProgressInfo(total_size, downloaded, speed)
                            progress_callback(progress_info)            
            return True
        except Exception as e:
            self.logger.warning(f"单线程下载失败: {e}")
            return False
    
    def _download_multithreaded(self, url: str, headers: Dict[str, str], 
                              filepath: str, file_size: int, 
                              progress_callback: Optional[ProgressCallback] = None) -> bool:
        """多线程下载"""
        try:
            num_threads = min(self.config.max_concurrent_downloads, 8)  # 最多8个线程
            chunk_size = file_size // num_threads
            
            # 创建下载任务
            download_tasks = []
            for i in range(num_threads):
                start = i * chunk_size
                end = (i + 1) * chunk_size - 1 if i < num_threads - 1 else file_size - 1
                download_tasks.append((start, end, i))
            
            # 进度跟踪
            downloaded_chunks = [0] * num_threads
            start_time = time.time()
            lock = threading.Lock()
            
            def update_progress():
                """更新总进度"""
                if progress_callback:
                    with lock:
                        total_downloaded = sum(downloaded_chunks)
                        elapsed_time = time.time() - start_time
                        speed = total_downloaded / elapsed_time if elapsed_time > 0 else 0.0
                        progress_info = ProgressInfo(file_size, total_downloaded, speed)
                        progress_callback(progress_info)
            
            # 使用线程池下载
            with ThreadPoolExecutor(max_workers=num_threads) as executor:
                future_to_index = {}
                
                for start, end, index in download_tasks:
                    future = executor.submit(self._download_chunk, url, headers, 
                                           start, end, filepath, index)
                    future_to_index[future] = index
                  # 等待所有任务完成
                for future in as_completed(future_to_index):
                    index = future_to_index[future]
                    try:
                        success, chunk_downloaded = future.result()
                        if success:
                            downloaded_chunks[index] = chunk_downloaded
                            update_progress()
                        else:
                            self.logger.info(f"下载块 {index} 失败")
                            return False
                    except Exception as e:
                        self.logger.info(f"线程 {index} 异常: {e}")
                        return False
            
            # 合并文件块
            if self._merge_chunks(filepath, num_threads):
                # 最终进度更新
                if progress_callback:
                    progress_info = ProgressInfo(file_size, file_size, 0.0)
                    progress_callback(progress_info)
                return True
            else:                return False
                
        except Exception as e:
            self.logger.warning(f"多线程下载失败: {e}")
            return False
    
    def get_video_info(self, url: str) -> Dict[str, Any]:
        """
        获取视频信息
        
        Args:
            url: 视频URL
            
        Returns:
            Dict: 视频信息
        """
        try:
            # 获取代理设置
            proxies = self._get_proxies()
            
            response = requests.head(
                url, 
                timeout=self.config.timeout,
                headers={'User-Agent': self.config.user_agent},
                proxies=proxies
            )
            response.raise_for_status()
            
            content_length = response.headers.get('Content-Length')
            content_type = response.headers.get('Content-Type', '')
            
            return {
                "title": os.path.basename(urlparse(url).path) or "unknown",
                "size": int(content_length) if content_length else 0,
                "content_type": content_type,
                "url": url            }
        except Exception as e:
            self.logger.error(f"获取视频信息失败: {e}")
            return {
                "title": "",
                "size": 0,
                "content_type": "",
                "url": url
            }

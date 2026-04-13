"""
M3U8视频下载器实现
"""

import hashlib
import os
import re
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple
from urllib.parse import urljoin

import requests

from pavone.config.settings import Config

from ...models import OperationItem, ProgressCallback, ProgressInfo
from ...models.progress_info import SegmentResult
from .base import BaseDownloader


@dataclass
class M3U8EncryptionInfo:
    """M3U8 AES加密信息"""

    method: str  # 加密方法，如 AES-128
    key: bytes  # 解密密钥
    iv: Optional[bytes]  # 初始化向量


class M3U8Downloader(BaseDownloader):
    """M3U8视频下载器"""

    def __init__(self, config: Config):
        super().__init__(config)
        self._session = requests.Session()
        self._lock = threading.Lock()
        self._encryption: Optional[M3U8EncryptionInfo] = None

    def _generate_m3u8_hash(self, content: str) -> str:
        """
        根据M3U8播放列表内容生成hash值

        Args:
            content: M3U8文件内容

        Returns:
            str: hash值（前16位）
        """
        # 移除空白行和注释行，只对实际的段URL进行hash，确保相同内容产生相同hash
        lines = [line.strip() for line in content.strip().split("\n") if line.strip() and not line.strip().startswith("#")]
        normalized_content = "\n".join(lines)
        return hashlib.sha256(normalized_content.encode()).hexdigest()[:16]

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
            response = self._session.get(
                url,
                headers=headers,
                proxies=self.proxies,
                timeout=self.download_config.timeout,
            )
            response.raise_for_status()
            return response.text
        except Exception as e:
            raise requests.RequestException(f"Failed to download M3U8 playlist: {e}")

    def _parse_m3u8_playlist(self, content: str, base_url: str) -> List[str]:
        """
        解析M3U8播放列表，提取视频段URL列表，并解析加密信息

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
            if not line:
                continue

            # 解析加密信息
            if line.startswith("#EXT-X-KEY:"):
                self._parse_encryption_key(line, base_url)
                continue

            # 跳过其他注释行
            if line.startswith("#"):
                continue

            # 如果是相对URL，转换为绝对URL
            if line.startswith("http"):
                segment_urls.append(line)
            else:
                segment_urls.append(urljoin(base_url, line))

        return segment_urls

    def _parse_encryption_key(self, line: str, base_url: str) -> None:
        """解析 #EXT-X-KEY 指令并下载密钥"""
        attrs = line[len("#EXT-X-KEY:") :]
        method_match = re.search(r"METHOD=([^,]+)", attrs)
        uri_match = re.search(r'URI="([^"]+)"', attrs)
        iv_match = re.search(r"IV=0x([0-9a-fA-F]+)", attrs)

        if not method_match:
            return

        method = method_match.group(1).strip()
        if method == "NONE":
            self._encryption = None
            return

        if method != "AES-128" or not uri_match:
            self.logger.warning(f"不支持的加密方式: {method}")
            return

        # 下载密钥
        key_uri = uri_match.group(1)
        if not key_uri.startswith("http"):
            key_uri = urljoin(base_url, key_uri)

        try:
            resp = self._session.get(
                key_uri,
                headers={"User-Agent": "Mozilla/5.0"},
                proxies=self.proxies,
                timeout=self.download_config.timeout,
            )
            resp.raise_for_status()
            key = resp.content
        except Exception as e:
            self.logger.error(f"下载加密密钥失败: {e}")
            return

        iv = bytes.fromhex(iv_match.group(1)) if iv_match else None

        self._encryption = M3U8EncryptionInfo(method=method, key=key, iv=iv)
        self.logger.info(f"检测到 {method} 加密，已获取密钥")

    def _decrypt_segment(self, data: bytes, segment_index: int) -> bytes:
        """解密AES-128加密的分段数据"""
        if not self._encryption:
            return data

        from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
        from cryptography.hazmat.primitives.padding import PKCS7

        key = self._encryption.key
        iv = self._encryption.iv or segment_index.to_bytes(16, byteorder="big")

        cipher = Cipher(algorithms.AES(key), modes.CBC(iv))
        decryptor = cipher.decryptor()
        decrypted = decryptor.update(data) + decryptor.finalize()

        # 移除 PKCS7 填充
        unpadder = PKCS7(128).unpadder()
        try:
            decrypted = unpadder.update(decrypted) + unpadder.finalize()
        except Exception:
            pass  # 部分流可能没有标准填充

        return decrypted

    def _check_segment_exists(self, segment_path: str) -> bool:
        """
        检查分段文件是否已存在且完整

        Args:
            segment_path: 分段文件路径

        Returns:
            bool: 文件是否存在且大小>0
        """
        if not os.path.exists(segment_path):
            return False
        # 检查文件大小，确保不是空文件
        try:
            return os.path.getsize(segment_path) > 0
        except OSError:
            return False

    def _download_segment(self, url: str, headers: Dict[str, str], segment_index: int) -> Tuple[int, bytes]:
        """
        下载单个视频段（如有加密则自动解密）

        Args:
            url: 视频段URL
            headers: HTTP头部
            segment_index: 段索引

        Returns:
            Tuple[int, bytes]: (段索引, 段数据)
        """
        try:
            response = self._session.get(
                url,
                headers=headers,
                proxies=self.proxies,
                timeout=self.download_config.timeout,
            )
            response.raise_for_status()
            data = response.content
            # 解密
            if self._encryption:
                data = self._decrypt_segment(data, segment_index)
            return segment_index, data
        except Exception as e:
            raise Exception(f"Failed to download segment {segment_index}: {e}")

    def get_last_segment_results(self) -> Optional[list[SegmentResult]]:
        """获取最近一次下载的分片结果列表 (仅在 execute() 返回 False 时有效)."""
        return getattr(self, "_last_segment_results", None)

    def retry_failed_segments(self) -> bool:
        """仅重试失败的分片, 复用已有的缓存和下载机制.

        Returns:
            bool: 重试后是否所有分片都成功
        """
        ctx = getattr(self, "_last_download_context", None)
        if not ctx:
            self.logger.error("没有可重试的下载上下文")
            return False

        segment_urls: list[str] = ctx["segment_urls"]
        headers: Dict[str, str] = ctx["headers"]
        temp_dir: str = ctx["temp_dir"]
        downloaded_segments: dict[int, str] = ctx["downloaded_segments"]

        results = self.get_last_segment_results()
        if not results:
            return False

        failed_indices = [r.index for r in results if not r.success]
        if not failed_indices:
            return True

        self.logger.info(f"重试 {len(failed_indices)} 个失败分片...")

        new_failed: list[SegmentResult] = []
        for idx in failed_indices:
            if self._interrupt_handler.is_interrupted():
                return False
            segment_file = os.path.join(temp_dir, f"segment_{idx:06d}.ts")
            url = segment_urls[idx]
            success = False
            for attempt in range(self.download_config.retry_times + 1):
                if self._interrupt_handler.is_interrupted():
                    return False
                try:
                    _, segment_data = self._download_segment(url, headers, idx)
                    with open(segment_file, "wb") as f:
                        f.write(segment_data)
                    downloaded_segments[idx] = segment_file
                    success = True
                    break
                except Exception as e:
                    if attempt < self.download_config.retry_times:
                        time.sleep(self.download_config.retry_interval / 1000.0)
                    else:
                        new_failed.append(SegmentResult(index=idx, success=False, error_message=str(e)))

            if not success and not any(r.index == idx for r in new_failed):
                new_failed.append(SegmentResult(index=idx, success=False, error_message="All retries failed"))

        # 更新结果
        updated_results: list[SegmentResult] = []
        for r in results:
            if r.index in failed_indices:
                match = next((nr for nr in new_failed if nr.index == r.index), None)
                if match:
                    updated_results.append(match)
                else:
                    updated_results.append(SegmentResult(index=r.index, success=True))
            else:
                updated_results.append(r)
        self._last_segment_results = updated_results

        return len(new_failed) == 0

    def merge_available_segments(self) -> bool:
        """合并所有已成功下载的分片 (跳过缺失的), 生成输出文件.

        Returns:
            bool: 合并是否成功
        """
        ctx = getattr(self, "_last_download_context", None)
        if not ctx:
            self.logger.error("没有可合并的下载上下文")
            return False

        downloaded_segments: dict[int, str] = ctx["downloaded_segments"]
        output_file: str = ctx["output_file"]
        total_segments: int = ctx["total_segments"]
        total_downloaded_bytes: int = ctx["total_downloaded_bytes"]
        progress_callback: ProgressCallback = ctx["progress_callback"]

        # 收集已有分片 (按顺序)
        segment_files: list[str] = []
        skipped: list[int] = []
        for i in range(total_segments):
            segment_file = downloaded_segments.get(i)
            if segment_file and os.path.exists(segment_file):
                segment_files.append(segment_file)
            else:
                skipped.append(i)

        if not segment_files:
            self.logger.error("没有可合并的分片")
            return False

        if skipped:
            self.logger.info(f"跳过 {len(skipped)} 个缺失分片: {skipped[:10]}{'...' if len(skipped) > 10 else ''}")

        actual_count = len(segment_files)
        progress_callback(
            ProgressInfo(
                total_size=0,
                downloaded=total_downloaded_bytes,
                speed=0.0,
                status_message=f"正在合并 {actual_count}/{total_segments} 个视频分段...",
            )
        )

        # 尝试 ffmpeg 合并
        import shutil
        import subprocess
        import tempfile

        ffmpeg_success = False
        if shutil.which("ffmpeg"):
            try:
                with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
                    for seg in segment_files:
                        safe_path = os.path.abspath(seg).replace("\\", "/")
                        f.write(f"file '{safe_path}'\n")
                    filelist_path = f.name
                cmd = ["ffmpeg", "-f", "concat", "-safe", "0", "-i", filelist_path, "-c", "copy", "-y", output_file]
                process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                _, stderr = process.communicate()
                ffmpeg_success = process.returncode == 0
                if not ffmpeg_success:
                    self.logger.warning(f"ffmpeg failed: {stderr.decode('utf-8', errors='replace')}")
                os.unlink(filelist_path)
            except Exception as e:
                self.logger.warning(f"ffmpeg error: {e}")

        if not ffmpeg_success:
            with open(output_file, "wb") as output:
                for sf in segment_files:
                    with open(sf, "rb") as f:
                        output.write(f.read())

        # 清理缓存
        temp_dir = ctx["temp_dir"]
        try:
            for sf in downloaded_segments.values():
                if os.path.exists(sf):
                    os.remove(sf)
            os.rmdir(temp_dir)
        except Exception as e:
            self.logger.warning(f"Failed to clean up: {e}")

        self.logger.info(f"合并完成: {actual_count}/{total_segments} 个分片 → {output_file}")
        progress_callback(
            ProgressInfo(total_size=total_segments, downloaded=actual_count, speed=0.0, status_message="✅ 合并完成！")
        )
        return True

    def execute(self, item: OperationItem) -> bool:  # noqa: C901
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

            def dummy_progress_callback(x: ProgressInfo) -> None:
                pass

            progress_callback = dummy_progress_callback

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
            output_file = target_path  # 创建临时目录存储视频段
            # 使用配置的缓存目录或基于输出文件创建临时目录
            # 根据m3u8内容生成hash，用于缓存目录名（实现断点续传）
            m3u8_hash = self._generate_m3u8_hash(m3u8_content)
            cache_dir = self.download_config.cache_dir
            if cache_dir:
                # 使用hash作为目录名，相同内容的m3u8会使用同一个缓存目录
                temp_dir = os.path.join(cache_dir, f"m3u8_{m3u8_hash}")
            else:
                temp_dir = output_file + f"_segments_{m3u8_hash}"
            os.makedirs(temp_dir, exist_ok=True)
            self.logger.info(f"Using cache directory: {temp_dir}")

            # 下载所有视频段
            downloaded_segments: dict[int, str] = {}
            failed_downloads: list[Tuple[int, str]] = []
            total_downloaded_bytes = 0
            successful_downloads = 0
            # 开始时间
            download_start_time = time.time()

            # 检查已存在的分段（断点续传）
            existing_segments = 0
            for i in range(total_segments):
                segment_file = os.path.join(temp_dir, f"segment_{i:06d}.ts")
                if self._check_segment_exists(segment_file):
                    downloaded_segments[i] = segment_file
                    existing_segments += 1
                    try:
                        segment_size = os.path.getsize(segment_file)
                        total_downloaded_bytes += segment_size
                    except OSError:
                        pass

            if existing_segments > 0:
                self.logger.info(f"Found {existing_segments} existing segments, resuming download...")
                successful_downloads = existing_segments
                # 显示断点续传状态
                progress_callback(
                    ProgressInfo(
                        total_size=0,
                        downloaded=total_downloaded_bytes,
                        speed=0.0,
                        status_message=f"发现 {existing_segments} 个已存在的分段，正在恢复下载...",
                        total_segments=total_segments,
                        completed_segments=existing_segments,
                        segment_speed=0.0,
                    )
                )
            else:
                # 显示开始下载状态
                progress_callback(
                    ProgressInfo(
                        total_size=0,
                        downloaded=0,
                        speed=0.0,
                        status_message=f"开始下载 {total_segments} 个视频分段...",
                        total_segments=total_segments,
                        completed_segments=0,
                        segment_speed=0.0,
                    )
                )

            def download_with_progress(segment_info: Tuple[int, str]) -> bool:
                nonlocal total_downloaded_bytes
                nonlocal successful_downloads

                # T006: 提交任务前检查中断标志
                if self._interrupt_handler.is_interrupted():
                    return False

                index, url = segment_info

                # 检查分段是否已存在（断点续传）
                segment_file = os.path.join(temp_dir, f"segment_{index:06d}.ts")
                if self._check_segment_exists(segment_file):
                    # 分段已存在，跳过下载
                    with self._lock:
                        # 更新进度（已存在的分段在初始化时已统计）
                        elapsed_time = time.time() - download_start_time
                        speed = total_downloaded_bytes / elapsed_time if elapsed_time > 0 else 0.0
                        seg_speed = successful_downloads / elapsed_time if elapsed_time > 0 else 0.0
                        progress_info = ProgressInfo(
                            total_size=0,
                            downloaded=total_downloaded_bytes,
                            speed=speed,
                            total_segments=total_segments,
                            completed_segments=successful_downloads,
                            segment_speed=seg_speed,
                        )
                        progress_callback(progress_info)
                    return True

                # 使用配置的重试次数进行重试
                for attempt in range(self.download_config.retry_times + 1):
                    # T007: 每次重试前检查中断标志
                    if self._interrupt_handler.is_interrupted():
                        return False

                    try:
                        segment_index, segment_data = self._download_segment(url, headers, index)
                        # 写入前再次检查中断
                        if self._interrupt_handler.is_interrupted():
                            return False
                        # 更新总字节数
                        with self._lock:
                            successful_downloads += 1
                            total_downloaded_bytes += len(segment_data)
                        # 将段数据写入临时文件
                        with open(segment_file, "wb") as f:
                            f.write(segment_data)

                        with self._lock:
                            # 计算下载速度
                            elapsed_time = time.time() - download_start_time
                            speed = total_downloaded_bytes / elapsed_time if elapsed_time > 0 else 0.0
                            seg_speed = successful_downloads / elapsed_time if elapsed_time > 0 else 0.0
                            downloaded_segments[segment_index] = segment_file
                            # 更新进度

                            progress_info = ProgressInfo(
                                total_size=0,
                                downloaded=total_downloaded_bytes,
                                speed=speed,
                                total_segments=total_segments,
                                completed_segments=successful_downloads,
                                segment_speed=seg_speed,
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
                    # T006: as_completed 循环中检查中断标志
                    if self._interrupt_handler.is_interrupted():
                        executor.shutdown(wait=False, cancel_futures=True)
                        self.logger.info("下载被用户中断")
                        return False
                    future.result()  # 等待完成

            # 检查是否有失败的下载
            if failed_downloads:
                self.logger.warning(f"Failed to download {len(failed_downloads)} segments")
                # 构建 SegmentResult 列表供调用方决策
                segment_results: list[SegmentResult] = []
                for i in range(total_segments):
                    if i in downloaded_segments:
                        segment_results.append(SegmentResult(index=i, success=True))
                    else:
                        error_msg = next((url for idx, url in failed_downloads if idx == i), "unknown")
                        segment_results.append(SegmentResult(index=i, success=False, error_message=f"Failed: {error_msg}"))
                # 存储状态供 retry/merge 使用
                self._last_segment_results = segment_results
                self._last_download_context = {
                    "segment_urls": segment_urls,
                    "headers": headers,
                    "temp_dir": temp_dir,
                    "output_file": output_file,
                    "total_segments": total_segments,
                    "downloaded_segments": downloaded_segments,
                    "total_downloaded_bytes": total_downloaded_bytes,
                    "progress_callback": progress_callback,
                }
                return False
            self.logger.info("Merging video segments...")

            # 显示合并状态
            progress_callback(
                ProgressInfo(
                    total_size=0,
                    downloaded=total_downloaded_bytes,
                    speed=0.0,
                    status_message=f"正在合并 {total_segments} 个视频分段...",
                )
            )

            def _merge_using_ffmpeg(segment_files: list[str], output_path: str) -> bool:
                """使用ffmpeg合并视频段"""
                import subprocess
                import tempfile

                # 创建临时文件列表
                with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
                    for segment in segment_files:
                        safe_path = os.path.abspath(segment).replace("\\", "/")
                        f.write(f"file '{safe_path}'\n")
                    filelist_path = f.name

                try:
                    # 使用ffmpeg合并视频段
                    cmd = [
                        "ffmpeg",
                        "-f",
                        "concat",
                        "-safe",
                        "0",
                        "-i",
                        filelist_path,
                        "-c",
                        "copy",
                        "-y",  # 覆盖输出文件
                        output_path,
                    ]

                    self.logger.info(f"Running ffmpeg command: {' '.join(cmd)}")
                    process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
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
                    except OSError:
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

                if shutil.which("ffmpeg"):
                    # 显示正在使用ffmpeg合并的状态
                    progress_callback(
                        ProgressInfo(
                            total_size=0,
                            downloaded=total_downloaded_bytes,
                            speed=0.0,
                            status_message="正在使用 ffmpeg 合并视频分段...",
                        )
                    )
                    ffmpeg_success = _merge_using_ffmpeg(segment_files, output_file)
            except Exception as e:
                self.logger.warning(f"Error checking for ffmpeg: {e}")

            # 如果ffmpeg失败或不可用，则使用传统方法合并
            if not ffmpeg_success:
                self.logger.info("Falling back to direct file merging...")
                progress_callback(
                    ProgressInfo(
                        total_size=0, downloaded=total_downloaded_bytes, speed=0.0, status_message="正在直接合并视频文件..."
                    )
                )
                with open(output_file, "wb") as output:
                    for segment_file in segment_files:
                        with open(segment_file, "rb") as f:
                            output.write(f.read())
            # 清理临时文件
            progress_callback(
                ProgressInfo(total_size=0, downloaded=total_downloaded_bytes, speed=0.0, status_message="正在清理临时文件...")
            )
            try:
                for segment_file in downloaded_segments.values():
                    if os.path.exists(segment_file):
                        os.remove(segment_file)
                os.rmdir(temp_dir)
            except Exception as e:
                self.logger.warning(f"Failed to clean up temporary files: {e}")

            self.logger.info(f"M3U8 video downloaded successfully: {output_file}")

            # 最终进度更新
            progress_info = ProgressInfo(
                total_size=total_segments, downloaded=total_segments, speed=0.0, status_message="✅ 下载完成！"
            )
            progress_callback(progress_info)

            return True

        except Exception as e:
            self.logger.error(f"M3U8 download failed: {e}")
            return False
        finally:
            self._session.close()

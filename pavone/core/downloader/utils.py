"""
下载器工具函数和示例
"""

from typing import Optional
from pavone.config.settings import DownloadConfig
from .http_downloader import HTTPDownloader
from .m3u8_downloader import M3U8Downloader
from .options import DownloadOpt
from .progress import create_console_progress_callback


def example_usage():
    """
    使用DownloadOpt的示例代码
    """
    # 创建配置
    config = DownloadConfig()
    
    # 创建下载器
    downloader = HTTPDownloader(config)
    
    # 创建下载选项，包含自定义HTTP头部
    download_opt = DownloadOpt(
        url="https://example.com/video.mp4",
        filename="my_video.mp4",
        custom_headers={
            "Referer": "https://example.com",
            "Authorization": "Bearer token123",
            "Custom-Header": "custom-value"
        }
    )
    
    # 创建进度回调
    progress_callback = create_console_progress_callback()
    
    # 执行下载
    success = downloader.download(download_opt, progress_callback)
    
    if success:
        print("下载成功!")
    else:
        print("下载失败!")


def example_usage_with_proxy():
    """
    使用代理设置的示例代码
    """
    # 创建带代理设置的下载配置
    config = DownloadConfig(
        output_dir="./downloads",
        timeout=30,
        proxy_enabled=True,
        http_proxy="http://127.0.0.1:1080",
        https_proxy="http://127.0.0.1:1080"
    )
    
    # 创建下载器
    downloader = HTTPDownloader(config)
    
    # 创建下载选项
    download_opt = DownloadOpt(
        url="https://example.com/video.mp4",
        filename="video.mp4",
        custom_headers={
            "Referer": "https://example.com"
        }
    )
    
    # 创建进度回调
    progress_callback = create_console_progress_callback()
    
    # 执行下载（会使用代理）
    success = downloader.download(download_opt, progress_callback)
    
    if success:
        print("下载成功!")
    else:
        print("下载失败!")


def example_multithreaded_download():
    """
    多线程下载示例
    """
    # 创建支持多线程的下载配置
    config = DownloadConfig(
        max_concurrent_downloads=4,  # 4个线程
        timeout=60,
        proxy_enabled=False
    )
    
    # 创建下载器
    downloader = HTTPDownloader(config)
    
    # 创建下载选项
    download_opt = DownloadOpt(
        url="https://example.com/large_video.mp4",  # 大文件
        filename="large_video.mp4"
    )
    
    # 创建进度回调
    progress_callback = create_console_progress_callback()
    
    print("开始下载（将自动检测是否使用多线程）...")
    success = downloader.download(download_opt, progress_callback)
    
    if success:
        print("\\n下载完成!")
    else:
        print("\\n下载失败!")


def create_high_performance_config() -> DownloadConfig:
    """
    创建高性能下载配置
    """
    return DownloadConfig(
        max_concurrent_downloads=6,  # 6个并发线程
        retry_times=5,
        timeout=120,  # 2分钟超时
        proxy_enabled=False
    )


def create_config_with_proxy(http_proxy: str, https_proxy: Optional[str] = None) -> DownloadConfig:
    """
    便利函数：创建带代理设置的下载配置
    
    Args:
        http_proxy: HTTP代理地址
        https_proxy: HTTPS代理地址，如果为None则使用http_proxy
    
    Returns:
        DownloadConfig: 配置好的下载配置
    """
    return DownloadConfig(
        proxy_enabled=True,
        http_proxy=http_proxy,
        https_proxy=https_proxy or http_proxy
    )


def create_m3u8_downloader_config(output_dir: str = "./downloads", 
                                  max_concurrent_downloads: int = 4,
                                  timeout: int = 30,
                                  with_proxy: bool = False,
                                  proxy_http: Optional[str] = None,
                                  proxy_https: Optional[str] = None) -> DownloadConfig:
    """
    创建M3U8下载器的配置
    
    Args:
        output_dir: 输出目录
        max_concurrent_downloads: 最大并发下载段数
        timeout: 超时时间（秒）
        with_proxy: 是否使用代理
        proxy_http: HTTP代理地址
        proxy_https: HTTPS代理地址
        
    Returns:
        DownloadConfig: 配置对象
    """
    return DownloadConfig(
        output_dir=output_dir,
        max_concurrent_downloads=max_concurrent_downloads,
        timeout=timeout,
        proxy_enabled=with_proxy,
        http_proxy=proxy_http or "",
        https_proxy=proxy_https or ""
    )


def example_m3u8_download():
    """
    M3U8下载器使用示例
    """
    # 创建M3U8下载配置
    config = create_m3u8_downloader_config(
        output_dir="./downloads/m3u8",
        max_concurrent_downloads=4,
        timeout=60
    )
    
    # 创建M3U8下载器
    downloader = M3U8Downloader(config)
    
    # 创建下载选项
    download_opt = DownloadOpt(
        url="https://example.com/video/playlist.m3u8",
        filename="example_video.mp4",
        custom_headers={
            "User-Agent": "MyM3U8Player/1.0",
            "Referer": "https://example.com"
        }
    )
    
    # 创建进度回调
    progress_callback = create_console_progress_callback()
    
    # 执行下载
    success = downloader.download(download_opt, progress_callback)
    
    if success:
        print("M3U8视频下载成功!")
    else:
        print("M3U8视频下载失败!")


def example_m3u8_download_with_auth():
    """
    带认证的M3U8下载示例
    """
    # 创建配置
    config = create_m3u8_downloader_config(
        output_dir="./downloads/secure",
        max_concurrent_downloads=2,
        timeout=30
    )
    
    # 创建下载器
    downloader = M3U8Downloader(config)
    
    # 创建带认证头部的下载选项
    download_opt = DownloadOpt(
        url="https://secure.example.com/premium/playlist.m3u8",
        filename="premium_video.mp4",
        custom_headers={
            "Authorization": "Bearer your_access_token",
            "X-API-Key": "your_api_key",
            "User-Agent": "AuthorizedClient/2.0"
        }
    )
    
    # 执行下载
    success = downloader.download(download_opt)
    
    if success:
        print("认证M3U8视频下载成功!")
    else:
        print("认证M3U8视频下载失败!")

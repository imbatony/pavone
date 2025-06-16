"""
DownloadManager使用示例

这个文件展示了如何使用DownloadManager进行下载管理
"""

from pavone.config.settings import DownloadConfig
from pavone.core.downloader.download_manager import DownloadManager, create_download_manager
from pavone.core.downloader.progress import ProgressInfo


def simple_progress_callback(progress: ProgressInfo):
    """简单的进度回调函数"""
    if progress.total_size > 0:
        percentage = progress.percentage
        print(f"\r下载进度: {percentage:.1f}% ({progress.downloaded}/{progress.total_size} bytes)", end="")
    else:
        print(f"\r已下载: {progress.downloaded} bytes", end="")


def example_single_download():
    """单个URL下载示例"""
    print("=== 单个URL下载示例 ===")
    
    # 创建配置
    config = DownloadConfig(
        output_dir="./downloads",
        max_concurrent_downloads=3,
        timeout=30
    )
    
    # 创建下载管理器
    manager = create_download_manager(config)
    
    # 测试URL列表
    test_urls = [
        "https://example.com/video.mp4",
        "https://example.com/playlist.m3u8",
        "https://youtube.com/watch?v=test123"
    ]
    
    for url in test_urls:
        print(f"\n处理URL: {url}")
        try:
            # 提取下载选项
            options = manager.extract_download_options(url)
            print(f"找到 {len(options)} 个下载选项")
            
            # 显示所有选项
            for i, opt in enumerate(options, 1):
                print(f"  {i}. {opt.get_full_description()}")
            
            # 自动选择第一个选项进行下载
            if options:
                success = manager.download_option(options[0], simple_progress_callback)
                print(f"\n下载结果: {'成功' if success else '失败'}")
                
        except ValueError as e:
            print(f"处理失败: {e}")


def example_interactive_download():
    """交互式下载示例"""
    print("\n=== 交互式下载示例 ===")
    
    config = DownloadConfig(output_dir="./downloads")
    manager = create_download_manager(config)
    
    # 模拟用户输入URL
    test_url = "https://bilibili.com/video/BV123456"
    
    print(f"开始处理URL: {test_url}")
    
    # 使用完整的下载流程（包含用户选择）
    # 注意：在实际使用中，这会要求用户输入选择
    # 这里我们使用auto_select=True来避免交互
    success = manager.download_from_url(test_url, simple_progress_callback, auto_select=True)
    print(f"下载结果: {'成功' if success else '失败'}")


def example_batch_download():
    """批量下载示例"""
    print("\n=== 批量下载示例 ===")
    
    config = DownloadConfig(
        output_dir="./downloads",
        max_concurrent_downloads=2
    )
    manager = create_download_manager(config)
    
    # URL列表
    urls = [
        "https://example.com/video1.mp4",
        "https://example.com/video2.mp4", 
        "https://example.com/stream.m3u8"
    ]
    
    # 批量下载
    results = manager.batch_download(urls, simple_progress_callback, auto_select=True)
    
    # 显示结果
    print("\n批量下载结果:")
    for url, success in results:
        status = "成功" if success else "失败"
        print(f"  {url}: {status}")


def example_downloader_selection():
    """下载器选择逻辑示例"""
    print("\n=== 下载器选择逻辑示例 ===")
    
    from pavone.core.downloader.options import DownloadOpt, LinkType
    
    config = DownloadConfig()
    manager = create_download_manager(config)
    
    # 测试不同类型的下载选项
    test_options = [
        DownloadOpt(
            url="https://example.com/video.mp4",
            link_type=LinkType.VIDEO,
            display_name="普通视频文件",
            quality="1080p"
        ),
        DownloadOpt(
            url="https://example.com/stream.m3u8",
            link_type=LinkType.STREAM,
            display_name="流媒体文件",
            quality="流媒体"
        ),
        DownloadOpt(
            url="https://example.com/image.jpg",
            link_type=LinkType.IMAGE,
            display_name="图片文件",
            quality="原图"
        )
    ]
    
    for opt in test_options:
        downloader_type, downloader = manager.get_downloader_for_option(opt)
        print(f"{opt.get_display_name()}: 使用 {downloader_type} 下载器")


if __name__ == "__main__":
    print("DownloadManager使用示例")
    print("注意：这是示例代码，实际运行时某些URL可能无法访问")
    
    try:
        # 运行示例
        example_downloader_selection()
        example_single_download()
        example_interactive_download()
        example_batch_download()
        
    except KeyboardInterrupt:
        print("\n用户中断操作")
    except Exception as e:
        print(f"\n运行示例时出错: {e}")

"""
Download commands - 下载相关命令
"""

import click
from typing import Optional
from ...config.settings import ConfigManager
from ..utils import echo_success, echo_error, echo_info, read_urls_from_file, read_urls_from_input


@click.command()
@click.argument('url')
@click.option('--auto-select', '-a', is_flag=True, help='自动选择第一个下载选项，无需手动选择')
@click.option('--silent', '-s', is_flag=True, help='静默模式，不显示下载进度')
@click.option('--filename', '-f', type=str, help='指定输出文件名')
@click.option('--output-dir', '-o', type=click.Path(), help='指定输出目录')
@click.option('--header', multiple=True, help='自定义HTTP头部 (可多次使用, 格式: "Key: Value")')
@click.option('--proxy', type=str, help='HTTP代理地址 (格式: http://proxy:port)')
@click.option('--organize', is_flag=True, help='下载后自动整理文件')
@click.option('--threads', '-t', type=click.IntRange(1, 16), help='下载线程数 (1-16)')
@click.option('--retry', '-r', type=click.IntRange(0, 10), help='失败重试次数 (0-10)')
@click.option('--timeout', type=click.IntRange(5, 300), help='连接超时时间(秒)')
def download(url: str, auto_select: bool, silent: bool, filename: Optional[str], 
             output_dir: Optional[str], header: tuple, proxy: Optional[str], 
             organize: bool, threads: Optional[int], retry: Optional[int], 
             timeout: Optional[int]):
    """下载指定URL的视频"""
    try:
        # 获取配置
        config_manager = ConfigManager()
        download_config = config_manager.config.download
        
        # 应用命令行选项覆盖配置
        if output_dir:
            download_config.output_dir = output_dir
        if threads:
            download_config.max_concurrent_downloads = threads
        if retry is not None:
            download_config.retry_times = retry
        if timeout:
            download_config.timeout = timeout
        
        # 处理代理设置
        if proxy:
            echo_info(f"使用代理: {proxy}")
        
        # 处理自定义HTTP头部
        custom_headers = {}
        for h in header:
            if ':' in h:
                key, value = h.split(':', 1)
                custom_headers[key.strip()] = value.strip()
            else:
                echo_error(f"无效的头部格式: {h} (应为 'Key: Value')")
                return 1
        
        # 导入必要的模块
        from ...core.downloader.download_manager import create_download_manager
        from ...core.downloader.progress import create_console_progress_callback, create_silent_progress_callback
        from ...plugins.manager import PluginManager
        
        # 创建插件管理器和下载管理器
        plugin_manager = PluginManager()
        download_manager = create_download_manager(download_config, plugin_manager)
        
        # 创建进度回调
        progress_callback = create_silent_progress_callback() if silent else create_console_progress_callback()
        
        click.echo(f"正在下载: {url}")
        if filename:
            echo_info(f"输出文件名: {filename}")
        if output_dir:
            echo_info(f"输出目录: {output_dir}")
        if custom_headers:
            echo_info(f"自定义头部: {len(custom_headers)} 个")
        
        # 执行下载
        success = download_manager.download_from_url(
            url=url,
            progress_callback=progress_callback,
            auto_select=auto_select
        )
        
        if success:
            echo_success("下载完成！")
            if organize:
                echo_info("开始自动整理文件...")
                # TODO: 调用整理功能
                echo_success("文件整理完成！")
        else:
            echo_error("下载失败！")
            return 1
            
    except Exception as e:
        echo_error(f"下载出错: {e}")
        return 1


@click.command()
@click.option('--file', '-f', type=click.Path(exists=True), help='从文件读取URL列表')
@click.option('--auto-select', '-a', is_flag=True, help='自动选择第一个下载选项，无需手动选择')
@click.option('--silent', '-s', is_flag=True, help='静默模式，不显示下载进度')
@click.option('--output-dir', '-o', type=click.Path(), help='指定输出目录')
@click.option('--header', multiple=True, help='自定义HTTP头部 (可多次使用, 格式: "Key: Value")')
@click.option('--proxy', type=str, help='HTTP代理地址 (格式: http://proxy:port)')
@click.option('--organize', is_flag=True, help='下载后自动整理文件')
@click.option('--threads', '-t', type=click.IntRange(1, 16), help='下载线程数 (1-16)')
@click.option('--retry', '-r', type=click.IntRange(0, 10), help='失败重试次数 (0-10)')
@click.option('--timeout', type=click.IntRange(5, 300), help='连接超时时间(秒)')
def batch_download(file: Optional[str], auto_select: bool, silent: bool,
                  output_dir: Optional[str], header: tuple, proxy: Optional[str], 
                  organize: bool, threads: Optional[int], retry: Optional[int], 
                  timeout: Optional[int]):
    """批量下载多个URL"""
    try:
        # 获取配置
        config_manager = ConfigManager()
        download_config = config_manager.config.download
        
        # 应用命令行选项覆盖配置
        if output_dir:
            download_config.output_dir = output_dir
        if threads:
            download_config.max_concurrent_downloads = threads
        if retry is not None:
            download_config.retry_times = retry
        if timeout:
            download_config.timeout = timeout
        
        # 处理代理设置
        if proxy:
            echo_info(f"使用代理: {proxy}")
        
        # 处理自定义HTTP头部
        custom_headers = {}
        for h in header:
            if ':' in h:
                key, value = h.split(':', 1)
                custom_headers[key.strip()] = value.strip()
            else:
                echo_error(f"无效的头部格式: {h} (应为 'Key: Value')")
                return 1
        
        # 导入必要的模块
        from ...core.downloader.download_manager import create_download_manager
        from ...core.downloader.progress import create_console_progress_callback, create_silent_progress_callback
        from ...plugins.manager import PluginManager
        
        # 读取URL列表
        urls = []
        if file:
            urls = read_urls_from_file(file)
        else:
            urls = read_urls_from_input()
        
        if not urls:
            echo_error("没有找到有效的URL")
            return 1
        
        # 创建插件管理器和下载管理器
        plugin_manager = PluginManager()
        download_manager = create_download_manager(download_config, plugin_manager)
        
        # 创建进度回调
        progress_callback = create_silent_progress_callback() if silent else create_console_progress_callback()
        
        click.echo(f"开始批量下载 {len(urls)} 个URL...")
        if output_dir:
            echo_info(f"输出目录: {output_dir}")
        if custom_headers:
            echo_info(f"自定义头部: {len(custom_headers)} 个")
        
        # 执行批量下载
        results = download_manager.batch_download(
            urls=urls,
            progress_callback=progress_callback,
            auto_select=auto_select
        )
        
        # 显示结果摘要
        successful = sum(1 for _, success in results if success)
        failed = len(results) - successful
        
        echo_info(f"批量下载完成:")
        echo_success(f"成功: {successful}")
        if failed > 0:
            echo_error(f"失败: {failed}")
        
        if organize and successful > 0:
            echo_info("开始自动整理文件...")
            # TODO: 调用整理功能
            echo_success("文件整理完成！")
        
        if failed > 0:
            click.echo("\n失败的URL:")
            for url, success in results:
                if not success:
                    click.echo(f"  - {url}")
            return 1
            
    except Exception as e:
        echo_error(f"批量下载出错: {e}")
        return 1

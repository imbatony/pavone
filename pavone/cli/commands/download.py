"""
Download commands - 下载相关命令
"""

import click
from typing import Optional
from ...config.settings import get_config_manager
from .utils import echo_success, echo_error, echo_info, read_urls_from_file, read_urls_from_input, echo_warning
# 导入必要的模块
from ...core.downloader.progress import create_console_progress_callback, create_silent_progress_callback
from ...plugins.manager import PluginManager

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
             output_dir: Optional[str], header: tuple[str,str], proxy: Optional[str], 
             organize: bool, threads: Optional[int], retry: Optional[int], 
             timeout: Optional[int]):
    """下载指定URL的视频"""
    try:
        # 获取配置
        config_manager = get_config_manager()
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
        config_manager = get_config_manager()
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

"""
下载器门面类
提供统一的下载接口，自动选择合适的下载器和提取器
"""

from typing import List, Optional, Tuple
from ...config.settings import DownloadConfig
from ...plugins.manager import PluginManager
from ...core.downloader.options import DownloadOpt, LinkType
from ...core.downloader.http_downloader import HTTPDownloader
from ...core.downloader.m3u8_downloader import M3U8Downloader
from ...core.downloader.progress import ProgressCallback
from ...core.downloader.base import BaseDownloader
from ...config.logging_config import get_logger


class DownloadManager:
    """下载管理器门面类
    
    提供统一的下载接口，自动处理URL提取、用户选择和下载器选择
    """
    
    def __init__(self,
     config: DownloadConfig,
     plugin_manager: Optional[PluginManager] = None):
        """
        初始化下载管理器
        
        Args:
            config: 下载配置
            plugin_manager: 插件管理器实例，如果为None则创建新实例
        """
        self.config = config
        self.plugin_manager = plugin_manager or PluginManager()
        self.logger = get_logger(__name__)
        
        # 初始化下载器
        self.http_downloader = HTTPDownloader(config)
        self.m3u8_downloader = M3U8Downloader(config)

        
        # 确保插件已加载
        if not self.plugin_manager.extractor_plugins:
            self.plugin_manager.load_plugins()
    
    def extract_download_options(self, url: str) -> List[DownloadOpt]:
        """
        从URL提取下载选项
        
        Args:
            url: 要处理的URL
            
        Returns:
            可用的下载选项列表
            
        Raises:
            ValueError: 如果找不到合适的提取器
        """
        # 获取合适的提取器
        extractor = self.plugin_manager.get_extractor_for_url(url)
        if not extractor:
            raise ValueError(f"没有找到能处理URL的提取器: {url}")        
        # 提取下载选项
        if hasattr(extractor, 'extract') and callable(getattr(extractor, 'extract')):
            options = extractor.extract(url)  # type: ignore
            if not options:
                raise ValueError(f"提取器 {extractor.name} 没有找到下载选项")
            return options
        else:
            raise ValueError(f"提取器 {extractor.name} 缺少extract方法")
    
    def select_download_option(self, options: List[DownloadOpt]) -> DownloadOpt:
        """
        让用户选择下载选项
        
        Args:
            options: 可用的下载选项列表
            
        Returns:
            用户选择的下载选项
              Raises:
            ValueError: 如果用户输入无效或取消选择
        """
        if len(options) == 1:
            echo_info(f"找到1个下载选项: {options[0].get_full_description()}")
            return options[0]
        
        echo_info(f"找到 {len(options)} 个下载选项:")
        for i, opt in enumerate(options, 1):
            print(f"  {i}. {opt.get_full_description()}")
        
        while True:
            try:
                choice = input(f"请选择下载选项 (1-{len(options)}, 0取消): ").strip()
                
                if choice == "0":
                    raise ValueError("用户取消了下载")
                
                choice_num = int(choice)
                if 1 <= choice_num <= len(options):
                    selected = options[choice_num - 1]
                    echo_info(f"已选择: {selected.get_full_description()}")
                    return selected
                else:
                    echo_info(f"请输入1到{len(options)}之间的数字")
                    
            except ValueError as e:
                if "用户取消了下载" in str(e):
                    raise
                echo_warning("输入无效，请输入数字")
            except KeyboardInterrupt:
                raise ValueError("用户取消了下载")
    
    def get_downloader_for_option(self, option: DownloadOpt) -> Tuple[str, BaseDownloader]:
        """
        根据下载选项选择合适的下载器
        
        Args:
            option: 下载选项
            
        Returns:
            (下载器类型, 下载器实例)
        """
        # M3U8Downloader只适用于stream类型
        if option.link_type == LinkType.STREAM or option.is_stream():
            return ("M3U8", self.m3u8_downloader)
        else:
            # 其他情况使用HTTPDownloader
            return ("HTTP", self.http_downloader)
    
    def download_from_url(self, url: str, 
                         progress_callback: Optional[ProgressCallback] = None,
                         auto_select: bool = False) -> bool:
        """
        从URL下载内容的完整流程
        
        Args:
            url: 要下载的URL
            progress_callback: 进度回调函数
            auto_select: 是否自动选择第一个选项（用于自动化场景）
              Returns:
            下载是否成功        """
        try:
            print(f"正在分析URL: {url}")
            
            # 1. 提取下载选项
            options = self.extract_download_options(url)
            
            # 2. 选择下载选项
            if auto_select:
                selected_option = options[0]
                print(f"自动选择: {selected_option.get_full_description()}")
            else:
                selected_option = self.select_download_option(options)
            
            # 3. 选择下载器并下载
            downloader_type, downloader = self.get_downloader_for_option(selected_option)
            print(f"使用 {downloader_type} 下载器")
            
            return downloader.download(selected_option, progress_callback)
            
        except Exception as e:
            print(f"下载失败: {e}")
            return False
    
    def download_option(self, option: DownloadOpt,
                       progress_callback: Optional[ProgressCallback] = None) -> bool:
        """
        直接下载指定的选项
        
        Args:
            option: 要下载的选项
            progress_callback: 进度回调函数
              Returns:
            下载是否成功
        """
        try:
            downloader_type, downloader = self.get_downloader_for_option(option)
            print(f"使用 {downloader_type} 下载器下载: {option.get_display_name()}")
            
            return downloader.download(option, progress_callback)
            
        except Exception as e:
            print(f"下载失败: {e}")
            return False
    
    def batch_download(self, urls: List[str],
                      progress_callback: Optional[ProgressCallback] = None,
                      auto_select: bool = True) -> List[Tuple[str, bool]]:
        """
        批量下载多个URL
        
        Args:
            urls: URL列表
            progress_callback: 进度回调函数
            auto_select: 是否自动选择第一个选项
              Returns:
            (URL, 成功状态) 的列表
        """
        results = []
        
        for i, url in enumerate(urls, 1):
            self.logger.debug(f"\n[{i}/{len(urls)}] 处理: {url}")
            success = self.download_from_url(url, progress_callback, auto_select)
            results.append((url, success))
            
            if not success:
                print(f"URL下载失败: {url}")
        
        # 输出总结
        successful = sum(1 for _, success in results if success)
        print(f"\n批量下载完成: {successful}/{len(urls)} 成功")
        
        return results


def create_download_manager(config: DownloadConfig, 
                           plugin_manager: Optional[PluginManager] = None) -> DownloadManager:
    """
    创建下载管理器实例的便利函数
    
    Args:
        config: 下载配置
        plugin_manager: 可选的插件管理器实例
        
    Returns:
        配置好的下载管理器实例
    """
    return DownloadManager(config, plugin_manager)
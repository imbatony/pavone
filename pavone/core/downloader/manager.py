"""
下载器门面类
提供统一的下载接口，自动选择合适的下载器和提取器
"""

from typing import List, Optional, Tuple, Union
from ...config.settings import DownloadConfig
from ...plugins.manager import PluginManager
from .options import DownloadOpt, LinkType
from .http_downloader import HTTPDownloader
from .m3u8_downloader import M3U8Downloader
from .progress import ProgressCallback
from .base import BaseDownloader


class DownloadManager:
    """下载管理器门面类
    
    提供统一的下载接口，自动处理URL提取、用户选择和下载器选择
    """
    
    def __init__(self, config: DownloadConfig, plugin_manager: Optional[PluginManager] = None):
        """
        初始化下载管理器
        
        Args:
            config: 下载配置
            plugin_manager: 插件管理器实例，如果为None则创建新实例
        """
        self.config = config
        self.plugin_manager = plugin_manager or PluginManager()
        
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
            print(f"找到1个下载选项: {options[0].get_full_description()}")
            return options[0]
        
        print(f"找到 {len(options)} 个下载选项:")
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
                    print(f"已选择: {selected.get_full_description()}")
                    return selected
                else:
                    print(f"请输入1到{len(options)}之间的数字")
            except ValueError as e:
                if "用户取消了下载" in str(e):
                    raise
                print("输入无效，请输入数字")
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
            下载是否成功
        """
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
            print(f"\n[{i}/{len(urls)}] 处理: {url}")
            success = self.download_from_url(url, progress_callback, auto_select)
            results.append((url, success))
            
            if not success:
                print(f"URL下载失败: {url}")
        
        # 输出总结
        successful = sum(1 for _, success in results if success)
        print(f"\n批量下载完成: {successful}/{len(urls)} 成功")
        
        return results

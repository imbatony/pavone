import requests
from abc import abstractmethod
from typing import List, Optional, Dict
from ..base import BasePlugin
from ...core.downloader.options import DownloadOpt
from ...config.settings import config_manager, get_download_config
import time
from ...config.logging_config import get_logger

class ExtractorPlugin(BasePlugin):
    """提取器插件基类
    
    提取器插件负责分析给定的URL并提取出可下载的资源列表，
    而不直接进行下载操作
    """
    
    def __init__(self):
        super().__init__()
        self.priority = 50  # 默认优先级，数值越小优先级越高
        self.logger = get_logger(__name__)
    
    @property
    def priority_level(self) -> int:
        """获取插件优先级
        
        Returns:
            优先级数值，越小优先级越高
        """
        return self.priority
    
    def set_priority(self, priority: int):
        """设置插件优先级
        
        Args:
            priority: 优先级数值，越小优先级越高
        """
        self.priority = priority
    
    def fetch_webpage(self, url: str, headers: Optional[Dict[str, str]] = None, 
                     timeout: int = 30, verify_ssl: bool = False, max_retry: Optional[int] = None) -> requests.Response:
        """统一的网页获取方法，自动处理代理配置和SSL验证
        
        Args:
            url: 要获取的URL
            headers: 自定义HTTP头部，如果为None则使用默认浏览器头部
            timeout: 请求超时时间（秒）
            verify_ssl: 是否验证SSL证书，默认为False忽略SSL错误
            max_retry: 最大重试次数，如果为None则使用配置中的值
            
        Returns:
            requests.Response: HTTP响应对象
            
        Raises:
            requests.RequestException: 网络请求失败时抛出
        """
        
        # 获取配置
        download_config = get_download_config()
        if max_retry is None:
            max_retry = download_config.retry_times
        retry_interval_ms = download_config.retry_interval
        
        # 禁用SSL警告（如果需要的话）
        if not verify_ssl:
            try:
                import urllib3
                from urllib3.exceptions import InsecureRequestWarning
                urllib3.disable_warnings(InsecureRequestWarning)
            except ImportError:
                # urllib3不可用时忽略警告禁用
                pass
        
        # 使用默认的浏览器头部
        if headers is None:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            }
        
        # 获取代理配置
        proxies = self._get_proxies()
        
        # 实现重试机制
        last_exception = None
        for attempt in range(max_retry + 1):
            try:
                # 发起请求
                response = requests.get(
                    url,
                    headers=headers,
                    proxies=proxies,
                    timeout=timeout,                
                    verify=verify_ssl  # SSL验证设置
                )
                response.raise_for_status()
                
                # 请求成功，记录日志（仅在重试后成功时）
                if attempt > 0:
                    self.logger.info(f"网页获取成功 {url} (第{attempt + 1}次尝试)")
                
                return response
                
            except requests.RequestException as e:
                last_exception = e
                
                if attempt < max_retry:
                    # 不是最后一次尝试，记录警告并等待重试
                    retry_delay = retry_interval_ms / 1000.0  # 转换为秒
                    self.logger.warning(f"网页获取失败 {url} (第{attempt + 1}次尝试): {e}，{retry_delay}秒后重试...")
                    time.sleep(retry_delay)
                else:
                    # 最后一次尝试失败，记录错误
                    self.logger.error(f"网页获取最终失败 {url} (共{max_retry + 1}次尝试): {e}")
        
        # 所有重试都失败了，抛出最后一个异常
        raise requests.RequestException(f"获取网页失败 {url}: {last_exception}")

    def _get_proxies(self) -> Optional[Dict[str, str]]:
        """获取当前的代理配置
        
        Returns:
            代理配置字典，如果未启用代理则返回None
        """
        try:
            config = config_manager.get_config()
            if not config.proxy.enabled:
                return None
            
            proxies = {}
            if config.proxy.http_proxy:
                proxies['http'] = config.proxy.http_proxy
            if config.proxy.https_proxy:
                proxies['https'] = config.proxy.https_proxy
            
            return proxies if proxies else None
        except Exception:
            # 如果获取配置失败，返回None（不使用代理）
            return None

    def sanitize_filename(self, filename: str) -> str:
        """
        清理文件名，移除非法字符
        
        Args:
            filename: 原始文件名
            
        Returns:
            清理后的文件名
        """
        if not filename or not filename.strip():
            return "video"
        
        # 移除或替换非法字符
        illegal_chars = ['<', '>', ':', '"', '/', '\\', '|', '?', '*']
        sanitized = filename
        for char in illegal_chars:
            sanitized = sanitized.replace(char, '_')
        
        # 限制文件名长度
        if len(sanitized) > 200:
            sanitized = sanitized[:200]
        
        return sanitized.strip()

    @abstractmethod
    def can_handle(self, url: str) -> bool:
        """检查是否能处理该URL"""
        pass
    
    @abstractmethod
    def extract(self, url: str) -> List[DownloadOpt]:
        """从URL中提取下载选项列表
        
        Args:
            url: 要分析的URL
            
        Returns:
            包含所有可下载资源的DownloadOpt列表
        """
        pass

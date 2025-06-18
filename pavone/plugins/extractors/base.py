"""
提取器插件基类
"""

import requests
from abc import abstractmethod
from typing import List, Optional, Dict, Any
from urllib.parse import urlparse

from ..base import BasePlugin
from ...core.downloader.options import DownloadOpt
from ...config.settings import config_manager


class ExtractorPlugin(BasePlugin):
    """提取器插件基类
    
    提取器插件负责分析给定的URL并提取出可下载的资源列表，
    而不直接进行下载操作
    """
    
    def __init__(self):
        super().__init__()
        self.priority = 50  # 默认优先级，数值越小优先级越高
    
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
                     timeout: int = 30, verify_ssl: bool = False) -> requests.Response:
        """统一的网页获取方法，自动处理代理配置和SSL验证
        
        Args:
            url: 要获取的URL
            headers: 自定义HTTP头部，如果为None则使用默认浏览器头部
            timeout: 请求超时时间（秒）
            verify_ssl: 是否验证SSL证书，默认为False忽略SSL错误
            
        Returns:
            requests.Response: HTTP响应对象
            
        Raises:
            requests.RequestException: 网络请求失败时抛出
        """
        try:
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
                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                    'Accept-Language': 'zh-CN,zh;q=0.8,en-US;q=0.5,en;q=0.3',
                    'Accept-Encoding': 'gzip, deflate',
                    'Connection': 'keep-alive',
                    'Upgrade-Insecure-Requests': '1'
                }
              # 获取代理配置
            proxies = self._get_proxies()
            
            # 发起请求
            response = requests.get(
                url,
                headers=headers,
                proxies=proxies,
                timeout=timeout,                
                verify=verify_ssl  # SSL验证设置
            )
            response.raise_for_status()
            return response
        except requests.RequestException as e:
            raise requests.RequestException(f"获取网页失败 {url}: {e}")

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

import time
from logging import Logger
from typing import Dict, Optional

import requests

from pavone.config.configs import DownloadConfig, ProxyConfig


class HttpUtils:
    @staticmethod
    def fetch(
        download_config: DownloadConfig,
        proxy_config: ProxyConfig,
        url: str,
        logger: Optional[Logger] = None,
        headers: Optional[Dict[str, str]] = None,
        timeout: int = 30,
        verify_ssl: bool = False,
        max_retry: Optional[int] = None,
        no_exceptions: bool = False,
    ) -> requests.Response:
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
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            }

        # 获取代理配置
        proxies = HttpUtils.get_proxies(proxy_config)

        # 实现重试机制
        last_exception = None
        last_response: Optional[requests.Response] = None
        for attempt in range(max_retry + 1):
            try:
                # 发起请求
                response = requests.get(
                    url,
                    headers=headers,
                    proxies=proxies,
                    timeout=timeout,
                    verify=verify_ssl,  # SSL验证设置
                )
                last_response = response
                response.raise_for_status()

                # 请求成功，记录日志（仅在重试后成功时）
                if attempt > 0 and logger:
                    logger.info(f"网页获取成功 {url} (第{attempt + 1}次尝试)")

                return response

            except requests.RequestException as e:
                last_exception = e

                if attempt < max_retry:
                    # 不是最后一次尝试，记录警告并等待重试
                    retry_delay = retry_interval_ms / 1000.0  # 转换为秒
                    time.sleep(retry_delay)
                else:
                    # 最后一次尝试失败，记录错误
                    if logger:
                        if attempt == 0:
                            logger.error(f"网页获取失败 {url}: {e}")
                        else:
                            logger.error(f"网页获取失败 {url} (第{attempt + 1}次尝试): {e}")

        # 所有重试都失败了，抛出最后一个异常
        if no_exceptions:
            # 如果设置了不抛出异常，返回一个空响应对象
            return last_response or requests.Response()
        raise requests.RequestException(f"获取网页失败 {url}: {last_exception}")

    @staticmethod
    def get_proxies(proxy_config: ProxyConfig) -> Optional[Dict[str, str]]:
        """获取当前的代理配置

        Returns:
            代理配置字典，如果未启用代理则返回None
        """
        try:
            if not proxy_config.enabled:
                return None

            proxies: Dict[str, str] = {}
            if proxy_config.http_proxy:
                proxies["http"] = proxy_config.http_proxy
            if proxy_config.https_proxy:
                proxies["https"] = proxy_config.https_proxy

            return proxies if proxies else None
        except Exception:
            # 如果获取配置失败，返回None（不使用代理）
            return None

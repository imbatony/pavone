import time
from logging import Logger
from typing import Dict, List, Optional, cast

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
        verify_ssl: bool = True,
        max_retry: Optional[int] = None,
        no_exceptions: bool = False,
    ) -> requests.Response:
        """统一的网页获取方法，自动处理代理配置和SSL验证

        Args:
            url: 要获取的URL
            headers: 自定义HTTP头部，如果为None则使用默认浏览器头部
            timeout: 请求超时时间（秒）
            verify_ssl: 是否验证SSL证书，默认为True启用SSL验证
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
            if logger:
                logger.warning("SSL 证书验证已禁用，存在安全风险")
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
        # retry_times 表示总尝试次数（包括首次尝试）
        last_exception = None
        last_response: Optional[requests.Response] = None
        for attempt in range(max_retry):
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

                if attempt < max_retry - 1:
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

    @staticmethod
    def fetch_with_browser(
        url: str,
        proxy_config: Optional[ProxyConfig] = None,
        logger: Optional[Logger] = None,
        wait_for_content: Optional[List[str]] = None,
        reject_content: Optional[List[str]] = None,
        max_wait: int = 30,
    ) -> requests.Response:
        """使用真实浏览器（DrissionPage）获取网页内容，可绕过 Cloudflare Turnstile 等保护

        获取完成后会自动关闭浏览器实例以释放资源。

        注意：不使用 headless 模式，因为 Cloudflare Turnstile 会检测无头浏览器。

        Args:
            url: 要获取的页面 URL
            proxy_config: 代理配置，如果为 None 则不使用代理
            logger: 日志记录器
            wait_for_content: 等待页面中出现的内容标记列表（如 ["application/ld+json", "og:title"]），
                              任一内容出现即认为页面加载完成
            reject_content: 拒绝的内容标记列表（如 ["请稍候", "Just a moment"]），
                            页面包含这些内容时认为尚未加载完成
            max_wait: 最大等待时间（秒），默认 30 秒

        Returns:
            requests.Response: 包含页面 HTML 的响应对象。
            成功时 status_code=200，失败时 status_code=503。
        """
        if wait_for_content is None:
            wait_for_content = ["application/ld+json", "og:title"]
        if reject_content is None:
            reject_content = ["请稍候", "Just a moment"]

        html: Optional[str] = None
        try:
            html = HttpUtils._fetch_html_with_browser(
                url=url,
                proxy_config=proxy_config,
                logger=logger,
                wait_for_content=wait_for_content,
                reject_content=reject_content,
                max_wait=max_wait,
            )
        except Exception as e:
            if logger:
                logger.error(f"浏览器获取页面失败: {e}")

        # 构建 requests.Response 对象
        resp = requests.Response()
        resp.url = url
        if html:
            resp.status_code = 200
            resp._content = html.encode("utf-8")
            resp.encoding = "utf-8"
        else:
            resp.status_code = 503
            resp._content = b""

        return resp

    @staticmethod
    def _fetch_html_with_browser(
        url: str,
        proxy_config: Optional[ProxyConfig],
        logger: Optional[Logger],
        wait_for_content: List[str],
        reject_content: List[str],
        max_wait: int,
    ) -> Optional[str]:
        """内部方法：使用 DrissionPage 浏览器获取页面 HTML

        获取完成后自动关闭浏览器实例。

        Returns:
            页面 HTML 内容，获取失败返回 None
        """
        from DrissionPage import Chromium, ChromiumOptions

        options = ChromiumOptions()
        options.auto_port()
        # 不使用 headless 模式 - Cloudflare Turnstile 会检测无头浏览器

        # 应用代理配置
        if proxy_config and proxy_config.enabled and proxy_config.http_proxy:
            options.set_proxy(proxy_config.http_proxy)

        browser = Chromium(options)
        try:
            tab = browser.latest_tab
            if not hasattr(tab, "get"):
                if logger:
                    logger.error("无法获取浏览器标签页")
                return None
            tab.get(url)  # type: ignore[union-attr]

            # Cloudflare Turnstile 挑战需要时间解决
            tab.wait.doc_loaded()  # type: ignore[union-attr]

            # 等待期望内容出现（表示真实页面已加载）
            start_time = time.time()
            while time.time() - start_time < max_wait:
                html: str = cast(str, tab.html)  # type: ignore[union-attr]
                if not html:
                    time.sleep(1)
                    continue

                # 检查期望内容是否出现
                for marker in wait_for_content:
                    if marker in html:
                        # 还需确认不包含拒绝内容
                        has_reject = any(r in html for r in reject_content)
                        if not has_reject:
                            if logger:
                                logger.info(f"页面加载完成（检测到 {marker}）")
                            return html

                time.sleep(1)

            # 超时后检查是否获取到有意义的内容
            html = cast(str, tab.html)  # type: ignore[union-attr]
            if html:
                has_reject = any(r in html[:500] for r in reject_content)
                if not has_reject:
                    if logger:
                        logger.warning("等待内容标记超时，但页面似乎已加载")
                    return html

            if logger:
                logger.error("无法绕过 Cloudflare 保护（超时）")
            return None
        finally:
            # 获取完成后自动关闭浏览器
            try:
                browser.quit()
            except Exception:
                pass

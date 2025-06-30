import os
from typing import Dict, Optional

from ...config.logging_config import get_logger
from ...config.settings import Config
from ..base import Operator


class BaseDownloader(Operator):
    """基础下载器类"""

    def __init__(self, config: Config):
        super().__init__(config, "下载")
        self.download_config = config.download
        self.organize_config = config.organize
        self.proxy_config = config.proxy
        os.makedirs(config.download.output_dir, exist_ok=True)
        self.logger = get_logger(__name__)
        self.proxies = self.get_proxies()

    def get_proxies(self) -> Optional[Dict[str, str]]:
        """获取代理配置"""
        if not self.proxy_config.enabled:
            return None

        proxies = {}
        if self.proxy_config.http_proxy:
            proxies["http"] = self.proxy_config.http_proxy
        if self.proxy_config.https_proxy:
            proxies["https"] = self.proxy_config.https_proxy

        return proxies if proxies else None

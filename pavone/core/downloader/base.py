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
        # logger 已经在 Operator 基类中使用子类模块名初始化，这里不需要重复设置
        self.proxies = self.get_proxies()

    def get_proxies(self) -> Optional[Dict[str, str]]:
        """获取代理配置"""
        if not self.proxy_config.enabled:
            return None

        proxies: Dict[str, str] = {}
        if self.proxy_config.http_proxy:
            proxies["http"] = self.proxy_config.http_proxy
        if self.proxy_config.https_proxy:
            proxies["https"] = self.proxy_config.https_proxy

        return proxies if proxies else None

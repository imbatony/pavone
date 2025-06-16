"""
基础下载器模块
"""

import os
from abc import ABC, abstractmethod
from typing import Optional
from pavone.config.settings import DownloadConfig
from .options import DownloadOpt
from .progress import ProgressCallback


class BaseDownloader(ABC):
    """基础下载器类"""
    
    def __init__(self, config: DownloadConfig):
        self.config = config
        os.makedirs(config.output_dir, exist_ok=True)
    
    @abstractmethod
    def download(self, download_opt: DownloadOpt, 
                 progress_callback: Optional[ProgressCallback] = None) -> bool:
        """
        下载文件
        
        Args:
            download_opt: 下载选项，包含URL、文件名和自定义HTTP头部
            progress_callback: 进度回调函数，接收ProgressInfo对象
            
        Returns:
            bool: 下载是否成功
        """
        pass

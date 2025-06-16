"""
PAVOne - 一个集下载,整理等多功能的插件化的AV管理工具
"""

__version__ = "0.1.0"
__author__ = "PAVOne Team"
__description__ = "一个集下载,整理等多功能的插件化的AV管理工具"

# 导入主要模块
from . import core
from . import config
from . import plugins

# 导入常用类
from .core import FileOrganizer
from .config import DownloadConfig, OrganizeConfig

__all__ = [
    'core',
    'config', 
    'plugins',
    'FileOrganizer',
    'DownloadConfig',
    'OrganizeConfig'
]

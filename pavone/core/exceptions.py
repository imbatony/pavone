"""
PAVOne 全局异常层级体系

所有 PAVOne 应用层异常的定义。CLI 最外层统一捕获 PavoneError
以输出友好错误信息，而非原始堆栈跟踪。
"""


class PavoneError(Exception):
    """PAVOne 基础异常，所有应用层异常的根基类。"""

    def __init__(self, message: str = "") -> None:
        self.message = message
        super().__init__(message)

    def __str__(self) -> str:
        return self.message


class NetworkError(PavoneError):
    """网络请求失败（连接超时、DNS 解析、SSL 错误等）。"""


class DownloadError(PavoneError):
    """下载过程中的错误（分片失败、合并失败、空间不足等）。"""


class ExtractError(PavoneError):
    """URL/元数据提取错误（页面结构变更、正则不匹配等）。"""


class PluginError(PavoneError):
    """插件系统错误（加载失败、初始化失败、生命周期异常）。"""


class ConfigError(PavoneError):
    """配置相关错误（文件不存在、格式错误、验证失败）。"""


class MetadataError(PavoneError):
    """元数据处理错误（解析失败、字段缺失、写入失败）。"""

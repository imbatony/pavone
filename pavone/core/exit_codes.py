"""退出码常量，用于 CLI 命令的退出状态区分。"""


class ExitCode:
    """CLI 命令退出码常量。"""

    SUCCESS = 0
    GENERAL_ERROR = 1
    USAGE_ERROR = 2
    NETWORK_ERROR = 3
    CONFIG_ERROR = 4

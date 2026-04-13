"""
PAVOne CLI主入口
提供命令行方式访问PAVOne的各种功能
"""

import os
import sys

import click

from .. import __version__
from ..config.logging_config import get_log_manager
from ..core.exceptions import ConfigError, NetworkError, PavoneError
from ..core.exit_codes import ExitCode
from .commands.config import config
from .commands.download import batch_download, download

# 导入所有命令模块
from .commands.init import init
from .commands.jellyfin import jellyfin
from .commands.metadata import metadata
from .commands.organize import organize
from .commands.search import search


@click.group()
@click.option("--verbose", "-v", is_flag=True, help="Enables verbose mode.")
@click.option("--no-color", is_flag=True, help="Disable color output.")
@click.version_option(version=__version__)
@click.pass_context
def main(ctx: click.Context, verbose: bool, no_color: bool) -> None:
    """PAVOne - 一个集下载,整理等多功能的插件化的AV管理工具"""
    ctx.obj = {}
    ctx.obj["verbose"] = verbose
    # 支持 --no-color 选项和 NO_COLOR 环境变量 (https://no-color.org/)
    ctx.obj["no_color"] = no_color or os.environ.get("NO_COLOR", "") != ""
    ctx.color = not ctx.obj["no_color"]
    if verbose:
        click.echo("Verbose mode is enabled.")
        # 设置日志级别为DEBUG
        log_manager = get_log_manager()
        log_manager.set_level("DEBUG")


def cli() -> None:
    """CLI 入口点，包含统一异常捕获。"""
    try:
        main(standalone_mode=False)
    except click.exceptions.Abort:
        sys.exit(ExitCode.GENERAL_ERROR)
    except click.exceptions.UsageError as e:
        click.echo(f"用法错误: {e}", err=True)
        sys.exit(ExitCode.USAGE_ERROR)
    except NetworkError as e:
        click.echo(f"网络错误: {e}", err=True)
        sys.exit(ExitCode.NETWORK_ERROR)
    except ConfigError as e:
        click.echo(f"配置错误: {e}", err=True)
        sys.exit(ExitCode.CONFIG_ERROR)
    except PavoneError as e:
        click.echo(f"错误: {e}", err=True)
        sys.exit(ExitCode.GENERAL_ERROR)
    except Exception as e:
        click.echo(f"未预期的错误: {e}", err=True)
        sys.exit(ExitCode.GENERAL_ERROR)


# 注册所有命令
main.add_command(init)
main.add_command(download)
main.add_command(batch_download)
main.add_command(config)
main.add_command(search)
main.add_command(metadata)
main.add_command(organize)
main.add_command(jellyfin)


if __name__ == "__main__":
    main()

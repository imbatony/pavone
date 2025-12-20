"""
PAVOne CLI主入口
提供命令行方式访问PAVOne的各种功能
"""

import click

from .. import __version__
from ..config.logging_config import get_log_manager
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
@click.version_option(version=__version__)
@click.pass_context
def main(ctx: click.Context, verbose: bool) -> None:
    """PAVOne - 一个集下载,整理等多功能的插件化的AV管理工具"""
    ctx.obj = {}
    ctx.obj["verbose"] = verbose
    if verbose:
        click.echo("Verbose mode is enabled.")
        # 设置日志级别为DEBUG
        log_manager = get_log_manager()
        log_manager.set_level("DEBUG")
    pass


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

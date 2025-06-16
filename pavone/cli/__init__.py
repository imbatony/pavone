"""
PAVOne CLI主入口
提供命令行方式访问PAVOne的各种功能
"""

import click
from .. import __version__

# 导入所有命令模块
from .commands.init import init
from .commands.download import download, batch_download
from .commands.config import config
from .commands.search import search
from .commands.organize import organize


@click.group()
@click.version_option(version=__version__)
def main():
    """PAVOne - 一个集下载,整理等多功能的插件化的AV管理工具"""
    pass


# 注册所有命令
main.add_command(init)
main.add_command(download)
main.add_command(batch_download)
main.add_command(config)
main.add_command(search)
main.add_command(organize)


if __name__ == '__main__':
    main()

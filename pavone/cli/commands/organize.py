"""
Organize command - 整理命令
"""

import click

from .utils import echo_info, echo_success


@click.command()
@click.argument("path")
def organize(path: str):
    """整理指定路径下的视频文件"""
    echo_info(f"正在整理: {path}")
    # TODO: 实现整理逻辑
    echo_success("整理完成！")

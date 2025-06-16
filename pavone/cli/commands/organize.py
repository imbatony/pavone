"""
Organize command - 整理命令
"""

import click


@click.command()
@click.argument('path')
def organize(path: str):
    """整理指定路径下的视频文件"""
    click.echo(f"正在整理: {path}")
    # TODO: 实现整理逻辑
    click.echo("整理完成！")

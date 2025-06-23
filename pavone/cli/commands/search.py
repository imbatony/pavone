"""
Search command - 搜索命令
"""

import click


@click.command()
@click.argument("keyword")
def search(keyword: str):
    """根据关键词搜索视频信息"""
    click.echo(f"正在搜索: {keyword}")
    # TODO: 实现搜索逻辑
    click.echo("搜索完成！")

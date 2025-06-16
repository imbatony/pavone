"""
Config command - 配置显示命令
"""

import click
from ...config.settings import ConfigManager


@click.command()
def config():
    """显示当前配置"""
    config_manager = ConfigManager()
    config = config_manager.config
    
    click.echo("=== PAVOne 当前配置 ===")
    click.echo(f"配置文件位置: {config_manager.config_file}")
    click.echo()
    
    click.echo("=== 下载配置 ===")
    click.echo(f"下载目录: {config.download.output_dir}")
    click.echo(f"最大并发下载: {config.download.max_concurrent_downloads}")
    click.echo(f"重试次数: {config.download.retry_times}")
    click.echo(f"连接超时: {config.download.timeout}秒")
    click.echo(f"User-Agent: {config.download.user_agent}")
    
    click.echo("\n=== 代理配置 ===")
    click.echo(f"使用代理: {'是' if config.proxy.enabled else '否'}")
    if config.proxy.enabled:
        click.echo(f"HTTP代理: {config.proxy.http_proxy}")
        click.echo(f"HTTPS代理: {config.proxy.https_proxy}")
    
    click.echo("\n=== 文件整理配置 ===")
    click.echo(f"自动整理: {'是' if config.organize.auto_organize else '否'}")
    click.echo(f"整理方式: {config.organize.organize_by}")
    click.echo(f"命名模式: {config.organize.naming_pattern}")
    click.echo(f"下载封面: {'是' if config.organize.download_cover else '否'}")
    click.echo(f"生成NFO: {'是' if config.organize.create_nfo else '否'}")
    
    click.echo("\n=== 搜索配置 ===")
    click.echo(f"最大搜索结果: {config.search.max_results_per_site}")
    click.echo(f"搜索超时: {config.search.search_timeout}秒")
    click.echo(f"启用的网站: {', '.join(config.search.enabled_sites or [])}")

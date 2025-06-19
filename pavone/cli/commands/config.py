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
    click.echo(f"重试间隔: {config.download.retry_interval}毫秒")
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
    
    click.echo("\n=== 日志配置 ===")
    click.echo(f"日志级别: {config.logging.level}")
    click.echo(f"控制台输出: {'是' if config.logging.console_enabled else '否'}")
    click.echo(f"文件日志: {'是' if config.logging.file_enabled else '否'}")
    if config.logging.file_enabled:
        click.echo(f"日志文件: {config.logging.file_path}")
        click.echo(f"最大文件大小: {config.logging.max_file_size // (1024*1024)}MB")
        click.echo(f"备份文件数: {config.logging.backup_count}")
    
    click.echo("\n=== 插件配置 ===")
    click.echo(f"插件目录: {config.plugin.plugin_dir}")
    click.echo(f"插件配置目录: {config.plugin.plugin_config_dir}")
    click.echo(f"自动发现插件: {'是' if config.plugin.auto_discovery else '否'}")
    click.echo(f"插件加载超时: {config.plugin.load_timeout}秒")
    if config.plugin.disabled_plugins:
        click.echo(f"禁用的插件: {', '.join(config.plugin.disabled_plugins)}")
    else:
        click.echo("禁用的插件: 无")
    if config.plugin.plugin_priorities:
        click.echo("插件优先级:")
        for plugin, priority in config.plugin.plugin_priorities.items():
            click.echo(f"  {plugin}: {priority}")
    else:
        click.echo("插件优先级: 默认")

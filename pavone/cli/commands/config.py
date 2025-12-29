"""
Config command - 配置显示命令
"""

import click

from ...config.settings import get_config_manager
from .utils import echo_info


@click.command()
def config():
    """显示当前配置"""
    config_manager = get_config_manager()
    config = config_manager.config

    echo_info("=== PAVOne 当前配置 ===")
    echo_info(f"配置文件位置: {config_manager.config_file}")
    echo_info("")

    echo_info("=== 下载配置 ===")
    echo_info(f"下载目录: {config.download.output_dir}")
    echo_info(f"最大并发下载: {config.download.max_concurrent_downloads}")
    echo_info(f"重试次数: {config.download.retry_times}")
    echo_info(f"重试间隔: {config.download.retry_interval}毫秒")
    echo_info(f"连接超时: {config.download.timeout}秒")
    echo_info(f"自定义请求头: {config.download.headers}")
    echo_info(f"缓存目录: {config.download.cache_dir or '默认系统缓存目录'}")
    echo_info(f"自动选择下载链接: {'是' if config.download.auto_select else '否'}")

    echo_info("")
    echo_info("=== 全局代理配置 ===")
    echo_info(f"使用代理: {'是' if config.proxy.enabled else '否'}")
    if config.proxy.enabled:
        echo_info(f"全局HTTP代理: {config.proxy.http_proxy}")
        echo_info(f"全局HTTPS代理: {config.proxy.https_proxy}")

    echo_info("")
    echo_info("=== 文件整理配置 ===")
    echo_info(f"自动整理: {'是' if config.organize.auto_organize else '否'}")
    echo_info(f"文件夹结构: {config.organize.folder_structure}")
    echo_info(f"命名模式: {config.organize.naming_pattern}")
    echo_info(f"下载封面: {'是' if config.organize.download_cover else '否'}")
    echo_info(f"生成NFO: {'是' if config.organize.create_nfo else '否'}")

    echo_info("")
    echo_info("=== 搜索配置 ===")
    echo_info(f"最大搜索结果: {config.search.max_results_per_site}")
    echo_info(f"搜索超时: {config.search.search_timeout}秒")
    echo_info(f"启用的网站: {', '.join(config.search.enabled_sites or [])}")

    echo_info("")
    echo_info("=== 日志配置 ===")
    echo_info(f"日志级别: {config.logging.level}")
    echo_info(f"控制台输出: {'是' if config.logging.console_enabled else '否'}")
    echo_info(f"文件日志: {'是' if config.logging.file_enabled else '否'}")
    if config.logging.file_enabled:
        echo_info(f"日志文件: {config.logging.file_path}")
        echo_info(f"最大文件大小: {config.logging.max_file_size // (1024 * 1024)}MB")
        echo_info(f"备份文件数: {config.logging.backup_count}")

    echo_info("")
    echo_info("=== 插件配置 ===")
    echo_info(f"插件目录: {config.plugin.plugin_dir}")
    echo_info(f"插件配置目录: {config.plugin.plugin_config_dir}")
    echo_info(f"自动发现插件: {'是' if config.plugin.auto_discovery else '否'}")
    echo_info(f"插件加载超时: {config.plugin.load_timeout}秒")
    if config.plugin.disabled_plugins:
        echo_info(f"禁用的插件: {', '.join(config.plugin.disabled_plugins)}")
    else:
        echo_info("禁用的插件: 无")
    if config.plugin.plugin_priorities:
        echo_info("插件优先级:")
        for plugin, priority in config.plugin.plugin_priorities.items():
            plugin_str = str(plugin)
            priority_str = str(priority)
            echo_info(f"  {plugin_str}: {priority_str}")
    else:
        echo_info("插件优先级: 默认")

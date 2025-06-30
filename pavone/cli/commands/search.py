"""
Search command - 搜索命令
"""

import click

from ...config.settings import get_config
from ...plugins.manager import get_plugin_manager
from .utils import echo_error, echo_info, echo_success


@click.command()
@click.argument("keyword")
def search(keyword: str):
    """搜索指定关键词"""
    try:
        # 获取配置
        config = get_config()
        search_config = config.search
        plugin_config = config.plugin

        # 获取插件管理器
        plugin_manager = get_plugin_manager()
        plugin_manager.load_plugins(plugin_dir=plugin_config.plugin_dir)

        # 执行搜索
        results = plugin_manager.search(
            keyword, limit=search_config.max_results_per_site, enable_sites=search_config.enabled_sites
        )

        if not results:
            echo_info("没有找到相关结果")
            return 0

        # 显示搜索结果
        for idx, result in enumerate(results, start=1):
            echo_success(f"{idx}. {result.site} - {result.title} - {result.url}")

        return 0

    except Exception as e:
        echo_error(f"搜索失败: {e}")
        return 1

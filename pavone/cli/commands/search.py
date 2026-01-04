"""
Search command - 搜索命令
"""

import click

from ...config.settings import get_config
from ...manager import get_search_manager
from ...manager.plugin_manager import get_plugin_manager
from .utils import (
    apply_proxy_config,
    common_proxy_option,
    echo_colored,
    echo_error,
    echo_info,
    echo_success,
)


@click.command()
@click.argument("keyword")
@common_proxy_option
def search(keyword: str, proxy: str):
    """搜索指定关键词"""
    try:
        # 获取配置
        config = get_config()
        search_config = config.search
        plugin_config = config.plugin

        # 处理代理设置
        error_msg = apply_proxy_config(proxy, config)
        if error_msg:
            echo_error(error_msg)
            return 1

        # 获取插件管理器
        plugin_manager = get_plugin_manager()
        plugin_manager.load_plugins(plugin_dir=plugin_config.plugin_dir)

        # 获取搜索管理器
        search_manager = get_search_manager(plugin_manager)

        # 执行搜索（使用去重功能）
        results = search_manager.search_with_dedup(
            keyword,
            limit=search_config.max_results_per_site,
            enable_sites=search_config.enabled_sites,
        )

        if not results:
            echo_info("没有找到相关结果")
            return 0

        # 显示搜索结果总数
        echo_success(f"\n找到 {len(results)} 个搜索结果:\n")

        # 显示搜索结果
        for idx, result in enumerate(results, start=1):
            # 站点标签 - 使用不同颜色
            if result.site == "Jellyfin":
                site_label = click.style(f"[{result.site}]", fg="cyan", bold=True)
            elif result.site == "MissAV":
                site_label = click.style(f"[{result.site}]", fg="magenta", bold=True)
            elif result.site == "PPVDataBank":
                site_label = click.style(f"[{result.site}]", fg="yellow", bold=True)
            else:
                site_label = click.style(f"[{result.site}]", fg="blue", bold=True)
            
            # 编号
            number = click.style(f"{idx}.", fg="green", bold=True)
            
            # 标题 - 截断过长的标题
            max_title_length = 80
            display_title = result.title
            if len(display_title) > max_title_length:
                display_title = display_title[:max_title_length] + "..."
            
            # 番号信息
            code_info = ""
            if result.code:
                code_info = click.style(f" [{result.code}]", fg="white", bold=True)
            
            # 输出主要信息
            print(f"{number} {site_label}{code_info}")
            print(f"   {display_title}")
            
            # URL - 使用灰色显示
            url_display = result.url
            if len(url_display) > 100:
                url_display = url_display[:97] + "..."
            print(click.style(f"   {url_display}", fg="bright_black"))
            
            # 添加空行分隔
            if idx < len(results):
                print()

        return 0

    except Exception as e:
        echo_error(f"搜索失败: {e}")
        return 1

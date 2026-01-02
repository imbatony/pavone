"""
Download commands - 下载相关命令
"""

from typing import Optional

import click

from ...config.settings import get_config
from ...manager.execution import create_exe_manager
from ...manager.plugin_manager import get_plugin_manager
from .utils import (
    apply_proxy_config,
    common_download_options,
    common_interaction_options,
    common_network_options,
    common_output_options,
    echo_error,
    echo_info,
    echo_success,
    parse_headers,
    read_urls_from_file,
    read_urls_from_input,
)


@click.command()
@click.argument("url")
@common_interaction_options
@click.option("--filename", "-f", type=str, help="指定输出文件名")
@common_output_options
@common_network_options
@common_download_options
def download(
    url: str,
    auto_select: bool,
    silent: bool,
    filename: Optional[str],
    output_dir: Optional[str],
    header: tuple[str, str],
    proxy: Optional[str],
    organize: bool,
    threads: Optional[int],
    retry: Optional[int],
    timeout: Optional[int],
):
    """下载指定URL的视频"""
    try:
        # 获取配置
        config = get_config()
        download_config = config.download
        organize_config = config.organize

        # 应用命令行选项覆盖配置
        if output_dir:
            download_config.output_dir = output_dir
        if threads:
            download_config.max_concurrent_downloads = threads
        if retry is not None:
            download_config.retry_times = retry
        if timeout:
            download_config.timeout = timeout
        if organize:
            organize_config.auto_organize = True

        # 检测文件名,指定文件名不能过长，并且不能包含非法字符
        if filename:
            if len(filename) > 255:
                echo_error("文件名不能超过255个字符")
                return 1
            if any(c in filename for c in r'<>:"/\|?*'):
                echo_error('文件名包含非法字符: <>:"/\\|?*')
                return 1

        # 处理代理设置
        error_msg = apply_proxy_config(proxy, config)
        if error_msg:
            echo_error(error_msg)
            return 1

        # 处理自定义HTTP头部
        custom_headers, error_msg = parse_headers(header)
        if error_msg:
            echo_error(error_msg)
            return 1

        # 创建插件管理器和下载管理器
        plugin_manager = get_plugin_manager()
        exe_manager = create_exe_manager(config=config, plugin_manager=plugin_manager)
        echo_info(f"正在下载: {url}")
        if filename:
            echo_info(f"输出文件名: {filename}")
        if output_dir:
            echo_info(f"输出目录: {output_dir}")
        if custom_headers:
            echo_info(f"自定义头部: {len(custom_headers)} 个")

        # 执行下载
        success = exe_manager.download_from_url(url=url, silent=silent, auto_select=auto_select, file_name=filename or None)

        if success:
            echo_success("下载完成！")
        else:
            echo_error("下载失败！")
            return 1

    except Exception as e:
        echo_error(f"下载出错: {e}")
        return 1


@click.command()
@click.option("--file", "-f", type=click.Path(exists=True), help="从文件读取URL列表")
@common_interaction_options
@common_output_options
@common_network_options
@common_download_options
def batch_download(
    file: Optional[str],
    auto_select: bool,
    silent: bool,
    output_dir: Optional[str],
    header: tuple[str, str],
    proxy: Optional[str],
    organize: bool,
    threads: Optional[int],
    retry: Optional[int],
    timeout: Optional[int],
):
    """批量下载多个URL"""
    try:
        # 获取配置
        config = get_config()
        download_config = config.download

        # 应用命令行选项覆盖配置
        if output_dir:
            download_config.output_dir = output_dir
        if threads:
            download_config.max_concurrent_downloads = threads
        if retry is not None:
            download_config.retry_times = retry
        if timeout:
            download_config.timeout = timeout

        # 处理代理设置
        error_msg = apply_proxy_config(proxy, config)
        if error_msg:
            echo_error(error_msg)
            return 1

        # 处理自定义HTTP头部
        custom_headers, error_msg = parse_headers(header)
        if error_msg:
            echo_error(error_msg)
            return 1

        # 读取URL列表
        urls = []
        if file:
            urls = read_urls_from_file(file)
        else:
            urls = read_urls_from_input()

        if not urls:
            echo_error("没有找到有效的URL")
            return 1

        # 创建插件管理器和下载管理器
        plugin_manager = get_plugin_manager()
        exe_manager = create_exe_manager(config=config, plugin_manager=plugin_manager)

        echo_info(f"开始批量下载 {len(urls)} 个URL...")
        if output_dir:
            echo_info(f"输出目录: {output_dir}")
        if custom_headers:
            echo_info(f"自定义头部: {len(custom_headers)} 个")

        # 执行批量下载
        results = exe_manager.batch_download(urls, silent)

        # 显示结果摘要
        successful = sum(1 for _, success in results if success)
        failed = len(results) - successful

        echo_info("批量下载完成:")
        echo_success(f"成功: {successful}")
        if failed > 0:
            echo_error(f"失败: {failed}")

        if failed > 0:
            click.echo("\n失败的URL:")
            for url, success in results:
                if not success:
                    click.echo(f"  - {url}")
            return 1

    except Exception as e:
        echo_error(f"批量下载出错: {e}")
        return 1

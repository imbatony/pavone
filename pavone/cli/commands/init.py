"""
Init command - 初始化PAVOne配置
"""

import click

from ...config.settings import ConfigManager, get_config_manager
from .utils import confirm_action, prompt_choice, prompt_int_range


@click.command()
@click.option("--force", is_flag=True, help="强制重新初始化，覆盖现有配置")
@click.option("--interactive/--no-interactive", "-i", default=True, help="交互式配置（默认）")
def init(force, interactive):
    """初始化PAVOne配置"""
    click.echo("欢迎使用PAVOne！")

    # 创建配置管理器
    config_manager = get_config_manager()
    # 检查是否已存在配置
    if config_manager.config_file.exists() and not force:
        if confirm_action("配置文件已存在，是否重新配置？"):
            config_manager.reset_config()
        else:
            click.echo("使用现有配置。")
            return

    if interactive:
        _interactive_config_setup(config_manager)
    else:
        # 使用默认配置
        config_manager.save_config()

    click.echo(f"配置文件已保存到: {config_manager.config_file}")
    click.echo("配置初始化完成！")

    # 显示配置摘要
    _show_config_summary(config_manager)


def _interactive_config_setup(config_manager: ConfigManager):
    """交互式配置设置"""
    click.echo("\n=== 下载配置 ===")

    # 下载目录配置
    default_output = config_manager.config.download.output_dir
    output_dir = click.prompt("下载目录", default=default_output, type=str)
    config_manager.config.download.output_dir = output_dir
    # 并发下载数配置
    max_concurrent = prompt_int_range(
        "最大并发下载数", min_val=1, max_val=10, default=config_manager.config.download.max_concurrent_downloads
    )
    config_manager.config.download.max_concurrent_downloads = max_concurrent
    # 重试次数配置
    retry_times = prompt_int_range(
        "下载失败重试次数", min_val=0, max_val=10, default=config_manager.config.download.retry_times
    )
    config_manager.config.download.retry_times = retry_times

    # 重试间隔配置
    retry_interval = prompt_int_range(
        "重试间隔（毫秒）", min_val=500, max_val=10000, default=config_manager.config.download.retry_interval
    )
    config_manager.config.download.retry_interval = retry_interval

    # 超时时间配置
    timeout = prompt_int_range("下载超时时间（秒）", min_val=10, max_val=300, default=config_manager.config.download.timeout)
    config_manager.config.download.timeout = timeout
    # 自定义User-Agent配置
    user_agent = click.prompt(
        "自定义User-Agent (留空使用默认)", default=config_manager.config.download.headers.get("User-Agent", ""), type=str
    )
    if user_agent:
        config_manager.config.download.headers["User-Agent"] = user_agent
    # 是否自动选择下载链接
    auto_select = confirm_action("是否自动选择下载链接？", default=config_manager.config.download.auto_select)
    config_manager.config.download.auto_select = auto_select

    # 缓存目录配置
    cache_dir = click.prompt(
        "缓存目录 (留空使用默认系统缓存目录)", default=config_manager.config.download.cache_dir or "", type=str
    )
    config_manager.config.download.cache_dir = cache_dir or None
    # 是否覆盖已存在的文件
    overwrite_existing = confirm_action("是否覆盖已存在的文件？", default=config_manager.config.download.overwrite_existing)
    config_manager.config.download.overwrite_existing = overwrite_existing

    click.echo("\n=== 代理配置 ===")
    use_proxy = confirm_action("是否使用代理？", default=False)
    config_manager.config.proxy.enabled = use_proxy

    if use_proxy:
        http_proxy = click.prompt("HTTP代理地址 (例: http://127.0.0.1:7890)", default="", type=str)
        https_proxy = click.prompt("HTTPS代理地址 (例: http://127.0.0.1:7890)", default="", type=str)
        config_manager.config.proxy.http_proxy = http_proxy
        config_manager.config.proxy.https_proxy = https_proxy
    # 整理配置
    click.echo("\n=== 文件整理配置 ===")
    auto_organize = confirm_action("是否自动整理下载的文件？", default=True)
    config_manager.config.organize.auto_organize = auto_organize

    if auto_organize:
        # 命名模式配置
        naming_pattern = click.prompt(
            "文件命名模式 (例如: {code} 或 {code} - {title})", default=config_manager.config.organize.naming_pattern, type=str
        )
        config_manager.config.organize.naming_pattern = naming_pattern
        # 文件夹结构配置
        folder_structure = click.prompt(
            "文件夹结构 (例如: {code} 或 {studio})", default=config_manager.config.organize.folder_structure, type=str
        )
        config_manager.config.organize.folder_structure = folder_structure
        download_cover = confirm_action("是否下载封面图？", default=True)
        config_manager.config.organize.download_cover = download_cover
        create_nfo = confirm_action("是否生成NFO文件？", default=True)
        config_manager.config.organize.create_nfo = create_nfo
    # 搜索配置
    click.echo("\n=== 搜索配置 ===")
    max_results = prompt_int_range(
        "每个网站最大搜索结果数", min_val=5, max_val=100, default=config_manager.config.search.max_results_per_site
    )
    config_manager.config.search.max_results_per_site = max_results

    # 搜索超时配置
    search_timeout = prompt_int_range(
        "搜索超时时间（秒）", min_val=5, max_val=60, default=config_manager.config.search.search_timeout
    )
    config_manager.config.search.search_timeout = search_timeout

    # 日志配置
    click.echo("\n=== 日志配置 ===")

    # 日志级别配置
    log_level_choices = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
    log_level = prompt_choice("日志级别", choices=log_level_choices, default=config_manager.config.logging.level)
    config_manager.config.logging.level = log_level

    # 是否启用控制台日志
    console_enabled = confirm_action("是否启用控制台日志？", default=config_manager.config.logging.console_enabled)
    config_manager.config.logging.console_enabled = console_enabled

    # 是否启用文件日志
    file_enabled = confirm_action("是否启用文件日志？", default=config_manager.config.logging.file_enabled)
    config_manager.config.logging.file_enabled = file_enabled

    if file_enabled:
        # 日志文件路径
        default_file_path = config_manager.config.logging.file_path
        file_path = click.prompt("日志文件路径", default=default_file_path, type=str)
        config_manager.config.logging.file_path = file_path

        # 日志文件最大大小（MB）
        max_file_size_mb = prompt_int_range(
            "日志文件最大大小（MB）",
            min_val=1,
            max_val=100,
            default=config_manager.config.logging.max_file_size // (1024 * 1024),
        )
        config_manager.config.logging.max_file_size = max_file_size_mb * 1024 * 1024

        # 备份文件数量
        backup_count = prompt_int_range(
            "日志备份文件数量", min_val=1, max_val=10, default=config_manager.config.logging.backup_count
        )
        config_manager.config.logging.backup_count = backup_count

    # 保存配置
    config_manager.save_config()


def _show_config_summary(config_manager: ConfigManager):
    """显示配置摘要"""
    config = config_manager.config

    click.echo("\n=== 配置摘要 ===")
    click.echo(f"下载目录: {config.download.output_dir}")
    click.echo(f"最大并发下载: {config.download.max_concurrent_downloads}")
    click.echo(f"重试次数: {config.download.retry_times}")
    click.echo(f"重试间隔: {config.download.retry_interval}ms")
    click.echo(f"下载超时: {config.download.timeout}s")
    click.echo(f"使用代理: {'是' if config.proxy.enabled else '否'}")
    if config.download.headers.get("User-Agent"):
        click.echo(f"自定义User-Agent: {config.download.headers['User-Agent']}")
    else:
        click.echo("自定义User-Agent: 使用默认")
    click.echo(f"缓存目录: {config.download.cache_dir or '默认系统缓存目录'}")
    click.echo(f"自动选择下载链接: {'是' if config.download.auto_select else '否'}")
    if config.proxy.enabled:
        click.echo(f"  HTTP代理: {config.proxy.http_proxy}")
        click.echo(f"  HTTPS代理: {config.proxy.https_proxy}")
    click.echo(f"自动整理: {'是' if config.organize.auto_organize else '否'}")
    if config.organize.auto_organize:
        click.echo(f"  文件夹结构: {config.organize.folder_structure}")
        click.echo(f"  命名模式: {config.organize.naming_pattern}")
        click.echo(f"  下载封面: {'是' if config.organize.download_cover else '否'}")
        click.echo(f"  生成NFO: {'是' if config.organize.create_nfo else '否'}")
    click.echo(f"最大搜索结果: {config.search.max_results_per_site}")
    click.echo(f"搜索超时: {config.search.search_timeout}s")
    click.echo(f"日志级别: {config.logging.level}")
    click.echo(f"控制台日志: {'是' if config.logging.console_enabled else '否'}")
    click.echo(f"文件日志: {'是' if config.logging.file_enabled else '否'}")
    if config.logging.file_enabled:
        file_size_mb = config.logging.max_file_size // (1024 * 1024)
        click.echo(f"  日志文件: {config.logging.file_path}")
        click.echo(f"  最大大小: {file_size_mb}MB")
        click.echo(f"  备份数量: {config.logging.backup_count}")
    click.echo()
    click.echo("提示: 你可以随时编辑配置文件或重新运行 'pavone init' 来修改设置。")

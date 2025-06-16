"""
Init command - 初始化PAVOne配置
"""

import click
from ...config.settings import ConfigManager
from ..utils import confirm_action, prompt_choice, prompt_int_range


@click.command()
@click.option('--force', is_flag=True, help='强制重新初始化，覆盖现有配置')
@click.option('--interactive/--no-interactive', '-i', default=True, help='交互式配置（默认）')
def init(force, interactive):
    """初始化PAVOne配置"""
    click.echo("欢迎使用PAVOne！")
    
    # 创建配置管理器
    config_manager = ConfigManager()
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
        "最大并发下载数", 
        min_val=1,
        max_val=10,
        default=config_manager.config.download.max_concurrent_downloads
    )
    config_manager.config.download.max_concurrent_downloads = max_concurrent
    
    # 重试次数配置
    retry_times = prompt_int_range(
        "下载失败重试次数",
        min_val=0,
        max_val=10,
        default=config_manager.config.download.retry_times
    )
    config_manager.config.download.retry_times = retry_times
      # 代理配置
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
        organize_choices = ['studio', 'genre', 'actor']
        organize_by = prompt_choice(
            "按什么方式整理文件",
            choices=organize_choices,
            default='studio'
        )
        config_manager.config.organize.organize_by = organize_by
        
        download_cover = confirm_action("是否下载封面图？", default=True)
        config_manager.config.organize.download_cover = download_cover
        
        create_nfo = confirm_action("是否生成NFO文件？", default=True)
        config_manager.config.organize.create_nfo = create_nfo
      # 搜索配置
    click.echo("\n=== 搜索配置 ===")
    max_results = prompt_int_range(
        "每个网站最大搜索结果数",
        min_val=5,
        max_val=100,
        default=config_manager.config.search.max_results_per_site
    )
    config_manager.config.search.max_results_per_site = max_results
    
    # 保存配置
    config_manager.save_config()


def _show_config_summary(config_manager: ConfigManager):
    """显示配置摘要"""
    config = config_manager.config
    
    click.echo("\n=== 配置摘要 ===")
    click.echo(f"下载目录: {config.download.output_dir}")
    click.echo(f"最大并发下载: {config.download.max_concurrent_downloads}")
    click.echo(f"重试次数: {config.download.retry_times}")
    click.echo(f"使用代理: {'是' if config.proxy.enabled else '否'}")
    if config.proxy.enabled:
        click.echo(f"  HTTP代理: {config.proxy.http_proxy}")
        click.echo(f"  HTTPS代理: {config.proxy.https_proxy}")
    click.echo(f"自动整理: {'是' if config.organize.auto_organize else '否'}")
    if config.organize.auto_organize:
        click.echo(f"  整理方式: {config.organize.organize_by}")
        click.echo(f"  下载封面: {'是' if config.organize.download_cover else '否'}")
        click.echo(f"  生成NFO: {'是' if config.organize.create_nfo else '否'}")
    click.echo(f"最大搜索结果: {config.search.max_results_per_site}")
    click.echo()
    click.echo("提示: 你可以随时编辑配置文件或重新运行 'pavone init' 来修改设置。")

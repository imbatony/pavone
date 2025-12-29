"""
CLI Utilities - 共享的辅助函数
"""

import functools
from typing import List, Optional

import click


def common_proxy_option(func):
    """添加通用的 proxy 选项装饰器"""

    @click.option("--proxy", type=str, help="HTTP代理地址 (格式: http://proxy:port)")
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        return func(*args, **kwargs)

    return wrapper


def common_header_option(func):
    """添加通用的 header 选项装饰器"""

    @click.option("--header", multiple=True, help='自定义HTTP头部 (可多次使用, 格式: "Key: Value")')
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        return func(*args, **kwargs)

    return wrapper


def apply_proxy_config(proxy: Optional[str], config):
    """应用代理配置

    Args:
        proxy: 代理地址
        config: 配置对象

    Returns:
        成功返回 None，失败返回错误消息字符串
    """
    if not proxy:
        return None

    # 检查代理格式
    if not proxy.startswith("http://") and not proxy.startswith("https://"):
        return "代理地址格式错误，应为 http://proxy:port 或 https://proxy:port"

    echo_info(f"使用代理: {proxy}")

    # 设置下载配置中的代理
    proxy_config = config.proxy
    proxy_config.enabled = True
    if proxy.startswith("http://"):
        proxy_config.http_proxy = proxy
    elif proxy.startswith("https://"):
        proxy_config.https_proxy = proxy
    else:
        return "不支持的代理协议，请使用 http:// 或 https://"

    return None


def parse_headers(header: tuple[str, ...]) -> tuple[Optional[dict[str, str]], Optional[str]]:
    """解析自定义HTTP头部

    Args:
        header: 头部元组，格式为 ("Key: Value", ...)

    Returns:
        成功返回 (headers_dict, None)，失败返回 (None, error_message)
    """
    if not header:
        return {}, None

    custom_headers: dict[str, str] = {}
    for h in header:
        if ":" in h:
            key, value = h.split(":", 1)
            custom_headers[key.strip()] = value.strip()
        else:
            return None, f"无效的头部格式: {h} (应为 'Key: Value')"

    return custom_headers, None


def confirm_action(message: str, default: bool = False) -> bool:
    """确认用户操作"""
    return click.confirm(message, default=default)


def echo_success(message: str) -> None:
    """显示成功消息"""
    click.echo(f"[OK] {message}")


def echo_error(message: str) -> None:
    """显示错误消息"""
    click.echo(f"[ERROR] {message}")


def echo_warning(message: str) -> None:
    """显示警告消息"""
    click.echo(f"[WARNING] {message}")


def echo_info(message: str) -> None:
    """显示信息消息"""
    click.echo(f"[INFO] {message}")


def echo_colored(
    message: str, fg: Optional[str] = None, bg: Optional[str] = None, bold: bool = False, nl: bool = True
) -> None:
    """显示彩色消息

    Args:
        message: 消息内容
        fg: 前景色 ('black', 'red', 'green', 'yellow', 'blue', 'magenta', 'cyan', 'white', 'bright_black', 'bright_red', etc.)
        bg: 背景色
        bold: 是否加粗
        nl: 是否换行
    """
    click.secho(message, fg=fg, bg=bg, bold=bold, nl=nl)


def echo_success_inline(message: str) -> None:
    """显示成功消息（彩色，内联）- 用于特殊格式化"""
    echo_colored(message, fg="green", bold=True)


def echo_inline(message: str) -> None:
    """显示内联消息（不换行）"""
    click.echo(message, nl=False)


def prompt_choice(message: str, choices: List[str], default: Optional[str] = None) -> str:
    """提示用户选择"""
    return click.prompt(message, type=click.Choice(choices), default=default)


def prompt_int_range(message: str, min_val: int, max_val: int, default: Optional[int] = None) -> int:
    """提示用户输入整数范围"""
    return click.prompt(message, type=click.IntRange(min_val, max_val), default=default)


def prompt_text(message: str, default: Optional[str] = None, type=str) -> str:
    """提示用户输入文本"""
    return click.prompt(message, default=default, type=type)


def prompt_int(message: str, default: Optional[int] = None) -> int:
    """提示用户输入整数"""
    return click.prompt(message, type=int, default=default)


def read_urls_from_file(file_path: str) -> List[str]:
    """从文件读取URL列表"""
    urls = []
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#"):
                    urls.append(line)
    except Exception as e:
        echo_error(f"读取文件失败: {e}")
    return urls


def read_urls_from_input() -> List[str]:
    """从用户输入读取URL列表"""
    urls = []
    echo_info("请输入URL列表，每行一个URL，输入空行结束:")
    while True:
        try:
            line = click.prompt("", prompt_suffix="", default="", show_default=False)
            if not line:
                break
            urls.append(line.strip())
        except click.Abort:
            break
    return urls

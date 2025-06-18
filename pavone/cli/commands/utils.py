"""
CLI Utilities - 共享的辅助函数
"""

import click
from typing import List, Optional


def confirm_action(message: str, default: bool = False) -> bool:
    """确认用户操作"""
    return click.confirm(message, default=default)


def echo_success(message: str):
    """显示成功消息"""
    click.echo(f"✅  {message}")


def echo_error(message: str):
    """显示错误消息"""
    click.echo(f"❌  {message}")


def echo_warning(message: str):
    """显示警告消息"""
    click.echo(f"⚠️  {message}")


def echo_info(message: str):
    """显示信息消息"""
    click.echo(f"ℹ️  {message}")


def prompt_choice(message: str, choices: List[str], default: Optional[str] = None) -> str:
    """提示用户选择"""
    return click.prompt(
        message,
        type=click.Choice(choices),
        default=default
    )


def prompt_int_range(message: str, min_val: int, max_val: int, default: Optional[int] = None) -> int:
    """提示用户输入整数范围"""
    return click.prompt(
        message,
        type=click.IntRange(min_val, max_val),
        default=default
    )


def read_urls_from_file(file_path: str) -> List[str]:
    """从文件读取URL列表"""
    urls = []
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#'):
                    urls.append(line)
    except Exception as e:
        echo_error(f"读取文件失败: {e}")
    return urls


def read_urls_from_input() -> List[str]:
    """从用户输入读取URL列表"""
    urls = []
    click.echo("请输入URL列表，每行一个URL，输入空行结束:")
    while True:
        line = input().strip()
        if not line:
            break
        urls.append(line)
    return urls

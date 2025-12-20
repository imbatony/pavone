from typing import TYPE_CHECKING, Any, Optional

if TYPE_CHECKING:
    from rich.progress import TaskID

try:
    from rich.progress import (
        BarColumn,
        DownloadColumn,
        Progress,
        TextColumn,
        TimeRemainingColumn,
        TransferSpeedColumn,
    )
    _HAS_RICH = True  # type: ignore
except ImportError:
    _HAS_RICH = False  # type: ignore

from ..models import ProgressCallback, ProgressInfo


def format_bytes(bytes_value: int) -> str:
    """格式化字节大小为可读字符串"""
    size = float(bytes_value)
    for unit in ["B", "KB", "MB", "GB"]:
        if size < 1024.0:
            return f"{size:.1f} {unit}"
        size /= 1024.0
    return f"{size:.1f} TB"


def create_console_progress_callback() -> ProgressCallback:
    """创建控制台进度显示回调函数（优先使用Rich库，回退到简单模式）"""
    if _HAS_RICH:
        return _create_rich_progress_callback()
    else:
        return _create_simple_progress_callback()


def _create_rich_progress_callback() -> ProgressCallback:
    """使用Rich库创建进度条（功能丰富，界面美观）"""
    # 创建Rich进度条，配置下载专用的列
    progress = Progress(  # type: ignore
        TextColumn("[bold blue]{task.description}", justify="right"),  # type: ignore
        BarColumn(bar_width=None),  # type: ignore
        "[progress.percentage]{task.percentage:>3.1f}%",
        "•",
        DownloadColumn(),  # type: ignore
        "•",
        TransferSpeedColumn(),  # type: ignore
        "•",
        TimeRemainingColumn(),  # type: ignore
    )
    
    task_id: Optional[Any] = None
    progress.start()

    def progress_callback(progress_info: ProgressInfo):
        nonlocal task_id
        
        # 如果有状态消息，显示在进度条上方
        if progress_info.status_message:
            progress.console.print(f"[yellow]ℹ️  {progress_info.status_message}[/yellow]")
        
        # 首次调用时创建任务
        if task_id is None:
            if progress_info.total_size > 0:
                task_id = progress.add_task(
                    "下载中",
                    total=progress_info.total_size,
                )
            else:
                # 总大小未知时，使用不确定的进度条
                task_id = progress.add_task(
                    "下载中",
                    total=None,
                )
        
        # 更新进度
        if task_id is not None:
            if progress_info.total_size > 0:
                # 已知总大小
                progress.update(
                    task_id,
                    completed=progress_info.downloaded,
                    total=progress_info.total_size,
                )
            else:
                # 未知总大小，只更新已下载量
                progress.update(
                    task_id,
                    completed=progress_info.downloaded,
                )
        
            # 如果下载完成，停止进度条
            if progress_info.total_size > 0 and progress_info.downloaded >= progress_info.total_size:
                progress.stop()

    # 返回带清理功能的回调
    progress_callback._progress = progress  # type: ignore
    return progress_callback


def _create_simple_progress_callback() -> ProgressCallback:
    """创建简单的进度显示（Rich不可用时的后备方案）"""
    last_status_message = ""

    def progress_callback(progress_info: ProgressInfo):
        nonlocal last_status_message
        
        # 如果有新的状态消息，显示在新行
        if progress_info.status_message and progress_info.status_message != last_status_message:
            print(f"\nℹ️  {progress_info.status_message}")
            last_status_message = progress_info.status_message
        
        if progress_info.total_size > 0:
            bar_length = 50
            filled_length = int(bar_length * progress_info.downloaded / progress_info.total_size)
            bar = "█" * filled_length + "-" * (bar_length - filled_length)

            total_str = format_bytes(progress_info.total_size)
            downloaded_str = format_bytes(progress_info.downloaded)
            speed_str = format_bytes(int(progress_info.speed)) + "/s"

            print(
                f"\r[{bar}] {progress_info.percentage:.1f}% " 
                f"({downloaded_str}/{total_str}) " 
                f"Speed: {speed_str}",
                end="",
                flush=True,
            )

            if progress_info.downloaded >= progress_info.total_size:
                print()  # 换行
        else:
            # 无法确定总大小时的简单显示
            downloaded_str = format_bytes(progress_info.downloaded)
            speed_str = format_bytes(int(progress_info.speed)) + "/s"
            print(f"\r下载中... {downloaded_str} Speed: {speed_str}", end="", flush=True)

    return progress_callback


def create_silent_progress_callback() -> ProgressCallback:
    """创建静默进度回调函数（仅记录，不显示）"""

    def progress_callback(progress: ProgressInfo):
        # 可以在这里添加日志记录等功能
        pass

    return progress_callback


def create_status_only_progress(status_message: str) -> ProgressInfo:
    """
    创建仅包含状态消息的ProgressInfo对象
    
    这是一个便捷函数，用于在不需要更新下载进度时只显示状态消息
    
    Args:
        status_message: 要显示的状态消息
        
    Returns:
        ProgressInfo: 包含状态消息的进度信息对象
        
    Example:
        >>> progress_callback(create_status_only_progress("正在合并视频..."))
    """
    return ProgressInfo(
        total_size=0,
        downloaded=0,
        speed=0.0,
        status_message=status_message
    )


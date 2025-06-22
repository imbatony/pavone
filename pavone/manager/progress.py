from ..models import ProgressCallback, ProgressInfo


def format_bytes(bytes_value: int) -> str:
    """格式化字节大小为可读字符串"""
    size = float(bytes_value)
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size < 1024.0:
            return f"{size:.1f} {unit}"
        size /= 1024.0
    return f"{size:.1f} TB"


def create_console_progress_callback() -> ProgressCallback:
    """创建控制台进度显示回调函数"""
    def progress_callback(progress: ProgressInfo):
        if progress.total_size > 0:
            bar_length = 50
            filled_length = int(bar_length * progress.downloaded / progress.total_size)
            bar = '█' * filled_length + '-' * (bar_length - filled_length)
            
            total_str = format_bytes(progress.total_size)
            downloaded_str = format_bytes(progress.downloaded)
            speed_str = format_bytes(int(progress.speed)) + "/s"
            
            print(f'\r[{bar}] {progress.percentage:.1f}% '
                  f'({downloaded_str}/{total_str}) '
                  f'Speed: {speed_str}', end='', flush=True)
            
            if progress.downloaded >= progress.total_size:
                print()  # 换行
        else:
            # 无法确定总大小时的简单显示
            downloaded_str = format_bytes(progress.downloaded)
            speed_str = format_bytes(int(progress.speed)) + "/s"
            print(f'\r下载中... {downloaded_str} Speed: {speed_str}', end='', flush=True)
    
    return progress_callback


def create_silent_progress_callback() -> ProgressCallback:
    """创建静默进度回调函数（仅记录，不显示）"""
    def progress_callback(progress: ProgressInfo):
        # 可以在这里添加日志记录等功能
        pass
    
    return progress_callback

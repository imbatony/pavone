"""
全局中断管理模块

提供基于 threading.Event 的全局中断标志, 在收到 SIGINT/SIGTERM 信号后
设置中断标志, 供所有下载线程检查并优雅退出.
"""

import signal
import sys
import threading
from types import FrameType
from typing import Any, Optional, Union

# signal.getsignal 返回类型
_SignalHandler = Union[signal.Handlers, Any]


class InterruptHandler:
    """全局中断处理器, 管理 SIGINT/SIGTERM 信号和中断标志."""

    _instance: Optional["InterruptHandler"] = None
    _lock = threading.Lock()

    def __init__(self) -> None:
        self._event = threading.Event()
        self._original_sigint: _SignalHandler = None
        self._original_sigterm: _SignalHandler = None
        self._registered = False

    @classmethod
    def get_instance(cls) -> "InterruptHandler":
        """获取全局单例实例."""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = cls()
        return cls._instance

    def register(self) -> None:
        """注册 SIGINT/SIGTERM 信号处理器.

        仅在主线程中调用. 重复调用是安全的 (幂等).
        """
        if self._registered:
            return

        if threading.current_thread() is not threading.main_thread():
            return

        self._original_sigint = signal.getsignal(signal.SIGINT)
        signal.signal(signal.SIGINT, self._handle_signal)

        # Windows 不支持 SIGTERM 的自定义处理
        if sys.platform != "win32":
            self._original_sigterm = signal.getsignal(signal.SIGTERM)
            signal.signal(signal.SIGTERM, self._handle_signal)

        self._registered = True

    def _handle_signal(self, signum: int, frame: Optional[FrameType]) -> None:
        """信号处理回调, 设置中断标志."""
        self._event.set()

    def is_interrupted(self) -> bool:
        """检查是否已收到中断信号. 线程安全, 可多次调用 (幂等)."""
        return self._event.is_set()

    def reset(self) -> None:
        """重置中断标志并恢复原始信号处理器."""
        self._event.clear()

        if self._registered:
            if threading.current_thread() is threading.main_thread():
                if self._original_sigint is not None:
                    signal.signal(signal.SIGINT, self._original_sigint)
                    self._original_sigint = None
                if sys.platform != "win32" and self._original_sigterm is not None:
                    signal.signal(signal.SIGTERM, self._original_sigterm)
                    self._original_sigterm = None
            self._registered = False


def get_interrupt_handler() -> InterruptHandler:
    """获取全局 InterruptHandler 单例的便捷函数."""
    return InterruptHandler.get_instance()

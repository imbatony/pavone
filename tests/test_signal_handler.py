"""InterruptHandler 单元测试"""

import signal
import threading
import unittest

from pavone.utils.signal_handler import InterruptHandler, get_interrupt_handler


class TestInterruptHandler(unittest.TestCase):
    """InterruptHandler 基础功能测试"""

    def setUp(self) -> None:
        # 每个测试使用独立实例, 避免单例污染
        self.handler = InterruptHandler()

    def tearDown(self) -> None:
        self.handler.reset()

    def test_initial_state_not_interrupted(self) -> None:
        """初始状态应为未中断"""
        self.assertFalse(self.handler.is_interrupted())

    def test_is_interrupted_idempotent(self) -> None:
        """多次调用 is_interrupted() 应返回相同结果"""
        self.assertFalse(self.handler.is_interrupted())
        self.assertFalse(self.handler.is_interrupted())
        self.assertFalse(self.handler.is_interrupted())

    def test_event_set_makes_interrupted_true(self) -> None:
        """手动设置 event 后 is_interrupted() 应为 True"""
        self.handler._event.set()
        self.assertTrue(self.handler.is_interrupted())
        # 多次调用仍为 True (幂等)
        self.assertTrue(self.handler.is_interrupted())

    def test_reset_clears_interrupted(self) -> None:
        """reset() 应清除中断标志"""
        self.handler._event.set()
        self.assertTrue(self.handler.is_interrupted())
        self.handler.reset()
        self.assertFalse(self.handler.is_interrupted())

    def test_register_sets_registered_flag(self) -> None:
        """register() 应设置 _registered 标志"""
        self.assertFalse(self.handler._registered)
        self.handler.register()
        self.assertTrue(self.handler._registered)
        self.handler.reset()
        self.assertFalse(self.handler._registered)

    def test_register_idempotent(self) -> None:
        """多次调用 register() 应为幂等"""
        self.handler.register()
        self.handler.register()
        self.assertTrue(self.handler._registered)

    def test_handle_signal_sets_event(self) -> None:
        """_handle_signal 应设置中断标志"""
        self.handler._handle_signal(signal.SIGINT, None)
        self.assertTrue(self.handler.is_interrupted())

    def test_thread_safety_is_interrupted(self) -> None:
        """is_interrupted() 应在多线程中安全调用"""
        results: list[bool] = []

        def check_interrupted() -> None:
            results.append(self.handler.is_interrupted())

        self.handler._event.set()
        threads = [threading.Thread(target=check_interrupted) for _ in range(10)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        self.assertEqual(len(results), 10)
        self.assertTrue(all(results))


class TestGetInterruptHandler(unittest.TestCase):
    """get_interrupt_handler() 便捷函数测试"""

    def test_returns_singleton(self) -> None:
        """应返回相同的单例实例"""
        h1 = get_interrupt_handler()
        h2 = get_interrupt_handler()
        self.assertIs(h1, h2)

    def test_returns_interrupt_handler_instance(self) -> None:
        """应返回 InterruptHandler 实例"""
        handler = get_interrupt_handler()
        self.assertIsInstance(handler, InterruptHandler)


if __name__ == "__main__":
    unittest.main()

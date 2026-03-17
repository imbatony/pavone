"""M3U8 进度条测试"""

import unittest

from pavone.models.progress_info import ProgressInfo


class TestProgressInfoSegmentFields(unittest.TestCase):
    """ProgressInfo 分片字段测试"""

    def test_default_segment_fields_zero(self) -> None:
        """默认分片字段应为 0"""
        info = ProgressInfo()
        self.assertEqual(info.total_segments, 0)
        self.assertEqual(info.completed_segments, 0)
        self.assertAlmostEqual(info.segment_speed, 0.0)

    def test_segment_fields_set_correctly(self) -> None:
        """分片字段应可正确设置"""
        info = ProgressInfo(
            total_segments=100,
            completed_segments=30,
            segment_speed=2.5,
        )
        self.assertEqual(info.total_segments, 100)
        self.assertEqual(info.completed_segments, 30)
        self.assertAlmostEqual(info.segment_speed, 2.5)

    def test_backward_compatible_without_segment_fields(self) -> None:
        """不传分片字段时应向后兼容"""
        info = ProgressInfo(total_size=1024, downloaded=512, speed=100.0)
        self.assertEqual(info.total_size, 1024)
        self.assertEqual(info.downloaded, 512)
        self.assertEqual(info.total_segments, 0)
        self.assertEqual(info.completed_segments, 0)

    def test_segment_percentage_calculation(self) -> None:
        """分片百分比应可手动计算"""
        info = ProgressInfo(total_segments=100, completed_segments=30)
        if info.total_segments > 0:
            pct = (info.completed_segments / info.total_segments) * 100
        else:
            pct = 0.0
        self.assertAlmostEqual(pct, 30.0)

    def test_cache_resume_nonzero_start(self) -> None:
        """从缓存恢复时, 初始 completed_segments 应非零"""
        # 模拟: 100 个分片中有 40 个已在缓存
        existing = 40
        info = ProgressInfo(
            total_segments=100,
            completed_segments=existing,
            segment_speed=0.0,
            status_message=f"发现 {existing} 个已存在的分段，正在恢复下载...",
        )
        self.assertEqual(info.completed_segments, 40)
        self.assertGreater(info.completed_segments, 0)
        self.assertIn("40", info.status_message)


class TestSegmentProgressCallback(unittest.TestCase):
    """分片级进度回调测试"""

    def test_create_segment_progress_callback_returns_callable(self) -> None:
        """create_segment_progress_callback() 应返回可调用对象"""
        from pavone.manager.progress import create_segment_progress_callback

        callback = create_segment_progress_callback()
        self.assertTrue(callable(callback))

    def test_callback_accepts_segment_progress_info(self) -> None:
        """回调应能正常接收包含 segment 字段的 ProgressInfo"""
        from pavone.manager.progress import create_silent_progress_callback

        callback = create_silent_progress_callback()
        info = ProgressInfo(
            total_segments=50,
            completed_segments=10,
            segment_speed=3.0,
        )
        # 不应抛出异常
        callback(info)


if __name__ == "__main__":
    unittest.main()

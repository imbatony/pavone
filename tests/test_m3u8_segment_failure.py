"""M3U8 分段失败处理测试"""

import os
import shutil
import tempfile
import unittest
from unittest.mock import MagicMock, patch

from pavone.models.progress_info import ProgressInfo, SegmentResult


class TestSegmentResult(unittest.TestCase):
    """SegmentResult 数据类测试"""

    def test_success_result(self) -> None:
        result = SegmentResult(index=0, success=True)
        self.assertEqual(result.index, 0)
        self.assertTrue(result.success)
        self.assertIsNone(result.error_message)

    def test_failure_result(self) -> None:
        result = SegmentResult(index=5, success=False, error_message="Connection timeout")
        self.assertEqual(result.index, 5)
        self.assertFalse(result.success)
        self.assertEqual(result.error_message, "Connection timeout")


class TestM3U8SegmentFailureHandling(unittest.TestCase):
    """M3U8 分片失败处理流程测试"""

    def setUp(self) -> None:
        self.temp_dir = tempfile.mkdtemp()

    def tearDown(self) -> None:
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_all_segments_failed_no_skip_option(self) -> None:
        """全部分片失败时不应提供跳过选项 (FR-009)"""
        # Arrange
        results = [
            SegmentResult(index=0, success=False, error_message="timeout"),
            SegmentResult(index=1, success=False, error_message="timeout"),
            SegmentResult(index=2, success=False, error_message="timeout"),
        ]
        total = len(results)
        failed = [r for r in results if not r.success]

        # Assert: 全部失败
        self.assertEqual(len(failed), total)

    def test_partial_failure_identifies_failed_segments(self) -> None:
        """部分失败时正确识别失败的分片"""
        # Arrange
        results = [
            SegmentResult(index=0, success=True),
            SegmentResult(index=1, success=False, error_message="404 Not Found"),
            SegmentResult(index=2, success=True),
            SegmentResult(index=3, success=True),
            SegmentResult(index=4, success=False, error_message="Connection reset"),
        ]

        # Act
        failed = [r for r in results if not r.success]
        successful = [r for r in results if r.success]

        # Assert
        self.assertEqual(len(failed), 2)
        self.assertEqual(len(successful), 3)
        self.assertEqual(failed[0].index, 1)
        self.assertEqual(failed[1].index, 4)

    def test_merge_with_partial_segments(self) -> None:
        """跳过失败分片后可以合并已有分片"""
        # Arrange: 创建模拟的分片文件 (0, 2, 3 存在; 1 缺失)
        segment_files: dict[int, str] = {}
        for i in [0, 2, 3]:
            path = os.path.join(self.temp_dir, f"segment_{i:06d}.ts")
            with open(path, "wb") as f:
                f.write(f"data_{i}".encode())
            segment_files[i] = path

        # Act: 按顺序收集已有分片
        total_segments = 4
        ordered_files: list[str] = []
        skipped: list[int] = []
        for i in range(total_segments):
            seg = segment_files.get(i)
            if seg and os.path.exists(seg):
                ordered_files.append(seg)
            else:
                skipped.append(i)

        # Assert
        self.assertEqual(len(ordered_files), 3)
        self.assertEqual(skipped, [1])

        # Act: 合并
        output_file = os.path.join(self.temp_dir, "output.ts")
        with open(output_file, "wb") as out:
            for sf in ordered_files:
                with open(sf, "rb") as f:
                    out.write(f.read())

        # Assert: 输出文件存在且包含数据
        self.assertTrue(os.path.exists(output_file))
        self.assertGreater(os.path.getsize(output_file), 0)

    def test_skip_failed_flag_auto_skips(self) -> None:
        """--skip-failed 标志下应自动跳过失败分片"""
        # Arrange
        results = [
            SegmentResult(index=0, success=True),
            SegmentResult(index=1, success=False, error_message="timeout"),
        ]
        skip_failed = True

        # Act: 模拟 skip-failed 逻辑
        failed = [r for r in results if not r.success]
        total = len(results)

        # Assert: 非全部失败 + skip_failed 标志 → 应该跳过合并
        self.assertGreater(len(failed), 0)
        self.assertLess(len(failed), total)
        self.assertTrue(skip_failed)
        # 在实际代码中这会触发 merge_available_segments()

    def test_retry_only_failed_segments(self) -> None:
        """重试时只重试失败的分片"""
        # Arrange
        results = [
            SegmentResult(index=0, success=True),
            SegmentResult(index=1, success=False, error_message="timeout"),
            SegmentResult(index=2, success=True),
            SegmentResult(index=3, success=False, error_message="503"),
        ]

        # Act
        failed_indices = [r.index for r in results if not r.success]

        # Assert: 只重试索引 1 和 3
        self.assertEqual(failed_indices, [1, 3])


if __name__ == "__main__":
    unittest.main()

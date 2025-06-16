"""
测试文件整理功能
"""

import unittest
import tempfile
from pathlib import Path
from pavone.core.organizer import FileOrganizer


class TestFileOrganizer(unittest.TestCase):
    """测试文件整理器"""
    
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.organizer = FileOrganizer(self.temp_dir)
    
    def tearDown(self):
        import shutil
        shutil.rmtree(self.temp_dir)
    
    def test_init(self):
        """测试初始化"""
        self.assertEqual(str(self.organizer.base_path), self.temp_dir)
        self.assertIn('.mp4', self.organizer.video_extensions)
        self.assertIn('.jpg', self.organizer.image_extensions)
    
    def test_extract_studio_from_filename(self):
        """测试从文件名提取制作商"""
        # 测试标准格式
        studio = self.organizer._extract_studio_from_filename("ABC-123.mp4")
        self.assertEqual(studio, "ABC")
        
        # 测试带数字的格式
        studio = self.organizer._extract_studio_from_filename("ABC123-456.mp4")
        self.assertEqual(studio, "ABC123")
        
        # 测试无匹配的情况
        studio = self.organizer._extract_studio_from_filename("random_video.mp4")
        self.assertIsNone(studio)
    
    def test_find_duplicates(self):
        """测试查找重复文件"""
        # 创建测试文件
        test_file1 = Path(self.temp_dir) / "test1.mp4"
        test_file2 = Path(self.temp_dir) / "test2.mp4"
        
        # 写入相同内容
        test_content = b"test video content"
        test_file1.write_bytes(test_content)
        test_file2.write_bytes(test_content)
        
        duplicates = self.organizer.find_duplicates(self.temp_dir)
        # 应该找到一组重复文件
        self.assertEqual(len(duplicates), 1)
        self.assertEqual(len(duplicates[0]), 2)


if __name__ == '__main__':
    unittest.main()

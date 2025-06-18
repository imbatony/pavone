"""
ExtractorPlugin基类测试
"""

import unittest
from typing import List

from pavone.plugins.extractors.base import ExtractorPlugin
from pavone.core.downloader.options import DownloadOpt


class MockExtractorPlugin(ExtractorPlugin):
    """测试用的提取器插件实现"""
    
    def __init__(self):
        super().__init__()
        self.name = "TestExtractor"
        
    def can_handle(self, url: str) -> bool:
        """测试用的URL处理检查"""
        return url.startswith("http://test.example.com")
    
    def extract(self, url: str) -> List[DownloadOpt]:
        """测试用的提取方法"""
        return []
    
    def initialize(self):
        """初始化插件"""
        return True
    
    def execute(self, *args, **kwargs):
        """执行插件功能"""
        if args and isinstance(args[0], str):
            return self.extract(args[0])
        return []
    
    def cleanup(self):
        """清理插件资源"""
        pass


class TestExtractorBase(unittest.TestCase):
    """ExtractorPlugin基类测试"""
    
    def setUp(self):
        """设置测试环境"""
        self.extractor = MockExtractorPlugin()
    
    def test_sanitize_filename(self):
        """测试文件名清理功能"""
        test_cases = [
            ('Test<>Video', 'Test__Video'),
            ('Video: Title', 'Video_ Title'),
            ('Video/Title\\Name', 'Video_Title_Name'),
            ('Video|Title?Name', 'Video_Title_Name'),
            ('Video*Title"Name', 'Video_Title_Name'),
            ('Normal Video', 'Normal Video'),
            ('', 'video'),
            ('   ', 'video'),  # 只有空格
            ('A' * 250, 'A' * 200),  # 超长文件名
            ('  Spaced Name  ', 'Spaced Name'),  # 前后空格
        ]
        
        for input_name, expected in test_cases:
            with self.subTest(input_name=input_name):
                result = self.extractor.sanitize_filename(input_name)
                self.assertEqual(result, expected)
    
    def test_sanitize_filename_all_illegal_chars(self):
        """测试所有非法字符的替换"""
        illegal_chars = ['<', '>', ':', '"', '/', '\\', '|', '?', '*']
        input_filename = 'Test' + ''.join(illegal_chars) + 'Video'
        expected = 'Test' + '_' * len(illegal_chars) + 'Video'
        
        result = self.extractor.sanitize_filename(input_filename)
        self.assertEqual(result, expected)
    
    def test_priority_management(self):
        """测试优先级管理"""
        # 默认优先级
        self.assertEqual(self.extractor.priority_level, 50)
        
        # 设置新优先级
        self.extractor.set_priority(10)
        self.assertEqual(self.extractor.priority_level, 10)
        self.assertEqual(self.extractor.priority, 10)


if __name__ == '__main__':
    unittest.main()

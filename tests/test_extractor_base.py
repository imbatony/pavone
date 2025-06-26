"""
ExtractorPlugin基类测试
"""

import unittest
from typing import List

from pavone.plugins.extractors.base import ExtractorPlugin
from pavone.models.operation import OperationItem


class MockExtractorPlugin(ExtractorPlugin):
    """测试用的提取器插件实现"""
    
    def __init__(self):
        super().__init__()
        self.name = "TestExtractor"
        
    def can_handle(self, url: str) -> bool:
        """测试用的URL处理检查"""
        return url.startswith("http://test.example.com")
    
    def extract(self, url: str) -> List[OperationItem]:
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
    
    def test_priority_management(self):
        """测试优先级管理"""
        # 默认优先级
        self.assertEqual(self.extractor.get_priority(), 50)

        # 设置新优先级
        self.extractor.set_priority(10)
        self.assertEqual(self.extractor.get_priority(), 10)
        self.assertEqual(self.extractor.priority, 10)


if __name__ == '__main__':
    unittest.main()

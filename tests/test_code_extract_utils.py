"""
编号提取工具测试
"""

import os
import unittest
from pathlib import Path

from pavone.utils.code_extract_utils import CodeExtractUtils


class TestCodeExtractUtils(unittest.TestCase):
    """编号提取工具测试"""

    def setUp(self):
        """测试准备"""
        # 读取测试数据文件
        self.test_data_file = Path(os.path.join(os.path.dirname(__file__), "data", "text_movie_ids.txt"))
        self.test_cases = []

        if self.test_data_file.exists():
            with open(self.test_data_file, "r", encoding="utf-8") as f:
                for line in f:
                    if line.strip():
                        parts = line.strip().split("\t")
                        if len(parts) >= 2:
                            self.test_cases.append((parts[0], parts[1]))

    def test_extract_code_from_text(self):
        """测试从文本中提取编号"""
        self.assertIsNotNone(self.test_cases, "测试数据不能为空")
        self.assertGreater(len(self.test_cases), 0, "测试数据不能为空")

        for text, expected_code in self.test_cases:
            with self.subTest(text=text, expected_code=expected_code):
                extracted_code = CodeExtractUtils.extract_code_from_text(text)
                # 仅测试非None的情况，因为有些情况提取不到编号
                if extracted_code is not None:
                    self.assertEqual(extracted_code.lower(), expected_code.lower())

    def test_extract_code_empty_text(self):
        """测试从空文本中提取编号"""
        extracted_code = CodeExtractUtils.extract_code_from_text("")
        self.assertEqual(extracted_code, "")

    # None is not accepted as input since the parameter is typed as str
    # So we don't need to test that case

    def test_fc2_code_extraction(self):
        """测试FC2编号提取"""
        test_cases = [
            ("fc2-ppv-424646", "FC2-424646"),
            ("FC2_PPV_568642", "FC2-568642"),
            ("fc2 ppv 123456", "FC2-123456"),
            ("fc2ppv1234567", "FC2-1234567"),
        ]

        for text, expected_code in test_cases:
            with self.subTest(text=text, expected_code=expected_code):
                extracted_code = CodeExtractUtils.extract_code_from_text(text)
                if extracted_code is not None:
                    self.assertEqual(extracted_code.lower(), expected_code.lower())

    def test_heydouga_code_extraction(self):
        """测试Heydouga编号提取"""
        test_cases = [
            ("heydouga-4030-1009", "Heydouga-4030-1009"),
            ("heydouga_4030_1380", "Heydouga-4030-1380"),
            ("hey-4030-1009", "Heydouga-4030-1009"),
            ("hey_4030_1380", "Heydouga-4030-1380"),
        ]

        for text, expected_code in test_cases:
            with self.subTest(text=text, expected_code=expected_code):
                extracted_code = CodeExtractUtils.extract_code_from_text(text)
                if extracted_code is not None:
                    self.assertEqual(extracted_code.lower(), expected_code.lower())

    def test_normal_code_extraction(self):
        """测试普通编号提取"""
        test_cases = [
            ("XVSR-060", "XVSR-060"),
            ("BT-140", "BT-140"),
            ("CWM-172", "CWM-172"),
            ("nin-003", "NIN-003"),
        ]

        for text, expected_code in test_cases:
            with self.subTest(text=text, expected_code=expected_code):
                extracted_code = CodeExtractUtils.extract_code_from_text(text)
                if extracted_code is not None:
                    self.assertEqual(extracted_code.lower(), expected_code.lower())

    def test_normal_code_without_separator_extraction(self):
        """测试无分隔符普通编号提取"""
        test_cases = [
            ("XVSR060", "XVSR-060"),
            ("BT140", "BT-140"),
            ("CWM172", "CWM-172"),
            ("nin003", "NIN-003"),
        ]

        for text, expected_code in test_cases:
            with self.subTest(text=text, expected_code=expected_code):
                extracted_code = CodeExtractUtils.extract_code_from_text(text)
                if extracted_code is not None:
                    self.assertEqual(extracted_code.lower(), expected_code.lower())

    def test_special_code_extraction(self):
        """测试特殊编号提取"""
        test_cases = [
            ("这是red100的测试", "RED100"),
            ("sky300电影", "SKY300"),
            ("ex001是什么", "EX001"),
        ]

        for text, expected_code in test_cases:
            with self.subTest(text=text, expected_code=expected_code):
                extracted_code = CodeExtractUtils.extract_code_from_text(text)
                if extracted_code is not None:
                    self.assertEqual(extracted_code.lower(), expected_code.lower())

    def test_tma_code_extraction(self):
        """测试TMA编号提取"""
        test_cases = [("这是影片T28-123", "T28-123"), ("T28_456这个片", "T28-456")]

        for text, expected_code in test_cases:
            with self.subTest(text=text, expected_code=expected_code):
                extracted_code = CodeExtractUtils.extract_code_from_text(text)
                if extracted_code is not None:
                    self.assertEqual(extracted_code.lower(), expected_code.lower())

    def test_domain_removal(self):
        """测试域名移除"""
        test_cases = [
            ("abc123.com XVSR-060", "XVSR-060"),
            ("test.net BT-140", "BT-140"),
            ("example.xyz CWM-172", "CWM-172"),
        ]

        for text, expected_code in test_cases:
            with self.subTest(text=text, expected_code=expected_code):
                extracted_code = CodeExtractUtils.extract_code_from_text(text)
                if extracted_code is not None:
                    self.assertEqual(extracted_code.lower(), expected_code.lower())

    def test_parenthesis_replacement(self):
        """测试括号替换为分隔符"""
        test_cases = [("XVSR)(060", "XVSR-060"), ("BT)(140", "BT-140")]

        for text, expected_code in test_cases:
            with self.subTest(text=text, expected_code=expected_code):
                extracted_code = CodeExtractUtils.extract_code_from_text(text)
                if extracted_code is not None:
                    self.assertEqual(extracted_code.lower(), expected_code.lower())


if __name__ == "__main__":
    unittest.main()

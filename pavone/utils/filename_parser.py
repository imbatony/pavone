"""
文件名解析工具

提供文件名正规化和代码提取功能，用于文件整理功能。
复用 CodeExtractUtils 进行代码提取，增加文件名特定的预处理逻辑。
"""

import re
from pathlib import Path
from typing import Any, Dict, List, Optional

from .code_extract_utils import CodeExtractUtils


class FilenameParser:
    """文件名解析器

    复用 CodeExtractUtils 进行代码提取，
    增加文件名特定的正规化逻辑。
    """

    @staticmethod
    def normalize_filename(filename: str) -> str:
        """正规化文件名，提高代码提取成功率

        处理逻辑:
        1. 移除文件扩展名
        2. 移除方括号内容（如: [Jable], [FHD], [1080p]）
        3. 移除圆括号内容（如: (uncensored)）
        4. 移除常见无用标记（如: _uncensored, -C, @）
        5. 清理多余空格和分隔符

        Args:
            filename: 原始文件名

        Returns:
            正规化后的文件名

        示例:
            "[Jable]SSIS-123 美少女.mp4" -> "SSIS-123 美少女"
            "FC2-PPV-1234567(uncensored).mp4" -> "FC2-PPV-1234567"
            "abc_123_uncensored.mp4" -> "abc 123"
        """
        # 1. 移除扩展名
        if "." in filename:
            filename = filename.rsplit(".", 1)[0]

        # 2. 移除方括号内容（包括方括号本身）
        filename = re.sub(r"\[.*?\]", "", filename)

        # 3. 移除圆括号内容（包括圆括号本身）
        filename = re.sub(r"\(.*?\)", "", filename)

        # 4. 移除常见无用标记
        # 移除 uncensored, uc, leak, ch, sub 等标记（不区分大小写）
        filename = re.sub(r"[-_]?(uncensored|uc|leak|ch|sub|code|cd\d+)", "", filename, flags=re.IGNORECASE)

        # 5. 移除特殊字符,但保留连字符（代码提取需要）
        # 保留中文、日文等非ASCII字符
        filename = re.sub(r"[@#$%^&*+=|\\/<>?]", " ", filename)

        # 6. 将下划线替换为连字符（统一分隔符）
        filename = filename.replace("_", "-")

        # 7. 清理多余空格（不处理连字符）
        filename = re.sub(r"\s+", " ", filename)

        # 7. 清理多余空格
        filename = " ".join(filename.split())

        return filename.strip()

    @staticmethod
    def extract_code(filename: str) -> Optional[str]:
        """从文件名提取视频代码

        工作流程:
        1. 正规化文件名
        2. 调用 CodeExtractUtils.extract_code_from_text()

        Args:
            filename: 原始文件名（可以包含路径）

        Returns:
            视频代码，失败返回 None

        示例:
            "[Jable]SSIS-123 美少女.mp4" -> "SSIS-123"
            "FC2-PPV-1234567.mp4" -> "FC2-1234567"
            "abc-123_uncensored.mp4" -> "ABC-123"
            "/path/to/video/SSIS-123.mp4" -> "SSIS-123"
        """
        # 处理空字符串
        if not filename:
            return None

        # 如果是路径，只取文件名部分
        if "/" in filename or "\\" in filename:
            filename = Path(filename).name

        # 正规化文件名
        normalized = FilenameParser.normalize_filename(filename)

        # 使用现有的 CodeExtractUtils 提取代码
        code = CodeExtractUtils.extract_code_from_text(normalized)

        # CodeExtractUtils 可能返回空字符串，统一转换为 None
        return code if code else None

    @staticmethod
    def extract_metadata_hints(filename: str) -> Dict[str, Any]:
        """从文件名提取元数据提示

        Args:
            filename: 原始文件名（可以包含路径）

        Returns:
            元数据提示字典，包含:
            - code: 视频代码
            - normalized_name: 正规化后的文件名
            - original_name: 原始文件名（不含路径和扩展名）

        示例:
            "[Jable]SSIS-123 美少女.mp4" -> {
                'code': 'SSIS-123',
                'normalized_name': 'SSIS-123 美少女',
                'original_name': '[Jable]SSIS-123 美少女'
            }
        """
        # 如果是路径，只取文件名部分
        if "/" in filename or "\\" in filename:
            filename = Path(filename).name

        # 移除扩展名作为原始名称
        original_name = filename
        if "." in filename:
            original_name = filename.rsplit(".", 1)[0]

        # 正规化文件名
        normalized = FilenameParser.normalize_filename(filename)

        # 提取代码
        code = CodeExtractUtils.extract_code_from_text(normalized)

        return {"code": code, "normalized_name": normalized, "original_name": original_name}

    @staticmethod
    def is_video_file(filename: str, extensions: Optional[List[str]] = None) -> bool:
        """检查是否为视频文件

        Args:
            filename: 文件名（可以包含路径）
            extensions: 支持的视频扩展名列表（默认使用常见视频格式）

        Returns:
            是否为视频文件

        示例:
            "video.mp4" -> True
            "video.txt" -> False
            "/path/to/video.mkv" -> True
        """
        if extensions is None:
            extensions = [".mp4", ".mkv", ".avi", ".mov", ".wmv", ".flv", ".ts", ".m4v", ".webm", ".rmvb"]

        # 转换为小写进行比较
        extensions = [ext.lower() for ext in extensions]

        # 获取文件扩展名
        path = Path(filename)
        ext = path.suffix.lower()

        return ext in extensions

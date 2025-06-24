"""
尝试从文件名或者keywords或者标题中提取编号代码
"""
class CodeExtractUtils:
    @staticmethod
    def extract_code_from_filename(filename: str) -> str:
        """
        从文件名中提取编号代码
        """
        parts = filename.split('_')
        if len(parts) > 1:
            return parts[0]
        return filename.split('.')[0]  # 返回文件名的第一部分

    @staticmethod
    def extract_code_from_keywords(keywords: str) -> str:
        """
        从keywords中提取编号代码
        """
        return keywords.split()[0] if keywords else ''
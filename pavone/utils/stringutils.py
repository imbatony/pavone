from typing import Optional


class StringUtils:
    @staticmethod
    def normalize_string(s: Optional[str]) -> str:
        """标准化字符串，去除多余空格和特殊字符"""
        if not s:
            return ""
        # 去除首尾空格
        s = s.strip()
        # 替换多个空格为一个空格
        s = " ".join(s.split())
        # 替换特殊字符
        special_chars = ["/", "\\", ":", "*", "?", '"', "<", ">", "|"]
        for char in special_chars:
            s = s.replace(char, "")
        return s

    @staticmethod
    def normalize_folder_path(folder: str) -> str:
        """
        规范化文件夹路径
        Args:
            folder: 文件夹路径
        Returns:
            规范化后的文件夹路径
        """
        if not folder:
            raise ValueError("文件夹路径不能为空")
        # 确保路径格式正确
        folder = folder.replace("\\", "/").strip("/")
        return folder

    @staticmethod
    def sha_256_hash(s: str) -> str:
        """
        计算字符串的 SHA-256 哈希值
        Args:
            s (str): 输入字符串
        Returns:
            str: SHA-256 哈希值
        """
        import hashlib

        return hashlib.sha256(s.encode("utf-8")).hexdigest()

    @staticmethod
    def create_identifier(site: str, code: str, url: str) -> str:
        """
        创建唯一标识符
        Args:
            site (str): 网站名称
            code (str): 视频代码
            url (str): 视频链接
        Returns:
            str: 唯一标识符
        """
        return f"{site}-{code}-{StringUtils.sha_256_hash(url)}"

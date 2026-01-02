"""
FC2 Base Metadata Plugin - FC2元数据提取器基类

提供FC2系列视频的通用元数据提取逻辑，供具体的FC2元数据插件继承使用。
"""

import re
from typing import List, Optional


from .base import MetadataPlugin


class FC2BaseMetadata(MetadataPlugin):
    """
    FC2元数据提取器基类

    提供FC2系列视频的通用逻辑，包括：
    - FC2代码提取和验证
    - FC2 URL构建
    - FC2特有的元数据字段处理
    """

    # FC2代码模式
    FC2_CODE_PATTERN = r"^(?:FC2[-_]?)?(?:PPV[-_]?)?(\d+)$"
    FC2_CODE_WITH_PREFIX_PATTERN = r"^FC2(-PPV)?-\d+$"

    def _extract_fc2_id(self, identifier: str) -> Optional[str]:
        """
        从identifier中提取FC2 ID（纯数字部分）

        Args:
            identifier: 可以是各种格式的FC2标识符，如：
                - FC2-1234567
                - FC2-PPV-1234567
                - FC2_PPV_1234567
                - 1234567

        Returns:
            提取的纯数字ID，如果无法提取则返回 None

        Examples:
            >>> _extract_fc2_id("FC2-PPV-1234567")
            "1234567"
            >>> _extract_fc2_id("FC2-1234567")
            "1234567"
            >>> _extract_fc2_id("1234567")
            "1234567"
        """
        identifier_stripped = identifier.strip().upper()
        match = re.match(self.FC2_CODE_PATTERN, identifier_stripped)
        return match.group(1) if match else None

    def _build_fc2_code(self, fc2_id: str) -> str:
        """
        构建标准FC2代码

        Args:
            fc2_id: FC2纯数字ID

        Returns:
            标准格式的FC2代码: FC2-XXXXXXX

        Examples:
            >>> _build_fc2_code("1234567")
            "FC2-1234567"
        """
        return f"FC2-{fc2_id}"

    def _build_fc2_ppv_code(self, fc2_id: str) -> str:
        """
        构建标准FC2-PPV代码

        Args:
            fc2_id: FC2纯数字ID

        Returns:
            标准格式的FC2-PPV代码: FC2-PPV-XXXXXXX

        Examples:
            >>> _build_fc2_ppv_code("1234567")
            "FC2-PPV-1234567"
        """
        return f"FC2-PPV-{fc2_id}"

    def _validate_fc2_identifier(self, identifier: str) -> bool:
        """
        验证是否为有效的FC2 identifier

        Args:
            identifier: 要验证的标识符

        Returns:
            如果是有效的FC2标识符则返回True，否则返回False

        Examples:
            >>> _validate_fc2_identifier("FC2-1234567")
            True
            >>> _validate_fc2_identifier("FC2-PPV-1234567")
            True
            >>> _validate_fc2_identifier("INVALID-123")
            False
        """
        identifier_stripped = identifier.strip().upper()

        # 检查是否为FC2代码格式
        if identifier_stripped.startswith("FC2"):
            return bool(re.match(self.FC2_CODE_WITH_PREFIX_PATTERN, identifier_stripped))

        # 检查是否为纯数字ID
        return bool(re.match(r"^\d+$", identifier_stripped))

    def _is_fc2_url(self, url: str) -> bool:
        """
        检查URL是否为FC2相关URL

        Args:
            url: 要检查的URL

        Returns:
            如果是FC2相关URL则返回True，否则返回False
        """
        # 子类可以重写此方法以实现特定的URL检查逻辑
        return "fc2" in url.lower()

    def _normalize_fc2_code(self, code: str) -> str:
        """
        标准化FC2代码格式

        Args:
            code: FC2代码（任意格式）

        Returns:
            标准化后的FC2代码

        Examples:
            >>> _normalize_fc2_code("fc2-ppv-1234567")
            "FC2-PPV-1234567"
            >>> _normalize_fc2_code("1234567")
            "FC2-1234567"
        """
        fc2_id = self._extract_fc2_id(code)
        if not fc2_id:
            return code

        # 如果原代码包含PPV，返回FC2-PPV格式
        if "PPV" in code.upper():
            return self._build_fc2_ppv_code(fc2_id)

        # 否则返回FC2格式
        return self._build_fc2_code(fc2_id)

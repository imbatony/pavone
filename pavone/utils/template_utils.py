"""
模板工具类

提供统一的模板解析功能，用于文件名和文件夹结构的格式化。
"""

from typing import TYPE_CHECKING, Optional

from .stringutils import StringUtils

if TYPE_CHECKING:
    from ..models.metadata import MovieMetadata


class TemplateUtils:
    """模板工具类

    提供统一的模板解析功能，支持以下占位符：
    - {code}: 番号
    - {title}: 标题
    - {studio}: 制作商
    - {year}: 年份
    - {actors}: 演员（逗号分隔）
    """

    @staticmethod
    def resolve_template(template: str, metadata: "MovieMetadata", max_actors: int = 3) -> str:
        """解析模板字符串，替换占位符

        Args:
            template: 模板字符串，如 "{studio}/{code}" 或 "{code} - {title}"
            metadata: 电影元数据
            max_actors: 最多包含的演员数量，默认3个

        Returns:
            解析后的字符串

        示例:
            >>> metadata = MovieMetadata(code="SSIS-123", title="测试", studio="S1", year=2024)
            >>> resolve_template("{code} - {title}", metadata)
            'SSIS-123 - 测试'
            >>> resolve_template("{studio}/{code}", metadata)
            'S1/SSIS-123'
        """
        # 准备替换值
        code = metadata.code or "UNKNOWN"
        title = metadata.title or ""
        studio = metadata.studio or "Unknown"
        year = str(metadata.year) if metadata.year else "0000"
        actors = ", ".join(metadata.actors[:max_actors]) if metadata.actors else "Unknown"

        # 清理文件名中的非法字符
        title = TemplateUtils.sanitize_filename(title)
        studio = TemplateUtils.sanitize_filename(studio)
        actors = TemplateUtils.sanitize_filename(actors)

        # 使用 format 进行替换
        try:
            result = template.format(
                code=code,
                title=title,
                studio=studio,
                year=year,
                actors=actors,
            )
        except KeyError:
            # 如果模板中包含不支持的占位符，保持原样
            result = template

        # 清理多余空格
        result = " ".join(result.split())

        return result

    @staticmethod
    def sanitize_filename(name: str) -> str:
        """清理文件名中的非法字符

        Args:
            name: 原始名称

        Returns:
            清理后的名称

        Windows 文件名不能包含: < > : " / \\ | ? *
        """
        if not name:
            return ""

        # 替换非法字符为空格
        illegal_chars = '<>:"/\\|?*'
        for char in illegal_chars:
            name = name.replace(char, " ")

        # 移除控制字符
        name = "".join(char for char in name if ord(char) >= 32)

        # 清理多余空格
        name = " ".join(name.split())

        return name.strip()

    @staticmethod
    def normalize_template_value(value: Optional[str]) -> str:
        """规范化模板值

        使用 StringUtils 进行标准化处理

        Args:
            value: 原始值

        Returns:
            规范化后的值
        """
        return StringUtils.normalize_string(value) if value else ""

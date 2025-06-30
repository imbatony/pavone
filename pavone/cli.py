"""
PAVOne CLI主入口 - 向后兼容导入
为了保持向后兼容性，从新的CLI模块结构导入main函数
"""

# 从新的CLI结构导入main函数
from .cli import main

# 保持向后兼容
__all__ = ["main"]


if __name__ == "__main__":
    main()

#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Jellyfin 库诊断工具入口点

使用方式:
  python -m pavone.tools.diagnose_jellyfin
"""

if __name__ == "__main__":
    from .diagnose_jellyfin import diagnose_jellyfin

    diagnose_jellyfin()

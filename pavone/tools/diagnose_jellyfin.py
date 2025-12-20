#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Jellyfin Library Diagnostic Tool
"""

import json
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from pavone.config.settings import get_config  # noqa: E402
from pavone.jellyfin.client import JellyfinClientWrapper  # noqa: E402
from pavone.jellyfin.library_manager import LibraryManager  # noqa: E402


def print_header(text: str) -> None:
    print(f"\n{'=' * 80}")
    print(f"  {text}")
    print(f"{'=' * 80}")


def print_section(text: str) -> None:
    print(f"\n{text}")
    print("-" * len(text))


def diagnose_jellyfin() -> None:
    """诊断 Jellyfin 配置"""

    print_header("Jellyfin 库诊断工具")

    try:
        # 步骤 1: 加载配置
        print_section("[1/6] 加载配置...")
        try:
            config = get_config()
            jf_config = config.jellyfin
            print("✓ 配置加载成功")
            print(f"  - 服务器: {jf_config.server_url}")
            print(f"  - 已启用: {jf_config.enabled}")
            print(f"  - 验证 SSL: {jf_config.verify_ssl}")
        except Exception as e:
            print(f"❌ 配置加载失败: {e}")
            print("   请检查配置文件是否存在和有效")
            return

        # 步骤 2: 创建客户端
        print_section("[2/6] 连接到 Jellyfin 服务器...")
        try:
            client = JellyfinClientWrapper(jf_config)
            client.authenticate()
            print("✓ 连接成功")
        except Exception as e:
            print(f"❌ 连接失败: {e}")
            print("   请检查:")
            print("   - Jellyfin 服务器是否正在运行")
            print(f"   - server_url 是否正确 ({jf_config.server_url})")
            print("   - API Key 或用户名/密码是否正确")
            return

        # 步骤 3: 获取库列表
        print_section("[3/6] 获取库列表...")
        try:
            libraries = client.get_libraries()
            print(f"✓ 找到 {len(libraries)} 个库:")
            for lib in libraries:
                print(f"  - {lib.name:20} (类型: {lib.type:12}, 项数: {lib.item_count})")
        except Exception as e:
            print(f"❌ 获取库列表失败: {e}")
            return

        # 步骤 4: 尝试获取物理位置
        print_section("[4/6] 获取库的物理位置...")
        try:
            locations = client.get_library_physical_locations()
            if locations:
                print(f"✓ 从 API 获取到 {len(locations)} 个库的物理位置:")
                for lib_name, paths in locations.items():
                    print(f"  - {lib_name}:")
                    for path in paths:
                        print(f"      📁 {path}")
            else:
                print("⚠ 没有从 API 获取到物理位置信息")
        except Exception as e:
            print(f"❌ 获取物理位置失败: {e}")

        # 步骤 5: 从库管理器获取文件夹
        print_section("[5/6] 从库管理器获取库文件夹...")
        try:
            manager = LibraryManager(client)
            folders = manager.get_library_folders()

            print("✓ 获取结果:")
            for lib_name, paths in folders.items():
                if paths:
                    print(f"  - {lib_name}:")
                    for path in paths:
                        print(f"      ✓ {path}")
                else:
                    print(f"  - {lib_name}:")
                    print("      ❌ [未找到文件夹路径]")
        except Exception as e:
            print(f"❌ 从库管理器获取失败: {e}")
            return

        # 步骤 6: 检查原始 API 响应
        print_section("[6/6] 检查原始 API 响应（virtual_folders）...")
        try:
            vf_result = client.client.jellyfin.virtual_folders()
            if vf_result and isinstance(vf_result, list):
                print(f"✓ virtual_folders API 返回 {len(vf_result)} 个虚拟文件夹:")
                for idx, vf in enumerate(vf_result, 1):
                    print(f"\n  虚拟文件夹 #{idx}: {vf.get('Name')}")
                    print(f"    - Locations: {vf.get('Locations')}")
                    print(f"    - 所有字段: {list(vf.keys())}")
            else:
                print(f"⚠ virtual_folders API 返回类型: {type(vf_result)}")
                if isinstance(vf_result, dict):
                    print(f"  返回内容: {json.dumps(vf_result, indent=4, ensure_ascii=False)[:500]}")
        except Exception as e:
            print(f"⚠ virtual_folders API 检查失败: {e}")

        # 步骤 7: 检查 media_folders API
        print_section("[7/7] 检查原始 API 响应（media_folders）...")
        try:
            result = client.client.jellyfin.media_folders()
            print(f"✓ media_folders API 返回 {len(result.get('Items', []))} 个项:")

            for idx, item in enumerate(result.get("Items", []), 1):
                print(f"\n  库 #{idx}: {item.get('Name')}")
                print(f"    - CollectionType: {item.get('CollectionType')}")
                print(f"    - PhysicalLocations: {item.get('PhysicalLocations')}")
                print(f"    - CollectionFolders: {item.get('CollectionFolders')}")
                print(f"    - Folders: {item.get('Folders')}")

                # 列出所有字段
                all_keys = [
                    k
                    for k in item.keys()
                    if k
                    not in [
                        "PhysicalLocations",
                        "CollectionFolders",
                        "Folders",
                        "CollectionType",
                        "Name",
                    ]
                ]
                if all_keys:
                    print(f"    - 其他字段: {all_keys}")

                # 如果都为空，显示警告
                if not any(
                    [
                        item.get("PhysicalLocations"),
                        item.get("CollectionFolders"),
                        item.get("Folders"),
                    ]
                ):
                    print("    ℹ 信息: 此库的文件夹路径通过 virtual_folders API 获取")

        except Exception as e:
            print(f"⚠ 检查原始响应失败: {e}")

        # 总结
        print_header("诊断完成")
        print(
            """
问题排查指南:

1. 如果获取库列表成功，但没有文件夹路径:
   - 在 Jellyfin 的管理面板中检查库的设置
   - 确保库已配置了本地文件夹路径
   - 在 "库管理" -> "编辑库" 中验证媒体文件夹位置

2. 如果连接失败:
   - 检查 Jellyfin 服务器是否在线
   - 验证 server_url 配置是否正确
   - 确认 API Key 或用户名/密码是否有效

3. 如果有其他问题:
   - 查看完整的日志输出（启用 DEBUG 日志）
   - 检查 Jellyfin 服务器的日志
        """
        )

    except KeyboardInterrupt:
        print("\n\n⚠ 诊断被中断")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ 诊断出错: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    diagnose_jellyfin()

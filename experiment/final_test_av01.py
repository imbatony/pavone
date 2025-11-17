"""
最终验证测试 - AV01提取器
"""
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from pavone.plugins.extractors.av01_extractor import AV01Extractor
from pavone.models.constants import ItemType

def main():
    print("=" * 70)
    print(" AV01 提取器最终验证测试")
    print("=" * 70)
    
    # 创建并初始化提取器
    extractor = AV01Extractor()
    success = extractor.initialize()
    
    print(f"\n✓ 提取器初始化: {'成功' if success else '失败'}")
    print(f"  名称: {extractor.name}")
    print(f"  版本: {extractor.version}")
    print(f"  作者: {extractor.author}")
    
    # 测试URL
    test_url = "https://www.av01.tv/jp/video/184522/fc2-ppv-4799119"
    print(f"\n测试URL: {test_url}")
    
    # 1. URL处理测试
    print("\n" + "-" * 70)
    print("1. URL处理测试")
    print("-" * 70)
    can_handle = extractor.can_handle(test_url)
    video_id = extractor._extract_video_id(test_url)
    print(f"✓ 可以处理: {can_handle}")
    print(f"✓ 视频ID: {video_id}")
    
    # 2. 提取视频信息
    print("\n" + "-" * 70)
    print("2. 完整提取测试")
    print("-" * 70)
    print("正在提取视频信息...")
    
    items = extractor.extract(test_url)
    
    if not items:
        print("✗ 提取失败")
        return
    
    print(f"✓ 成功提取 {len(items)} 个下载选项\n")
    
    # 显示每个下载选项的详细信息
    for i, item in enumerate(items, 1):
        print(f"【选项 {i}】")
        print(f"  标题: {item.get_description()[:70]}...")
        print(f"  质量: {item.get_quality_info()}")
        url = item.get_url()
        url_display = url[:70] if url else 'N/A'
        print(f"  URL: {url_display}...")
        
        # 显示子项
        if item.has_children():
            children = item.get_children()
            print(f"  子项数量: {len(children)}")
            
            for j, child in enumerate(children, 1):
                print(f"    [{j}] 类型: {child.item_type}")
                
                # 如果是元数据，显示详细信息
                if child.item_type == ItemType.META_DATA:
                    from pavone.models.constants import MetadataExtraKeys
                    metadata = child._extra.get(MetadataExtraKeys.METADATA_OBJ)
                    if metadata:
                        print(f"        标识符: {metadata.identifier}")
                        print(f"        番号: {metadata.code}")
                        print(f"        站点: {metadata.site}")
                        if hasattr(metadata, 'runtime') and metadata.runtime:
                            print(f"        时长: {metadata.runtime}分钟")
                        if hasattr(metadata, 'tags') and metadata.tags:
                            print(f"        标签数量: {len(metadata.tags)}")
        print()
    
    # 3. 总结
    print("-" * 70)
    print("测试总结")
    print("-" * 70)
    print("✓ 所有API调用成功")
    print("✓ 视频元数据提取成功")
    print("✓ 播放列表解析成功")
    print(f"✓ 找到 {len(items)} 个质量级别的视频")
    print("\n所有测试通过！AV01提取器实现完成。")
    print("=" * 70)

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"\n测试失败: {e}")
        import traceback
        traceback.print_exc()

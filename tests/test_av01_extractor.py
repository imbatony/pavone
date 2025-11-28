"""
AV01提取器测试

测试AV01Extractor从 av01.tv 提取视频信息（完全基于API）
"""

import os
import sys

# 添加项目根目录到路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from pavone.models.constants import ItemType, MetadataExtraKeys
from pavone.plugins.extractors.av01_extractor import AV01Extractor


def print_separator(title="", char="="):
    """打印分隔线"""
    if title:
        print(f"\n{char * 20} {title} {char * 20}")
    else:
        print(char * 60)


def test_can_handle():
    """测试URL识别"""
    print_separator("URL识别测试")
    
    extractor = AV01Extractor()
    
    test_cases = [
        ("https://www.av01.tv/jp/video/184522/fc2-ppv-4799119", True),
        ("https://av01.tv/en/video/123456/test-video", True),
        ("https://www.av01.tv/video/99999", True),
        ("https://www.missav.com/dm18/sdab-183", False),
        ("https://example.com/video.mp4", False),
        ("ftp://av01.tv/video", False),
    ]
    
    print()
    for url, expected in test_cases:
        result = extractor.can_handle(url)
        status = "✓" if result == expected else "✗"
        url_display = url if len(url) <= 60 else url[:57] + "..."
        print(f"{status} {url_display}")
        print(f"  结果: {result}, 期望: {expected}")


def test_video_id_extraction():
    """测试视频ID提取"""
    print_separator("视频ID提取测试")
    
    extractor = AV01Extractor()
    
    test_urls = [
        ("https://www.av01.tv/jp/video/184522/fc2-ppv-4799119", "184522"),
        ("https://av01.tv/en/video/123456/test-video", "123456"),
        ("https://www.av01.tv/video/99999", "99999"),
    ]
    
    print()
    for url, expected_id in test_urls:
        video_id = extractor._extract_video_id(url)
        status = "✓" if video_id == expected_id else "✗"
        print(f"{status} {url}")
        print(f"  提取ID: {video_id}, 期望: {expected_id}")


def test_geo_api():
    """测试geo API"""
    print_separator("Geo API测试")
    
    extractor = AV01Extractor()
    extractor.initialize()
    
    print("\n正在获取geo数据...")
    geo_data = extractor._get_geo_data()
    
    if geo_data:
        print("✓ 成功获取geo数据")
        print(f"  Token: {geo_data.token[:15]}...")
        print(f"  IP: {geo_data.ip}")
        print(f"  Expires: {geo_data.expires}")
        print(f"  Country: {geo_data.country}")
        print(f"  ISP: {geo_data.isp}")
        print(f"  TTL: {geo_data.ttl}秒")
    else:
        print("✗ 获取geo数据失败")


def test_video_metadata():
    """测试视频元数据API"""
    print_separator("视频元数据API测试")
    
    extractor = AV01Extractor()
    extractor.initialize()
    
    video_id = "184522"
    metadata_url = f"https://www.av01.tv/api/v1/videos/{video_id}"
    
    print(f"\n正在获取视频元数据: {video_id}")
    metadata = extractor._get_video_metadata(metadata_url)
    
    if metadata:
        print("✓ 成功获取视频元数据")
        print(f"  标题: {metadata.title}")
        print(f"  番号: {metadata.dvd_id}")
        print(f"  时长: {metadata.duration}秒")
        print(f"  发布日期: {metadata.published_time}")
        
        actors = metadata.get_actor_names()[:3]
        if actors:
            print(f"  演员: {', '.join(actors)}")
        
        if metadata.maker:
            print(f"  制作商: {metadata.maker}")
        
        tags = metadata.get_tag_names()[:5]
        if tags:
            print(f"  标签: {', '.join(tags)}")
    else:
        print("✗ 获取视频元数据失败")


def test_full_extraction():
    """测试完整的视频提取流程"""
    print_separator("完整提取流程测试")
    
    extractor = AV01Extractor()
    
    print(f"\n提取器信息:")
    print(f"  名称: {extractor.name}")
    print(f"  版本: {extractor.version}")
    print(f"  描述: {extractor.description}")
    print(f"  作者: {extractor.author}")
    print(f"  优先级: {extractor.priority}")
    
    # 测试URL
    test_url = "https://www.av01.tv/jp/video/184522/fc2-ppv-4799119"
    print(f"\n测试URL: {test_url}")
    
    # 检查是否可以处理
    print("\n1. 检查URL...")
    can_handle = extractor.can_handle(test_url)
    print(f"   {'✓' if can_handle else '✗'} {'可以处理' if can_handle else '无法处理'}")
    
    if not can_handle:
        print("\n测试失败：提取器无法处理该URL")
        return
    
    # 初始化
    print("\n2. 初始化提取器...")
    if extractor.initialize():
        print("   ✓ 初始化成功")
    else:
        print("   ✗ 初始化失败")
        return
    
    # 提取视频信息
    print("\n3. 提取视频信息...")
    print("   这可能需要几秒钟，请稍候...\n")
    
    try:
        operation_items = extractor.extract(test_url)
        
        if not operation_items:
            print("   ✗ 未能提取到视频信息")
            return
        
        print(f"   ✓ 成功提取到 {len(operation_items)} 个下载选项\n")
        
        # 显示提取结果
        print_separator("提取结果详情")
        
        for i, item in enumerate(operation_items, 1):
            print(f"\n【下载选项 {i}】")
            print(f"  描述: {item.get_description()}")
            
            url = item.get_url()
            if url:
                url_display = url if len(url) <= 80 else url[:77] + "..."
                print(f"  URL: {url_display}")
            
            print(f"  操作类型: {item.opt_type}")
            print(f"  项目类型: {item.item_type}")
            print(f"  质量: {item.get_quality_info()}")
            
            # 显示子项
            if item.has_children():
                children = item.get_children()
                print(f"\n  子项: {len(children)} 个")
                
                for j, child in enumerate(children, 1):
                    print(f"\n  [{j}] {child.item_type}")
                    print(f"      描述: {child.get_description()[:60]}...")
                    
                    if child.get_url():
                        child_url = child.get_url()
                        if child_url:
                            child_url_display = child_url if len(child_url) <= 60 else child_url[:57] + "..."
                            print(f"      URL: {child_url_display}")
                    
                    # 如果是元数据，显示详细信息
                    if child.item_type == ItemType.META_DATA:
                        try:
                            metadata = child._extra.get(MetadataExtraKeys.METADATA_OBJ)
                            if metadata:
                                print(f"\n      【元数据详情】")
                                print(f"      番号: {metadata.code}")
                                print(f"      标识符: {metadata.identifier}")
                                
                                if metadata.actors:
                                    actors_display = ', '.join(metadata.actors[:3])
                                    if len(metadata.actors) > 3:
                                        actors_display += f" 等{len(metadata.actors)}人"
                                    print(f"      演员: {actors_display}")
                                
                                if metadata.studio:
                                    print(f"      制作商: {metadata.studio}")
                                
                                if metadata.release_date:
                                    print(f"      发布日期: {metadata.release_date}")
                                
                                if metadata.duration:
                                    minutes = metadata.duration // 60
                                    seconds = metadata.duration % 60
                                    print(f"      时长: {metadata.duration}秒 ({minutes}分{seconds}秒)")
                                
                                if metadata.genres:
                                    genres_display = ', '.join(metadata.genres[:5])
                                    if len(metadata.genres) > 5:
                                        genres_display += f" 等{len(metadata.genres)}个"
                                    print(f"      类型: {genres_display}")
                                
                                if metadata.tags:
                                    tags_display = ', '.join(metadata.tags[:5])
                                    if len(metadata.tags) > 5:
                                        tags_display += f" 等{len(metadata.tags)}个"
                                    print(f"      标签: {tags_display}")
                                
                                if metadata.description:
                                    desc = metadata.description[:100]
                                    if len(metadata.description) > 100:
                                        desc += "..."
                                    print(f"      描述: {desc}")
                        except Exception as e:
                            print(f"      (无法显示元数据详情: {e})")
        
        print_separator()
        print("\n✓ 测试完成！")
        
    except Exception as e:
        print(f"   ✗ 提取失败: {e}")
        import traceback
        traceback.print_exc()


def main():
    """主函数"""
    print("=" * 60)
    print("AV01 提取器测试套件")
    print("=" * 60)
    
    # 运行各项测试
    test_can_handle()
    test_video_id_extraction()
    test_geo_api()
    test_video_metadata()
    test_full_extraction()
    
    print("\n" + "=" * 60)
    print("所有测试完成")
    print("=" * 60)


if __name__ == "__main__":
    main()

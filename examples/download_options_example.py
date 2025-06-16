"""
DownloadOpt 使用示例
演示如何使用新增的 link_type 字段
"""

from pavone.core.downloader.options import DownloadOpt, LinkType, create_download_opt


def main():
    """演示 DownloadOpt 的使用"""
    print("=== DownloadOpt 使用示例 ===\n")
    
    # 1. 基本使用 - 不指定链接类型
    print("1. 基本使用:")
    basic_opt = DownloadOpt("https://example.com/video.mp4")
    print(f"   URL: {basic_opt.url}")
    print(f"   类型: {basic_opt.get_type_description()}")
    print()
    
    # 2. 指定视频类型
    print("2. 视频文件下载:")
    video_opt = DownloadOpt(
        url="https://example.com/movie.mp4",
        filename="movie.mp4",
        link_type=LinkType.VIDEO
    )
    print(f"   URL: {video_opt.url}")
    print(f"   文件名: {video_opt.filename}")
    print(f"   类型: {video_opt.get_type_description()}")
    print(f"   是视频: {video_opt.is_video()}")
    print()
    
    # 3. 封面图片下载
    print("3. 封面图片下载:")
    cover_opt = create_download_opt(
        url="https://example.com/cover.jpg",
        filename="cover.jpg",
        link_type=LinkType.COVER,
        Referer="https://example.com"
    )
    print(f"   URL: {cover_opt.url}")
    print(f"   文件名: {cover_opt.filename}")
    print(f"   类型: {cover_opt.get_type_description()}")
    print(f"   是图片: {cover_opt.is_image()}")
    print(f"   自定义头部: {cover_opt.custom_headers}")
    print()
    
    # 4. 字幕文件下载
    print("4. 字幕文件下载:")
    subtitle_opt = DownloadOpt(
        url="https://example.com/subtitle.srt",
        filename="subtitle.srt",
        link_type=LinkType.SUBTITLE,
        custom_headers={"Authorization": "Bearer token"}
    )
    print(f"   URL: {subtitle_opt.url}")
    print(f"   文件名: {subtitle_opt.filename}")
    print(f"   类型: {subtitle_opt.get_type_description()}")
    print(f"   是元数据: {subtitle_opt.is_metadata()}")
    print()
    
    # 5. 批量创建不同类型的下载选项
    print("5. 批量创建示例:")
    download_items = [
        ("https://example.com/video.mp4", "视频文件", LinkType.VIDEO),
        ("https://example.com/cover.jpg", "封面图", LinkType.COVER),
        ("https://example.com/thumb.jpg", "缩略图", LinkType.THUMBNAIL),
        ("https://example.com/info.nfo", "NFO文件", LinkType.METADATA),
        ("https://example.com/subtitle.srt", "字幕文件", LinkType.SUBTITLE),
    ]
    
    for url, description, link_type in download_items:
        opt = create_download_opt(url=url, link_type=link_type)
        print(f"   {description}: {opt.get_type_description()}")
    
    print()
    
    # 6. 演示类型检测
    print("6. 类型检测示例:")
    test_opts = [
        create_download_opt("https://example.com/video.mp4", link_type=LinkType.VIDEO),
        create_download_opt("https://example.com/cover.jpg", link_type=LinkType.COVER),
        create_download_opt("https://example.com/info.nfo", link_type=LinkType.METADATA),
    ]
    
    for i, opt in enumerate(test_opts, 1):
        print(f"   选项 {i}:")
        print(f"     类型: {opt.get_type_description()}")
        print(f"     是视频: {opt.is_video()}")
        print(f"     是图片: {opt.is_image()}")
        print(f"     是元数据: {opt.is_metadata()}")
        print()


if __name__ == "__main__":
    main()

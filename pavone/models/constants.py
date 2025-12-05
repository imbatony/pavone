# 常用链接类型常量


class OperationType:
    """
    操作类型常量, 这个类定义了所有可能的操作类型
    包括下载视频、图片、字幕、种子等，或者移动文件等操作
    这些类型可以帮助执行器更好地处理和分类资源
    """

    DOWNLOAD = "download"  # 下载资源
    MOVE = "move"  # 移动资源
    SAVE_METADATA = "save_metadata"  # 保存元数据


class ItemType:
    """
    操作类型常量,这个类定义了所有可能的操作类型
    包括下载视频、图片、字幕、种子等，或者移动文件等操作
    这些类型可以帮助执行器更好地处理和分类资源
    """

    VIDEO = "video"  # 下载视频文件
    STREAM = "stream"  # 下载流媒体
    IMAGE = "image"  # 下载图片文件
    SUBTITLE = "subtitle"  # 下载字幕文件
    TORRENT = "torrent"  # 下载种子文件
    META_DATA = "metadata"  # 保存元数据文件, 如 NFO 文件


class ItemSubType:
    """
    子类型常量, 用于细分类型链接
    包括封面、海报、缩略图和背景图片
    这些子类型可以帮助下载器更好地处理和分类图片资源
    """

    # 视频子类型
    MOVIE = "movie"  # 电影
    TV_SHOW = "tv_show"  # 电视剧
    EPISODE = "episode"  # 电视剧集
    CLIP = "clip"  # 短片或片段
    DOCUMENTARY = "documentary"  # 纪录片
    # 封面、海报、缩略图和背景图片的子类型
    COVER = "cover"  # 封面图片
    POSTER = "poster"  # 海报图片
    LANDSCAPE = "landscape"  # 风景图片
    THUMBNAIL = "thumbnail"  # 缩略图
    BACKDROP = "backdrop"  # 背景图片
    LANDSCAPE = "landscape"  # 横幅图片, 通常用于视频的横幅展示
    # 字幕文件的子类型
    SUBTITLE_SRT = "subtitle_srt"  # SRT格式字幕
    SUBTITLE_VTT = "subtitle_vtt"  # VTT格式字幕
    # UNKNOWN 子类型
    UNKNOWN = "unknown"  # 未知子类型, 用于未分类的链接


class CommonExtraKeys:
    """
    额外的通用信息类型常量
    """

    ITEM_SUBTYPE = "item_subtype"  # 子类型, 如 COVER, POSTER, THUMBNAIL, BACKDROP 等
    TARGET_PATH = "target_path"  # 目标路径
    CUSTOM_HEADERS = "cus_headers"  # 自定义 HTTP 头部, 用于下载时的请求头部
    CUSTOM_FILENAME_PREFIX = "custom_filename_prefix"  # 自定义文件名, 用于下载时指定文件名
    PROGRESS_CALLBACK = "progress_callback"  # 进度回调函数, 用于下载进度更新


class VideoCoreExtraKeys:
    """
    视频额外信息类型常量
    """

    # 主要信息，将影响到命名和分类
    # 视频的必要信息
    TITLE = "title"  # 视频标题, 不含编号
    YEAR = "year"  # 年份, 如 2023
    SITE = "site"  # 来源网站, 如 YouTube、Bilibili 等
    # 非必要信息, 但有助于分类和搜索
    CODE = "code"  # 资源代码, 如 AV 编号等
    STUDIO = "studio"  # 制作公司, 如 S1、SOD 等
    ACTORS = "actors"  # 演员列表, 包含主要演员的名称
    QUALITY = "quality"  # 质量信息

    # 分集信息，将影响到分集的命名
    PART = "part"  # 分集信息, 单集或分集编号


class ImageExtraKeys:
    """图片额外信息类型常量"""

    IMAGE_SIZE = "image_size"  # 图片尺寸, 如 1920x1080
    IMAGE_FORMAT = "image_format"  # 图片格式, 如 JPEG, PNG 等


class MetadataExtraKeys:
    """元数据额外信息类型常量"""

    METADATA_OBJ = "metadata_obj"  # 元数据字典, 用于存储视频的详细信息


class Quality:
    """
    质量常量类, 定义了常见的视频质量选项
    包括 4K、1080p、720p、480p 等
    """

    UHD = "4k"  # 超高清分辨率, 通常指 2160p 分辨率, 即 3840x2160 或 4096x2160
    QHD = "2k"  # 2K 分辨率, 通常指 1440p 分辨率, 即 2560x1440
    FHD = "1080p"  # 全高清分辨率
    HD = "720p"  # 高清分辨率
    SD = "480p"  # 标清分辨率
    LOW = "360p"  # 低清分辨率
    UNKNOWN = "未知"  # 未知质量

    @classmethod
    def guess(cls, text: str) -> str:
        """
        从视频名称, 视频链接或者文本猜测视频质量
        Args:
            text (str): 视频名称或链接文本
        Returns:
            str: 猜测的质量, 可能的值包括 UHD, QHD, FHD, HD, SD, LOW 或 UNKNOWN
        """
        if not text:
            return Quality.UNKNOWN

        text = text.lower()
        # 去除多余的空格和特殊字符
        text = "".join(text.split())
        if "4k" in text or "2160p" in text or "3840x2160" in text or "4096x2160" in text:
            return Quality.UHD
        if "2k" in text or "1440p" in text or "2560x1440" in text:
            return Quality.QHD
        if "1080p" in text or "1920x1080" in text:
            return Quality.FHD
        if "720p" in text or "1280x720" in text:
            return Quality.HD
        if "480p" in text or "842x480" in text:
            return Quality.SD
        if "360p" in text or "640x360" in text:
            return Quality.LOW
        # 中文质量描述
        if "超清" in text or "4k" in text:
            return Quality.UHD
        if "高清" in text or "1080p" in text:
            return Quality.FHD
        if "标清" in text or "480p" in text:
            return Quality.SD
        if "低清" in text or "360p" in text:
            return Quality.LOW
        # 如果没有匹配到任何已知质量，返回未知质量
        return Quality.UNKNOWN

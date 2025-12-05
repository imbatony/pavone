"""Jellyfin Item Metadata Model

这个模块提供 ItemMetadata 类，将 Jellyfin API 返回的元数据字典转换为类型安全的属性访问。

使用示例：
    from pavone.jellyfin import JellyfinClientWrapper
    from pavone.models import ItemMetadata
    
    client = JellyfinClientWrapper(config.jellyfin)
    client.authenticate()
    
    item = client.get_item(item_id)
    metadata = ItemMetadata(item.metadata or {})
    
    # 直接访问属性而不是字典键
    print(metadata.title)           # 标题
    print(metadata.year)            # 发行年份
    print(metadata.runtime_minutes) # 时长（分钟）
    print(metadata.actors)          # 演员列表
    print(metadata.has_primary_image)    # 是否有主图
    print(metadata.backdrop_count)  # 背景图数量
"""

from typing import Any, Dict, List, Optional


class ItemMetadata:
    """Jellyfin 项目元数据类"""
    
    def __init__(self, data: Optional[Dict[str, Any]] = None):
        """初始化元数据
        
        Args:
            data: 原始元数据字典
        """
        self._data = data or {}
    
    # 基础属性
    @property
    def external_id(self) -> Optional[str]:
        """代码/番号"""
        return self._data.get('ExternalId')
    
    @property
    def year(self) -> Optional[int]:
        """发行年份"""
        # Jellyfin API 返回 ProductionYear，而不是 Year
        return self._data.get('ProductionYear') or self._data.get('Year')
    
    @property
    def sort_name(self) -> Optional[str]:
        """排序标题"""
        return self._data.get('SortName')
    
    @property
    def premiere_date(self) -> Optional[str]:
        """首映日期"""
        return self._data.get('PremiereDate')
    
    @property
    def runtime_ticks(self) -> int:
        """时长（单位：ticks）"""
        return self._data.get('RunTimeTicks', 0)
    
    @property
    def runtime_minutes(self) -> int:
        """时长（分钟）"""
        return self.runtime_ticks // 600000000
    
    # 电影/视频属性
    @property
    def studios(self) -> List[Dict[str, str]]:
        """制作公司列表"""
        return self._data.get('Studios', [])
    
    @property
    def studio_names(self) -> List[str]:
        """制作公司名称列表"""
        return [s.get('Name', '未知') for s in self.studios]
    
    @property
    def genres(self) -> List[str]:
        """类型列表（已去重）"""
        genres = self._data.get('Genres', [])
        # 去重同时保持顺序
        return list(dict.fromkeys(genres))
    
    @property
    def tags(self) -> List[str]:
        """标签列表（已去重）"""
        tags = self._data.get('Tags', [])
        # 去重同时保持顺序
        return list(dict.fromkeys(tags))
    
    @property
    def taglines(self) -> List[str]:
        """宣传词/标语列表"""
        return self._data.get('Taglines', [])
    
    @property
    def name(self) -> Optional[str]:
        """元数据中的标题名称（如果存在）"""
        return self._data.get('Name')
    
    @property
    def original_title(self) -> Optional[str]:
        """原始标题（OriginalTitle 字段）"""
        return self._data.get('OriginalTitle')
    
    @property
    def overview(self) -> Optional[str]:
        """描述/简介"""
        return self._data.get('Overview')
    
    @property
    def rating(self) -> Optional[float]:
        """评分（通常是0-10的评分系统）"""
        return self._data.get('CommunityRating')
    
    @property
    def official_rating(self) -> Optional[str]:
        """官方分级（如PG, R, PG-13等，或地区分级）"""
        return self._data.get('OfficialRating')
    
    @property
    def series_name(self) -> Optional[str]:
        """系列名称"""
        return self._data.get('SeriesName')
    
    # 人员属性
    @property
    def people(self) -> List[Dict[str, Any]]:
        """参与人员列表"""
        return self._data.get('People', [])
    
    @property
    def directors(self) -> List[str]:
        """导演列表"""
        return [p.get('Name', '未知') for p in self.people if p.get('Type') == 'Director']
    
    @property
    def actors(self) -> List[str]:
        """演员列表"""
        return [p.get('Name', '未知') for p in self.people if p.get('Type') == 'Actor']
    
    # 图片属性
    @property
    def image_tags(self) -> Dict[str, str]:
        """图片标签（包括Primary主图、Thumb缩略图）"""
        return self._data.get('ImageTags', {})
    
    @property
    def has_primary_image(self) -> bool:
        """是否有主图"""
        return 'Primary' in self.image_tags
    
    @property
    def has_thumb_image(self) -> bool:
        """是否有缩略图"""
        return 'Thumb' in self.image_tags
    
    @property
    def backdrop_image_tags(self) -> List[str]:
        """背景图列表"""
        return self._data.get('BackdropImageTags', [])
    
    @property
    def backdrop_count(self) -> int:
        """背景图数量"""
        return len(self.backdrop_image_tags)
    
    @property
    def image_blur_hashes(self) -> Dict[str, Any]:
        """图片模糊哈希"""
        return self._data.get('ImageBlurHashes', {})
    
    @property
    def primary_image_aspect_ratio(self) -> Optional[float]:
        """主图长宽比"""
        return self._data.get('PrimaryImageAspectRatio')
    
    # 媒体流属性
    @property
    def media_streams(self) -> List[Dict[str, Any]]:
        """媒体流列表"""
        return self._data.get('MediaStreams', [])
    
    @property
    def video_streams(self) -> List[Dict[str, Any]]:
        """视频流列表"""
        return [s for s in self.media_streams if s.get('Type') == 'Video']
    
    @property
    def audio_streams(self) -> List[Dict[str, Any]]:
        """音频流列表"""
        return [s for s in self.media_streams if s.get('Type') == 'Audio']
    
    @property
    def subtitle_streams(self) -> List[Dict[str, Any]]:
        """字幕流列表"""
        return [s for s in self.media_streams if s.get('Type') == 'Subtitle']
    
    # 文件属性
    @property
    def size(self) -> int:
        """文件大小（字节）"""
        return self._data.get('Size', 0)
    
    @property
    def size_str(self) -> str:
        """文件大小字符串"""
        size = self.size
        if size > 1e9:
            return f"{size / 1e9:.2f} GB"
        elif size > 1e6:
            return f"{size / 1e6:.2f} MB"
        elif size > 1e3:
            return f"{size / 1e3:.2f} KB"
        else:
            return f"{size} B"
    
    # 用户数据属性
    @property
    def user_data(self) -> Dict[str, Any]:
        """用户数据（播放信息）"""
        return self._data.get('UserData', {})
    
    @property
    def playback_position_ticks(self) -> int:
        """已播放位置（ticks）"""
        return self.user_data.get('PlaybackPositionTicks', 0)
    
    @property
    def playback_minutes(self) -> int:
        """已播放时长（分钟）"""
        return self.playback_position_ticks // 600000000
    
    @property
    def is_played(self) -> bool:
        """是否已观看"""
        return self.user_data.get('Played', False)
    
    @property
    def play_count(self) -> int:
        """播放次数"""
        return self.user_data.get('PlayCount', 0)
    
    @property
    def last_played_date(self) -> Optional[str]:
        """最后播放日期"""
        return self.user_data.get('LastPlayedDate')
    
    # 其他属性
    @property
    def date_created(self) -> Optional[str]:
        """创建日期"""
        return self._data.get('DateCreated')
    
    @property
    def added_date(self) -> Optional[str]:
        """添加日期"""
        return self._data.get('Added') or self._data.get('DateCreated')
    
    @property
    def video_codec(self) -> Optional[str]:
        """视频编码"""
        return self._data.get('VideoCodec')
    
    @property
    def video_bitrate(self) -> int:
        """视频比特率"""
        return self._data.get('VideoBitrate', 0)
    
    # 原始访问
    def get(self, key: str, default: Any = None) -> Any:
        """获取原始值"""
        return self._data.get(key, default)
    
    def __getitem__(self, key: str) -> Any:
        """索引访问"""
        return self._data[key]
    
    def __contains__(self, key: str) -> bool:
        """检查键是否存在"""
        return key in self._data

"""
Jellyfin 相关数据模型
"""

from dataclasses import dataclass
from typing import Any, Dict, List, Optional


@dataclass
class JellyfinItem:
    """
    Jellyfin 库项

    代表 Jellyfin 库中的单个视频项。

    Attributes:
        id: 项的唯一标识符
        name: 项的名称
        type: 项的类型（如 "Movie", "Series", "Episode" 等）
        container: 文件容器格式（如 "mkv", "mp4" 等）
        path: 文件在文件系统中的路径
        metadata: 完整的 API 返回的元数据字典
    """

    id: str
    name: str
    type: str
    container: Optional[str]
    path: Optional[str]
    metadata: Dict[str, Any]

    def __repr__(self) -> str:
        return f"JellyfinItem(id={self.id}, name={self.name}, type={self.type})"


@dataclass
class JellyfinMetadata:
    """
    Jellyfin 元数据

    提取自 Jellyfin 项的结构化元数据。

    Attributes:
        title: 标题
        year: 发布年份
        genres: 类型列表
        overview: 概述/描述
        runtime_minutes: 时长（分钟）
        premiere_date: 首映日期
        rating: 评分
        studio: 工作室/制作商
        directors: 导演列表
        actors: 演员列表
    """

    title: str
    year: Optional[int] = None
    genres: List[str] = None
    overview: str = ""
    runtime_minutes: Optional[int] = None
    premiere_date: Optional[str] = None
    rating: Optional[float] = None
    studio: Optional[str] = None
    directors: List[str] = None
    actors: List[str] = None

    def __post_init__(self):
        """初始化默认值"""
        if self.genres is None:
            self.genres = []
        if self.directors is None:
            self.directors = []
        if self.actors is None:
            self.actors = []

    def __repr__(self) -> str:
        return f"JellyfinMetadata(title={self.title}, year={self.year})"


@dataclass
class LibraryInfo:
    """
    Jellyfin 库信息

    Attributes:
        name: 库名称
        id: 库的唯一标识符
        type: 库类型（如 "movies", "tvshows" 等）
        item_count: 库中的项数
    """

    name: str
    id: str
    type: str
    item_count: int = 0

    def __repr__(self) -> str:
        return f"LibraryInfo(name={self.name}, type={self.type}, items={self.item_count})"

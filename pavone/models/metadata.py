# 元数据

from abc import abstractmethod
from datetime import datetime
from typing import Optional

from pydantic import BaseModel

"""与操作nfo文件相关的功能"""
from lxml.builder import E
from lxml.etree import _Element, tostring


class MetadataType:
    """
    元数据类型枚举
    定义了不同的元数据类型
    """

    MOVIE = "movie"
    TV_SHOW = "tv_show"
    ANIME = "anime"
    DOCUMENTARY = "documentary"
    MUSIC = "music"
    CLIP = "clip"

    @classmethod
    def to_nfo_root(cls, type_name: str) -> _Element:
        """
        根据元数据类型名称返回对应的 NFO 根元素
        :param type_name: 元数据类型名称
        :return: 对应的 NFO 根元素
        """
        if type_name == cls.MOVIE:
            return E.movie()
        elif type_name == cls.TV_SHOW:
            return E.tvshow()
        elif type_name == cls.ANIME:
            return E.anime()
        elif type_name == cls.DOCUMENTARY:
            return E.documentary()
        elif type_name == cls.MUSIC:
            return E.music()
        elif type_name == cls.CLIP:
            return E.clip()
        else:
            raise ValueError(f"未知的元数据类型: {type_name}")


class BaseMetadata(BaseModel):
    """
    基础元数据模型
    包含所有元数据的公共字段
    """

    identifier: str  # 唯一标识符, 通常包括站点标识和影片番号
    title: str  # 影片标题（不含番号）
    url: str  # 影片链接
    site: str  # 站点标识符
    code: str  # 影片番号或者 ID
    site: str  # 站点标识符, 用于区分不同站点的影片
    type: str  # 元数据类型, 例如 "movie", "tv_show", "anime" 等

    def to_nfo(self) -> str:
        """
        将元数据转换为 NFO 格式字符串
        需要在子类中实现具体的转换逻辑
        """
        nfo = MetadataType.to_nfo_root(self.type)
        # 添加基本信息
        nfo.append(E.title(self.title))

        # 自定义的信息
        nfo.append(E.uniqueid(self.identifier, type="pavid"))
        nfo.append(E.uniqueid(self.code, type="pavcode"))
        nfo.append(E.uniqueid(self.site, type="pavsite"))
        nfo.append(E.uniqueid(self.url, type="pavurl"))

        self.append_extra_fields(nfo)
        return tostring(nfo, pretty_print=True, encoding="UTF-8", xml_declaration=True).decode("utf-8")

    @abstractmethod
    def append_extra_fields(self, nfo: _Element) -> None:
        """
        子类需要实现此方法来添加特定的元数据字段到 NFO 中
        :param nfo: NFO XML 根元素
        """
        raise NotImplementedError("子类必须实现 append_extra_fields 方法")


class MovieMetadata(BaseMetadata):

    def __init__(self, **data):
        super().__init__(type=MetadataType.MOVIE, **data)

    """
    电影元数据模型
    包含电影特有的元数据字段
    """
    tagline: Optional[str] = None  # 标语或副标题
    original_title: Optional[str] = None  # 原始标题
    plot: Optional[str] = None  # 影片简介
    cover: Optional[str] = None  # 封面图片链接
    thumbnail: Optional[str] = None  # 缩略图链接
    poster: Optional[str] = None  # 海报链接
    backdrop: Optional[str] = None  # 背景图片链接
    actors: Optional[list[str]] = None  # 演员列表
    actors_normalized: Optional[list[str]] = None  # 标准化演员列表
    director: Optional[str] = None  # 导演
    studio: Optional[str] = None  # 制作公司或者独立制片人
    premiered: Optional[str] = None  # 发行日期
    runtime: Optional[int] = None  # 影片时长（分钟）
    tags: Optional[list[str]] = None  # 标签列表
    tags_normalized: Optional[list[str]] = None  # 标准化标签列表
    rating: Optional[float] = None  # 评分
    genres: Optional[list[str]] = None  # 类型列表
    genres_normalized: Optional[list[str]] = None  # 标准化类型列表
    mpaa: Optional[str] = None  # 家长分级（如 PG-13, R 等）
    serial: Optional[str] = None  # 系列名称
    year: Optional[int] = None  # 发行年份
    trailer: Optional[str] = None  # 预告片链接

    def append_extra_fields(self, nfo: _Element) -> None:
        d = self  # 简化引用
        # 添加可选信息
        if d.tagline:
            nfo.append(E.tagline(d.tagline))

        if d.original_title:
            nfo.append(E.originaltitle(d.original_title))

        if d.plot:
            nfo.append(E.plot(d.plot))

        if d.tagline:
            nfo.append(E.tagline(d.tagline))

        if d.rating:
            nfo.append(E.rating(str(d.rating)))

        if d.premiered:
            nfo.append(E.premiered(d.premiered))

        if d.year:
            nfo.append(E.year(str(d.year)))
        elif d.premiered:
            # 如果没有年份但有发行日期，则从日期中提取年份
            try:
                d.year = datetime.strptime(d.premiered, "%Y-%m-%d").year
                nfo.append(E.year(str(d.year)))
            except ValueError:
                pass

        if d.runtime:
            nfo.append(E.runtime(str(d.runtime)))

        if d.mpaa:
            nfo.append(E.mpaa(d.mpaa))

        if d.director:
            nfo.append(E.director(d.director))

        if d.studio:
            nfo.append(E.studio(d.studio))

        if d.url:
            nfo.append(E.url(d.url))

        if d.serial:
            nfo.append(E.set(E.name(d.serial)))

        if d.trailer:
            nfo.append(E.trailer(d.trailer))

        # 添加多值字段
        # 优先使用标准化字段
        genres = d.genres_normalized if d.genres_normalized else d.genres if d.genres else []
        # 去重
        genres = list(set(genres))
        for genre in genres:
            nfo.append(E.genre(genre))

        tags = d.tags_normalized if d.tags_normalized else d.tags if d.tags else []
        # 去重
        tags = list(set(tags))
        for tag in tags:
            nfo.append(E.tag(tag))

        actors = d.actors_normalized if d.actors_normalized else d.actors if d.actors else []
        # 去重
        actors = list(set(actors))
        for actor in actors:
            nfo.append(E.actor(E.name(actor), E.type("Actor")))


class TVShowMetadata(BaseMetadata):
    def __init__(self, **data):
        super().__init__(type=MetadataType.TV_SHOW, **data)

    def append_extra_fields(self, nfo: _Element) -> None:
        """
        添加 TVShow 特有的元数据字段到 NFO 中
        需要在子类中实现具体的转换逻辑
        """
        pass


class AnimeMetadata(BaseMetadata):
    """
    动漫元数据模型
    包含动漫特有的元数据字段
    """

    def __init__(self, **data):
        super().__init__(type=MetadataType.ANIME, **data)

    def append_extra_fields(self, nfo: _Element) -> None:
        """
        添加 Anime 特有的元数据字段到 NFO 中
        需要在子类中实现具体的转换逻辑
        """
        pass


class DocumentaryMetadata(BaseMetadata):
    """
    纪录片元数据模型
    包含纪录片特有的元数据字段
    """

    def __init__(self, **data):
        super().__init__(type=MetadataType.DOCUMENTARY, **data)

    def append_extra_fields(self, nfo: _Element) -> None:
        """
        添加 Documentary 特有的元数据字段到 NFO 中
        需要在子类中实现具体的转换逻辑
        """
        pass


class MusicMetadata(BaseMetadata):
    """
    音乐元数据模型
    包含音乐特有的元数据字段
    """

    def __init__(self, **data):
        super().__init__(type=MetadataType.MUSIC, **data)

    def append_extra_fields(self, nfo: _Element) -> None:
        """
        添加 Music 特有的元数据字段到 NFO 中
        需要在子类中实现具体的转换逻辑
        """
        pass


class ClipMetadata(BaseMetadata):
    """
    剪辑元数据模型
    包含剪辑特有的元数据字段
    """

    def __init__(self, **data):
        super().__init__(type=MetadataType.CLIP, **data)

    def append_extra_fields(self, nfo: _Element) -> None:
        """
        添加 Clip 特有的元数据字段到 NFO 中
        需要在子类中实现具体的转换逻辑
        """
        pass


__all__ = [
    "BaseMetadata",
    "MovieMetadata",
    "TVShowMetadata",
    "AnimeMetadata",
    "DocumentaryMetadata",
    "MusicMetadata",
    "ClipMetadata",
]

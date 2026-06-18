"""
复合型元数据提取器 (CompositeMetadata) 测试

使用伪造的 provider 验证组合与合并逻辑，不依赖网络。
"""

from typing import List, Optional

from pavone.models import BaseMetadata, MovieMetadata
from pavone.plugins.metadata.base import MetadataPlugin
from pavone.plugins.metadata.composite import CompositeMetadata
from pavone.utils.metadata_builder import MetadataBuilder


class _FakeProvider(MetadataPlugin):
    """可控的伪 provider：根据预设决定能否处理及返回的元数据。"""

    def __init__(self, name: str, handles: bool, metadata: Optional[BaseMetadata], priority: int = 50):
        super().__init__(name=name, priority=priority)
        self._handles = handles
        self._metadata = metadata
        self.called = False

    def can_extract(self, identifier: str) -> bool:
        return self._handles

    def extract_metadata(self, identifier: str) -> Optional[BaseMetadata]:
        self.called = True
        return self._metadata


def _make_metadata(
    code: str,
    title: str = "标题",
    studio: Optional[str] = None,
    actors: Optional[List[str]] = None,
    runtime: Optional[int] = None,
    plot: Optional[str] = None,
    cover: Optional[str] = None,
) -> MovieMetadata:
    builder = MetadataBuilder().set_title(title, code)
    builder.set_identifier("SITE", code, f"https://example.com/{code}")
    builder.set_studio(studio)
    builder.set_actors(actors)
    builder.set_runtime(runtime)
    builder.set_plot(plot)
    builder.set_cover(cover)
    return builder.build()


class TestCompositeMetadata:
    # ===================== can_extract =====================

    def test_can_extract_any_member(self):
        p1 = _FakeProvider("p1", handles=False, metadata=None)
        p2 = _FakeProvider("p2", handles=True, metadata=None)
        composite = CompositeMetadata(providers=[p1, p2])
        assert composite.can_extract("CODE-1") is True

    def test_cannot_extract_when_no_member(self):
        p1 = _FakeProvider("p1", handles=False, metadata=None)
        composite = CompositeMetadata(providers=[p1])
        assert composite.can_extract("CODE-1") is False

    def test_empty_composite_cannot_extract(self):
        """无参构造（自动加载场景）得到空壳，恒不可处理。"""
        composite = CompositeMetadata()
        assert composite.can_extract("CODE-1") is False

    # ===================== extract_metadata / merge =====================

    def test_only_handling_providers_called(self):
        m = _make_metadata("CODE-1", studio="工作室A")
        p1 = _FakeProvider("p1", handles=False, metadata=None)
        p2 = _FakeProvider("p2", handles=True, metadata=m)
        composite = CompositeMetadata(providers=[p1, p2])

        result = composite.extract_metadata("CODE-1")
        assert result is not None
        assert p1.called is False
        assert p2.called is True

    def test_returns_none_when_all_fail(self):
        p1 = _FakeProvider("p1", handles=True, metadata=None)
        composite = CompositeMetadata(providers=[p1])
        assert composite.extract_metadata("CODE-1") is None

    def test_merge_fills_missing_fields(self):
        # 主结果有 studio 但缺 actors/runtime；次结果补齐
        primary = _make_metadata("CODE-1", title="主标题", studio="工作室A")
        secondary = _make_metadata("CODE-1", title="次标题", actors=["演员X"], runtime=120)
        p1 = _FakeProvider("p1", handles=True, metadata=primary)
        p2 = _FakeProvider("p2", handles=True, metadata=secondary)
        composite = CompositeMetadata(providers=[p1, p2])

        result = composite.extract_metadata("CODE-1")
        assert isinstance(result, MovieMetadata)
        # 标识/标题字段来自主结果，不被覆盖
        assert result.title == "CODE-1 主标题"
        # 主结果已有的字段保留
        assert result.studio == "工作室A"
        # 缺失字段由次结果填充
        assert result.actors == ["演员X"]
        assert result.runtime == 120

    def test_merge_does_not_override_existing_fields(self):
        primary = _make_metadata("CODE-1", studio="工作室A", runtime=90)
        secondary = _make_metadata("CODE-1", studio="工作室B", runtime=120)
        p1 = _FakeProvider("p1", handles=True, metadata=primary)
        p2 = _FakeProvider("p2", handles=True, metadata=secondary)
        composite = CompositeMetadata(providers=[p1, p2])

        result = composite.extract_metadata("CODE-1")
        assert isinstance(result, MovieMetadata)
        # 第一个非空值胜出（主结果优先）
        assert result.studio == "工作室A"
        assert result.runtime == 90

    def test_single_result_passthrough(self):
        m = _make_metadata("CODE-1", studio="工作室A")
        p1 = _FakeProvider("p1", handles=True, metadata=m)
        composite = CompositeMetadata(providers=[p1])

        result = composite.extract_metadata("CODE-1")
        assert result is m

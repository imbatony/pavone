"""
复合型元数据提取器插件

``CompositeMetadata`` 将多个 ``MetadataPlugin`` 组合为一个提取器：
- 构造时显式传入一组 provider（按传入顺序代表优先级）。
- ``can_extract``: 任一成员能处理该 identifier 即返回 True。
- ``extract_metadata``: 依次调用所有能处理的成员，收集各自的 ``MovieMetadata``，
  再通过 ``_merge`` 合并为单个结果。

合并策略目前为「按 provider 顺序填充缺失字段」（第一个非空字段胜出）。
多 provider 的具体字段取舍规则待后续明确，``_merge`` 方法被刻意独立出来以便替换。

注意: 该插件需要显式构造（传入 providers）。若被插件管理器以无参方式自动实例化，
将得到一个空壳（``providers`` 为空），其 ``can_extract`` 恒为 False，不参与任何提取流程。
"""

from typing import List, Optional, cast

from ...models import BaseMetadata, MovieMetadata
from .base import MetadataPlugin

PLUGIN_NAME = "CompositeMetadata"
PLUGIN_VERSION = "1.0.0"
PLUGIN_DESCRIPTION = "组合多个元数据提取器并合并其结果"
PLUGIN_AUTHOR = "PAVOne"
PLUGIN_PRIORITY = 50

# 合并时由「主结果」决定、不参与跨 provider 覆盖的必填/标识字段
_IDENTITY_FIELDS = {"identifier", "title", "url", "site", "code", "type"}


class CompositeMetadata(MetadataPlugin):
    """复合型元数据提取器：组合多个 provider 并合并结果。"""

    def __init__(
        self,
        providers: Optional[List[MetadataPlugin]] = None,
        name: str = PLUGIN_NAME,
        priority: int = PLUGIN_PRIORITY,
    ):
        super().__init__(
            name=name,
            version=PLUGIN_VERSION,
            description=PLUGIN_DESCRIPTION,
            author=PLUGIN_AUTHOR,
            priority=priority,
        )
        self.providers: List[MetadataPlugin] = providers or []

    def can_extract(self, identifier: str) -> bool:
        """任一成员 provider 能处理该 identifier 即可。"""
        return any(p.can_extract(identifier) for p in self.providers)

    def extract_metadata(self, identifier: str) -> Optional[BaseMetadata]:
        """依次调用所有能处理的 provider，收集结果并合并。"""
        results: List[MovieMetadata] = []
        for provider in self.providers:
            if not provider.can_extract(identifier):
                continue
            try:
                metadata = provider.extract_metadata(identifier)
            except Exception as e:
                self.logger.warning(f"成员 {provider.name} 提取失败 ({identifier}): {e}")
                continue
            if metadata:
                self.logger.info(f"成员 {provider.name} 提取成功: {identifier}")
                results.append(cast(MovieMetadata, metadata))

        if not results:
            self.logger.warning(f"所有成员均未提取到元数据: {identifier}")
            return None

        return self._merge(results)

    def _merge(self, results: List[MovieMetadata]) -> MovieMetadata:
        """合并多个 provider 的元数据结果。

        当前策略: 以第一个结果为「主结果」，其标识字段（番号、URL、站点等）保持不变；
        其余可选字段按 provider 顺序填充——某字段为空时，采用后续 provider 中第一个非空值。

        TODO: 多 provider 的字段取舍规则待明确后在此调整。
        """
        if len(results) == 1:
            return results[0]

        merged = results[0]
        merged_data = merged.model_dump()

        for other in results[1:]:
            other_data = other.model_dump()
            for field, value in other_data.items():
                if field in _IDENTITY_FIELDS:
                    continue
                if self._is_empty(merged_data.get(field)) and not self._is_empty(value):
                    merged_data[field] = value

        # MovieMetadata.__init__ 会自行注入 type，需移除避免重复关键字参数
        merged_data.pop("type", None)
        return MovieMetadata(**merged_data)

    @staticmethod
    def _is_empty(value: object) -> bool:
        """判断字段值是否为「空」（None / 空字符串 / 空列表 / 0）。"""
        if value is None:
            return True
        if isinstance(value, str):
            return value.strip() == ""
        if isinstance(value, (list, tuple, dict)):
            return not value
        if isinstance(value, (int, float)):
            return value == 0
        return False

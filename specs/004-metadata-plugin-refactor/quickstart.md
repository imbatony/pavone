# 快速开始: 元数据插件架构重构

**功能**: 004-metadata-plugin-refactor | **日期**: 2025-07-18

## 前提条件

```bash
# 确保在功能分支
git checkout 004-metadata-plugin-refactor

# 安装依赖
uv sync

# 确认当前测试全部通过
uv run pytest tests/ -v -m "not integration"
```

## 阶段一: 创建基类

### 步骤 1: 在 base.py 中新增 HtmlMetadataPlugin

在 `pavone/plugins/metadata/base.py` 中，在 `MetadataPlugin` 类之后新增 `HtmlMetadataPlugin`:

```python
# 新增导入
import json
import re
from abc import abstractmethod
from typing import Any, Dict, Optional, Tuple
from urllib.parse import urlparse

import requests
from bs4 import BeautifulSoup

class HtmlMetadataPlugin(MetadataPlugin):
    """HTML 解析类元数据插件的公共基类。"""

    def extract_metadata(self, identifier: str) -> Optional[BaseMetadata]:
        # 模板方法: resolve → fetch → parse
        ...

    def _fetch_page(self, url: str) -> requests.Response:
        return self.fetch(url, timeout=30)

    @abstractmethod
    def _resolve(self, identifier: str) -> Tuple[Optional[str], Optional[str]]:
        ...

    @abstractmethod
    def _parse(self, soup: BeautifulSoup, movie_id: str, page_url: str) -> Optional[BaseMetadata]:
        ...

    # 静态工具方法: _abs, _parse_runtime, _parse_date, _parse_iso_duration, _get_tag_attr
```

### 步骤 2: 新增 ApiMetadataPlugin 和 JsonLdMetadataPlugin

同文件中继续新增。详见 `plan.md` 阶段一设计。

### 步骤 3: 修改 FC2BaseMetadata

在 `pavone/plugins/metadata/fc2_base.py` 中:

```python
# 修改前:
from .base import MetadataPlugin
class FC2BaseMetadata(MetadataPlugin):

# 修改后:
from .base import HtmlMetadataPlugin
class FC2BaseMetadata(HtmlMetadataPlugin):
```

### 步骤 4: 验证基类

```bash
# 确认基类定义无语法错误
uv run python -c "from pavone.plugins.metadata.base import HtmlMetadataPlugin, ApiMetadataPlugin, JsonLdMetadataPlugin; print('OK')"

# 确认 FC2BaseMetadata 继承链
uv run python -c "from pavone.plugins.metadata.fc2_base import FC2BaseMetadata; print(FC2BaseMetadata.__mro__)"

# 类型检查
uv run pyright pavone/plugins/metadata/base.py

# 全量测试 (基类新增不应破坏任何现有测试)
uv run pytest tests/ -v -m "not integration"
```

## 阶段二: 分批迁移

### 迁移单个插件 (以 dahlia 为例)

**1. 修改导入和继承:**

```python
# 修改前:
from .base import MetadataPlugin
class DahliaMetadata(MetadataPlugin):

# 修改后:
from .base import HtmlMetadataPlugin
class DahliaMetadata(HtmlMetadataPlugin):
```

**2. 删除 extract_metadata 模板方法** (基类已提供)

**3. 添加 _fetch_page 覆写** (如有自定义 HTTP 逻辑):

```python
def _fetch_page(self, url: str) -> requests.Response:
    return self.fetch(url, headers={"Cookie": "modal=off"}, timeout=30)
```

**4. 删除重复的工具方法:**
- 删除 `_abs` (基类已提供)
- 删除 `_parse_runtime` (基类已提供)
- 删除 `_parse_date` (基类已提供)

**5. 保留核心方法:**
- `can_extract` — 保留不变
- `_resolve` — 保留不变
- `_parse` — 保留不变

**6. 验证:**

```bash
# 单插件测试
uv run pytest tests/metadata/test_dahlia.py -v

# 全量回归
uv run pytest tests/ -v -m "not integration"

# 类型检查
uv run pyright pavone/plugins/metadata/dahlia_metadata.py
```

### 每批次完成后

```bash
# 全量测试
uv run pytest tests/ -v -m "not integration"

# 格式检查
uv run black --check pavone/plugins/metadata/
uv run isort --check-only pavone/plugins/metadata/

# 类型检查
uv run pyright pavone/plugins/metadata/

# 提交
git add pavone/plugins/metadata/
git commit -m "refactor: batch N - migrate X plugins to HtmlMetadataPlugin"
```

## 常见问题

### Q: 迁移后 `resp.text` vs `resp.content` 报错？

A: 基类模板使用 `resp.text`。如果原插件使用 `resp.content` 传入 BeautifulSoup，需修改为 `resp.text` 或在 `_fetch_page` 中返回适配。

### Q: 某插件的 `_parse_runtime` 与基类行为不同？

A: 基类使用超集策略覆盖所有已知格式。如有未覆盖的格式，在该插件中覆写 `_parse_runtime`。

### Q: ppvdatabank 的多重继承怎么处理？

A: `PpvDataBankMetadata(FC2BaseMetadata, SearchPlugin)` 保持不变。FC2BaseMetadata 改继承 HtmlMetadataPlugin 后，MRO 自动调整，SearchPlugin 不受影响。

### Q: 特殊插件 (fanza/avbase) 如何迁移？

A: 根据 FR-018，评估后决定：如果迁移使代码更简洁则迁移并覆写 `extract_metadata`；否则保留直接继承 `MetadataPlugin`。

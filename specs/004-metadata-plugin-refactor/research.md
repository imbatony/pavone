# 研究报告: 元数据插件架构重构

**功能**: 004-metadata-plugin-refactor | **日期**: 2025-07-18

## 研究 1: 公共工具方法变体分析与超集策略

### `_abs` 方法 (16 份实现)

**Decision**: 所有 16 份实现逻辑一致，采用统一版本，无需变体合并。

**Rationale**: 代码审查确认所有 16 份实现（aventertainments, dahlia, duga, faleno, gcolle, getchu, heydouga, heyzo, jav321, javbus, kin8tengoku, mgstage, mywife, pcolle, sod, tokyohot）逻辑完全相同：
```python
if url.startswith("http"): return url
parsed = urlparse(base)
if url.startswith("//"): return f"{parsed.scheme}:{url}"
return f"{parsed.scheme}://{parsed.netloc}{url}"
```

**Alternatives considered**: 使用 `urllib.parse.urljoin` 标准库替代。排除原因：`urljoin` 在处理 `//` 前缀 URL 时行为不同，可能引入行为变化。

### `_parse_runtime` 方法 (14 份实现, 3 种变体)

**Decision**: 采用超集策略，合并 3 种变体为一个方法，按优先级匹配：日文分 → 英文 Min → HH:MM(:SS)。

**Rationale**: 三种变体互不冲突（不同的正则模式匹配不同格式的输入文本）：
- **变体 1** (8 个插件): 仅匹配 `(\d+)\s*分`
- **变体 2** (5 个插件): 匹配 `(\d+)\s*分` + `(\d+):(\d+)` (HH:MM)
- **变体 3** (1 个插件 aventertainments): 额外支持 `Apx. 122 Min.`

超集合并后，任何格式的输入只会匹配一种模式，不会产生歧义。例如 "120分" 只匹配变体 1 的正则，"1:30" 只匹配变体 2 的正则。

**Alternatives considered**:
1. 保持各插件独立实现 — 排除原因：违背重构核心目标。
2. 基类提供可组合的解析函数 — 排除原因：增加复杂度但无额外收益。

### `_parse_date` 方法 (23 份实现, 3 种变体)

**Decision**: 采用单一正则 `(\d{4})[年/\-.](\d{1,2})[月/\-.](\d{1,2})` 统一所有变体。

**Rationale**: 三种变体本质上只是分隔符集合不同：
- **变体 1** (13 个插件): 匹配 `/`, `-`, `.` 分隔符
- **变体 2** (8 个插件): 额外匹配 `年`, `月` 日文分隔符
- **变体 3** (2 个插件): 更复杂的多格式处理

超集正则 `[年/\-.]` 覆盖所有分隔符变体，`\d{1,2}` 兼容有无前导零。

**Alternatives considered**: 使用 `dateutil.parser` — 排除原因：引入新依赖且行为不可预测。

### `_parse_iso_duration` 方法 (5 个插件共享)

**Decision**: 在基类中提供统一实现，供 JSON-LD 类插件使用。

**Rationale**: 5 个实现（c0930, h0930, h4610, fc2hub, heyzo）逻辑完全一致，解析 ISO 8601 duration `PT(\d+)H(\d+)M(\d+)S` 格式。

---

## 研究 2: 插件分类与迁移批次

### 分类统计

| 类别 | 插件数 | 占比 | 代表插件 |
|------|--------|------|---------|
| HTML 解析 | 20 | 58.8% | dahlia, sod, javbus |
| JSON-LD + HTML | 5 | 14.7% | c0930, h0930, heyzo |
| API/JSON | 6 | 17.6% | modelmediaasia, tenmusume |
| 混合/特殊 | 3 | 8.8% | fanza, avbase, caribbeancom |

### 迁移风险评估

**低风险** (23 个): 结构清晰、字段少、解析逻辑简单的插件。直接替换基类和删除重复方法。

**中风险** (8 个): 复杂 HTML 解析或 JSON-LD 插件。需要验证 JSON-LD 提取逻辑与基类兼容。

**高风险** (3 个): fanza (`__NEXT_DATA__` 多通道)、avbase (Next.js API)、caribbeancom (最大 HTML 解析器)。可能需要保留直接继承 MetadataPlugin 或大幅覆写基类方法。

---

## 研究 3: 模板方法模式最佳实践

### Python 模板方法模式实现

**Decision**: 使用 `@abstractmethod` 标记子类必须实现的方法，钩子方法提供默认实现。

**Rationale**: Python 的 `abc.ABC` + `@abstractmethod` 提供编译期（实例化时）契约检查。结合非抽象的钩子方法（如 `_fetch_page`），允许子类选择性覆写。

**实现要点**:
- `extract_metadata` 为模板方法，定义 resolve → fetch → parse 流程 + 统一 try/except
- `_resolve` 和 `_parse` 为 `@abstractmethod`，子类必须实现
- `_fetch_page` 为钩子方法，有默认实现（`self.fetch(url, timeout=30)`），子类可覆写
- `_abs`, `_parse_runtime`, `_parse_date` 为 `@staticmethod` 工具方法

### 自定义 _fetch_page 的插件清单

| 插件 | 自定义原因 | _fetch_page 覆写内容 |
|------|-----------|---------------------|
| dahlia, faleno | 年龄弹窗跳过 | `headers={"Cookie": "modal=off"}` |
| javbus | Cookie + Referer | `cookies={"existmag": "all"}, headers={"Referer": ...}` |
| mgstage | Cookie | 年龄确认 Cookie |
| pcolle | Cookie | 登录 Cookie |
| heydouga | Cookie | 年龄确认 Cookie |
| fanza | Cookie | `age_check_done=1` |

---

## 研究 4: JsonLdMetadataPlugin 继承设计

**Decision**: `JsonLdMetadataPlugin` 继承 `HtmlMetadataPlugin`（而非并列关系）。

**Rationale**: 所有 JSON-LD 插件的工作流程为：获取 HTML 页面 → 从 `<script type="application/ld+json">` 提取 JSON-LD → 用 JSON-LD 填充字段 → 用 HTML 作为 fallback。这是 HTML 解析的扩展（超集），不是独立流程。

**设计要点**:
- `JsonLdMetadataPlugin` 覆写 `extract_metadata` 模板方法，增加 JSON-LD 提取步骤
- 提供 `_extract_jsonld(soup)` 方法自动解析所有 `application/ld+json` 脚本标签
- 子类实现 `_parse_with_jsonld(soup, jsonld, movie_id, page_url)` 替代 `_parse`
- 保留 `_parse` 的兼容性（重定向到 `_parse_with_jsonld`）

**Alternatives considered**: 使用 Mixin 而非继承 — 排除原因：增加多重继承复杂度，且 JSON-LD 和 HTML 解析不是独立关注点。

---

## 研究 5: FC2BaseMetadata 继承链改造

**Decision**: `FC2BaseMetadata` 改为继承 `HtmlMetadataPlugin`。

**Rationale**: FC2 系列插件（fc2hub, fc2ppvdb, supfc2, ppvdatabank）的工作流程与标准 HTML 解析一致（resolve → fetch → parse），只是增加了 FC2 专属的 ID 提取和标准化逻辑。通过改变继承链，FC2 插件自动获得模板方法和工具方法。

**继承链变化**:
```
修改前: MetadataPlugin → FC2BaseMetadata → Fc2HubMetadata / SupFc2Metadata
修改后: MetadataPlugin → HtmlMetadataPlugin → FC2BaseMetadata → SupFc2Metadata / PpvDataBankMetadata
```

**注意**: fc2hub 使用 JSON-LD 解析，将改为继承 `JsonLdMetadataPlugin` 而非通过 FC2BaseMetadata。

**注意**: ppvdatabank 同时继承 `FC2BaseMetadata` 和 `SearchPlugin`（多重继承），需确保 MRO 不冲突。

---

## 研究 6: 测试兼容性验证策略

**Decision**: 利用现有 Mock 测试作为行为兼容性回归套件，无需额外快照机制。

**Rationale**: 30 个插件测试文件使用固定 HTML fixture（`tests/sites/*.html`）+ `unittest.mock.patch` 替换 `fetch` 方法。这些测试直接验证：给定固定 HTML 输入，`extract_metadata` 返回预期的元数据字段值。迁移后运行相同测试即可确认行为一致性。

**验证流程**:
1. 每个插件迁移后：`uv run pytest tests/metadata/test_<name>.py -v`
2. 每批迁移后：`uv run pytest tests/ -v -m "not integration"`
3. 全部迁移后：`uv run pytest tests/ -v`（含集成测试可选）

**测试覆盖**: 661 个测试函数，其中 231 个专属于元数据插件，每个插件 ~7-8 个测试用例。

# 任务: 元数据插件架构重构 (PAVOne v0.3.2)

**输入**: 来自 `/specs/004-metadata-plugin-refactor/` 的设计文档
**前置条件**: plan.md(必需), spec.md(必需), research.md, data-model.md, contracts/, quickstart.md

**测试**: 功能规范明确要求利用现有 Mock 测试验证行为兼容性（FR-015, SC-008, SC-009），每批迁移后运行全量测试。无需新增测试文件，仅验证现有测试无回归。

**组织结构**: 任务按用户故事分组。US1（新插件开发效率）和 US2（行为兼容性）通过基类创建和分批迁移交叉验证。US3（渐进式迁移）通过批次检查点保障。US4（维护效率）和 US5（灵活性保留）在迁移中自然实现。US6（类型安全）在基类中一次性交付。

## 格式: `[ID] [P?] [Story] 描述`
- **[P]**: 可以并行运行（不同文件, 无依赖关系）
- **[Story]**: 此任务属于哪个用户故事（US1/US2/US3/US4/US5/US6）
- 在描述中包含确切的文件路径

## 路径约定
- **源码**: `pavone/plugins/metadata/`（元数据插件目录）
- **基类**: `pavone/plugins/metadata/base.py`（MetadataPlugin + 新增中间基类）
- **FC2 基类**: `pavone/plugins/metadata/fc2_base.py`
- **测试**: `tests/metadata/`（30 个现有 Mock 单元测试文件）
- **HTML fixtures**: `tests/sites/`（33 个 HTML fixture 文件）

---

## 阶段 1: 设置

**目的**: 确认当前代码库状态，建立基准线，确保重构起点健康

- [X] T001 运行 `uv run pytest tests/ -v -m "not integration"` 确认所有现有测试通过，记录当前测试数量作为基准线（预期 661 个测试函数）
- [X] T002 运行 `uv run pyright pavone/plugins/metadata/` 确认现有代码类型检查通过，记录当前警告数量作为基准线

---

## 阶段 2: 基础（阻塞前置条件）

**目的**: 创建三个中间基类和公共工具方法，这是所有插件迁移的前提

**⚠️ 关键**: 在此阶段确认通过后，方可开始阶段 3+ 的分批迁移

### 基类创建

- [X] T003 [US1] 在 `pavone/plugins/metadata/base.py` 中新增 `HtmlMetadataPlugin` 类，继承 `MetadataPlugin`，实现 `extract_metadata` 模板方法（resolve → fetch → parse 流程 + 统一 try/except 错误处理），定义 `_fetch_page` 钩子方法（默认 `self.fetch(url, timeout=30)`），声明 `_resolve` 和 `_parse` 为 `@abstractmethod`。参考 `contracts/html-metadata-plugin.md` 合同定义和 `plan.md` 1.2 节代码设计
- [X] T004 [US1] 在 `pavone/plugins/metadata/base.py` 中新增公共静态工具方法：`_abs`（相对 URL 转绝对 URL，统一 16 份实现），`_parse_runtime`（超集合并 3 种变体：日文分 → 英文 Min → HH:MM:SS），`_parse_date`（超集正则 `[年/\-.]` 统一 3 种分隔符变体），`_parse_iso_duration`（ISO 8601 PT 格式解析）。方法签名和实现参考 `plan.md` 1.2 节和 `research.md` 研究 1
- [X] T005 [US6] 在 `pavone/plugins/metadata/base.py` 的 `HtmlMetadataPlugin` 中新增 `_get_tag_attr(tag: Optional[Any], attr: str) -> Optional[str]` 静态方法，安全获取 BeautifulSoup 标签属性，消除 `_AttributeValue` 类型问题。实现参考 `plan.md` 1.2 节
- [X] T006 [US1] 在 `pavone/plugins/metadata/base.py` 中新增 `ApiMetadataPlugin` 类，继承 `MetadataPlugin`（非 `HtmlMetadataPlugin`），实现 `extract_metadata` 模板方法（resolve → build_api_url → fetch_api → json → parse 流程 + 统一错误处理），定义 `_fetch_api` 钩子方法，声明 `_build_api_url`、`_resolve`、`_parse` 为 `@abstractmethod`。参考 `contracts/api-metadata-plugin.md` 合同定义和 `plan.md` 1.3 节代码设计
- [X] T007 [US1] 在 `pavone/plugins/metadata/base.py` 中新增 `JsonLdMetadataPlugin` 类，继承 `HtmlMetadataPlugin`，覆写 `extract_metadata` 模板方法增加 JSON-LD 提取步骤（resolve → fetch → BS4 → extract_jsonld → parse_with_jsonld），实现 `_extract_jsonld(soup)` 方法解析 `<script type="application/ld+json">` 标签，声明 `_parse_with_jsonld` 为 `@abstractmethod`，提供 `_parse` 兼容重定向。参考 `contracts/jsonld-metadata-plugin.md` 合同定义和 `plan.md` 1.4 节代码设计

### 基类验证

- [X] T008 运行 `uv run python -c "from pavone.plugins.metadata.base import HtmlMetadataPlugin, ApiMetadataPlugin, JsonLdMetadataPlugin; print('OK')"` 确认基类定义无语法错误且可正常导入
- [X] T009 运行 `uv run pyright pavone/plugins/metadata/base.py` 确认新增基类通过类型检查，无新增错误
- [X] T010 运行 `uv run pytest tests/ -v -m "not integration"` 确认新增基类不影响任何现有测试（全量通过，测试数量不变）

**检查点**: 三个中间基类创建完成，通过导入验证、类型检查和全量测试 ✅

---

## 阶段 3: 用户故事 1+2+3 — 批次 1：基础验证迁移（优先级: P1）🎯 MVP

**目标**: 迁移最简单的 4 个插件（dahlia, faleno, mywife → HtmlMetadataPlugin; tenmusume → ApiMetadataPlugin），验证两个基类的正确性

**独立测试**: 运行 `uv run pytest tests/metadata/test_dahlia.py tests/metadata/test_faleno.py tests/metadata/test_mywife.py tests/metadata/test_tenmusume.py -v` 确认 4 个插件测试全部通过，再运行全量测试确认无回归

### 批次 1 实施

- [X] T011 [P] [US2] 迁移 `pavone/plugins/metadata/dahlia_metadata.py`：改继承 `HtmlMetadataPlugin`，删除本地 `extract_metadata` 模板（~16 行）、`_abs`（~5 行）、`_parse_runtime`（~7 行）、`_parse_date`（~4 行），新增 `_fetch_page` 覆写设置 `headers={"Cookie": "modal=off"}`，保留 `can_extract`、`_resolve`、`_parse` 不变
- [X] T012 [P] [US2] 迁移 `pavone/plugins/metadata/faleno_metadata.py`：改继承 `HtmlMetadataPlugin`，删除本地 `extract_metadata`、`_abs`、`_parse_runtime`、`_parse_date`，新增 `_fetch_page` 覆写设置 `headers={"Cookie": "modal=off"}`，保留核心方法不变
- [X] T013 [P] [US2] 迁移 `pavone/plugins/metadata/mywife_metadata.py`：改继承 `HtmlMetadataPlugin`，删除本地 `extract_metadata`、`_abs`，保留核心方法不变（无自定义 fetch）
- [X] T014 [P] [US2] 迁移 `pavone/plugins/metadata/tenmusume_metadata.py`：改继承 `ApiMetadataPlugin`，删除本地 `extract_metadata` 模板，适配 `_build_api_url`、`_resolve`、`_parse` 抽象方法签名，保留核心解析逻辑不变

### 批次 1 验证

- [X] T015 [US3] 运行 `uv run pytest tests/metadata/test_dahlia.py tests/metadata/test_faleno.py tests/metadata/test_mywife.py tests/metadata/test_tenmusume.py -v` 确认批次 1 的 4 个插件测试全部通过
- [X] T016 [US3] 运行 `uv run pytest tests/ -v -m "not integration"` 确认全量测试通过（包括已迁移和未迁移的插件），运行 `uv run pyright pavone/plugins/metadata/dahlia_metadata.py pavone/plugins/metadata/faleno_metadata.py pavone/plugins/metadata/mywife_metadata.py pavone/plugins/metadata/tenmusume_metadata.py` 确认类型检查通过

**检查点**: 批次 1 完成 — HtmlMetadataPlugin 和 ApiMetadataPlugin 基类验证通过，4 个插件迁移成功 ✅

---

## 阶段 4: 用户故事 2+3 — 批次 2：标准 HTML 插件迁移（优先级: P1）

**目标**: 迁移 5 个标准 HTML 解析插件（sod, mgstage, getchu, kin8tengoku, madouqu）至 HtmlMetadataPlugin

**独立测试**: 运行对应 5 个插件测试 + 全量回归

### 批次 2 实施

- [X] T017 [P] [US2] 迁移 `pavone/plugins/metadata/sod_metadata.py`：改继承 `HtmlMetadataPlugin`，删除本地 `extract_metadata`、`_abs`、`_parse_runtime`、`_parse_date`，保留 `can_extract`、`_resolve`、`_parse` 不变
- [X] T018 [P] [US2] 迁移 `pavone/plugins/metadata/mgstage_metadata.py`：改继承 `HtmlMetadataPlugin`，删除本地 `extract_metadata`、`_abs`、`_parse_runtime`、`_parse_date`，新增 `_fetch_page` 覆写设置年龄确认 Cookie，保留核心方法不变
- [X] T019 [P] [US2] 迁移 `pavone/plugins/metadata/getchu_metadata.py`：改继承 `HtmlMetadataPlugin`，删除本地 `extract_metadata`、`_abs`、`_parse_date`，保留核心方法不变
- [X] T020 [P] [US2] 迁移 `pavone/plugins/metadata/kin8tengoku_metadata.py`：改继承 `HtmlMetadataPlugin`，删除本地 `extract_metadata`、`_abs`、`_parse_runtime`、`_parse_date`，保留核心方法不变
- [X] T021 [P] [US2] 迁移 `pavone/plugins/metadata/madouqu_metadata.py`：改继承 `HtmlMetadataPlugin`，删除本地 `extract_metadata`、`_parse_date`，保留核心方法不变

### 批次 2 验证

- [X] T022 [US3] 运行 `uv run pytest tests/metadata/test_sod.py tests/metadata/test_mgstage.py tests/metadata/test_getchu.py tests/metadata/test_kin8tengoku.py tests/metadata/test_madouqu.py -v` 确认批次 2 的 5 个插件测试全部通过
- [X] T023 [US3] 运行 `uv run pytest tests/ -v -m "not integration"` 确认全量测试通过，运行 `uv run pyright pavone/plugins/metadata/sod_metadata.py pavone/plugins/metadata/mgstage_metadata.py pavone/plugins/metadata/getchu_metadata.py pavone/plugins/metadata/kin8tengoku_metadata.py pavone/plugins/metadata/madouqu_metadata.py` 确认类型检查通过

**检查点**: 批次 2 完成 — 累计 9 个插件已迁移，全量测试通过 ✅

---

## 阶段 5: 用户故事 2+3 — 批次 3：API/JSON 插件迁移（优先级: P1）

**目标**: 迁移 5 个 API/JSON 型插件（modelmediaasia, muramura, pacopacomama, onepondo, theporndb）至 ApiMetadataPlugin

**独立测试**: 运行对应 5 个插件测试 + 全量回归

### 批次 3 实施

- [X] T024 [P] [US2] 迁移 `pavone/plugins/metadata/modelmediaasia_metadata.py`：改继承 `ApiMetadataPlugin`，删除本地 `extract_metadata` 模板，适配抽象方法签名，如有 Referer header 需求则覆写 `_fetch_api`，保留核心解析逻辑不变
- [X] T025 [P] [US2] 迁移 `pavone/plugins/metadata/muramura_metadata.py`：改继承 `ApiMetadataPlugin`，删除本地 `extract_metadata`，如有 Content-Type header 需求则覆写 `_fetch_api`，保留核心方法不变
- [X] T026 [P] [US2] 迁移 `pavone/plugins/metadata/pacopacomama_metadata.py`：改继承 `ApiMetadataPlugin`，删除本地 `extract_metadata`，适配抽象方法签名，保留核心方法不变
- [X] T027 [P] [US2] 迁移 `pavone/plugins/metadata/onepondo_metadata.py`：改继承 `ApiMetadataPlugin`，删除本地 `extract_metadata`，适配抽象方法签名，保留核心方法不变
- [X] T028 [P] [US2] 迁移 `pavone/plugins/metadata/theporndb_metadata.py`：改继承 `ApiMetadataPlugin`，删除本地 `extract_metadata`，覆写 `_fetch_api` 添加 Bearer token auth header，保留核心方法不变

### 批次 3 验证

- [X] T029 [US3] 运行 `uv run pytest tests/metadata/test_modelmediaasia.py tests/metadata/test_muramura.py tests/metadata/test_pacopacomama.py tests/metadata/test_onepondo.py tests/metadata/test_theporndb.py -v` 确认批次 3 的 5 个插件测试全部通过
- [X] T030 [US3] 运行 `uv run pytest tests/ -v -m "not integration"` 确认全量测试通过，运行 `uv run pyright` 对已迁移的 API 插件进行类型检查

**检查点**: 批次 3 完成 — ApiMetadataPlugin 基类全面验证，累计 14 个插件已迁移 ✅

---

## 阶段 6: 用户故事 2+3 — 批次 4：JSON-LD 插件迁移（优先级: P1）

**目标**: 迁移 5 个 JSON-LD 型插件（c0930, h0930, h4610, fc2hub, heyzo）至 JsonLdMetadataPlugin，验证 JSON-LD 基类的正确性

**独立测试**: 运行对应 5 个插件测试 + 全量回归

### 批次 4 实施

- [X] T031 [P] [US2] 迁移 `pavone/plugins/metadata/c0930_metadata.py`：改继承 `JsonLdMetadataPlugin`，删除本地 `extract_metadata` 模板和 JSON-LD 提取逻辑、`_parse_iso_duration`、`_parse_date`，将 `_parse` 重构为 `_parse_with_jsonld(soup, jsonld, movie_id, page_url)` 签名，保留核心解析逻辑不变
- [X] T032 [P] [US2] 迁移 `pavone/plugins/metadata/h0930_metadata.py`：改继承 `JsonLdMetadataPlugin`，删除本地 `extract_metadata`、JSON-LD 提取逻辑、`_parse_iso_duration`，重构为 `_parse_with_jsonld` 签名，保留核心方法不变
- [X] T033 [P] [US2] 迁移 `pavone/plugins/metadata/h4610_metadata.py`：改继承 `JsonLdMetadataPlugin`，删除本地 `extract_metadata`、JSON-LD 提取逻辑、`_parse_iso_duration`，重构为 `_parse_with_jsonld` 签名，保留核心方法不变
- [X] T034 [P] [US2] 迁移 `pavone/plugins/metadata/fc2hub_metadata.py`：改继承 `JsonLdMetadataPlugin`（注意：从 FC2BaseMetadata 改为直接继承 JsonLdMetadataPlugin，参考 research.md 研究 5），删除本地 JSON-LD 提取逻辑、`_parse_iso_duration`、`_parse_date`，重构为 `_parse_with_jsonld` 签名
- [X] T035 [P] [US2] 迁移 `pavone/plugins/metadata/heyzo_metadata.py`：改继承 `JsonLdMetadataPlugin`，删除本地 `extract_metadata`、JSON-LD 提取逻辑、`_parse_iso_duration`、`_parse_date`，重构为 `_parse_with_jsonld` 签名，保留核心方法不变

### 批次 4 验证

- [X] T036 [US3] 运行 `uv run pytest tests/metadata/test_c0930.py tests/metadata/test_h0930.py tests/metadata/test_h4610.py tests/metadata/test_fc2hub.py tests/metadata/test_heyzo.py -v` 确认批次 4 的 5 个插件测试全部通过
- [X] T037 [US3] 运行 `uv run pytest tests/ -v -m "not integration"` 确认全量测试通过，运行 `uv run pyright` 对已迁移的 JSON-LD 插件进行类型检查

**检查点**: 批次 4 完成 — JsonLdMetadataPlugin 基类全面验证，累计 19 个插件已迁移 ✅

---

## 阶段 7: 用户故事 2+3 — 批次 5：复杂 HTML 插件迁移（优先级: P1）

**目标**: 迁移 5 个复杂 HTML 解析插件（duga, jav321, javbus, tokyohot, heydouga）至 HtmlMetadataPlugin

**独立测试**: 运行对应 5 个插件测试 + 全量回归

### 批次 5 实施

- [X] T038 [P] [US2] 迁移 `pavone/plugins/metadata/duga_metadata.py`：改继承 `HtmlMetadataPlugin`，删除本地 `extract_metadata`、`_abs`、`_parse_runtime`、`_parse_date`，保留 `can_extract`、`_resolve`、`_parse` 不变
- [X] T039 [P] [US2] 迁移 `pavone/plugins/metadata/jav321_metadata.py`：改继承 `HtmlMetadataPlugin`，删除本地 `extract_metadata`、`_abs`、`_parse_runtime`、`_parse_date`，保留核心方法不变
- [X] T040 [P] [US2] 迁移 `pavone/plugins/metadata/javbus_metadata.py`：改继承 `HtmlMetadataPlugin`，删除本地 `extract_metadata`、`_abs`、`_parse_runtime`、`_parse_date`，新增 `_fetch_page` 覆写设置 `cookies={"existmag": "all"}` 和 Referer header，保留核心方法不变
- [X] T041 [P] [US2] 迁移 `pavone/plugins/metadata/tokyohot_metadata.py`：改继承 `HtmlMetadataPlugin`，删除本地 `extract_metadata`、`_abs`、`_parse_runtime`、`_parse_date`，保留核心方法不变
- [X] T042 [P] [US2] 迁移 `pavone/plugins/metadata/heydouga_metadata.py`：改继承 `HtmlMetadataPlugin`，删除本地 `extract_metadata`、`_abs`、`_parse_runtime`、`_parse_date`，如有年龄确认 Cookie 需求则覆写 `_fetch_page`，保留核心方法不变

### 批次 5 验证

- [X] T043 [US3] 运行 `uv run pytest tests/metadata/test_duga.py tests/metadata/test_jav321.py tests/metadata/test_javbus.py tests/metadata/test_tokyohot.py tests/metadata/test_heydouga.py -v` 确认批次 5 的 5 个插件测试全部通过
- [X] T044 [US3] 运行 `uv run pytest tests/ -v -m "not integration"` 确认全量测试通过

**检查点**: 批次 5 完成 — 累计 24 个插件已迁移，全量测试通过 ✅

---

## 阶段 8: 用户故事 2+3 — 批次 6：中等 HTML 插件迁移（优先级: P1）

**目标**: 迁移 4 个中等复杂度 HTML 插件（aventertainments, gcolle, javfree, pcolle）至 HtmlMetadataPlugin

**独立测试**: 运行对应 4 个插件测试 + 全量回归

### 批次 6 实施

- [X] T045 [P] [US2] 迁移 `pavone/plugins/metadata/aventertainments_metadata.py`：改继承 `HtmlMetadataPlugin`，删除本地 `extract_metadata`、`_abs`、`_parse_date`，注意 `_parse_runtime` 含 `Apx. N Min.` 英文格式（基类超集已覆盖），保留核心方法不变
- [X] T046 [P] [US2] 迁移 `pavone/plugins/metadata/gcolle_metadata.py`：改继承 `HtmlMetadataPlugin`，删除本地 `extract_metadata`、`_abs`、`_parse_date`，保留核心方法不变
- [X] T047 [P] [US2] 迁移 `pavone/plugins/metadata/javfree_metadata.py`：改继承 `HtmlMetadataPlugin`，删除本地 `extract_metadata`、`_parse_date`，保留核心方法不变
- [X] T048 [P] [US2] 迁移 `pavone/plugins/metadata/pcolle_metadata.py`：改继承 `HtmlMetadataPlugin`，删除本地 `extract_metadata`、`_abs`、`_parse_date`，新增 `_fetch_page` 覆写设置登录 Cookie，保留核心方法不变

### 批次 6 验证

- [X] T049 [US3] 运行 `uv run pytest tests/metadata/test_aventertainments.py tests/metadata/test_gcolle.py tests/metadata/test_javfree.py tests/metadata/test_pcolle.py -v` 确认批次 6 的 4 个插件测试全部通过
- [X] T050 [US3] 运行 `uv run pytest tests/ -v -m "not integration"` 确认全量测试通过

**检查点**: 批次 6 完成 — 累计 28 个插件已迁移，全量测试通过 ✅

---

## 阶段 9: 用户故事 2+3+5 — 批次 7：FC2 家族迁移（优先级: P1）

**目标**: 修改 FC2BaseMetadata 继承链，迁移 FC2 家族 3 个插件（fc2ppvdb, supfc2, ppvdatabank）

**独立测试**: 运行 FC2 相关插件测试 + 全量回归

### 批次 7 实施

- [X] T051 [US2] 修改 `pavone/plugins/metadata/fc2_base.py`：将 `FC2BaseMetadata` 的基类从 `MetadataPlugin` 改为 `HtmlMetadataPlugin`（`from .base import HtmlMetadataPlugin`），保留所有 FC2 专属方法（`_extract_fc2_id`、`_build_fc2_code`、`_validate_fc2_identifier` 等）不变，确认 FC2BaseMetadata 自动获得模板方法和工具方法。参考 `plan.md` 1.5 节和 `research.md` 研究 5
- [X] T052 运行 `uv run python -c "from pavone.plugins.metadata.fc2_base import FC2BaseMetadata; print(FC2BaseMetadata.__mro__)"` 确认继承链正确：FC2BaseMetadata → HtmlMetadataPlugin → MetadataPlugin → BasePlugin
- [X] T053 [P] [US2] 迁移 `pavone/plugins/metadata/fc2ppvdb_metadata.py`：删除本地 `extract_metadata` 模板和重复的工具方法，如需 `verify_ssl=False` 则覆写 `_fetch_page`，保留核心方法不变
- [X] T054 [P] [US2] 迁移 `pavone/plugins/metadata/supfc2_metadata.py`：删除本地 `extract_metadata` 和重复方法，覆写 `_fetch_page` 设置 `verify_ssl=False` 和 `max_retry=2`，保留核心方法不变
- [X] T055 [P] [US5] 迁移 `pavone/plugins/metadata/ppvdatabank_metadata.py`：删除本地 `extract_metadata` 和重复方法，注意保持 `PpvDataBankMetadata(FC2BaseMetadata, SearchPlugin)` 多重继承不变，验证 MRO 无冲突，覆写 `_fetch_page` 如需要

### 批次 7 验证

- [X] T056 [US3] 运行 `uv run pytest tests/metadata/test_fc2ppvdb.py tests/metadata/test_supfc2.py tests/metadata/test_ppvdatabank.py -v` 确认批次 7 的 3 个 FC2 插件测试全部通过
- [X] T057 [US3] 运行 `uv run pytest tests/ -v -m "not integration"` 确认全量测试通过（特别注意 fc2hub 在批次 4 已迁移至 JsonLdMetadataPlugin，确认其仍正常工作）

**检查点**: 批次 7 完成 — FC2 家族迁移成功，MRO 无冲突，累计 31 个插件已迁移 ✅

---

## 阶段 10: 用户故事 2+3+5 — 批次 8：混合/特殊插件迁移（优先级: P1）

**目标**: 处理 3 个最复杂的特殊插件（caribbeancom, fanza, avbase），根据 FR-018 灵活性保留原则评估迁移策略

**独立测试**: 运行对应插件测试 + 全量回归

### 批次 8 实施

- [X] T058 [US2] 迁移 `pavone/plugins/metadata/caribbeancom_metadata.py`：改继承 `HtmlMetadataPlugin`，删除本地 `extract_metadata` 模板和重复的工具方法（`_abs`、`_parse_runtime`、`_parse_date`），保留核心 `_parse` 逻辑不变
- [X] T059 [US5] 评估 `pavone/plugins/metadata/fanza_metadata.py` 迁移策略：如果迁移至 `HtmlMetadataPlugin` 并覆写 `extract_metadata`（保留 `__NEXT_DATA__` + HTML + JSON-LD 多通道逻辑）能使代码更简洁则迁移，否则保留直接继承 `MetadataPlugin`。无论哪种方案，删除可复用的重复工具方法
- [X] T060 [US5] 评估 `pavone/plugins/metadata/avbase_metadata.py` 迁移策略：如果迁移至 `ApiMetadataPlugin` 并覆写 `extract_metadata`（保留 Next.js API + HTML fallback 逻辑）能使代码更简洁则迁移，否则保留直接继承 `MetadataPlugin`。无论哪种方案，删除可复用的重复工具方法

### 批次 8 验证

- [X] T061 [US3] 运行 `uv run pytest tests/metadata/test_caribbeancom.py tests/metadata/test_fanza.py tests/metadata/test_avbase.py -v` 确认批次 8 的 3 个插件测试全部通过
- [X] T062 [US3] 运行 `uv run pytest tests/ -v -m "not integration"` 确认全量测试通过

**检查点**: 批次 8 完成 — 全部 34 个插件处理完毕，全量测试通过 ✅

---

## 阶段 11: 用户故事 4 — 代码维护效率验证（优先级: P2）

**目标**: 验证重构后的代码维护效率提升 — 基类中的公共方法修改能自动传播到所有子类

**独立测试**: 通过代码统计和继承关系验证

### 维护效率验证

- [X] T063 [US4] 运行代码统计：确认 `_abs` 方法仅在 `pavone/plugins/metadata/base.py` 中定义 1 份（原 16 份），`_parse_runtime` 仅 1 份（原 14 份），`_parse_date` 仅 1 份（原 23 份），`extract_metadata` 模板不超过 3 份（HTML/API/JSON-LD 各 1 份）。使用 `grep -r "def _abs\|def _parse_runtime\|def _parse_date" pavone/plugins/metadata/` 统计
- [X] T064 [US4] 运行代码行数统计：确认插件总代码行数从约 7,148 行降至 5,700 行以下（≥20% 减少）。使用 `wc -l pavone/plugins/metadata/*.py` 统计并与基准对比

**检查点**: 代码维护效率提升已验证 ✅

---

## 阶段 12: 完善与横切关注点

**目的**: 最终质量保障、格式化检查和文档更新

- [X] T065 [P] 运行 `uv run black --check pavone/plugins/metadata/` 和 `uv run isort --check-only pavone/plugins/metadata/` 确认所有已修改文件通过代码格式检查，如有问题则运行 `uv run black pavone/plugins/metadata/ && uv run isort pavone/plugins/metadata/` 修复
- [X] T066 [P] 运行 `uv run pyright pavone/plugins/metadata/` 对整个元数据插件目录进行类型检查，确认无新增错误（相比 T002 基准线）
- [X] T067 运行 `uv run pytest tests/ -v` 执行最终全量测试（含集成测试可选），确认所有 661 个测试函数通过，通过率 100%
- [X] T068 运行 `quickstart.md` 中的验证步骤：确认基类导入正常、FC2BaseMetadata 继承链正确、分批迁移插件测试全部通过
- [X] T069 更新 `CHANGELOG.md`，在 v0.3.2 部分记录：新增 HtmlMetadataPlugin/ApiMetadataPlugin/JsonLdMetadataPlugin 三个中间基类；统一 _abs/_parse_runtime/_parse_date 公共方法；34 个插件分 8 批迁移至新基类；新增 _get_tag_attr 类型安全方法

---

## 依赖关系与执行顺序

### 阶段依赖关系

- **设置（阶段 1）**: 无依赖 — 可立即开始
- **基础（阶段 2）**: 依赖于设置完成 — 阻塞所有迁移批次
- **批次 1-8（阶段 3-10）**: 都依赖于基础阶段完成
  - 批次 1 必须最先完成（验证基类正确性）
  - 批次 2-6 可在批次 1 验证通过后并行进行（互不依赖）
  - 批次 7（FC2 家族）依赖于 T051 的 FC2BaseMetadata 继承改造
  - 批次 8（特殊插件）建议最后处理（风险最高）
- **维护效率验证（阶段 11）**: 依赖于所有迁移批次完成
- **完善（阶段 12）**: 依赖于所有前序阶段完成

### 用户故事依赖关系

- **US1（新插件开发效率）**: 通过阶段 2 的基类创建实现 — 基类就绪即可验证
- **US2（行为兼容性）**: 通过每个迁移任务的测试验证 — 贯穿阶段 3-10
- **US3（渐进式迁移）**: 通过每批次末尾的检查点验证 — 贯穿阶段 3-10
- **US4（代码维护效率）**: 通过阶段 11 的统计验证 — 依赖所有迁移完成
- **US5（特殊插件灵活性）**: 通过批次 7-8 的特殊处理验证 — 在阶段 9-10 实现
- **US6（类型安全）**: 通过 T005 的 `_get_tag_attr` 实现 — 在阶段 2 完成

### 每批次内部

- 同批次的插件迁移任务（标记 [P]）可并行执行
- 迁移任务全部完成后执行验证任务
- 批次验证通过后方可移至下一批次

### 并行机会

- 阶段 2 中 T003-T007 的基类创建任务需按顺序执行（T007 依赖 T003）
- 每批次内标记 [P] 的迁移任务可全部并行（不同文件，无依赖）
- 批次 2-6 可在批次 1 验证后并行开始（如有多个开发人员）
- 阶段 12 中的格式检查和类型检查（T065, T066）可并行执行

---

## 并行示例: 批次 1

```bash
# 批次 1 中 4 个插件迁移可全部并行启动:
任务: "迁移 pavone/plugins/metadata/dahlia_metadata.py 至 HtmlMetadataPlugin"
任务: "迁移 pavone/plugins/metadata/faleno_metadata.py 至 HtmlMetadataPlugin"
任务: "迁移 pavone/plugins/metadata/mywife_metadata.py 至 HtmlMetadataPlugin"
任务: "迁移 pavone/plugins/metadata/tenmusume_metadata.py 至 ApiMetadataPlugin"
```

## 并行示例: 批次 2-6 跨批并行（多人协作）

```bash
# 批次 1 验证通过后，如果有多名开发人员，可同时启动:
开发者 A: 批次 2 (sod, mgstage, getchu, kin8tengoku, madouqu)
开发者 B: 批次 3 (modelmediaasia, muramura, pacopacomama, onepondo, theporndb)
开发者 C: 批次 4 (c0930, h0930, h4610, fc2hub, heyzo)
# 注意: 批次 7 和 8 建议在批次 1-6 完成后再开始
```

---

## 实施策略

### 仅 MVP（基类 + 批次 1）

1. 完成阶段 1: 设置（建立基准线）
2. 完成阶段 2: 基础（创建三个中间基类）
3. 完成阶段 3: 批次 1（4 个最简单插件验证基类正确性）
4. **停止并验证**: 全量测试通过，基类设计已验证
5. 此时新插件开发者已可使用新基类开发，核心价值已交付

### 增量交付（推荐）

1. 完成设置 + 基础 + 批次 1 → MVP 验证 ✅
2. 批次 2-6（标准插件）→ 每批独立验证 → 28 个插件迁移完成
3. 批次 7（FC2 家族）→ 继承链改造验证 → 31 个插件
4. 批次 8（特殊插件）→ 灵活性策略评估 → 34 个插件全部处理
5. 维护效率验证 + 完善 → 全部完成
6. 每个批次都是独立可提交的增量，可随时暂停

### 每批次标准流程

1. 同批次内插件并行迁移（修改继承、删除重复代码）
2. 运行单插件测试确认功能不变
3. 运行全量测试确认无回归
4. 运行类型检查确认无新增错误
5. `git commit` 提交该批次

---

## 注意事项

- [P] 任务 = 不同文件, 无依赖关系, 可并行执行
- [Story] 标签将任务映射到 spec.md 中的用户故事以实现可追溯性
- 每个批次应该是独立可验证的交付单元
- 迁移时注意 `resp.text` vs `resp.content` 一致性（基类模板使用 `resp.text`）
- 对于 `_parse_runtime` 有细微差异的插件，先检查基类超集是否覆盖，如未覆盖则在该插件中覆写
- 避免: 跨批次依赖、一次性大量修改、跳过验证步骤

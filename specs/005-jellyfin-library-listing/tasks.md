# 任务: Jellyfin 媒体库视频列表

**输入**: 来自 `/specs/005-jellyfin-library-listing/` 的设计文档
**前置条件**: plan.md(必需), spec.md(用户故事必需), research.md, data-model.md, contracts/

**组织结构**: 任务按用户故事分组, 以便每个故事能够独立实施和测试.

## 格式: `[ID] [P?] [Story] 描述`
- **[P]**: 可以并行运行(不同文件, 无依赖关系)
- **[Story]**: 此任务属于哪个用户故事(例如: US1, US2, US3, US4)
- 在描述中包含确切的文件路径

## 用户故事映射
- **US1** (P1): 指定媒体库列取视频并排序
- **US2** (P2): 元数据丰富度评分与排序
- **US3** (P2): 交互式选择媒体库
- **US4** (P1): 表格化展示结果

---

## 阶段 1: 基础(阻塞前置条件)

**目的**: 扩展现有基础设施，为所有用户故事提供数据获取和评分计算能力

**⚠️ 关键**: 在此阶段完成之前, 无法开始任何用户故事工作

- [X] T001 [P] 在 pavone/jellyfin/client.py 的 `get_library_items` 方法中添加 `sort_by: Optional[str] = None` 和 `sort_order: Optional[str] = None` 参数，将其映射为 Jellyfin API 的 `SortBy` 和 `SortOrder` 请求参数。当 `sort_by` 为 `"SortName"` 或 `"DateCreated"` 时传递给 API，否则忽略。保持方法的向后兼容性（默认值为 None 时行为不变）
- [X] T002 [P] 在 pavone/models/jellyfin_item.py 的 `ItemMetadata` 类中添加模块级常量 `METADATA_SCORE_WEIGHTS: dict[str, int]`（含 10 个维度权重: name=5, overview=20, genres=10, year=5, actors=15, directors=10, primary_image=15, rating=5, tags=10, studios=5）和 `metadata_score` 计算属性，遍历权重字典，根据对应属性是否有值（非空/非 None/非零）累加权重，返回 int 类型的 0-100 评分
- [X] T003 [P] 在 tests/test_metadata_score.py 中为 `ItemMetadata.metadata_score` 编写单元测试: (1) 全部元数据为空时评分为 0; (2) 仅有标题时评分为 5; (3) 全部元数据齐全时评分为 100; (4) 部分元数据存在时评分为对应权重之和; (5) 验证返回类型为 int 且值域 [0, 100]

**检查点**: 基础就绪 — `get_library_items` 支持排序参数, `metadata_score` 可计算, 评分单测全绿

---

## 阶段 2: 用户故事 1 + 用户故事 4 — 列取视频并以表格展示 (优先级: P1) 🎯 MVP

**目标**: 用户可以指定媒体库名称，通过 `jellyfin list` 命令获取视频列表，以表格形式展示（含序号、名称、加入时间、元数据评分、路径），支持按名称和加入时间排序

**独立测试**: 运行 `pavone jellyfin list "媒体库名称"` 验证表格输出包含正确列且排序生效；运行 `pavone jellyfin list "不存在的库"` 验证错误提示

### 实施

- [X] T004 [US1] [US4] 在 pavone/cli/commands/jellyfin.py 中新增 `list` 子命令函数，注册在 `jellyfin` Click 命令组下。定义参数: `library_name`（可选 str 参数），`--sort-by` / `-s`（Click.Choice: name, date_added, metadata_score，默认 date_added），`--order` / `-o`（Click.Choice: asc, desc，默认 desc），`--limit` / `-n`（click.IntRange(1, 10000)，默认 50）
- [X] T005 [US1] 在 pavone/cli/commands/jellyfin.py 的 `list` 命令中实现核心数据获取逻辑: (1) 初始化 `JellyfinClientWrapper` 并认证; (2) 调用 `client.get_libraries()` 获取所有媒体库; (3) 根据 `library_name` 参数查找匹配的媒体库（按名称匹配）; (4) 若库名不存在，调用 `echo_error` 输出错误并列出可用库名，返回; (5) 根据 sort_by 映射为 Jellyfin API 排序参数（name→SortName, date_added→DateCreated），调用 `client.get_library_items(library_ids=[lib.id], sort_by=..., sort_order=..., limit=limit)` 获取数据; (6) 对 metadata_score 排序则获取全量数据后在客户端排序并截取前 limit 条
- [X] T006 [US4] 在 pavone/cli/commands/jellyfin.py 的 `list` 命令中实现表格展示逻辑: (1) 导入 `tabulate` 和 `ItemMetadata`; (2) 将获取到的 `JellyfinItem` 列表转换为表格数据行——每行包含: 序号(enumerate 1-based)、名称(截断至 30 显示宽度)、加入时间(从 `ItemMetadata(item.metadata).added_date` 提取并格式化为 YYYY-MM-DD，None 时显示 "N/A")、评分(`ItemMetadata(item.metadata).metadata_score`)、路径(`item.path` 截断至 50 显示宽度，None 时显示 "N/A"); (3) 输出摘要行 `"媒体库: {name} (共 {total} 个视频, 显示前 {shown} 条, 按{sort_field}{order})"`; (4) 使用 `tabulate(rows, headers=["#", "名称", "加入时间", "评分", "路径"], tablefmt="simple")` 格式化并 `click.echo` 输出; (5) 空结果时输出 `'媒体库 "{name}" 为空，没有视频内容。'`; (6) 验证 tabulate 对中文字符的列宽对齐效果——若 CJK 字符导致列错位，则回退到使用已有的 `pad_text` + `get_display_width` 手动拼接方案（参见 research.md 注意事项）
- [X] T007 [US4] 在 pavone/cli/commands/jellyfin.py 中新增 `_truncate_text(text: str, max_width: int) -> str` 辅助函数: 使用已有的 `get_display_width` 计算文本显示宽度，当超过 `max_width` 时截断并追加 "..."，确保截断后总显示宽度不超过 `max_width`
- [X] T008 [US1] [US4] 在 tests/test_jellyfin_list.py 中编写 list 命令测试: (1) Mock `JellyfinClientWrapper` 的 `authenticate`、`get_libraries`、`get_library_items` 方法; (2) 测试指定有效库名时输出包含表头和数据行; (3) 测试库名不存在时输出错误信息并列出可用库; (4) 测试空库时输出友好提示; (5) 测试 --sort-by name --order asc 参数正确传递给 client; (6) 测试 --limit 参数限制输出行数

**检查点**: `pavone jellyfin list "有效库名"` 输出完整表格, 排序和 limit 生效, 错误处理正确, 所有测试通过

---

## 阶段 3: 用户故事 2 — 元数据丰富度评分排序 (优先级: P2)

**目标**: 用户可以指定 `--sort-by metadata_score` 按元数据丰富度排序，评分低的视频排在前面方便补充元数据

**独立测试**: 运行 `pavone jellyfin list "库名" -s metadata_score -o asc` 验证评分低的在前，评分高的在后

### 实施

- [X] T009 [US2] 在 pavone/cli/commands/jellyfin.py 的 `list` 命令中完善 metadata_score 排序分支: 当 `sort_by == "metadata_score"` 时 (1) 使用分页循环调用 `client.get_library_items` 获取指定媒体库的全量视频（每次 limit=100, start_index 递增直到返回为空）; (2) 为每个 item 构造 `ItemMetadata(item.metadata)` 计算 `metadata_score`; (3) 按 metadata_score 排序（asc 升序 / desc 降序）; (4) 截取前 `limit` 条结果传入表格展示
- [X] T010 [US2] 在 tests/test_jellyfin_list.py 中追加 metadata_score 排序测试: (1) Mock 返回元数据丰富度不同的多个 item; (2) 验证 `-s metadata_score -o asc` 时评分低的在前; (3) 验证 `-s metadata_score -o desc` 时评分高的在前; (4) 验证 `--limit` 截断在排序后生效

**检查点**: 元数据评分排序功能完整, `metadata_score` 升序/降序均正确, 测试通过

---

## 阶段 4: 用户故事 3 — 交互式选择媒体库 (优先级: P2)

**目标**: 用户不指定媒体库名称时，系统展示编号列表供交互式选择；仅一个库时自动选择

**独立测试**: 运行 `pavone jellyfin list`（不带库名）验证展示选择列表并能输入编号获取结果

### 实施

- [X] T011 [US3] 在 pavone/cli/commands/jellyfin.py 的 `list` 命令中实现交互式媒体库选择逻辑: 当 `library_name` 为 None 时 (1) 调用 `client.get_libraries()` 获取全部媒体库; (2) 若仅 1 个库，自动选择并用 `echo_colored` 输出 `"✓ 自动选择库: {name}"`; (3) 若多个库，展示编号列表（格式: `"  {i}. {name} ({item_count} 项)"`），使用 `click.prompt("请选择库", type=click.IntRange(1, len(libraries)))` 获取用户输入; (4) 若无库则 `echo_error` 提示无可用媒体库并返回; (5) 选择后继续执行已有的列取和展示逻辑
- [X] T012 [US3] 在 tests/test_jellyfin_list.py 中追加交互式选择测试: (1) Mock 多个库，使用 `click.testing.CliRunner` 的 `input` 参数模拟用户输入编号; (2) 验证选中后输出正确库的视频列表; (3) Mock 仅有 1 个库时验证自动选择（无 prompt）; (4) 验证无库时输出错误提示

**检查点**: 交互式选择流程完整，单库自动选择，多库手动选择，无库错误处理，测试通过

---

## 阶段 5: 完善与横切关注点

**目的**: 代码质量、文档、格式化

- [X] T013 [P] 对所有修改和新增文件运行 `uv run black pavone/models/jellyfin_item.py pavone/cli/commands/jellyfin.py pavone/jellyfin/client.py tests/test_metadata_score.py tests/test_jellyfin_list.py` 和 `uv run isort pavone/models/jellyfin_item.py pavone/cli/commands/jellyfin.py pavone/jellyfin/client.py tests/test_metadata_score.py tests/test_jellyfin_list.py` 进行格式化，并运行 `uv run flake8 pavone/models/jellyfin_item.py pavone/cli/commands/jellyfin.py pavone/jellyfin/client.py --select=E9,F63,F7,F82` 进行关键错误检查
- [X] T014 [P] 对修改文件运行 `uv run pyright pavone/models/jellyfin_item.py pavone/cli/commands/jellyfin.py pavone/jellyfin/client.py` 进行类型检查，修复所有类型错误
- [X] T015 运行 `uv run pytest tests/test_metadata_score.py tests/test_jellyfin_list.py -v` 确认所有测试通过
- [ ] T016 运行 quickstart.md 中的验证命令进行端到端验证（需要可用的 Jellyfin 服务器）
- [X] T017 [P] 更新 docs/usage.md 添加 `jellyfin list` 命令的使用文档，包含命令签名、参数说明、排序选项和使用示例（章程要求: 新增 CLI 命令 MUST 更新 docs/usage.md）

---

## 依赖关系与执行顺序

### 阶段依赖关系

- **基础(阶段 1)**: 无依赖关系 — T001、T002、T003 可全部并行
- **US1+US4(阶段 2)**: 依赖于 T001（排序参数）和 T002（评分属性）完成
  - T004 可先开始（命令骨架不依赖基础）
  - T005 依赖 T001（调用排序参数）和 T002（计算评分）
  - T006 依赖 T002（ItemMetadata.metadata_score）和 T005（数据获取）
  - T007 与 T004 并行（辅助函数独立）
  - T008 依赖 T004-T007 全部完成
- **US2(阶段 3)**: 依赖阶段 2 完成（T005 的数据获取框架，T006 的展示逻辑）
- **US3(阶段 4)**: 依赖阶段 2 完成（T005 的库匹配逻辑，T006 的展示逻辑）
  - US2 和 US3 之间无直接依赖，如并行开发需注意 jellyfin.py 文件冲突
- **完善(阶段 5)**: 依赖所有期望的用户故事完成

### 用户故事依赖关系

```
T001 ─┐
T002 ─┤── 阶段 2 (US1+US4: T004→T005→T006, T007∥T004, T008 最后)
T003 ─┘        │
               ├── 阶段 3 (US2: T009→T010)
               └── 阶段 4 (US3: T011→T012)
                        │
                        └── 阶段 5 (T013∥T014, T015, T016)
```

### 并行机会

- **阶段 1**: T001、T002、T003 全部并行（各在不同文件）
- **阶段 2**: T004 和 T007 并行（命令骨架与辅助函数）
- **阶段 3 和阶段 4**: 理论上可并行但操作同一文件(jellyfin.py)，建议顺序执行
- **阶段 5**: T013 和 T014 并行

---

## 实施策略

### 仅 MVP(阶段 1 + 阶段 2)

1. 完成阶段 1: 基础（排序参数 + 评分属性 + 评分测试）
2. 完成阶段 2: US1 + US4（list 命令 + 表格展示）
3. **停止并验证**: 运行 `pavone jellyfin list "库名"` 确认表格输出正确
4. MVP 可交付 — 用户已可列取视频并按名称/时间排序

### 增量交付

1. 完成基础 → 评分测试通过
2. 添加 US1+US4 → `jellyfin list "库名"` 可用 (MVP!)
3. 添加 US2 → `jellyfin list -s metadata_score` 可用
4. 添加 US3 → `jellyfin list`（无参数交互式选择）可用
5. 每阶段独立增加价值且不破坏已有功能

---

## 注意事项

- [P] 任务 = 不同文件, 无依赖关系
- [Story] 标签将任务映射到特定用户故事以实现可追溯性
- 每个用户故事应该独立可完成和可测试
- 在每个任务或逻辑组后提交
- 在任何检查点停止以独立验证故事
- 阶段 2 中 US1 和 US4 合并为同一阶段，因为表格展示(US4)是列取(US1)的必要输出层，拆分后无法独立运行
- metadata_score 排序(US2)需要全量数据拉取，注意大媒体库的性能

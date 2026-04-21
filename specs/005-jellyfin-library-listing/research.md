# 研究报告: Jellyfin 媒体库视频列表

**功能**: 005-jellyfin-library-listing
**日期**: 2026-04-17

## 研究任务与发现

### 1. Jellyfin API 服务端排序能力

**Decision**: 利用 Jellyfin API 原生 `SortBy`/`SortOrder` 参数实现服务端排序（名称、加入时间），元数据评分排序在客户端完成。

**Rationale**: Jellyfin API 的 `user_items()` 方法接受 `params` 字典，支持 `SortBy` 和 `SortOrder` 参数。服务端排序避免了将全量数据拉取到客户端再排序的性能问题。但元数据丰富度评分是 PAVOne 自定义的计算值，Jellyfin API 不支持此排序字段，必须在客户端完成。

**Alternatives considered**:
- 全部客户端排序：简单但对大媒体库性能差，需要拉取全量数据
- 全部服务端排序：无法支持自定义评分排序
- **混合方案（选定）**: 名称/时间用服务端排序 + 评分用客户端排序

**API 参数映射**:
| 用户排序字段 | Jellyfin SortBy 值 | 说明 |
|---|---|---|
| `name` | `SortName` | 按排序名称字母序 |
| `date_added` | `DateCreated` | 按加入时间 |
| `metadata_score` | N/A（客户端排序） | 需拉取全量数据后计算评分再排序 |

**SortOrder 映射**: `asc` → `"Ascending"`, `desc` → `"Descending"`

### 2. 表格格式化方案

**Decision**: 使用项目已有的 `tabulate` 依赖（v0.10.0）进行表格格式化，替代手动 `pad_text` 拼接。

**Rationale**: `tabulate` 已是项目依赖但尚未使用。它提供专业的表格渲染，支持多种格式，处理列宽对齐比手动实现更可靠。使用 `tabulate` 可以减少自定义对齐代码的维护负担。

**Alternatives considered**:
- 手动 `pad_text` 拼接（现有模式）：已在 `jellyfin.py` 中使用，但对中文对齐处理不够完善
- `rich` 库的表格：项目已依赖 `rich`，但 `tabulate` 更轻量且专注表格
- **tabulate（选定）**: 已有依赖，专业表格渲染，支持 CJK 字符宽度

**注意事项**: tabulate 对中文字符列宽需要搭配现有的 `get_display_width` 辅助函数，或使用 `wcwidth` 参数。需在实现时验证 CJK 对齐效果，若不理想则回退到手动 `pad_text` 方案。

### 3. 元数据丰富度评分维度与权重

**Decision**: 采用加权评分模型，10 个维度各有不同权重，总分 100。

**Rationale**: 不同元数据维度对用户的价值不同。标题和封面图对浏览体验影响最大，简介和演员信息次之，标签和工作室影响最小。

**Alternatives considered**:
- 等权重模型：每项 10 分，简单但不反映实际价值差异
- 二分法（有/无）：过于粗糙，无法区分"有一点"和"很丰富"
- **加权模型（选定）**: 维度权重反映用户体验价值

**评分维度与权重设计**:

| 维度 | 权重 | 检测方式 | 说明 |
|------|------|----------|------|
| 标题 (name) | 5 | 非空 | 基本字段，几乎总有 |
| 简介 (overview) | 20 | 非空且长度 > 0 | 用户浏览核心信息 |
| 类型 (genres) | 10 | 列表非空 | 分类和筛选依赖 |
| 年份 (year) | 5 | 非 None | 基本识别信息 |
| 演员 (actors) | 15 | 列表非空 | 用户关注度高 |
| 导演 (directors) | 10 | 列表非空 | 制作信息 |
| 封面图 (primary image) | 15 | has_primary_image | 视觉浏览核心 |
| 评分 (rating) | 5 | 非 None 且 > 0 | 质量参考 |
| 标签 (tags) | 10 | 列表非空 | 细粒度分类 |
| 工作室 (studios) | 5 | studio_names 非空 | 来源信息 |
| **总计** | **100** | | |

### 4. 交互式选择最佳实践

**Decision**: 复用 `move` 命令中已有的交互式选择模式，使用 `click.prompt` + `click.IntRange` 验证。

**Rationale**: `move` 命令已实现了完整的交互式库选择模式，经过实际使用验证。复用此模式保持 CLI 体验一致性，降低实现风险。

**Alternatives considered**:
- `click.Choice` 按名称选择：用户需要输入完整库名，易出错
- 第三方交互库 (inquirer, questionary)：引入新依赖，过度工程化
- **click.IntRange 编号选择（选定）**: 已有模式，简洁可靠

**额外优化**: 当仅有 1 个媒体库时自动选择（规范 FR-007），跳过交互界面。

### 5. 数据获取策略

**Decision**: 按排序类型采用不同的数据获取策略。

**Rationale**: 服务端排序和分页时，只需获取用户请求的页大小数据。客户端排序（评分排序）时，需要获取全量数据计算评分后再排序取前 N 条。

**策略**:
- **名称/时间排序**: 扩展 `get_library_items` 方法添加 `sort_by`/`sort_order` 参数，利用 `Limit` + `SortBy` + `SortOrder` 一次性获取指定数量的已排序结果
- **评分排序**: 使用分页循环获取全量数据，全量计算评分后排序，截取前 N 条展示

### 6. 集成点与依赖分析

**Decision**: 修改 3 个现有文件 + 新增 2 个测试文件。

| 文件 | 修改类型 | 内容 |
|------|----------|------|
| `pavone/jellyfin/client.py` | 修改 | `get_library_items` 添加 `sort_by`, `sort_order` 参数 |
| `pavone/models/jellyfin_item.py` | 修改 | `ItemMetadata` 添加 `metadata_score` 属性 |
| `pavone/cli/commands/jellyfin.py` | 修改 | 新增 `list` 子命令 |
| `tests/test_metadata_score.py` | 新增 | 评分计算单元测试 |
| `tests/test_jellyfin_list.py` | 新增 | list 命令集成测试 |

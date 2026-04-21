# 实施计划: Jellyfin 媒体库视频列表

**分支**: `005-jellyfin-library-listing` | **日期**: 2026-04-17 | **规范**: [spec.md](./spec.md)
**输入**: 来自 `/specs/005-jellyfin-library-listing/spec.md` 的功能规范

**注意**: 此模板由 `/speckit.plan` 命令填充. 执行工作流程请参见 `.specify/templates/plan-template.md`.

## 摘要

为 PAVOne CLI 添加 `jellyfin list` 子命令，支持列取指定 Jellyfin 媒体库中的视频并以表格形式展示。核心能力包括：按名称/加入时间/元数据丰富度评分排序，交互式媒体库选择（未指定时），以及基于 10 个元数据维度的百分制丰富度评分计算。复用现有 `JellyfinClientWrapper`、`LibraryManager`、`ItemMetadata` 模型及 `tabulate` 依赖。

## 技术背景

**语言/版本**: Python 3.10+
**主要依赖**: Click 8.x (CLI 框架), tabulate 0.9.x (表格格式化), jellyfin-apiclient-python (Jellyfin API)
**存储**: N/A (无持久化需求，数据来自 Jellyfin API 实时查询)
**测试**: pytest + unittest.TestCase, Mock 网络边界
**目标平台**: Windows/Linux/macOS CLI
**项目类型**: CLI 工具
**性能目标**: 1000 个视频的列取和展示应在合理时间内完成
**约束条件**: 复用现有 Jellyfin 客户端连接体系，不引入新依赖
**规模/范围**: 单个 CLI 子命令 + 1 个评分计算模块，影响文件 3-5 个

## 章程检查

*门控: 必须在阶段 0 研究前通过. 阶段 1 设计后重新检查.*

| 章程原则 | 合规状态 | 说明 |
|-----------|----------|------|
| I. 代码质量与类型安全 | ✅ 通过 | 所有新代码将包含完整类型注解，通过 Pyright standard 检查 |
| I. 格式规范 | ✅ 通过 | Black + isort (行宽 127, black profile) |
| I. 抽象契约 | ✅ 通过 | 不涉及新插件或下载器，复用现有 `JellyfinClientWrapper` |
| II. 测试标准 | ✅ 通过 | 评分计算逻辑的单元测试，CLI 命令的集成测试，AAA 模式 |
| II. Mock 边界 | ✅ 通过 | 仅 Mock Jellyfin API 调用（网络边界），内部逻辑用真实实现 |
| III. CLI 框架 | ✅ 通过 | 使用 Click 框架实现，注册在 `jellyfin` 命令组下 |
| III. 输出规范 | ✅ 通过 | 使用 tabulate 格式化表格输出到 stdout，错误输出到 stderr |
| III. 日志分级 | ✅ 通过 | 复用 `--verbose` 标志和 `get_logger()` |
| III. 错误恢复 | ✅ 通过 | 网络错误给出明确提示，不涉及批量操作 |
| IV. 启动时间 | ✅ 通过 | 不新增启动时加载的组件 |
| IV. 网络效率 | ✅ 通过 | 复用现有 Session 连接池 |

**门控结果**: 全部通过，无违规项。

## 项目结构

### 文档(此功能)

```
specs/005-jellyfin-library-listing/
├── plan.md              # 此文件
├── spec.md              # 功能规范
├── research.md          # 阶段 0 输出
├── data-model.md        # 阶段 1 输出
├── quickstart.md        # 阶段 1 输出
├── contracts/           # 阶段 1 输出 (CLI 命令模式)
└── tasks.md             # 阶段 2 输出
```

### 源代码(仓库根目录)

```
pavone/
├── cli/
│   └── commands/
│       └── jellyfin.py          # 新增 list 子命令 (修改)
├── jellyfin/
│   ├── client.py                # 扩展 get_library_items 排序参数 (修改)
│   └── library_manager.py       # 可能扩展列取方法 (修改)
├── models/
│   └── jellyfin_item.py         # 新增 metadata_score 属性 (修改)
tests/
├── test_metadata_score.py       # 评分计算单元测试 (新增)
└── test_jellyfin_list.py        # list 命令测试 (新增)
```

**结构决策**: 采用现有单项目结构，在已有文件中扩展功能。评分计算逻辑作为 `ItemMetadata` 的属性方法实现，避免引入新模块。

## 复杂度跟踪

> 无章程违规，无需复杂度证明。

# 实施计划: 技术欠债清理与体验优化

**分支**: `001-tech-debt-optimization` | **日期**: 2026-03-16 | **规范**: [spec.md](spec.md)
**输入**: 来自 `/specs/001-tech-debt-optimization/spec.md` 的功能规范

## 摘要

本次迭代聚焦于 5 个技术欠债和体验优化领域: Ctrl+C 优雅终止、M3U8 分段失败可跳过、M3U8 进度条优化、插件自动发现、代码去重。所有变更在现有架构上进行增量改进，不涉及架构重设计。

## 技术背景

**语言/版本**: Python 3.10+
**主要依赖**: Click (CLI), Rich (进度条), requests (HTTP), beautifulsoup4 (解析), pydantic (配置验证)
**存储**: 文件系统 (下载缓存, 配置文件)
**测试**: pytest + unittest.TestCase + pytest-cov
**目标平台**: Windows/Linux/macOS
**项目类型**: CLI 工具 + 插件化库
**约束条件**: Ctrl+C 3秒内退出; Pyright standard 零错误

## 章程检查

| 原则 | 合规状态 |
|------|---------|
| I. 代码质量与类型安全 | ✅ 所有新增代码需通过 Pyright standard, Black, isort, flake8 (FR-017/FR-018 重构需完整类型注解) |
| II. 测试标准 | ✅ 各故事需附带对应测试, AAA 模式, Mock 仅限系统边界 |
| III. 用户体验一致性 | ✅ 进度条使用 Rich (FR-010/FR-011), 错误输出 stderr, 插件加载失败降级 (FR-015) |
| IV. 性能要求 | ✅ 插件延迟加载 (FR-013), 信号处理资源清理 (FR-001/FR-003) |

## 项目结构

### 文档 (此功能)

```
specs/001-tech-debt-optimization/
├── plan.md              # 此文件
├── spec.md              # 功能规范
├── tasks.md             # 任务列表 (/speckit.tasks 输出)
└── checklists/
    └── requirements.md  # 需求质量检查清单
```

### 源代码 (受影响的文件)

```
pavone/
├── core/
│   └── downloader/
│       ├── base.py              # BaseDownloader (中断标志集成)
│       ├── m3u8_downloader.py   # M3U8 下载 (US1+US2+US3 核心变更)
│       └── http_downloader.py   # HTTP 下载 (US1 信号处理)
├── manager/
│   ├── execution.py             # ExecutionManager (US1 信号处理入口)
│   ├── plugin_manager.py        # PluginManager (US4 自动发现)
│   └── progress.py              # 进度回调 (US3 分片进度)
├── models/
│   └── progress_info.py         # ProgressInfo (US3 分片字段扩展)
├── plugins/
│   ├── base.py                  # BasePlugin (不变)
│   ├── __init__.py              # 导入清理 (US4)
│   ├── missav_plugin.py         # (US5 重构提取逻辑)
│   ├── javrate_plugin.py        # (US5 重构提取逻辑)
│   ├── jtable_plugin.py         # (US5 重构提取逻辑)
│   ├── memojav_plugin.py        # (US5 重构提取逻辑)
│   └── av01_plugin.py           # (US5 重构提取逻辑)
├── utils/
│   ├── html_metadata_utils.py   # (US5 扩展提取函数)
│   └── signal_handler.py        # 新增: 全局中断管理 (US1)
└── cli/
    ├── __init__.py              # --skip-failed 全局标志 (US2)
    └── commands/
        └── download.py          # --skip-failed 传递 (US2)
tests/
├── test_signal_handler.py       # 新增: 信号处理测试
├── test_m3u8_segment_failure.py # 新增: 分段失败处理测试
├── test_m3u8_progress.py        # 新增: 进度条测试
├── test_plugin_autodiscovery.py # 新增: 自动发现测试
└── test_extract_utils.py        # 新增: 共享提取函数测试
```

**结构决策**: 在现有项目结构上增量修改，新增 `pavone/utils/signal_handler.py` 作为全局中断管理模块，扩展 `pavone/utils/html_metadata_utils.py` 增加独立提取函数。

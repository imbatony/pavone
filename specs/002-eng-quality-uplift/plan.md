# 实施计划: PAVOne v0.3.0 工程质量提升

**分支**: `002-eng-quality-uplift` | **日期**: 2026-04-13 | **规范**: [spec.md](spec.md)
**输入**: 来自 `/specs/002-eng-quality-uplift/spec.md` 的功能规范

## 摘要

本计划实施 PAVOne v0.3.0 工程质量提升，聚焦五个领域：
1. **配置统一**: 删除冗余的 setup.py/setup.cfg，以 pyproject.toml 为唯一真相源
2. **安全修复**: SSL 验证默认开启 + 全局异常层级体系 + 统一退出码
3. **输出规范化**: 消除 79 处 print() 调用，添加 --no-color 支持
4. **开源标准化**: CONTRIBUTING.md + pre-commit + Makefile + conftest.py
5. **CI/CD 加固**: 安全扫描强制执行 + 依赖上界约束

技术方法：渐进式重构，每阶段独立可验证，不引入破坏性 API 变更。

## 技术背景

**语言/版本**: Python 3.10+
**主要依赖**: Click 8.x (CLI), Rich 13.x (输出), Pydantic 2.x (配置验证), requests 2.x (HTTP), BeautifulSoup4 (解析), DrissionPage 4.x (浏览器自动化)
**存储**: 文件系统 (配置文件 + 下载内容)
**测试**: pytest + unittest.TestCase + pytest-cov, 26 个测试文件, 无 conftest.py
**目标平台**: 跨平台 CLI (Windows 主要, Linux/macOS 次要)
**项目类型**: CLI 工具 + 插件系统
**性能目标**: CLI 冷启动 < 2s, 下载器支持并发分片
**约束条件**: 不引入破坏性 API 变更, 向后兼容现有配置
**规模/范围**: ~50 个 Python 源文件, 26 个测试文件, 9 个 CLI 命令, 6 个插件

## 章程检查

*门控: 必须在阶段 0 研究前通过. 阶段 1 设计后重新检查.*

### 阶段 0 前检查

| 章程原则 | 合规状态 | 说明 |
|----------|---------|------|
| I. 代码质量与类型安全 | ✅ 一致 | 本计划直接改善类型注解覆盖率 (FR-012), 建立异常层级 (FR-006), 符合章程要求 |
| II. 测试标准 | ✅ 一致 | 新增 conftest.py (FR-016) 改善测试基础设施, 符合 AAA 模式和隔离性要求 |
| III. 用户体验一致性 | ✅ 一致 | print→click.echo/logger (FR-009/010), --no-color (FR-011), 异常友好化 (FR-007) 直接落实章程 |
| IV. 性能要求 | ✅ 无影响 | 本计划不涉及性能变更, 不会降低现有性能指标 |
| 技术栈与质量门控 | ✅ 一致 | 删除 setup.py 统一到 pyproject.toml, 符合 uv 优先策略 |
| CI 流水线质量门 | ✅ 一致 | 安全扫描强制执行 (FR-018) 直接加强 CI 质量门控 |

**门控结果**: ✅ 全部通过, 无违规, 可进入阶段 0

## 项目结构

### 文档(此功能)

```
specs/002-eng-quality-uplift/
├── plan.md              # 此文件
├── research.md          # 阶段 0 输出
├── data-model.md        # 阶段 1 输出
├── quickstart.md        # 阶段 1 输出
├── contracts/           # 阶段 1 输出 (本功能无外部接口合同)
└── tasks.md             # 阶段 2 输出
```

### 源代码(仓库根目录)

```
pavone/                      # 主源码包
├── __init__.py              # 版本声明 (__version__)
├── __main__.py              # python -m pavone 入口
├── cli/
│   ├── __init__.py          # Click 主命令组 + main() 入口
│   └── commands/            # 9 个 CLI 命令模块
│       ├── config.py
│       ├── download.py
│       ├── batch_download.py
│       ├── init.py
│       ├── jellyfin.py
│       ├── metadata.py
│       ├── organize.py
│       ├── search.py
│       └── utils.py
├── config/                  # 配置管理
│   ├── configs.py
│   ├── logging_config.py
│   ├── manager.py           # ConfigManager (含 print 调用)
│   ├── settings.py
│   └── validator.py
├── core/                    # 核心功能
│   ├── base.py              # BaseDownloader 抽象基类
│   ├── dummy.py
│   ├── file_mover.py
│   ├── exceptions.py        # [新增] 全局异常层级
│   ├── exit_codes.py        # [新增] 退出码常量
│   ├── downloader/          # 下载器实现
│   └── metadata/            # 元数据提取器
├── jellyfin/                # Jellyfin 集成
│   ├── client.py
│   ├── download_helper.py
│   ├── exceptions.py        # [修改] 继承 PavoneError
│   ├── library_manager.py
│   └── models.py
├── manager/                 # 执行引擎
│   ├── execution.py         # [修改] print→click.echo
│   ├── metadata_manager.py
│   ├── plugin_manager.py
│   ├── progress.py          # [修改] print→click.echo
│   └── search_manager.py
├── models/                  # 数据模型
├── plugins/                 # 插件系统
│   ├── base.py              # BasePlugin 抽象基类
│   └── ...
├── utils/
│   └── http_utils.py        # [修改] SSL 默认值
└── py.typed                 # [新增] PEP 561

# 项目根目录新增/修改文件
├── pyproject.toml           # [修改] 唯一构建配置
├── CONTRIBUTING.md          # [新增]
├── Makefile                 # [新增]
├── .pre-commit-config.yaml  # [新增]
├── setup.py                 # [删除]
├── setup.cfg                # [删除]

tests/
├── conftest.py              # [新增] 共享 fixtures
└── ...                      # 26 个现有测试文件
```

**结构决策**: 采用现有的单一项目结构, 所有变更在已有目录体系内进行, 不引入新的顶层包或重组目录.

## 章程检查 — 阶段 1 设计后重新评估

| 章程原则 | 合规状态 | 说明 |
|----------|---------|------|
| I. 代码质量与类型安全 | ✅ 一致 | 异常层级 (PavoneError) 为类型安全的错误处理提供了基础；退出码常量消除了魔数 |
| II. 测试标准 | ✅ 一致 | conftest.py 集中管理 fixtures，符合隔离性和 DRY 原则 |
| III. 用户体验一致性 | ✅ 一致 | print→click.echo/logger 统一了输出渠道；--no-color 符合"输出规范"章程要求；异常友好化符合"错误信息 MUST 输出到 stderr 并包含可执行的修复建议" |
| IV. 性能要求 | ✅ 无影响 | 异常层级和 print 替换不影响运行时性能 |
| 技术栈与质量门控 | ✅ 一致 | 删除 setup.py/setup.cfg 统一到 pyproject.toml；.flake8 保持代码质量门控；pre-commit 加强提交前检查 |
| CI 流水线质量门 | ✅ 一致 | 移除 `|| true` 强制安全扫描；依赖上界约束防止意外破坏 |

**设计后门控结果**: ✅ 全部通过, 无复杂度违规, 可进入阶段 2 (tasks)

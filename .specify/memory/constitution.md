<!--
同步影响报告
==============
版本更改: 0.0.0 → 1.0.0 (MAJOR: 首次正式采用章程)
修改的原则列表:
  - 新增: I. 代码质量与类型安全
  - 新增: II. 测试标准
  - 新增: III. 用户体验一致性
  - 新增: IV. 性能要求
添加的部分:
  - 核心原则 (4 条)
  - 技术栈与质量门控
  - 开发工作流
  - 治理
删除的部分: 无 (首次创建)
需要更新的模板:
  - .specify/templates/plan-template.md ✅ 无需更新 (章程检查部分为动态引用)
  - .specify/templates/spec-template.md ✅ 无需更新 (模板使用通用占位符)
  - .specify/templates/tasks-template.md ✅ 无需更新 (任务类型为动态生成)
  - .specify/templates/checklist-template.md ✅ 无需更新 (检查清单为动态生成)
后续 TODO: 无
-->

# PAVOne 项目章程

## 核心原则

### I. 代码质量与类型安全

所有 Python 代码 MUST 满足以下质量标准:

- **类型注解**: 所有函数定义 MUST 包含完整的参数类型注解和返回值类型注解. 禁止 `Any` 类型逃逸, 除非与第三方库交互且无法推导具体类型.
- **类型检查**: 代码 MUST 通过 Pyright standard 模式检查, 零错误. 禁止使用 `# type: ignore` 除非附带明确的技术理由注释.
- **代码格式**: 所有代码 MUST 通过 Black (行宽 127) 和 isort (black profile) 格式化. CI 流水线中格式检查失败 MUST 阻止合并.
- **静态分析**: 代码 MUST 通过 flake8 关键错误检查 (E9, F63, F7, F82). 圈复杂度 MUST 不超过 20.
- **抽象契约**: 插件 MUST 继承自 `BasePlugin` 并实现所有抽象方法. 下载器 MUST 继承自 `BaseDownloader`. 违反契约的代码不得合并.
- **导入规范**: 禁止循环导入 (`reportImportCycles: error`). 跨模块依赖 MUST 通过 `pavone.manager` 的延迟导入模式解耦.

理由: PAVOne 的插件化架构依赖清晰的类型契约来保证插件兼容性和系统可维护性. 严格的类型检查在编译期捕获错误, 降低运行时故障风险.

### II. 测试标准

所有功能变更 MUST 附带对应的测试, 遵循以下标准:

- **测试结构**: 测试 MUST 遵循 AAA 模式 (Arrange-Act-Assert). 测试类 MUST 继承 `unittest.TestCase` 或使用 pytest 函数风格.
- **隔离性**: 每个测试 MUST 独立运行, 不依赖其他测试的执行顺序. 文件系统操作 MUST 使用 `tempfile` 临时目录, 并在 tearDown 中清理.
- **标记分类**: 集成测试 MUST 使用 `@pytest.mark.integration` 标记. 网络依赖测试 MUST 使用 `@pytest.mark.network` 标记. 默认 CI 运行 MUST 排除 integration 标记的测试.
- **覆盖率**: 新增代码的测试覆盖率 SHOULD 不低于 80%. 核心模块 (`pavone/core/`, `pavone/manager/`) 的覆盖率 SHOULD 不低于 90%.
- **Mock 边界**: 仅在系统边界 (网络请求, 文件 I/O, 外部 API) 使用 Mock. 内部模块间调用 MUST 使用真实实现进行测试.
- **回归测试**: 每个 Bug 修复 MUST 附带复现该 Bug 的测试用例, 确保不会回归.

理由: 插件系统和多站点下载器的复杂交互需要可靠的测试保障. 严格的隔离性和标记机制确保 CI 快速反馈, 同时保留完整集成验证能力.

### III. 用户体验一致性

CLI 交互和输出 MUST 保持一致的用户体验:

- **CLI 框架**: 所有命令 MUST 使用 Click 框架实现, 注册在 `pavone.cli` 主命令组下. 命令 MUST 提供 `--help` 自动生成文档.
- **输出规范**: 用户可见的进度信息 MUST 通过 Rich 或 tqdm 呈现. 错误信息 MUST 输出到 stderr 并包含可执行的修复建议. 正常输出 MUST 输出到 stdout.
- **日志分级**: `--verbose` (-v) 标志 MUST 启用 DEBUG 级别日志. 默认运行 MUST 仅显示 WARNING 及以上级别. 日志 MUST 通过 `LogManager` 统一管理.
- **配置一致性**: 用户配置 MUST 通过 `ConfigManager` 统一读写, 使用 Pydantic 模型验证. 配置变更 MUST 对用户可见 (通过 `pavone config` 子命令).
- **插件透明性**: 插件加载失败 MUST 降级处理并通知用户, 不得导致整个程序崩溃. 不可用的插件 SHOULD 在 verbose 模式下列出原因.
- **错误恢复**: 下载任务 MUST 支持断点续传. 批量操作中单个项目的失败 MUST NOT 终止整个批次, 失败项 MUST 在操作结束时汇总报告.

理由: PAVOne 作为命令行工具, 用户体验的一致性直接决定了工具的可用性. 统一的输出规范和错误处理减少用户认知负担, 提高操作效率.

### IV. 性能要求

系统 MUST 满足以下性能基线:

- **下载性能**: HTTP 下载器 MUST 支持并发分片下载. M3U8 下载器 MUST 支持并发分片获取和合并. 并发度 MUST 可通过配置调整.
- **启动时间**: CLI 冷启动到命令就绪 SHOULD 不超过 2 秒. 插件延迟加载 MUST 确保未使用的插件不影响启动性能.
- **内存管理**: 大文件下载 MUST 使用流式处理, 禁止将完整文件内容加载到内存. M3U8 分片合并 MUST 采用流式写入.
- **网络效率**: HTTP 请求 MUST 复用连接 (Session). 失败请求 MUST 使用指数退避重试策略. 代理配置 MUST 全局生效, 通过 `ProxyConfig` 统一管理.
- **资源清理**: 所有插件 MUST 实现 `cleanup()` 方法, 释放持有的资源 (连接, 临时文件, 句柄). 异常退出时 MUST 通过信号处理进行清理.

理由: 作为下载和管理工具, 性能直接影响用户等待时间和系统资源占用. 流式处理和并发机制是处理大文件和多文件场景的基本要求.

## 技术栈与质量门控

- **语言**: Python 3.10+
- **包管理**: uv (首选), pip 兼容
- **依赖管理**: pyproject.toml 声明, uv.lock 锁定
- **格式化**: Black (行宽 127) + isort (black profile, 行宽 127)
- **静态检查**: Pyright standard 模式 + flake8 (关键错误)
- **测试框架**: pytest + unittest.TestCase + pytest-cov
- **CI 流水线质量门**: 所有 PR MUST 通过以下检查才能合并:
  1. Black 格式检查
  2. isort 导入排序检查
  3. flake8 关键错误检查
  4. Pyright 类型检查
  5. pytest 单元测试 (Python 3.10, 3.11, 3.12 矩阵)
  6. 安全扫描 (safety + bandit)

## 开发工作流

- **分支策略**: 功能开发 MUST 在独立分支上进行, 分支名 MUST 遵循 `<type>/<description>` 格式.
- **提交规范**: 提交消息 SHOULD 遵循 Conventional Commits 规范 (feat:, fix:, docs:, refactor:, test:, chore:).
- **PR 审查**: PR 描述 MUST 包含变更摘要和测试说明. CI 全绿是合并的前提条件.
- **文档维护**: 公共 API 变更 MUST 同步更新 `docs/` 下的相关文档. 新增 CLI 命令 MUST 更新 `docs/usage.md`.

## 治理

本章程是 PAVOne 项目所有开发实践的最高准则. 所有代码变更、架构决策和工具选型 MUST 与章程原则保持一致.

- **修订程序**: 章程修订 MUST 记录变更内容、理由和版本号变更. 原则的添加或删除属于 MINOR 版本变更. 原则的重新定义或删除不可协商规则属于 MAJOR 版本变更. 措辞修正属于 PATCH 版本变更.
- **合规审查**: 代码审查中 MUST 验证变更是否符合章程原则. 使用 `plan-template.md` 中的"章程检查"部分进行实施前门控.
- **例外处理**: 违反章程原则的技术决策 MUST 在 PR 中明确标注并提供书面理由. 临时例外 MUST 附带还原计划和时间线.
- **运行时指导**: 开发环境配置参见 `docs/dev/development.md`. 架构参考参见 `docs/dev/architecture.md`. 测试指南参见 `docs/dev/testing.md`.

**版本**: 1.0.0 | **批准日期**: 2026-03-16 | **最后修订**: 2026-03-16

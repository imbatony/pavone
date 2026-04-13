# 任务: PAVOne v0.3.0 工程质量提升

**输入**: 来自 `/specs/002-eng-quality-uplift/` 的设计文档
**前置条件**: plan.md(必需), spec.md(必需), research.md, data-model.md, quickstart.md

**测试**: 本功能规范未明确要求测试驱动开发，因此不生成独立测试任务。但每个阶段的检查点要求运行现有测试套件以确认无回归。

**组织结构**: 任务按用户故事分组，以便每个故事能够独立实施和测试。

## 格式: `[ID] [P?] [Story] 描述`
- **[P]**: 可以并行运行(不同文件, 无依赖关系)
- **[Story]**: 此任务属于哪个用户故事(例如: US1, US2, US3)
- 在描述中包含确切的文件路径

## 路径约定
- **源码**: `pavone/` (主包)
- **测试**: `tests/`
- **项目根目录**: 构建配置、文档、CI 配置

---

## 阶段 1: 设置(共享基础设施)

**目的**: 创建新模块文件和迁移配置，为后续所有用户故事奠定基础

- [x] T001 在 pavone/core/exceptions.py 中创建全局异常层级体系，定义 PavoneError 基类及 NetworkError、DownloadError、ExtractError、PluginError、ConfigError、MetadataError 子类（参考 data-model.md 层级关系）
- [x] T001a [P] 在 tests/test_exceptions.py 中为 pavone/core/exceptions.py 编写单元测试：验证异常层级继承关系（所有子类 isinstance PavoneError）、message 属性、__str__ 输出
- [x] T002 [P] 在 pavone/core/exit_codes.py 中创建退出码常量类 ExitCode，定义 SUCCESS=0、GENERAL_ERROR=1、USAGE_ERROR=2、NETWORK_ERROR=3、CONFIG_ERROR=4（参考 data-model.md 映射关系）
- [x] T002a [P] 在 tests/test_exit_codes.py 中为 pavone/core/exit_codes.py 编写单元测试：验证退出码常量值正确、无重复值
- [x] T003 [P] 创建空文件 pavone/py.typed 作为 PEP 561 类型标记，并在 pyproject.toml 的 [tool.setuptools.package-data] 中添加 pavone = ["py.typed"]

---

## 阶段 2: 基础(阻塞前置条件)

**目的**: 完成配置统一和核心基础设施变更，这些是所有用户故事的前提

**⚠️ 关键**: 在此阶段完成之前，无法安全地开始用户故事工作

- [x] T004 将 setup.cfg 中 [flake8] 配置段迁移到项目根目录的 .flake8 文件（max-line-length=127, max-complexity=20, exclude=.git,__pycache__,build,dist,*.egg-info,.venv,venv），然后删除 setup.cfg
- [x] T005 删除 setup.py 文件，确认 pyproject.toml 的 [build-system] 和 [project.scripts] 配置完整正确
- [x] T006 验证 pyproject.toml 是唯一构建配置：运行 `pip install -e .` 和 `uv build` 确认安装正常，所有模块可导入，pavone 命令可执行
- [x] T007 [P] 更新 README.md 中 Python 版本说明从 "3.9+" 改为 "3.10+"，更新对应的版本 badge
- [x] T008 在 pavone/jellyfin/exceptions.py 中修改 JellyfinException 使其继承自 pavone.core.exceptions.PavoneError（而非直接继承 Exception），保持所有子异常不变

**检查点**: 运行 `uv run pytest` 确认所有测试通过，`pip install -e .` 安装成功

---

## 阶段 3: 用户故事 1 — 安装体验一致性 (优先级: P1) 🎯 MVP

**目标**: 以 pyproject.toml 为唯一真相源，消除多文件版本/依赖冲突

**独立测试**: 分别执行 `pip install -e .`、`uv build`、`python -c "import pavone; print(pavone.__version__)"` 验证安装一致性

> 注意: 此故事的核心任务（删除 setup.py/setup.cfg、统一版本）已在阶段 2 基础任务中完成。以下为补充验证和清理任务。

- [x] T009 [US1] 确认 pavone/__init__.py 中 __version__ 与 pyproject.toml 中 version 一致（当前均为 "0.2.2"），如存在不一致则修正为 pyproject.toml 值
- [x] T010 [US1] 清理 pavone.egg-info/ 目录（如存在），将其添加到 .gitignore（如尚未包含）

**检查点**: 项目根目录仅保留 pyproject.toml 作为构建配置文件，三种安装方式全部通过 ✅

---

## 阶段 4: 用户故事 2 — 安全默认行为 (优先级: P1)

**目标**: SSL 验证默认开启，显式禁用时输出安全警告

**独立测试**: 检查 HttpUtils.fetch() 默认 verify_ssl=True；显式传入 False 时日志输出 WARNING

- [x] T011 [US2] 在 pavone/utils/http_utils.py 中将 HttpUtils.fetch() 方法的 verify_ssl 参数默认值从 False 改为 True
- [x] T012 [US2] 在 pavone/utils/http_utils.py 的 fetch() 方法中，当 verify_ssl=False 时添加 logger.warning() 调用，输出安全警告信息（如 "SSL 证书验证已禁用，存在安全风险"）
- [x] T013 [US2] 在 pavone/jellyfin/client.py 中，当 self.config.verify_ssl 为 False 时添加 logger.warning() 安全警告（当前仅静默禁用 urllib3 警告）
- [x] T014 [US2] 审查 pavone/plugins/ 目录下所有显式传入 verify_ssl=False 的调用点（missav_plugin.py、ppvdatabank_metadata.py、supfc2_metadata.py），确认每处都有注释说明禁用原因

**检查点**: 默认安全，仅在显式声明时跳过验证；运行 `uv run pytest` 确认无回归 ✅

---

## 阶段 5: 用户故事 3 — 清晰的错误反馈 (优先级: P1)

**目标**: 建立异常→退出码映射，CLI 统一捕获并输出友好错误信息

**独立测试**: 模拟各种异常场景，验证 CLI 输出分类明确的错误信息（非堆栈跟踪），返回有意义的退出码

### 异常替换（核心模块）

- [x] T015 [P] [US3] 在 pavone/core/downloader/ 目录中将关键 except Exception 替换为 DownloadError 和 NetworkError，确保下载失败时抛出具体异常类型
- [x] T016 [P] [US3] 在 pavone/plugins/base.py 中将关键 except Exception 替换为 PluginError 和 NetworkError，确保插件加载/初始化失败时抛出具体异常
- [x] T017 [P] [US3] 在 pavone/config/manager.py 中将 except Exception 替换为 ConfigError，确保配置加载/保存失败时抛出具体异常；同时将该文件中 3 处 print(f"ERROR: ...") 和 print("WARNING: ...") 替换为 logger.error() 和 logger.warning()（与 T021 合并，避免重复修改同一文件）
- [x] T018 [P] [US3] 在 pavone/manager/metadata_manager.py 中将关键 except Exception 替换为 MetadataError 和 ExtractError

### CLI 统一错误处理

- [x] T019 [US3] 在 pavone/cli/__init__.py 的 main() 函数中添加 PavoneError 统一捕获逻辑：捕获 NetworkError→退出码 3、ConfigError→退出码 4、其他 PavoneError→退出码 1，使用 click.echo(str(e), err=True) 输出友好信息
- [x] T020 [US3] 在 pavone/cli/commands/ 目录下的命令文件（download.py、batch_download.py、search.py、metadata.py、jellyfin.py、organize.py）中，将最外层 except Exception 替换为 except PavoneError 或更具体的异常类型，使用 ExitCode 常量返回退出码

**检查点**: CLI 层不再泄露原始堆栈跟踪；运行 `uv run pytest` 确认无回归 ✅

---

## 阶段 6: 用户故事 4 — 规范化的命令行输出 (优先级: P2)

**目标**: 消除所有 print() 调用，添加 --no-color 支持

**独立测试**: `grep -r "print(" pavone/ --include="*.py"` 返回 0 结果；`pavone --no-color search "test"` 输出无 ANSI 转义码

### print() 替换

- [x] T021 [P] [US4] 在 pavone/config/manager.py 中确认 print 替换已在 T017 中完成（如尚有遗漏则补全）
- [x] T022 [P] [US4] 在 pavone/cli/commands/search.py 中将用户交互输出的 print() 替换为 click.echo()
- [x] T023 [P] [US4] 在 pavone/cli/commands/jellyfin.py 中将 11 处 print() 替换为 click.echo()（用户输出）或 logger（错误/调试信息）
- [x] T024 [P] [US4] 在 pavone/cli/commands/metadata.py 中将 3 处 print() 替换为 click.echo()
- [x] T025 [P] [US4] 在 pavone/cli/commands/enrich_helper.py 中将 12 处 print() 替换为 click.echo()（用户输出）或 logger（错误信息）
- [x] T026 [P] [US4] 在 pavone/jellyfin/download_helper.py 中将 8 处 print() 替换为 click.echo()（进度信息）或 logger（调试信息）
- [x] T027 [P] [US4] 在 pavone/manager/progress.py 中将 8 处 print() 替换为 click.echo()（用户可见的进度输出）
- [x] T028 [P] [US4] 在 pavone/manager/execution.py 中将 14 处 print() 替换为 click.echo()（交互提示）或 logger（调试信息）
- [x] T029 [US4] 扫描 pavone/ 下所有剩余 print() 调用（如 config/validator.py、models/jellyfin_item.py 等），逐一替换或添加注释说明保留理由

### --no-color 支持

- [x] T030 [US4] 在 pavone/cli/__init__.py 中为 main() Click group 添加 `@click.option("--no-color", is_flag=True)` 选项，同时检测 NO_COLOR 环境变量，将结果存入 ctx.obj["no_color"]
- [x] T031 [US4] 在 pavone/manager/progress.py 中修改 Rich Progress/Console 初始化逻辑，使其尊重 no_color 设置（通过 Console(no_color=True) 参数）

**检查点**: 源码中 print() 调用降至 0（或极少数有合理理由的例外）；--no-color 选项可用 ✅

---

## 阶段 7: 用户故事 5 — 贡献者友好的开发环境 (优先级: P2)

**目标**: 提供 CONTRIBUTING.md、pre-commit、Makefile 和 conftest.py

**独立测试**: 新贡献者可按 CONTRIBUTING.md 指引完成：克隆 → uv sync → make test → pre-commit install → 提交代码

- [x] T032 [P] [US5] 在项目根目录创建 CONTRIBUTING.md，内容包括：开发环境搭建（uv sync）、代码风格要求（Black 行宽 127、isort black profile）、测试运行方式（uv run pytest / dev.ps1 test）、类型检查（uv run pyright）、PR 提交流程与分支命名规范
- [x] T033 [P] [US5] 在项目根目录创建 .pre-commit-config.yaml，配置 hooks：black、isort、flake8、trailing-whitespace、end-of-file-fixer；在 CONTRIBUTING.md 中说明安装方式
- [x] T034 [P] [US5] 在项目根目录创建 Makefile，提供 install/test/lint/format/type-check/check/ci 目标命令，与 dev.ps1 等效
- [x] T035 [P] [US5] 在 tests/conftest.py 中创建共享 fixtures：config（测试用 Config 实例）、temp_workspace（基于 tmp_path）、sample_metadata（示例元数据字典）
- [x] T036 [US5] 审查现有测试文件中与 conftest.py 新 fixtures 重复的 fixture 定义，将其替换为对共享 fixture 的引用（优先处理 test_file_mover.py 和 test_file_operation_builder.py 中的 config fixture）
- [x] T037 [US5] 在 README.md 的"贡献"或"开发"章节中添加到 CONTRIBUTING.md 的链接，说明 make 和 dev.ps1 的用法差异

**检查点**: `pre-commit run --all-files` 通过；`make test` 或 `uv run pytest` 全部通过 ✅

---

## 阶段 8: 用户故事 6 — CI/CD 安全守护 (优先级: P3)

**目标**: 安全扫描强制执行，依赖添加上界约束

**独立测试**: CI 中 safety/bandit 失败时流水线标红；`uv lock && uv run pytest` 通过

- [x] T038 [US6] 在 pyproject.toml 的 dependencies 中为所有主要依赖添加上界约束（requests<3, beautifulsoup4<5, click<9, rich<15, pydantic<3, lxml<6, pillow<12, 等），运行 `uv lock` 验证依赖解析无冲突
- [x] T039 [US6] 本地运行 `uv run bandit -r pavone/ -f json` 获取当前报告，对误报在代码中添加 `# nosec` 注释并附带理由说明
- [x] T040 [US6] 本地运行 `uv run safety check --json` 获取当前报告，对已知无法立即修复的漏洞创建 .safety-policy.yml 显式忽略并注明原因
- [x] T041 [US6] 在 .github/workflows/ci.yml 中移除 safety check 命令后的 `|| true` 后缀，使安全扫描失败时阻断流水线
- [x] T042 [US6] 在 .github/workflows/ci.yml 中移除 bandit 命令后的 `|| true` 后缀，使安全扫描失败时阻断流水线

**检查点**: CI 中安全扫描失败正确阻断流水线；依赖解析和测试套件全部通过 ✅

---

## 阶段 9: 完善与横切关注点

**目的**: 类型注解补全、docstring 补充、最终验证

- [ ] T043 [P] 为 pavone/cli/commands/ 下的命令文件（download.py、search.py、init.py、organize.py、config.py、batch_download.py）补充完整类型注解，确保 `uv run pyright` 无新增错误
- [ ] T044 [P] 为 pavone/config/validator.py 和 pavone/config/logging_config.py 补充完整类型注解
- [ ] T045 [P] 为 pavone/plugins/base.py 的 BasePlugin 类及其方法补充 Google 风格 docstring（含 Args/Returns），记录插件生命周期
- [ ] T046 [P] 为 pavone/core/downloader/ 下载器公开接口、pavone/manager/execution.py 的 ExecutionManager、pavone/config/manager.py 的 ConfigManager 补充 Google 风格 docstring
- [x] T047 运行完整验证：`uv run pytest` 全部通过、`uv run pyright` 无新增错误、`grep -r "print(" pavone/ --include="*.py"` 结果为 0 或极少数合理例外、`pip install -e .` 成功
- [x] T048 运行 quickstart.md 中的验证步骤确认所有用户侧变更按预期工作

---

## 依赖关系与执行顺序

### 阶段依赖关系

- **阶段 1 设置**: 无依赖 — 可立即开始
- **阶段 2 基础**: 依赖阶段 1 完成（异常类和退出码模块必须存在）
- **阶段 3 US1**: 依赖阶段 2 完成（setup.py/setup.cfg 已删除）
- **阶段 4 US2**: 依赖阶段 2 完成（JellyfinException 已继承 PavoneError）
- **阶段 5 US3**: 依赖阶段 1 完成（异常层级存在）和阶段 2（JellyfinException 继承链完成），与 US2 无依赖可并行
- **阶段 6 US4**: 依赖阶段 5 完成（CLI 统一错误处理就位后才替换 print）
- **阶段 7 US5**: 依赖阶段 2 完成（setup.cfg 已删除、.flake8 已创建）
- **阶段 8 US6**: 依赖阶段 2 完成（pyproject.toml 依赖列表已确定）
- **阶段 9 完善**: 依赖所有用户故事完成

### 用户故事依赖关系

```
阶段 1 (设置)
    │
    ▼
阶段 2 (基础)
    │
    ├──────────┬──────────┬──────────┬──────────┐
    ▼          ▼          ▼          ▼          ▼
阶段 3(US1) 阶段 4(US2) 阶段 5(US3) 阶段 7(US5) 阶段 8(US6)
    │          │          │          │          │
    │          │          ▼          │          │
    │          │       阶段 6(US4)   │          │
    │          │          │          │          │
    ├──────────┴──────────┴──────────┴──────────┘
    ▼
阶段 9 (完善)
```

### 并行机会

**阶段 1 内**: T001、T002、T003 中 T002 和 T003 可并行（T001 为基础依赖）
**阶段 2 内**: T004 和 T005 顺序执行，T007 可并行
**阶段 2 后**: US1(阶段 3)、US2(阶段 4)、US3(阶段 5)、US5(阶段 7)、US6(阶段 8) 可并行
**阶段 5 后**: US4(阶段 6) 依赖 US3 的 CLI 错误处理就位
**阶段 6 内**: T021-T029 的 print() 替换任务全部可并行（不同文件）
**阶段 7 内**: T032-T035 可完全并行
**阶段 9 内**: T043-T046 可完全并行

---

## 并行示例: 阶段 2 完成后

```bash
# 团队成员 A: 用户故事 1 (安装一致性验证)
任务: T009 确认版本一致
任务: T010 清理 egg-info

# 团队成员 B: 用户故事 2 (SSL 安全修复)
任务: T011 修改 HttpUtils 默认值
任务: T012 添加 SSL 禁用警告
任务: T013 Jellyfin 客户端警告
任务: T014 审查显式 verify_ssl=False 调用

# 团队成员 C: 用户故事 5 (开发者工具)
任务: T032 创建 CONTRIBUTING.md
任务: T033 创建 .pre-commit-config.yaml
任务: T034 创建 Makefile
任务: T035 创建 conftest.py

# 团队成员 D: 用户故事 6 (CI/CD 加固)
任务: T038 依赖上界约束
任务: T039 Bandit 误报处理
任务: T040 Safety 策略文件
任务: T041 移除 safety || true
任务: T042 移除 bandit || true
```

---

## 实施策略

### MVP 范围

**MVP = 阶段 1 + 阶段 2 + 阶段 3 (US1)**

仅完成配置统一即可交付一个可验证的改善：
- 删除冗余构建文件
- 统一版本号
- 安装方式全部正常

### 增量交付顺序

1. **MVP**: 配置统一 (US1) — 消除最严重的工程问题
2. **+安全**: SSL 修复 (US2) — 消除安全隐患
3. **+错误处理**: 异常层级 + CLI 友好化 (US3) — 改善用户体验
4. **+输出规范**: print 替换 + --no-color (US4) — 统一输出渠道
5. **+开发者体验**: 贡献指南 + 工具链 (US5) — 降低贡献门槛
6. **+CI 加固**: 安全扫描强制 + 依赖约束 (US6) — 持续质量保障
7. **完善**: 类型注解 + docstring — 长期可维护性

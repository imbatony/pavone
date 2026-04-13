# 研究报告: PAVOne v0.3.0 工程质量提升

**功能**: 002-eng-quality-uplift
**日期**: 2026-04-13

## 1. setup.cfg 迁移分析

### Decision: 删除 setup.cfg，仅迁移 flake8 配置

### Rationale:
setup.cfg 包含 6 个配置段：`[flake8]`、`[tool:pytest]`、`[mypy]`、`[coverage:run]`、`[coverage:report]`、`[coverage:html]`。经审查，pytest、mypy、coverage 的配置已全部存在于 pyproject.toml 中（且 pyproject.toml 的版本更新更完整）。唯一缺失的是 `[flake8]` 配置。

flake8 不支持 `pyproject.toml` 原生配置（需要 `flake8-pyproject` 插件或使用独立的 `.flake8` 文件）。考虑到项目已使用 pyproject.toml 作为主配置，最简方案是创建 `.flake8` 文件存放 flake8 专属配置。

### Alternatives considered:
- **方案 A**: 安装 `flake8-pyproject` 插件 → 引入额外依赖，不推荐
- **方案 B**: 创建 `.flake8` 文件 → 最小侵入，flake8 原生支持 ✅ **选择此方案**
- **方案 C**: 保留 setup.cfg 仅含 flake8 → 文件名具误导性，不推荐

### 迁移清单:

| setup.cfg 段 | pyproject.toml 状态 | 操作 |
|-------------|-------------------|------|
| `[flake8]` | ❌ 不存在 | 迁移到 `.flake8` 文件 |
| `[tool:pytest]` | ✅ 已存在 `[tool.pytest.ini_options]` | 无需操作 |
| `[mypy]` | ✅ 已存在 `[tool.mypy]` | 无需操作 |
| `[coverage:run]` | ✅ 已存在 `[tool.coverage.run]` | 无需操作 |
| `[coverage:report]` | ✅ 已存在 `[tool.coverage.report]` | 无需操作 |
| `[coverage:html]` | ✅ 已存在 `[tool.coverage.html]` | 无需操作 |

**注意**: setup.cfg 中 mypy 的 `python_version = 3.9` 与 pyproject.toml 的 `python_version = "3.10"` 不一致，以 pyproject.toml 为准。

---

## 2. SSL 验证默认值分析

### Decision: 将 HttpUtils.fetch() 的 verify_ssl 默认值从 False 改为 True

### Rationale:

**关键发现**: 存在默认值不一致问题：
- `HttpUtils.fetch()` (http_utils.py): `verify_ssl: bool = False`
- `BasePlugin.fetch()` (plugins/base.py): `verify_ssl: bool = True`

由于大部分插件通过 `BasePlugin.fetch()` 调用（内部再调用 `HttpUtils.fetch()`），实际运行时 14 处未显式传入 verify_ssl 的调用 **已经使用 True**（来自 BasePlugin 的默认值）。因此，修改 HttpUtils 的默认值不会影响这些调用者。

**调用统计**:
- 3 处显式 `verify_ssl=True` (av01_plugin.py) → 无影响
- 6 处显式 `verify_ssl=False` (missav, ppvdatabank, supfc2) → 无影响（显式声明）
- 14 处无显式参数 → 通过 BasePlugin 传入 True → **无影响**

**Jellyfin**: 使用独立的 SSL 管理（jellyfin-apiclient-python 内置），不经过 http_utils，`JellyfinConfig.verify_ssl` 默认已为 True。无需额外处理。

### Alternatives considered:
- **方案 A**: 仅修改 HttpUtils 默认值 → 风险最低，与 BasePlugin 一致 ✅ **选择此方案**
- **方案 B**: 同时添加配置文件层面的全局 SSL 开关 → 过度工程化，本版本不需要

---

## 3. Python 版本确认

### Decision: 统一 Python 版本要求为 >=3.10

### Rationale:
代码库确认使用了 Python 3.10+ 特性：
- **Walrus 操作符** (`:=`): 在 `pavone/utils/code_extract_utils.py` 多处使用（实际为 3.8+ 特性）
- **PEP 604 类型联合** (`X | Y`): 在 `pavone/manager/plugin_manager.py` 使用（3.10+ 特性）

pyproject.toml 已正确声明 `>=3.10`。需修改：
- README.md: "3.9+" → "3.10+"
- setup.py: `>=3.9` → 删除文件
- setup.cfg: mypy `python_version = 3.9` → 删除文件

### Alternatives considered:
- 降低到 3.9 → 需移除 PEP 604 语法，增加维护负担，不推荐

---

## 4. --no-color 实现策略

### Decision: 在 Click 主命令组添加 --no-color 选项，同时支持 NO_COLOR 环境变量

### Rationale:
当前 Rich 使用集中在 `pavone/manager/progress.py`（进度条）。Click 主入口 `pavone/cli/__init__.py` 已有 `--verbose` 选项和 `click.pass_context` 模式。添加 `--no-color` 遵循相同模式：
1. 在 `main()` 添加 `@click.option("--no-color")`
2. 存入 `ctx.obj["no_color"]`
3. 检测 `NO_COLOR` 环境变量（https://no-color.org/）
4. 传入 Rich Console 的 `no_color` 参数

### Alternatives considered:
- 仅使用环境变量 → 不够直观，CLI 工具应提供显式选项
- 使用 click-extra 库 → 引入额外依赖，不推荐

---

## 5. 异常层级设计

### Decision: 创建以 PavoneError 为根的异常层级，让 JellyfinException 继承自 PavoneError

### Rationale:
当前仅 `jellyfin/exceptions.py` 有自定义异常（6 个，继承自 `Exception`）。全项目约 50+ 处 `except Exception`。

异常层级按功能域划分：
- `PavoneError` → 所有应用异常的基类
- `NetworkError` → 网络请求失败
- `DownloadError` → 下载过程错误
- `ExtractError` → URL/元数据提取错误
- `PluginError` → 插件系统错误
- `ConfigError` → 配置相关错误
- `MetadataError` → 元数据处理错误

渐进式替换策略：优先处理 CLI 层（用户直接看到的）和核心模块，不要求一次性替换所有 `except Exception`。

### Alternatives considered:
- 扁平异常（全部直接继承 Exception） → 无法在 CLI 统一捕获
- 更深层级（每个插件独立异常树） → 过度设计

---

## 6. print() 替换策略

### Decision: 分三类替换，用 click.echo() 处理用户输出，logger 处理日志

### Rationale:
项目中 79 处 print() 调用，分为：
1. **用户交互输出**（搜索结果、进度、表格展示）→ `click.echo()`
2. **错误/警告**（config/manager.py 的 ERROR/WARNING）→ `logger.error()` / `logger.warning()`
3. **调试信息** → `logger.debug()`

章程规定："用户可见的进度信息 MUST 通过 Rich 或 tqdm 呈现。错误信息 MUST 输出到 stderr"。

### Alternatives considered:
- 全部改为 logger → 用户交互输出不应走日志系统
- 全部改为 click.echo → 错误/警告信息应通过 logger 输出到 stderr

---

## 7. flake8 配置迁移

### Decision: 创建 `.flake8` 文件

### Rationale:
从 setup.cfg 迁移以下配置：
```ini
[flake8]
max-line-length = 127
max-complexity = 20
exclude = .git,__pycache__,build,dist,*.egg-info,.venv,venv
```

flake8 不原生支持 pyproject.toml，需要独立配置文件。

---

## 8. 测试基础设施分析

### Decision: 创建 tests/conftest.py 集中管理共享 fixtures

### Rationale:
当前 14 个 @pytest.fixture 分散在各测试文件中，存在重复：
- `Config()` fixture 在 test_file_mover.py 和 test_file_operation_builder.py 重复定义
- 临时目录 fixture 在多个文件重复

共享 fixtures 候选：
- `config` — 测试用 Config 实例
- `temp_workspace` — 基于 tmp_path 的临时工作目录
- `sample_metadata` — 示例元数据字典

### Alternatives considered:
- 保持分散 → 违反 DRY 原则，增加维护成本

---

## 9. CI 安全扫描分析

### Decision: 移除 `|| true` 后缀，但为误报提供策略文件

### Rationale:
CI 中 safety 和 bandit 均使用 `|| true` 静默忽略失败：
- `uv run safety check --json || true`
- `uv run bandit -r pavone/ -f json || true`

移除 `|| true` 前需：
1. 运行 safety check 确认当前是否有真实漏洞
2. 运行 bandit 确认当前误报数量
3. 对误报使用 `# nosec` 注释或 `.bandit` 排除文件
4. 对无法立即修复的真实漏洞使用 `.safety-policy.yml` 显式忽略

### Alternatives considered:
- 使用 `continue-on-error: true` → 与 `|| true` 效果相同，不推荐
- 完全移除安全扫描 → 违背安全原则

---

## 10. 依赖上界约束策略

### Decision: 使用 `<N` 约束主版本号上界

### Rationale:
当前所有依赖使用 `>=` 无上界。添加上界约束策略：
```
requests>=2.31.0,<3
beautifulsoup4>=4.12.0,<5
click>=8.1.0,<9
rich>=13.0.0,<15
pydantic>=2.12.4,<3
lxml>=4.9.0,<6
pillow>=10.0.0,<12
```

上界设为当前主版本号的下一个（或已知兼容的范围）。

### Alternatives considered:
- 使用 `~=` 兼容约束 → 过于严格，可能阻止补丁更新
- 不加上界 → 大版本升级可能破坏兼容性

# PAVOne Agent Instructions

本文件是仓库内 AI 编程和自动化修改的唯一规范源。所有代理在分析、编码、测试、提交和创建 PR 时都必须遵守。

## Build, Test, and Lint

```bash
uv sync
uv run pytest tests/ -v
uv run pytest tests/test_foo.py::test_bar
uv run pytest -m integration
uv run black pavone/ tests/
uv run isort pavone/ tests/
uv run flake8 pavone/ tests/
uv run pyright pavone/
make -f scripts/Makefile check
```

仅运行覆盖当前改动所需的最小检查；修改依赖时只能使用 `uv add` 或 `uv sync`，禁止使用 `pip install` 和
`uv pip install`。

## Architecture

- `pavone/cli/`: Click 命令层，统一将 `PavoneError` 映射为 `ExitCode`。
- `pavone/plugins/`: 插件系统；所有插件继承 `BasePlugin`，优先级数值越低越优先。
- `pavone/core/`: 下载器、元数据基础设施、异常层次和退出码。
- `pavone/config/`: Pydantic 配置，通过 `get_config_manager()` 访问。
- `pavone/jellyfin/`: Jellyfin 集成。

## Code Conventions

- 新代码必须包含类型标注，并通过 Pyright。
- 用户输出使用 `click.echo()`，日志使用 `pavone.config.logging_config.get_logger()`；禁止使用 `print()`。
- 应用异常必须继承 `PavoneError`，并优先使用已有领域异常。
- Black 与 isort 行宽均为 127；需要注释或 docstring 时使用中文。
- 测试放在 `tests/`；集成测试标记为 `integration`，网络测试标记为 `network`。
- SSL 默认开启；如确需关闭，必须说明原因并记录安全警告。
- 不修改无关代码，不覆盖用户现有改动，不通过宽泛捕获或静默回退掩盖错误。

## Pull Requests and Releases

- PR 标题必须符合 Conventional Commits：`type(scope)!: description`。允许的 type 为 `feat`、`fix`、`docs`、
  `refactor`、`perf`、`test`、`build`、`ci`、`chore`、`style`、`revert`。
- `feat` 默认递增 minor；带 `!` 或包含 `BREAKING` 默认递增 major；其余默认递增 patch。
- 如需覆盖推断，只能添加一个标签：`release:major`、`release:minor`、`release:patch`、`release:skip`。
- PR 正文必须保留 `release-notes:start` 与 `release-notes:end` 标记，并用中文填写面向用户的变更。
- Release Notes 仅允许 `### 新增`、`### 修复`、`### 改进`、`### 重大变更`、`### 变更`，每项使用 `- `。
- 测试、格式化、重命名等纯内部变化不要写入 Release Notes；无用户可感知变化时使用 `release:skip`。
- major 变更必须提供 `### 重大变更`，并说明兼容性影响或迁移方式。
- 普通 PR 禁止手动修改 `pyproject.toml`、`pavone/__init__.py` 中的版本号及 CHANGELOG 版本条目；发布工作流统一处理。

创建或更新 PR 前，代理必须检查标题、发布标签和 Release Notes 是否满足以上规则。

# 贡献指南

感谢你对 PAVOne 的兴趣！以下是参与开发的指南。

## 开发环境搭建

### 环境要求

- Python 3.10+
- [uv](https://docs.astral.sh/uv/) (推荐) 或 pip

### 快速开始

```bash
# 克隆仓库
git clone https://github.com/imbatony/pavone.git
cd pavone

# 安装依赖
uv sync

# 安装 pre-commit hooks (可选但推荐)
pip install pre-commit
pre-commit install

# 运行测试
uv run pytest
```

## 代码风格

本项目使用以下工具保持代码质量：

- **Black** — 代码格式化 (行宽 127)
- **isort** — import 排序 (black profile, 行宽 127)
- **flake8** — 代码质量检查
- **Pyright** — 静态类型检查 (standard 模式)

### 格式化代码

```bash
# Windows
.\scripts\dev.ps1 format

# Linux/macOS
make -f scripts/Makefile format
```

### 运行检查

```bash
# Windows
.\scripts\dev.ps1 type-check

# Linux/macOS
make -f scripts/Makefile type-check
```

## 测试

```bash
# 运行所有单元测试
uv run pytest

# 运行测试并生成覆盖率报告
uv run pytest --cov=pavone --cov-report=html

# Windows 快捷方式
.\scripts\dev.ps1 test

# Linux/macOS
make -f scripts/Makefile test
```

### 测试规范

- 测试遵循 AAA 模式 (Arrange-Act-Assert)
- 集成测试使用 `@pytest.mark.integration` 标记
- 网络测试使用 `@pytest.mark.network` 标记
- 仅在系统边界使用 Mock

## 提交代码

### 分支命名

- `feat/描述` — 新功能
- `fix/描述` — Bug 修复
- `docs/描述` — 文档更新
- `refactor/描述` — 重构

### 提交消息

推荐使用 [Conventional Commits](https://www.conventionalcommits.org/) 规范：

```
feat: 添加新的搜索插件
fix: 修复 SSL 验证默认值
docs: 更新 README 版本说明
refactor: 统一异常处理
test: 添加退出码测试
chore: 更新依赖版本
```

### PR 流程

1. Fork 仓库并创建分支
2. 编写代码和测试
3. 确保所有检查通过：`make -f scripts/Makefile check` 或 `.\scripts\dev.ps1 check`
4. 使用 Conventional Commits 格式填写 PR 标题
5. 在 PR 模板的 Release Notes 标记内，用中文填写用户可感知的变更
6. 如需覆盖自动版本推断，添加且仅添加一个 `release:major`、`release:minor`、`release:patch` 或
   `release:skip` 标签
7. 不要手动修改版本号和 CHANGELOG 版本条目，发布工作流会在合并后统一处理
8. 提交 PR 并在描述中说明变更内容和测试方式
9. 等待 PR Conventions、CI 和代码审查通过

版本默认按标题推断：`feat` 为 minor，带 `!` 或包含 `BREAKING` 为 major，其余为 patch。没有用户可感知变化时，
使用 `release:skip`；major 变更必须在 Release Notes 中提供 `### 重大变更` 小节和迁移说明。

## 开发工具

| 平台 | 命令 |
|------|------|
| Windows | `.\scripts\dev.ps1 <command>` |
| Linux/macOS | `make -f scripts/Makefile <command>` |

可用命令：`install`, `test`, `lint`, `format`, `type-check`, `check`, `ci`

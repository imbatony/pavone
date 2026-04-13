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
.\dev.ps1 format

# Linux/macOS
make format
```

### 运行检查

```bash
# Windows
.\dev.ps1 type-check

# Linux/macOS
make type-check
```

## 测试

```bash
# 运行所有单元测试
uv run pytest

# 运行测试并生成覆盖率报告
uv run pytest --cov=pavone --cov-report=html

# Windows 快捷方式
.\dev.ps1 test

# Linux/macOS
make test
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
3. 确保所有检查通过：`make check` 或 `.\dev.ps1 check`
4. 提交 PR 并在描述中说明变更内容和测试方式
5. 等待 CI 通过和代码审查

## 开发工具

| 平台 | 命令 |
|------|------|
| Windows | `.\dev.ps1 <command>` |
| Linux/macOS | `make <command>` |

可用命令：`install`, `test`, `lint`, `format`, `type-check`, `check`, `ci`

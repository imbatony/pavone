# 开发工作流

本文档说明如何使用 `dev.ps1` 脚本进行本地开发和测试。

## 快速开始

```powershell
# 1. 安装依赖
.\dev.ps1 install

# 2. 激活开发环境
.\dev.ps1 dev

# 3. 运行测试
.\dev.ps1 test
```

## 可用命令

### 📦 环境管理

- `.\dev.ps1 install` - 安装项目依赖
- `.\dev.ps1 dev` - 激活虚拟环境
- `.\dev.ps1 clean` - 清理缓存文件

### 🧪 测试命令

- `.\dev.ps1 test` - 运行单元测试（不包括集成测试）**推荐用于日常开发**
- `.\dev.ps1 test-all` - 运行所有测试（包括集成测试）
- `.\dev.ps1 test-cov` - 运行测试并生成覆盖率报告

### 🎨 代码质量

- `.\dev.ps1 format` - 格式化代码（black + isort）
- `.\dev.ps1 format-check` - 检查代码格式（不修改文件）
- `.\dev.ps1 lint` - 运行 lint 检查（flake8）
- `.\dev.ps1 type-check` - 运行类型检查（pyright）
- `.\dev.ps1 check` - 运行完整代码质量检查（format + lint + type-check）

### 🚀 CI/CD

- `.\dev.ps1 ci` - 运行完整 CI 流程（本地模拟）

### 📦 其他

- `.\dev.ps1 run [args]` - 运行 PAVOne CLI
- `.\dev.ps1 build` - 构建项目包

## 开发工作流

### 日常开发

1. **编写代码**
2. **格式化代码**：`.\dev.ps1 format`
3. **运行测试**：`.\dev.ps1 test`
4. **提交代码**

### 提交前检查

提交代码前，运行完整检查：

```powershell
.\dev.ps1 check
```

这将依次运行：
1. 代码格式检查（black、isort）
2. 代码质量检查（flake8）
3. 类型检查（pyright）

### 本地模拟 CI

在提交 PR 前，可以本地模拟完整的 CI 流程：

```powershell
.\dev.ps1 ci
```

这将运行：
1. 完整代码质量检查
2. 单元测试并生成覆盖率报告

## 代码规范

### 格式化规则

- **Black**：行长度 127，Python 3.10+
- **isort**：使用 black profile，按标准库、第三方库、本地模块排序

### Lint 规则

- **flake8**：
  - 最大行长度：127
  - 最大复杂度：10
  - 严格检查：E9（语法错误）、F63/F7/F82（未定义、未使用等）

### 类型检查

- **Pyright**（Pylance 后端）：严格模式，检查所有类型错误

## 测试策略

### 单元测试 vs 集成测试

- **单元测试**：默认运行，快速验证功能
- **集成测试**：需要外部资源（网络、数据库等），使用 `@pytest.mark.integration` 标记

### 运行特定测试

```powershell
# 运行单元测试（默认）
.\dev.ps1 test

# 运行所有测试
.\dev.ps1 test-all

# 运行特定测试文件
uv run pytest tests/test_specific.py -v

# 运行特定测试函数
uv run pytest tests/test_specific.py::test_function -v
```

## 常见问题

### 格式检查失败

运行 `.\dev.ps1 format` 自动修复格式问题。

### 类型检查失败

检查 Pyright 输出的错误信息，添加必要的类型注解。

### 测试失败

1. 确保依赖已安装：`.\dev.ps1 install`
2. 检查测试输出的错误信息
3. 使用 `-v` 参数查看详细输出

## VS Code 集成

推荐的 VS Code 设置：

```json
{
  "python.formatting.provider": "black",
  "python.linting.enabled": true,
  "python.linting.flake8Enabled": true,
  "python.linting.pylintEnabled": false,
  "editor.formatOnSave": true,
  "[python]": {
    "editor.codeActionsOnSave": {
      "source.organizeImports": true
    }
  }
}
```

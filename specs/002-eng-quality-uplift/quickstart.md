# 快速开始: PAVOne v0.3.0 工程质量提升

**功能**: 002-eng-quality-uplift

## 概述

本功能无新增用户可见功能，专注于工程质量提升。以下是各变更对用户和开发者的影响说明。

## 对最终用户的影响

### 1. 安装方式不变

```bash
# 以下方式继续正常工作
pip install -e .
uv tool install .
```

`setup.py` 和 `setup.cfg` 被删除后，`pip` 和 `uv` 自动使用 `pyproject.toml`，用户无需任何操作。

### 2. SSL 验证默认开启

默认行为更安全。如果连接自签名证书的 Jellyfin 服务器，需在配置中显式设置 `verify_ssl = false`。

### 3. 更清晰的错误信息

原来：
```
Error: 发生错误
```

现在：
```
ERROR: 网络请求失败: 无法连接到 example.com (连接超时)
```

### 4. 新增 --no-color 选项

```bash
# 禁用颜色输出
pavone --no-color search "test"

# 通过环境变量
NO_COLOR=1 pavone search "test"
```

## 对开发者的影响

### 1. 异常处理

```python
# 新的异常层级
from pavone.core.exceptions import PavoneError, NetworkError, DownloadError

try:
    # 业务逻辑
    ...
except NetworkError as e:
    logger.error(f"网络错误: {e}")
except PavoneError as e:
    logger.error(f"应用错误: {e}")
```

### 2. 退出码

```python
from pavone.core.exit_codes import ExitCode

sys.exit(ExitCode.NETWORK_ERROR)
```

### 3. 输出规范

```python
# ❌ 不再使用
print("搜索结果:")

# ✅ 用户交互输出
click.echo("搜索结果:")

# ✅ 错误/警告
logger.error("加载配置失败: %s", e)
```

### 4. 新贡献者流程

```bash
# 克隆代码
git clone <repo>
cd pavone

# 安装依赖
uv sync

# 安装 pre-commit hooks
pip install pre-commit && pre-commit install

# 运行测试
uv run pytest        # 或 make test (Linux/macOS)
dev.ps1 test         # 或 (Windows)

# 类型检查
uv run pyright       # 或 make type-check
```

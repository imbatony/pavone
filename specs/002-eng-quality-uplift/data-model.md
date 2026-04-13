# 数据模型: PAVOne v0.3.0 工程质量提升

**功能**: 002-eng-quality-uplift
**日期**: 2026-04-13

## 1. 异常层级体系

### 实体: PavoneError (基础异常)

所有 PAVOne 应用层异常的根基类。CLI 最外层统一捕获此类型以输出友好错误信息。

**层级关系**:

```
Exception
└── PavoneError
    ├── NetworkError          # 网络请求失败 (连接超时, DNS 解析, SSL 错误等)
    ├── DownloadError         # 下载过程错误 (分片失败, 合并失败, 空间不足等)
    ├── ExtractError          # URL/元数据提取错误 (页面结构变更, 正则不匹配等)
    ├── PluginError           # 插件系统错误 (加载失败, 初始化失败, 生命周期异常)
    ├── ConfigError           # 配置相关错误 (文件不存在, 格式错误, 验证失败)
    ├── MetadataError         # 元数据处理错误 (解析失败, 字段缺失, 写入失败)
    └── JellyfinException     # [已有] Jellyfin 集成错误 (改为继承 PavoneError)
        ├── JellyfinConnectionError
        ├── JellyfinAuthenticationError
        ├── JellyfinAPIError
        ├── JellyfinVideoMatchError
        └── JellyfinLibraryError
```

**属性**:
- `message: str` — 用户友好的错误描述
- `__str__()` — 返回 message

### 实体: ExitCode (退出码常量)

CLI 命令的退出码枚举，用于脚本化处理和错误分类。

**字段**:

| 常量名 | 值 | 说明 |
|--------|-----|------|
| SUCCESS | 0 | 命令成功完成 |
| GENERAL_ERROR | 1 | 通用错误 |
| USAGE_ERROR | 2 | 命令用法/参数错误 |
| NETWORK_ERROR | 3 | 网络请求失败 |
| CONFIG_ERROR | 4 | 配置错误 |

**映射关系** (异常→退出码):

| 异常类型 | 退出码 |
|---------|--------|
| PavoneError (通用) | GENERAL_ERROR (1) |
| NetworkError | NETWORK_ERROR (3) |
| ConfigError | CONFIG_ERROR (4) |
| Click UsageError | USAGE_ERROR (2) |
| 未捕获异常 | GENERAL_ERROR (1) |

---

## 2. 配置文件结构

### 现有实体变更

**pyproject.toml** — 唯一构建配置文件:
- 新增: `[tool.setuptools.package-data]` 包含 `py.typed`
- 修改: `dependencies` 添加版本上界约束

**已删除实体**:
- `setup.py` — 冗余构建配置
- `setup.cfg` — 冗余配置 (flake8 迁移到 `.flake8`)

### 新增配置文件

**.flake8** — flake8 独立配置:
- `max-line-length = 127`
- `max-complexity = 20`
- `exclude` 列表

**.pre-commit-config.yaml** — Git 提交检查钩子:
- hooks: black, isort, flake8, trailing-whitespace, end-of-file-fixer

---

## 3. CLI 上下文扩展

### 现有实体变更: Click Context (ctx.obj)

**新增字段**:

| 字段 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `no_color` | `bool` | `False` | 禁用颜色输出 (通过 --no-color 或 NO_COLOR 环境变量) |

**状态转换**:
- `no_color = False` → 终端正常彩色输出
- `no_color = True` → Rich Console 禁用颜色, click.echo 不使用 ANSI 转义码

---

## 4. 新增项目文件

| 文件路径 | 类型 | 说明 |
|---------|------|------|
| `pavone/core/exceptions.py` | Python 模块 | 全局异常层级定义 |
| `pavone/core/exit_codes.py` | Python 模块 | 退出码常量 |
| `pavone/py.typed` | 标记文件 | PEP 561 类型支持声明 (空文件) |
| `.flake8` | 配置文件 | flake8 配置 (从 setup.cfg 迁移) |
| `.pre-commit-config.yaml` | 配置文件 | Git hooks 配置 |
| `CONTRIBUTING.md` | 文档 | 贡献指南 |
| `Makefile` | 构建脚本 | 跨平台任务运行器 |
| `tests/conftest.py` | Python 模块 | 共享测试 fixtures |

## 5. 测试 Fixtures

### 实体: 共享测试 Fixtures (tests/conftest.py)

**Fixtures**:

| Fixture 名 | Scope | 返回类型 | 说明 |
|------------|-------|---------|------|
| `config` | function | Config | 测试用配置实例 (默认配置) |
| `temp_workspace` | function | Path | 基于 tmp_path 的临时工作目录 |
| `sample_metadata` | function | dict | 示例元数据字典 |

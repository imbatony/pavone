# PAVOne 开发文档

## 📁 项目结构

```
pavone/
├── pavone/                         # 主包
│   ├── __init__.py
│   ├── __main__.py                 # 包入口点
│   ├── cli.py                      # 命令行接口
│   ├── cli/                        # CLI 命令模块
│   │   ├── __init__.py
│   │   ├── commands/               # 具体命令实现
│   │   │   ├── __init__.py
│   │   │   ├── config.py           # 配置管理命令
│   │   │   ├── download.py         # 下载命令
│   │   │   ├── init.py             # 初始化命令
│   │   │   └── batch_download.py   # 批量下载命令
│   │   └── utils.py                # CLI 工具函数
│   ├── core/                       # 核心功能模块
│   │   ├── __init__.py
│   │   ├── base.py                 # 基础类定义
│   │   ├── dummy.py                # 虚拟实现
│   │   ├── utils.py                # 核心工具函数
│   │   └── downloader/             # 下载器实现
│   │       ├── __init__.py
│   │       ├── http.py             # HTTP下载器
│   │       └── m3u8.py             # M3U8下载器
│   ├── models/                     # 数据模型
│   │   ├── __init__.py
│   │   ├── constants.py            # 常量定义
│   │   ├── metadata.py             # 元数据模型
│   │   ├── operation.py            # 操作项和结果模型
│   │   └── progress_info.py        # 进度信息模型
│   ├── manager/                    # 管理器模块
│   │   ├── __init__.py
│   │   ├── execution.py            # 执行管理器
│   │   └── progress.py             # 进度管理器
│   ├── plugins/                    # 插件系统
│   │   ├── __init__.py
│   │   ├── base.py                 # 插件基类
│   │   ├── manager.py              # 插件管理器
│   │   ├── extractors/             # 提取器插件
│   │   │   ├── __init__.py
│   │   │   ├── base.py             # 提取器基类
│   │   │   ├── direct_link.py      # 直接链接提取器
│   │   │   └── missav.py           # MissAV提取器(可选)
│   │   ├── metadata/               # 元数据插件目录
│   │   │   └── __init__.py
│   │   └── search/                 # 搜索插件目录
│   │       └── __init__.py
│   ├── config/                     # 配置管理
│   │   ├── __init__.py
│   │   ├── configs.py              # 配置数据类
│   │   ├── logging_config.py       # 日志配置
│   │   ├── manager.py              # 配置管理器
│   │   ├── settings.py             # 设置管理
│   │   └── validator.py            # 配置验证
│   └── utils/                      # 工具模块
│       ├── __init__.py
│       └── stringutils.py          # 字符串工具
├── tests/                          # 测试套件
│   ├── __init__.py
│   ├── test_*.py                   # 各种测试文件
│   ├── metadata/                   # 测试元数据
│   └── sites/                      # 测试站点数据
├── docs/                           # 文档
│   ├── *.md                        # 各种文档文件
├── examples/                       # 示例代码
├── downloads/                      # 默认下载目录
├── logs/                           # 日志目录
├── pyproject.toml                  # 项目配置
├── pyrightconfig.json              # 类型检查配置
├── setup.cfg                       # 工具配置
├── setup.py                        # 安装脚本
├── requirements.txt                # 依赖
├── LICENSE                         # 许可证
├── dev.ps1                         # 开发脚本
└── README.md                       # 项目说明
```

## 🏗️ 核心架构

### 统一操作模型

PAVOne 采用统一的操作模型，所有功能都通过 `OperationItem` 描述：

```python
@dataclass
class OperationItem:
    operation_type: OperationType
    url: Optional[str] = None
    urls: Optional[List[str]] = None  # 批量操作
    output_dir: Optional[str] = None
    filename: Optional[str] = None
    auto_select: bool = False
    silent: bool = False
    progress_callback: Optional[Callable] = None
    metadata: Optional[Dict] = None
```

### 执行管理器

`ExecutionManager` 是核心组件，负责：
- 操作项验证和预处理
- 提取器插件的自动发现
- 下载器的选择和配置
- 进度监控和错误处理
- 统一的结果返回

```python
class ExecutionManager:
    def execute(self, operation: OperationItem) -> OperationResult:
        """执行操作项并返回结果"""
        pass
```

### 数据模型层 (models/)

#### `operation.py` - 操作和结果模型

```python
@dataclass
class OperationItem:
    """操作项：描述要执行的操作"""
    operation_type: OperationType
    url: Optional[str] = None
    # ... 其他字段

@dataclass
class OperationResult:
    """操作结果：统一的返回格式"""
    success: bool
    message: str = ""
    error: Optional[str] = None
    output_path: Optional[str] = None
    # ... 其他字段

@dataclass
class DownloadOption:
    """下载选项：描述一个可下载的内容"""
    url: str
    filename: str
    quality: Optional[str] = None
    format: Optional[str] = None
    # ... 其他字段
```

#### `progress_info.py` - 进度信息模型

```python
@dataclass
class ProgressInfo:
    """下载进度信息"""
    downloaded: int = 0
    total_size: int = 0
    speed: float = 0.0
    percentage: float = 0.0
    elapsed_time: float = 0.0
    estimated_time: float = 0.0
```

### 插件系统 (plugins/)

#### 插件基类架构

```python
class BasePlugin(ABC):
    """所有插件的基类"""
    @abstractmethod
    def initialize(self) -> bool: pass
    
    @abstractmethod
    def execute(self, *args, **kwargs) -> Any: pass

class ExtractorPlugin(BasePlugin):
    """提取器插件基类"""
    @abstractmethod
    def can_handle(self, url: str) -> bool: pass
    
    @abstractmethod
    def extract(self, url: str) -> List[DownloadOption]: pass
```

#### 内置提取器

- **DirectLinkExtractor**: 处理直接下载链接 (.mp4, .m3u8 等)
- **MissAVExtractor**: MissAV 网站提取器（可选）

#### 插件管理器

```python
class PluginManager:
    """插件管理器：负责插件的加载、注册和管理"""
    
    def load_plugins(self, plugin_dir: Optional[str] = None):
        """自动加载插件"""
        pass
        
    def get_extractor_for_url(self, url: str) -> Optional[ExtractorPlugin]:
        """获取最适合的提取器"""
        pass
        
    def register_extractor(self, extractor: ExtractorPlugin):
        """注册提取器"""
        pass
```

### 下载器层 (core/downloader/)

#### HTTP 下载器

```python
class HTTPDownloader:
    """HTTP/HTTPS 文件下载器"""
    
    def download(self, url: str, output_path: str, 
                 progress_callback: Optional[Callable] = None) -> bool:
        """下载文件"""
        pass
```

#### M3U8 下载器

```python
class M3U8Downloader:
    """HLS (M3U8) 流媒体下载器"""
    
    def download(self, m3u8_url: str, output_path: str,
                 progress_callback: Optional[Callable] = None) -> bool:
        """下载 M3U8 流媒体"""
        pass
```

### 配置管理 (config/)

#### 配置数据类

```python
@dataclass
class Config:
    """主配置类"""
    output_dir: str = "./downloads"
    max_concurrent_downloads: int = 3
    timeout: int = 30
    user_agent: str = "..."
    proxy: Optional[Dict[str, Any]] = None
    logging: Optional[Dict[str, Any]] = None
```

#### 配置管理器

```python
class ConfigManager:
    """配置管理器：负责配置的读取、写入和验证"""
    
    def load_config(self) -> Config: pass
    def save_config(self, config: Config): pass
    def validate_config(self, config: Config) -> List[str]: pass
```

## 🚀 开发指南

### 添加新的提取器插件

1. **继承 ExtractorPlugin 基类**

```python
from pavone.plugins.extractors.base import ExtractorPlugin
from pavone.models.operation import DownloadOption
from typing import List

class MyExtractor(ExtractorPlugin):
    def __init__(self):
        super().__init__()
        self.name = "MyExtractor"
        self.priority = 10  # 数值越小优先级越高
        self.description = "自定义网站提取器"
    
    def can_handle(self, url: str) -> bool:
        """检查是否能处理该URL"""
        return "mysite.com" in url
    
    def extract(self, url: str) -> List[DownloadOption]:
        """提取下载选项"""
        # 实现网站特定的提取逻辑
        return [
            DownloadOption(
                url="https://mysite.com/video.mp4",
                filename="video.mp4",
                quality="1080p",
                format="mp4"
            )
        ]
    
    def initialize(self) -> bool:
        """初始化插件（检查依赖等）"""
        return True
    
    def execute(self, *args, **kwargs) -> List[DownloadOption]:
        """执行插件（委托给extract方法）"""
        if args:
            return self.extract(args[0])
        return []
```

2. **注册插件**

```python
from pavone.plugins.manager import plugin_manager

# 创建并注册插件
extractor = MyExtractor()
if extractor.initialize():
    plugin_manager.register_extractor(extractor)
```

3. **自动加载（推荐）**

将插件文件放在 `~/.pavone/plugins/extractors/` 目录下，系统会自动加载。

### 添加新的下载器

1. **实现下载器接口**

```python
from pavone.core.downloader.base import BaseDownloader
from pavone.models.progress_info import ProgressInfo
from typing import Optional, Callable

class MyDownloader:
    """自定义下载器"""
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
    
    def download(self, url: str, output_path: str,
                 progress_callback: Optional[Callable[[ProgressInfo], None]] = None) -> bool:
        """下载文件"""
        try:
            # 实现下载逻辑
            total_size = self._get_file_size(url)
            downloaded = 0
            
            # 模拟下载过程
            while downloaded < total_size:
                # 下载数据块...
                downloaded += chunk_size
                
                # 更新进度
                if progress_callback:
                    progress = ProgressInfo(
                        downloaded=downloaded,
                        total_size=total_size,
                        percentage=(downloaded / total_size) * 100
                    )
                    progress_callback(progress)
            
            return True
        except Exception as e:
            print(f"下载失败: {e}")
            return False
```

2. **集成到 ExecutionManager**

修改 `ExecutionManager` 以支持新的下载器。

### 添加新的命令

1. **创建命令模块**

```python
# pavone/cli/commands/my_command.py
import click
from pavone.manager.execution import ExecutionManager
from pavone.models.operation import OperationItem, OperationType

@click.command()
@click.argument('url')
@click.option('--output', '-o', help='输出目录')
def my_command(url: str, output: str):
    """自定义命令的描述"""
    manager = ExecutionManager()
    
    operation = OperationItem(
        operation_type=OperationType.DOWNLOAD,  # 或自定义类型
        url=url,
        output_dir=output
    )
    
    result = manager.execute(operation)
    
    if result.success:
        click.echo(f"操作成功: {result.message}")
    else:
        click.echo(f"操作失败: {result.error}", err=True)
```

2. **注册命令**

在 `pavone/cli/__init__.py` 中注册新命令：

```python
from .commands.my_command import my_command

cli.add_command(my_command)
```

## 🧪 测试框架

### 测试结构

```
tests/
├── __init__.py
├── test_*.py                       # 各种功能测试
├── metadata/                       # 测试用元数据文件
│   ├── movie1.nfo
│   └── movie2.nfo
├── sites/                          # 测试用网站数据
│   ├── missav.html
│   ├── missav.m3u8
│   ├── missav2.html
│   └── missav2.m3u8
```

### 主要测试文件

- `test_config.py` - 配置系统测试
- `test_download_manager.py` - 下载管理测试
- `test_download_options.py` - 下载选项测试
- `test_downloader.py` - 下载器基础测试
- `test_extractor_base.py` - 提取器基类测试
- `test_logging_config.py` - 日志配置测试
- `test_m3u8_downloader.py` - M3U8下载器测试
- `test_missav_extractor.py` - MissAV提取器测试
- `test_organizer.py` - 文件整理测试

### 运行测试

```bash
# 运行所有测试
python -m pytest tests/ -v

# 运行特定测试文件
python -m pytest tests/test_downloader.py -v

# 运行带覆盖率的测试
python -m pytest tests/ --cov=pavone --cov-report=html --cov-report=term-missing

# 运行特定测试方法
python -m pytest tests/test_m3u8_downloader.py::TestM3U8Downloader::test_download -v

# 使用VS Code任务
pavone run tests  # 或在VS Code中运行 "run tests" 任务
```

### 测试最佳实践

1. **使用 Mock 模拟网络请求**

```python
import unittest.mock as mock
from pavone.core.downloader.http import HTTPDownloader

def test_http_download_success():
    with mock.patch('requests.get') as mock_get:
        mock_response = mock.Mock()
        mock_response.status_code = 200
        mock_response.headers = {'content-length': '1024'}
        mock_response.iter_content.return_value = [b'data'] * 1024
        mock_get.return_value = mock_response
        
        downloader = HTTPDownloader()
        result = downloader.download("http://example.com/file.mp4", "./test.mp4")
        
        assert result is True
        mock_get.assert_called_once()
```

2. **测试插件系统**

```python
def test_extractor_plugin_registration():
    from pavone.plugins.manager import plugin_manager
    from pavone.plugins.extractors.base import ExtractorPlugin
    
    class TestExtractor(ExtractorPlugin):
        def can_handle(self, url: str) -> bool:
            return "test.com" in url
        
        def extract(self, url: str) -> List[DownloadOption]:
            return []
    
    extractor = TestExtractor()
    plugin_manager.register_extractor(extractor)
    
    result = plugin_manager.get_extractor_for_url("https://test.com/video")
    assert result is not None
    assert isinstance(result, TestExtractor)
```

3. **测试操作执行**

```python
def test_execution_manager():
    from pavone.manager.execution import ExecutionManager
    from pavone.models.operation import OperationItem, OperationType
    
    manager = ExecutionManager()
    
    operation = OperationItem(
        operation_type=OperationType.DOWNLOAD,
        url="https://example.com/video.mp4",
        auto_select=True,
        silent=True
    )
    
    # 使用 mock 避免实际下载
    with mock.patch.object(manager, '_execute_download') as mock_download:
        mock_download.return_value = True
        result = manager.execute(operation)
        
        assert result.success is True
        mock_download.assert_called_once()
```

## 🔧 代码质量工具

### 类型检查

```bash
# Pyright (Pylance后端) - 推荐
pyright pavone/

# MyPy
mypy pavone/
```

### 代码格式化

```bash
# Black 代码格式化
black pavone/ tests/

# isort 导入排序
isort pavone/ tests/

# 检查格式
black --check pavone/ tests/
isort --check-only pavone/ tests/
```

### 代码风格检查

```bash
# flake8 风格检查
flake8 pavone/ tests/

# pylint 深度分析
pylint pavone/
```

### 安全检查

```bash
# safety - 检查依赖漏洞
safety check

# bandit - 安全代码扫描
bandit -r pavone/
```

## 🚀 开发环境设置

### 必需环境

- **Python**: 3.9+ (推荐 3.11+)
- **包管理**: pip
- **版本控制**: Git

### 推荐开发工具

- **IDE**: Visual Studio Code
- **扩展**:
  - Python Extension Pack
  - Pylance (类型检查)
  - Black Formatter
  - isort
  - GitLens

### VS Code 配置

项目包含预配置文件：

- `pyrightconfig.json` - Pylance/Pyright 配置
- `pyproject.toml` - Black, isort, pytest 配置
- `setup.cfg` - flake8, coverage 配置
- `.vscode/tasks.json` - VS Code 任务配置

### 开发脚本

使用 `dev.ps1` (Windows PowerShell) 进行快速开发：

```powershell
# 格式化代码
./dev.ps1 format

# 运行类型检查
./dev.ps1 typecheck

# 运行测试
./dev.ps1 test

# 运行所有检查
./dev.ps1 check
```

### 环境变量

开发时可设置的环境变量：

```bash
# 启用调试模式
export PAVONE_DEBUG=1

# 指定配置文件
export PAVONE_CONFIG_FILE=/path/to/config.json

# 设置日志级别
export PAVONE_LOG_LEVEL=DEBUG

# 测试模式（使用测试数据）
export PAVONE_TEST_MODE=1
```

##  代码规范

### Python 版本要求

- **最低版本**: Python 3.9
- **推荐版本**: Python 3.11+
- **测试版本**: 3.9, 3.10, 3.11, 3.12

### 代码风格标准

- **格式化工具**: Black (line-length=127)
- **导入排序**: isort (配合Black)
- **风格检查**: flake8, pylint
- **类型检查**: mypy, pyright/Pylance

### 命名规范

- **文件名**: 小写字母+下划线 (`snake_case`)
- **类名**: 大驼峰 (`PascalCase`)
- **函数/变量名**: 小写字母+下划线 (`snake_case`)
- **常量**: 大写字母+下划线 (`UPPER_CASE`)
- **私有成员**: 前缀下划线 (`_private`)

### 类型注解

所有公共接口都必须包含类型注解：

```python
from typing import Optional, List, Dict, Callable
from pavone.models.operation import OperationItem, OperationResult

def execute_operation(
    operation: OperationItem,
    progress_callback: Optional[Callable[[ProgressInfo], None]] = None
) -> OperationResult:
    """执行操作项并返回结果."""
    pass
```

### 文档字符串

使用 Google 风格的 docstring：

```python
def download_video(url: str, output_path: str, quality: Optional[str] = None) -> bool:
    """下载视频文件.
    
    Args:
        url: 视频URL地址
        output_path: 输出文件路径
        quality: 可选的质量设置，如 "1080p", "720p"
        
    Returns:
        bool: 下载是否成功
        
    Raises:
        ValueError: URL格式不正确时抛出
        IOError: 文件写入失败时抛出
        
    Example:
        >>> success = download_video("https://example.com/video.mp4", "./video.mp4")
        >>> if success:
        ...     print("下载成功")
    """
    pass
```

### 错误处理

1. **使用具体的异常类型**

```python
# 好的做法
if not url.startswith(('http://', 'https://')):
    raise ValueError(f"无效的URL格式: {url}")

# 避免的做法
if not url.startswith(('http://', 'https://')):
    raise Exception("URL错误")
```

2. **提供有意义的错误信息**

```python
# 好的做法
raise FileNotFoundError(f"配置文件不存在: {config_path}")

# 避免的做法
raise FileNotFoundError("文件不存在")
```

3. **记录异常信息**

```python
import logging

logger = logging.getLogger(__name__)

try:
    result = risky_operation()
except SomeSpecificError as e:
    logger.error(f"操作失败: {e}", exc_info=True)
    raise
```

## 🤝 贡献指南

### 提交信息规范

使用 [约定式提交](https://www.conventionalcommits.org/zh-hans/) 格式：

```
<类型>[可选 作用域]: <描述>

[可选 正文]

[可选 脚注]
```

**类型说明**:

- `feat`: 新功能
- `fix`: Bug修复
- `docs`: 文档更新
- `style`: 代码风格调整（不影响功能的格式化等）
- `refactor`: 代码重构（既不是新功能也不是Bug修复）
- `test`: 测试相关
- `chore`: 构建过程或辅助工具的变动
- `perf`: 性能优化
- `ci`: CI/CD 相关

**示例**:

```
feat(extractor): 添加新的视频网站支持

- 实现 CustomSite 提取器
- 支持多种视频质量选择
- 添加相应的单元测试
- 更新文档

Closes #123
```

```
fix(downloader): 修复M3U8下载进度计算错误

修复了在下载大文件时进度百分比计算不准确的问题。

影响范围: M3U8Downloader.download() 方法
```

### Pull Request 流程

1. **Fork 项目并创建功能分支**

```bash
git checkout -b feature/add-new-extractor
```

2. **进行开发并确保代码质量**

```bash
# 格式化代码
black pavone/ tests/
isort pavone/ tests/

# 类型检查
pyright pavone/

# 运行测试
python -m pytest tests/ -v

# 风格检查
flake8 pavone/ tests/
```

3. **提交更改**

```bash
git add .
git commit -m "feat(extractor): 添加新的视频网站支持"
```

4. **推送分支并创建 PR**

```bash
git push origin feature/add-new-extractor
```

### Code Review 检查清单

#### 功能检查

- [ ] 功能实现正确且完整
- [ ] 包含适当的错误处理
- [ ] 性能考虑得当
- [ ] 安全性考虑（输入验证、文件路径等）

#### 代码质量

- [ ] 代码结构清晰，职责分明
- [ ] 变量和函数命名有意义
- [ ] 避免重复代码
- [ ] 遵循项目架构模式（操作项 -> 执行管理器 -> 插件）

#### 类型安全

- [ ] 完整的类型注解
- [ ] 通过 pyright/mypy 检查
- [ ] 正确使用泛型和联合类型

#### 测试

- [ ] 包含单元测试
- [ ] 测试覆盖率充足
- [ ] 测试用例有意义
- [ ] Mock 使用得当

#### 文档

- [ ] 更新相关文档
- [ ] 添加或更新 docstring
- [ ] 更新 README.md（如需要）
- [ ] 更新使用示例

### 发布流程

1. **版本号管理**: 遵循 [语义化版本](https://semver.org/lang/zh-CN/)
   - MAJOR: 不兼容的API变更
   - MINOR: 新增功能（向后兼容）
   - PATCH: Bug修复（向后兼容）

2. **更新版本号**

```python
# pavone/__init__.py
__version__ = "1.2.3"
```

3. **更新变更日志**

在 `CHANGELOG.md` 中记录：
- 新功能
- Bug修复
- 破坏性变更
- 弃用功能

4. **创建标签和发布**

```bash
git tag -a v1.2.3 -m "Release v1.2.3"
git push origin v1.2.3
```

## 📋 架构决策记录 (ADR)

### ADR-001: 采用统一的操作模型

**状态**: 已接受

**背景**: 原架构中下载、搜索、整理等功能各自独立，缺乏统一的数据模型和执行流程。

**决策**: 引入 `OperationItem` 统一操作模型，通过 `ExecutionManager` 统一执行。

**后果**:
- ✅ 统一的API接口
- ✅ 更好的可测试性
- ✅ 易于扩展新功能
- ❌ 需要重写现有功能

### ADR-002: 插件化架构

**状态**: 已接受

**背景**: 需要支持多种视频网站和下载方式，硬编码不利于扩展。

**决策**: 采用插件架构，提取器、下载器都通过插件系统管理。

**后果**:
- ✅ 高度可扩展
- ✅ 功能模块化
- ✅ 第三方插件支持
- ❌ 初期实现复杂度较高

### ADR-003: 类型安全优先

**状态**: 已接受

**背景**: Python 的动态特性容易导致运行时错误。

**决策**: 全面采用类型注解，使用 pyright 进行严格的类型检查。

**后果**:
- ✅ 减少运行时错误
- ✅ 更好的IDE支持
- ✅ 自文档化代码
- ❌ 开发时需要更多类型声明

这个架构确保了 PAVOne 的可维护性、可扩展性和代码质量，为长期发展奠定了坚实基础。

# PAVOne 开发文档

## 📁 项目结构

```
pavone/
├── pavone/                         # 主包
│   ├── __init__.py
│   ├── cli.py                      # 命令行入口
│   ├── core/                       # 核心功能模块
│   │   ├── __init__.py
│   │   ├── metadata.py             # 元数据提取
│   │   ├── organizer.py            # 文件整理
│   │   ├── searcher.py             # 搜索功能
│   │   └── downloader/             # 下载器模块
│   │       ├── __init__.py
│   │       ├── base.py             # 基础下载器类
│   │       ├── http_downloader.py  # HTTP下载器实现
│   │       ├── m3u8_downloader.py  # M3U8流媒体下载器
│   │       ├── options.py          # 下载选项管理
│   │       ├── progress.py         # 进度管理
│   │       └── utils.py            # 工具函数
│   ├── plugins/                    # 插件系统
│   │   ├── __init__.py
│   │   └── base.py                 # 插件基类
│   └── config/                     # 配置管理
│       ├── __init__.py
│       └── settings.py             # 配置管理
├── tests/                          # 测试套件
│   ├── __init__.py
│   ├── test_downloader.py          # 基础下载器测试
│   ├── test_m3u8_downloader.py     # M3U8下载器测试
│   └── test_organizer.py           # 文件整理测试
├── docs/                           # 文档
│   ├── config.md                   # 配置文档
│   ├── development.md              # 开发文档
│   └── usage.md                    # 使用文档
├── pyproject.toml                  # 项目配置和工具设置
├── pyrightconfig.json              # Pylance/Pyright配置
├── setup.cfg                       # 工具配置(flake8, pytest等)
├── setup.py                        # 安装脚本
├── requirements.txt                # 项目依赖
├── LICENSE                         # 开源协议
├── dev.ps1                         # 开发脚本
└── README.md                       # 项目说明
```

## 🏗️ 核心模块

### 📥 下载器模块 (core/downloader/)

下载器模块采用模块化设计，包含多个文件：

#### `base.py` - 基础下载器类
```python
class BaseDownloader(ABC):
    """基础下载器类，定义下载器的标准接口"""
    
    @abstractmethod
    def download(self, download_opt: DownloadOpt, 
                 progress_callback: Optional[ProgressCallback] = None) -> bool:
        """下载文件的抽象方法"""
        pass
```

#### `http_downloader.py` - HTTP下载器
- **功能**: 处理HTTP/HTTPS协议的文件下载
- **特性**:
  - 多线程并发下载
  - Range请求支持
  - 断点续传
  - 代理支持
  - 自动重试机制
  - 实时进度监控

#### `m3u8_downloader.py` - M3U8流媒体下载器 🆕
- **功能**: 专门处理M3U8 (HLS) 流媒体下载
- **特性**:
  - M3U8播放列表解析
  - 并发视频段下载
  - 自动文件合并
  - 临时文件管理
  - 相对/绝对URL处理
  - 错误处理和重试

#### `options.py` - 下载选项管理
```python
class DownloadOpt:
    """下载选项类，封装下载参数"""
    def __init__(self, url: str, filename: Optional[str] = None, 
                 custom_headers: Optional[Dict[str, str]] = None):
        # 下载配置
```

#### `progress.py` - 进度管理
```python
class ProgressInfo:
    """下载进度信息"""
    def __init__(self, total_size: int = 0, downloaded: int = 0, speed: float = 0.0):
        # 进度状态管理

ProgressCallback = Callable[[ProgressInfo], None]
```

#### `utils.py` - 工具函数
- 下载器工具函数
- 配置创建辅助函数
- 使用示例代码

### 📊 元数据提取 (metadata.py)

负责提取视频的元数据信息：

- `BaseMetadataExtractor`: 基础提取器，提供通用元数据提取功能
  - 支持基本元数据结构定义
  - 提供可扩展的提取接口
  - 可通过继承或插件系统扩展特定网站的元数据提取

该模块当前仅包含基础提取器类，具体的元数据提取器可通过继承 `BaseMetadataExtractor` 或使用插件系统进行扩展。

### 📁 文件整理 (organizer.py)

负责视频文件的整理和管理：

- `FileOrganizer`: 文件整理器
- 支持按制作商、类型、演员等方式整理
- 提供重复文件检测
- 支持多CD和系列处理

### 🔍 搜索功能 (searcher.py)

提供视频搜索功能：

- `BaseSearcher`: 基础搜索器，提供通用搜索功能
  - 支持基本搜索接口定义
  - 提供可扩展的搜索框架
  - 可通过继承或插件系统扩展特定网站的搜索功能

该模块当前仅包含基础搜索器类，具体的搜索器可通过继承 `BaseSearcher` 或使用插件系统进行扩展。

## 🔌 插件系统

### 插件基类

所有插件都继承自 `BasePlugin`：

```python
class BasePlugin(ABC):
    @abstractmethod
    def initialize(self) -> bool:
        """初始化插件"""
        pass
    
    @abstractmethod
    def execute(self, *args, **kwargs) -> Any:
        """执行插件功能"""
        pass
```

### 专用插件类型

- `DownloaderPlugin`: 下载器插件
- `MetadataPlugin`: 元数据插件  
- `SearchPlugin`: 搜索插件

### 插件管理

`PluginManager` 负责插件的加载、注册和管理。

## ⚙️ 配置系统

使用 `ConfigManager` 管理配置：

- 支持JSON格式配置文件
- 提供默认配置
- 支持配置热更新

## 🚀 开发指南

### 架构设计理念

PAVOne 采用模块化和插件化的设计：

- **核心模块**: 提供基础功能和抽象接口
- **插件系统**: 支持功能扩展，便于添加新的下载源和功能
- **配置管理**: 统一的配置系统，支持灵活配置
- **类型安全**: 完整的类型注解和检查
- **测试覆盖**: 全面的单元测试和集成测试

### 🎬 添加新的下载器

有三种方式添加新的下载器：

**方式一：继承 BaseDownloader**
```python
from pavone.core.downloader.base import BaseDownloader
from pavone.core.downloader.options import DownloadOpt
from pavone.core.downloader.progress import ProgressCallback

class MyDownloader(BaseDownloader):
    def download(self, download_opt: DownloadOpt, 
                 progress_callback: Optional[ProgressCallback] = None) -> bool:
        # 实现特定的下载逻辑
        pass
```

**方式二：参考现有实现**
- 参考 `HTTPDownloader` 实现HTTP协议下载器
- 参考 `M3U8Downloader` 实现流媒体下载器

**方式三：使用插件系统**
1. 继承 `DownloaderPlugin`
2. 实现 `can_handle()` 和 `download()` 方法
3. 注册到插件管理器

### 📊 添加新的元数据提取器

1. 继承 `MetadataPlugin`
2. 实现 `can_extract()` 和 `extract_metadata()` 方法
3. 注册到插件管理器

### 🔍 添加新的搜索引擎

1. 继承 `SearchPlugin`
2. 实现 `search()` 方法
3. 注册到插件管理器

## 🧪 测试框架

### 测试结构
```
tests/
├── test_downloader.py          # 基础下载器测试
├── test_m3u8_downloader.py     # M3U8下载器测试
└── test_organizer.py           # 文件整理测试
```

### 运行测试
```bash
# 运行所有测试
python -m pytest tests/ -v

# 运行特定测试文件
python -m pytest tests/test_m3u8_downloader.py -v

# 运行测试并生成覆盖率报告
python -m pytest tests/ --cov=pavone --cov-report=html --cov-report=term-missing

# 运行特定测试方法
python -m pytest tests/test_m3u8_downloader.py::TestM3U8Downloader::test_parse_m3u8_playlist -v
```

### 测试最佳实践
- 使用 `unittest.mock` 进行网络请求模拟
- 编写独立的单元测试
- 添加集成测试验证完整流程
- 保持高测试覆盖率

## 🔧 代码质量工具

### 类型检查
```bash
# Pyright (Pylance后端)
pyright pavone/

# MyPy
mypy pavone/
```

### 代码格式化
```bash
# Black 格式化
black pavone/ tests/

# isort 导入排序
isort pavone/ tests/

# 检查格式是否正确
black --check pavone/ tests/
isort --check-only pavone/ tests/
```

### 代码风格检查
```bash
# flake8
flake8 pavone/ tests/

# pylint
pylint pavone/
```

### 安全检查
```bash
# safety - 检查依赖漏洞
safety check

# bandit - 安全代码扫描
bandit -r pavone/
```

## 🚀 CI/CD 流程

### GitHub Actions工作流

项目配置了完整的CI/CD流程：

#### 主要工作流文件

##### `ci.yml` - 主CI/CD流水线
- **触发条件**: Push到main/develop分支，PR创建或更新
- **执行内容**:
  - **Lint和类型检查**: Black, isort, flake8, pylint, mypy, pyright
  - **多版本测试**: Python 3.9, 3.10, 3.11, 3.12
  - **安全扫描**: safety, bandit
  - **包构建验证**: 构建和验证Python包
  - **集成测试**: CLI和基本功能测试
  - **自动PR总结**: 生成详细的检查报告

##### `code-quality.yml` - 代码质量专项检查
- **Pylance类型检查**: 使用Pyright进行高级类型分析
- **代码格式化检查**: Black和isort一致性验证
- **M3U8下载器专项测试**: 新功能的专门测试
- **依赖安全审计**: 检查已知安全漏洞
- **质量报告生成**: 详细的检查结果和建议

### Pull Request流程

1. **自动触发**: PR创建时自动运行所有检查
2. **并行执行**: 多个检查任务并行执行，提高效率
3. **结果聚合**: 自动生成质量检查总结
4. **状态反馈**: 在PR界面显示所有检查状态
5. **合并条件**: 所有检查通过后才能合并

### 本地开发检查

在提交前，建议本地运行以下检查：

```bash
# 代码格式化
black pavone/ tests/
isort pavone/ tests/

# 类型检查
pyright pavone/

# 代码风格
flake8 pavone/ tests/

# 运行测试
python -m pytest tests/ -v

# 安全检查
safety check
bandit -r pavone/
```

## 🛠️ 开发环境设置

### 推荐开发工具

- **IDE**: Visual Studio Code
- **Python**: 3.9+
- **扩展**: 
  - Python Extension Pack
  - Pylance (自动启用)
  - Black Formatter
  - isort

### VS Code配置

项目包含以下配置文件：

- `pyrightconfig.json`: Pylance/Pyright配置
- `pyproject.toml`: Black, isort, pytest配置
- `setup.cfg`: flake8, coverage配置
- `.pylintrc`: pylint配置

### 环境变量

开发时可设置以下环境变量：

```bash
# 启用详细日志
export PAVONE_DEBUG=1

# 设置配置文件路径
export PAVONE_CONFIG_PATH=/path/to/config.json

# 设置测试模式
export PAVONE_TEST_MODE=1
```

## 📝 代码规范

### Python版本要求
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

### 文档字符串
使用Google风格的docstring：

```python
def download_video(url: str, output_path: str) -> bool:
    """下载视频文件.
    
    Args:
        url: 视频URL地址
        output_path: 输出文件路径
        
    Returns:
        bool: 下载是否成功
        
    Raises:
        ValueError: URL格式不正确时抛出
        IOError: 文件写入失败时抛出
    """
    pass
```

## 🤝 贡献指南

### 提交规范

使用[约定式提交](https://www.conventionalcommits.org/zh-hans/)格式：

```
<类型>[可选 作用域]: <描述>

[可选 正文]

[可选 脚注]
```

**类型说明**:
- `feat`: 新功能
- `fix`: Bug修复
- `docs`: 文档更新
- `style`: 代码风格调整
- `refactor`: 代码重构
- `test`: 测试相关
- `chore`: 构建过程或辅助工具的变动

**示例**:
```
feat(downloader): 添加M3U8流媒体下载支持

- 实现M3U8播放列表解析
- 添加并发视频段下载
- 支持自动文件合并
- 包含完整的单元测试

Closes #123
```

### Code Review检查清单

#### 功能检查
- [ ] 功能实现正确且完整
- [ ] 包含适当的错误处理
- [ ] 性能考虑得当
- [ ] 安全性考虑

#### 代码质量
- [ ] 代码结构清晰，职责分明
- [ ] 变量和函数命名有意义
- [ ] 避免重复代码
- [ ] 遵循项目架构模式

#### 测试
- [ ] 包含单元测试
- [ ] 测试覆盖率充足
- [ ] 测试用例有意义
- [ ] Mock使用得当

#### 文档
- [ ] 更新相关文档
- [ ] 添加或更新docstring
- [ ] 更新CHANGELOG (如需要)

### 发布流程

1. **版本号管理**: 遵循[语义化版本](https://semver.org/lang/zh-CN/)
2. **变更日志**: 更新CHANGELOG.md
3. **标签创建**: 创建版本标签
4. **自动发布**: GitHub Actions自动发布到PyPI

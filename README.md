# PAVOne (WIP)

[![CI/CD Pipeline](https://github.com/imbatony/pavone/actions/workflows/ci.yml/badge.svg)](https://github.com/username/pavone/actions/workflows/ci.yml)
[![Code Quality Check](https://github.com/imbatony/pavone/actions/workflows/code-quality.yml/badge.svg)](https://github.com/imbatony/pavone/actions/workflows/code-quality.yml)
[![Python Version](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)


## 关于
PAVOne(WIP)是一个集下载、整理等多功能的插件化的AV管理工具。

## 为什么要有这个项目
1. 目前的元数据抓取大部分只支持JAV，对其他类型视频网站没有支持
2. 海报图缺乏打标功能单一，查找繁琐 
3. 下载工具并不自带整理功能，后期整理繁琐费时
4. 整理功能大部分对多cd，系列等处理不正常
5. 多个工具分散
6. 视频分散在多个视频网站，需要多次寻找
7. 缺乏视频去重和质量升级功能

## 特性

### 🎬 视频下载
- **多协议支持**: HTTP/HTTPS、M3U8 (HLS) 流媒体下载
- **并发下载**: 多线程并发下载，提升下载效率  
- **断点续传**: 支持大文件的断点续传功能
- **代理支持**: 完整的HTTP/HTTPS代理配置
- **进度监控**: 实时下载进度显示和回调

### 📊 元数据管理
- **智能提取**: 自动提取视频元数据信息
- **多源支持**: 支持多种数据源和网站
- **标准化**: 统一的元数据格式和存储

### 📁 文件整理
- **智能整理**: 基于元数据的智能文件整理
- **多种模式**: 支持按制作商、演员、类型等整理方式
- **重复检测**: 智能重复文件检测和处理
- **批量处理**: 支持批量文件操作

### 🔍 搜索功能
- **跨平台搜索**: 支持多个视频网站的统一搜索
- **关键词搜索**: 灵活的关键词和分类搜索
- **结果聚合**: 智能搜索结果聚合和排序

### 🔧 开发特性
- **插件化架构**: 可扩展的插件系统
- **类型安全**: 完整的类型注解和检查
- **测试覆盖**: 全面的单元测试和集成测试
- **CI/CD**: 自动化的代码质量检查和部署

## 安装

### 📋 环境要求
- Python 3.9+ 
- Windows/Linux/macOS

### 🚀 快速安装

```bash
# 克隆仓库
git clone https://github.com/imbatony/pavone.git
cd pavone

# 安装依赖
pip install -r requirements.txt

# 开发模式安装
pip install -e .
```

### 📦 PyPI安装 (即将支持)
```bash
pip install pavone
```

## 快速开始

### 初始化配置

```bash
pavone init
```

### 下载视频

```bash
# 下载单个视频
pavone download "https://example.com/video.mp4"

### 下载视频

```bash
# HTTP/HTTPS视频下载
pavone download "https://example.com/video.mp4"

# M3U8流媒体下载
pavone download "https://example.com/video/playlist.m3u8" --filename "my_video.mp4"

# 带自定义头部的下载
pavone download "https://secure.example.com/video.mp4" \
  --header "Authorization: Bearer token123" \
  --header "Referer: https://example.com"

# 使用代理下载
pavone download "https://example.com/video.mp4" \
  --proxy "http://127.0.0.1:7890"

# 下载并自动整理
pavone download "https://example.com/video.mp4" --organize

# 自动选择第一个下载选项
pavone download "https://missav.ai/video/12345" --auto-select

# 静默下载（无进度显示）
pavone download "https://example.com/video.mp4" --silent

# 批量下载
pavone batch-download urls.txt --auto-select
```

### 搜索视频

```bash
# 搜索关键词
pavone search "关键词"

# 在特定网站搜索
pavone search "关键词" --site javbus
```

### 整理视频文件

```bash
# 整理指定目录
pavone organize "/path/to/videos"

# 按制作商整理
pavone organize "/path/to/videos" --by studio

# 查找重复文件
pavone organize "/path/to/videos" --find-duplicates
```

## 📁 项目结构

```
pavone/
├── pavone/                    # 主包
│   ├── __init__.py
│   ├── cli.py                 # 命令行入口
│   ├── core/                  # 核心功能模块
│   │   ├── __init__.py
│   │   ├── base.py            # 基础操作类
│   │   ├── dummy.py           # 测试用占位操作类
│   │   └── downloader/        # 下载器模块
│   │       ├── __init__.py
│   │       ├── base.py        # 基础下载器类
│   │       ├── http_downloader.py  # HTTP下载器
│   │       └── m3u8_downloader.py  # M3U8流媒体下载器
│   ├── models/                # 数据模型
│   │   ├── __init__.py
│   │   ├── operation.py       # 操作项模型
│   │   ├── constants.py       # 常量定义
│   │   ├── metadata.py        # 元数据模型
│   │   └── progress_info.py   # 进度信息模型
│   ├── manager/               # 管理器模块
│   │   ├── __init__.py
│   │   ├── execution.py       # 执行管理器
│   │   └── progress.py        # 进度管理
│   ├── plugins/               # 插件系统
│   │   ├── __init__.py
│   │   ├── base.py           # 插件基类
│   │   ├── manager.py        # 插件管理器
│   │   └── extractors/       # 提取器插件
│   │       ├── __init__.py
│   │       ├── base.py       # 提取器基类
│   │       ├── missav_extractor.py    # MissAV提取器
│   │       ├── m3u8_direct.py         # M3U8直链提取器
│   │       └── mp4_direct.py          # MP4直链提取器
│   ├── utils/                # 工具模块
│   │   ├── __init__.py
│   │   └── stringutils.py    # 字符串工具
│   └── config/               # 配置管理
│       ├── __init__.py
│       ├── configs.py        # 配置类定义
│       ├── manager.py        # 配置管理器
│       ├── settings.py       # 配置设置
│       ├── validator.py      # 配置验证器
│       └── logging_config.py # 日志配置
├── tests/                    # 测试套件
│   ├── __init__.py
│   ├── test_downloader.py    # 基础下载器测试
│   ├── test_m3u8_downloader.py  # M3U8下载器测试
│   └── test_organizer.py     # 文件整理测试
├── docs/                     # 文档
│   ├── config.md             # 配置文档
│   ├── development.md        # 开发文档
│   └── usage.md              # 使用文档
├── pyproject.toml            # 项目配置
├── pyrightconfig.json        # Pylance配置
├── setup.cfg                 # 工具配置
├── setup.py                  # 安装脚本
├── requirements.txt          # 依赖列表
├── LICENSE                   # 开源协议
├── dev.ps1                   # 开发脚本
└── README.md                 # 项目说明
```

## 🚀 核心功能

### 📥 下载器系统
- **`BaseDownloader`**: 下载器基类，定义统一接口
- **`HTTPDownloader`**: HTTP/HTTPS协议下载器
  - 支持多线程并发下载
  - 断点续传功能
  - Range请求支持
  - 自动重试机制
- **`M3U8Downloader`**: HLS流媒体下载器
  - M3U8播放列表解析
  - 并发视频段下载
  - 自动文件合并
  - 实时进度监控

### 📊 元数据系统
- **智能提取**: 自动识别和提取视频元信息
- **多源聚合**: 支持多个元数据源的信息聚合
- **标准化格式**: 统一的元数据结构和存储格式
- **可扩展架构**: 通过插件系统支持新的元数据源

### 📁 文件整理系统
- **智能分类**: 基于元数据的智能文件分类和整理
- **多种模式**: 支持按制作商、演员、类型、日期等维度整理
- **重复检测**: 高效的重复文件检测算法
- **批量操作**: 支持大批量文件的快速处理

### 🔍 搜索系统
- **统一接口**: 提供统一的搜索接口和结果格式
- **多源搜索**: 同时搜索多个视频网站和数据源
- **智能排序**: 基于相关性和质量的搜索结果排序
- **缓存机制**: 搜索结果缓存，提升响应速度

## ⚙️ 配置

配置文件位于 `~/.pavone/config.json`：

```json
{
  "download": {
    "output_dir": "./downloads",
    "max_concurrent_downloads": 4,
    "retry_times": 3,
    "timeout": 30,
    "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "proxy_enabled": false,
    "http_proxy": "",
    "https_proxy": ""
  },
  "organize": {
    "auto_organize": true,
    "organize_by": "studio",
    "naming_pattern": "{studio}-{code}-{title}",
    "create_directories": true
  },
  "search": {
    "max_results_per_site": 20,
    "enabled_sites": ["javbus", "javlibrary"],
    "cache_enabled": true,
    "cache_duration": 3600
  },
  "metadata": {
    "auto_fetch": true,
    "preferred_language": "zh-CN",
    "fallback_language": "en-US"
  }
}
```

## 📚 文档

详细文档请参考：

- [使用文档](docs/usage.md) - 完整的使用指南和示例
- [配置文档](docs/config.md) - 详细的配置选项说明
- [开发文档](docs/development.md) - 开发指南和API文档

## 🤝 贡献

我们欢迎所有形式的贡献！请阅读我们的贡献指南：

### 贡献流程
1. Fork 本仓库
2. 创建您的功能分支 (`git checkout -b feature/amazing-feature`)
3. 提交您的更改 (`git commit -m 'Add some amazing feature'`)
4. 推送到分支 (`git push origin feature/amazing-feature`)
5. 打开一个 Pull Request

### 代码质量
- 所有代码必须通过 Pylance/Pyright 类型检查
- 遵循 Black 代码格式化标准
- 添加适当的单元测试
- 更新相关文档

## 🧪 开发

### 运行测试
```bash
# 运行所有测试
python -m pytest tests/ -v

# 运行特定测试
python -m pytest tests/test_m3u8_downloader.py -v

# 运行测试并生成覆盖率报告
python -m pytest tests/ --cov=pavone --cov-report=html
```

### 代码质量检查
```bash
# 类型检查
pyright pavone/

# 代码格式化
black pavone/ tests/
isort pavone/ tests/

# 代码风格检查
flake8 pavone/ tests/
pylint pavone/
```

### 启用详细日志
```bash
pavone --verbose download "url"
```

## 📄 许可证

本项目采用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情。

## 🙏 致谢

感谢所有贡献者和开源社区的支持！
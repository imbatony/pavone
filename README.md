# PAVOne (WIP)

[![CI/CD Pipeline](https://github.com/imbatony/pavone/actions/workflows/ci.yml/badge.svg)](https://github.com/imbatony/pavone/actions/workflows/ci.yml)
[![Code Quality Check](https://github.com/imbatony/pavone/actions/workflows/code-quality.yml/badge.svg)](https://github.com/imbatony/pavone/actions/workflows/code-quality.yml)
[![Python Version](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## 简介

PAVOne(WIP)是一个集下载、整理等多功能的插件化的AV管理工具。

## 功能特性

### 🎬 视频下载
- **多协议支持**: HTTP/HTTPS、M3U8 (HLS) 流媒体下载
- **并发下载**: 多线程并发下载，提升下载效率  
- **断点续传**: 支持大文件的断点续传功能
- **代理支持**: 完整的HTTP/HTTPS代理配置
- **进度监控**: 实时下载进度显示和回调

### 📊 元数据管理
- **智能提取**: 自动提取视频元数据信息
- **多源支持**: 支持多种数据源和网站
- **标准化格式**: 统一的元数据结构和存储

### 📁 文件整理
- **智能整理**: 基于元数据的智能文件整理
- **多种模式**: 支持按制作商、演员、类型等整理方式
- **重复检测**: 智能重复文件检测和处理

### 🔍 搜索功能
- **统一搜索**: 支持多个视频网站的统一搜索
- **关键词搜索**: 灵活的关键词和分类搜索
- **结果聚合**: 智能搜索结果聚合和排序

### 🔧 开发特性
- **插件化架构**: 可扩展的插件系统
- **类型安全**: 完整的类型注解和检查
- **测试覆盖**: 全面的单元测试和集成测试
- **CI/CD**: 自动化的代码质量检查和部署

## 安装

### 环境要求
- Python 3.9+ 
- Windows/Linux/macOS

### 快速安装

```bash
# 克隆仓库
git clone https://github.com/imbatony/pavone.git
cd pavone

# 安装依赖
pip install -e .
```

## 使用示例

### 初始化配置
```bash
pavone init
```

### 下载视频
```bash
# HTTP/HTTPS视频下载
pavone download "https://example.com/video.mp4"

# M3U8流媒体下载
pavone download "https://example.com/playlist.m3u8" --filename "video.mp4"

# 使用代理下载
pavone download "https://example.com/video.mp4" --proxy "http://127.0.0.1:7890"

# 下载并自动整理
pavone download "https://example.com/video.mp4" --organize
```

### 搜索视频
```bash
pavone search "关键词"
pavone search "关键词" --site javbus
```

### 整理视频文件
```bash
pavone organize "/path/to/videos"
pavone organize "/path/to/videos" --find-duplicates
```

## 项目结构

详见 [docs/dev/architecture.md](docs/dev/architecture.md)

## 文档

- [使用指南](docs/usage.md) - 详细的使用示例和文档
- [配置说明](docs/config.md) - 配置选项详解
- [开发指南](docs/dev/development.md) - 开发环境和贡献指南
- [项目架构](docs/dev/architecture.md) - 项目结构和核心设计
- [测试指南](docs/dev/testing.md) - 测试运行和代码质量检查

## 贡献

我们欢迎所有形式的贡献！请参考 [docs/dev/development.md](docs/dev/development.md) 了解贡献流程。

## 许可证

MIT License - 详见 [LICENSE](LICENSE)

## 致谢

感谢所有贡献者和开源社区的支持！

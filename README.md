# PAVOne (WIP)

[![CI/CD Pipeline](https://github.com/imbatony/pavone/actions/workflows/ci.yml/badge.svg)](https://github.com/imbatony/pavone/actions/workflows/ci.yml)
[![Code Quality Check](https://github.com/imbatony/pavone/actions/workflows/code-quality.yml/badge.svg)](https://github.com/imbatony/pavone/actions/workflows/code-quality.yml)
[![Python Version](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## 简介

PAVOne(WIP)是一个集下载、整理等多功能的插件化的AV管理工具。

## 功能特性

- 🎬 **视频下载** - 支持 HTTP/HTTPS 和 M3U8 协议，并发下载，断点续传
- 📊 **元数据管理** - 智能提取视频信息，支持多源，统一格式存储
- 📁 **文件整理** - 基于元数据的智能整理，支持按制作商、演员、类型等分类
- 🔍 **搜索功能** - 统一搜索多个视频网站，灵活的关键词和分类搜索
- 🔧 **插件化架构** - 可扩展的插件系统，完整的类型注解，全面的测试覆盖

## 支持的网站

### 📥 视频提取器
支持从以下网站提取视频下载链接和元数据：

- **AV01** (`av01.tv`, `av01.media`) - 基于 geo API token 认证系统
- **MissAV** (`missav.ai`, `missav.com`, `missav.ws`) - 支持 M3U8 流媒体
- **Memojav** (`memojav.com`) - 日本视频内容
- **JTable** (`jable.tv`, `jp.jable.tv`) - 基于 JS 表格的网站
- **Javrate** (`javrate.com`) - 使用浏览器自动化绕过 Cloudflare

### 📊 元数据提取
支持从以下网站提取视频元数据（FC2 系列）：

- **PPVDataBank** (`ppvdatabank.com`) - FC2 视频元数据提取与搜索
- **SupFC2** (`supfc2.com`) - FC2 视频元数据提取

### 🔗 通用下载
支持直接下载链接，无需元数据提取：

- **M3U8 Direct** - 直接 M3U8 链接支持
- **MP4 Direct** - 直接 MP4 文件下载

### 🔎 搜索功能
支持以下网站/服务的搜索：

- **MissAV** - 关键词和分类搜索
- **PPVDataBank** - FC2 视频 ID / 代码搜索
- **Jellyfin** - 本地 Jellyfin 媒体库搜索

## 安装

### 环境要求
- Python 3.10+
- Windows/Linux/macOS

### 快速安装

```bash
# 通过 uvx 安装（推荐）
uv tool install git+https://github.com/imbatony/pavone.git
```

### 从源码安装

```bash
# 克隆仓库
git clone https://github.com/imbatony/pavone.git
cd pavone

# 安装依赖
uv sync
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

我们欢迎所有形式的贡献！请参考 [CONTRIBUTING.md](CONTRIBUTING.md) 了解贡献流程。

开发环境搭建：

```bash
# 使用 uv (推荐)
uv sync && uv run pytest

# 使用 make (Linux/macOS)
make install && make test

# 使用 dev.ps1 (Windows)
.\dev.ps1 test
```

详细的开发指南请参考 [docs/dev/development.md](docs/dev/development.md)。

## 许可证

MIT License - 详见 [LICENSE](LICENSE)

## 致谢

感谢所有贡献者和开源社区的支持！

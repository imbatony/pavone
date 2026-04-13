# PAVOne (WIP)

[![CI/CD Pipeline](https://github.com/imbatony/pavone/actions/workflows/ci.yml/badge.svg)](https://github.com/imbatony/pavone/actions/workflows/ci.yml)
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

| 网站 | 域名 | 提取 | 元数据 | 搜索 | 说明 |
|------|------|:----:|:------:|:----:|------|
| MissAV | `missav.ai` `missav.com` `missav.ws` | ✅ | ✅ | ✅ | M3U8 流媒体，全功能 |
| AV01 | `av01.tv` `av01.media` | ✅ | ✅ | | geo API token 认证 |
| JTable | `jable.tv` `jp.jable.tv` | ✅ | ✅ | | JS 表格解析 |
| Memojav | `memojav.com` | ✅ | ✅ | | 嵌入视频提取 |
| Javrate | `javrate.com` | ✅ | ✅ | | Cloudflare 绕过 |
| PPVDataBank | `ppvdatabank.com` | | ✅ | ✅ | FC2 视频 |
| SupFC2 | `supfc2.com` | | ✅ | | FC2 视频 |
| Caribbeancom | `caribbeancom.com` `caribbeancompr.com` | | ✅ | | 加勒比系列 |
| 1Pondo | `1pondo.tv` | | ✅ | | 一本道系列 |
| Jellyfin | 自建服务器 | | | ✅ | 本地媒体库 |
| M3U8 Direct | 任意 `.m3u8` 链接 | ✅ | | | 通用 M3U8 |
| MP4 Direct | 任意 `.mp4` 链接 | ✅ | | | 通用 MP4 |

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

## 许可证

MIT License - 详见 [LICENSE](LICENSE)

## 致谢

感谢所有贡献者和开源社区的支持！

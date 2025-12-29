# 项目架构

## 项目结构

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
│   │   ├── progress_info.py   # 进度信息模型
│   │   └── search_result.py   # 搜索结果模型
│   ├── manager/               # 管理器模块
│   │   ├── __init__.py
│   │   ├── execution.py       # 执行管理器
│   │   └── progress.py        # 进度管理器
│   ├── plugins/               # 插件系统
│   │   ├── __init__.py
│   │   ├── base.py            # 插件基类
│   │   ├── manager.py         # 插件管理器
│   │   ├── missav_plugin.py   # MissAV统一插件
│   │   ├── extractors/        # 提取器插件
│   │   │   ├── __init__.py
│   │   │   ├── base.py        # 提取器基类
│   │   │   ├── m3u8_direct.py
│   │   │   ├── mp4_direct.py
│   │   │   └── ...
│   │   ├── metadata/          # 元数据处理插件
│   │   └── search/            # 搜索插件
│   ├── utils/                 # 工具模块
│   │   ├── __init__.py
│   │   ├── code_extract_utils.py
│   │   ├── http_utils.py
│   │   └── stringutils.py
│   └── config/                # 配置管理
│       ├── __init__.py
│       ├── configs.py         # 配置类定义
│       ├── manager.py         # 配置管理器
│       ├── settings.py        # 配置设置
│       ├── validator.py       # 配置验证器
│       └── logging_config.py  # 日志配置
├── tests/                     # 测试套件
├── docs/                      # 文档
├── pyproject.toml
├── setup.py
└── README.md
```

## 核心模块说明

### 📥 下载器系统 (`core/downloader/`)

#### BaseDownloader
- 所有下载器的基类
- 定义统一的下载接口
- 提供公共的配置和工具

#### HTTPDownloader
- HTTP/HTTPS 协议下载器
- 功能：
  - 多线程并发下载
  - 断点续传支持
  - Range 请求支持
  - 自动重试机制
  - 代理配置
  - 自定义请求头

#### M3U8Downloader
- HLS 流媒体下载器
- 功能：
  - M3U8 播放列表解析
  - 并发视频段下载
  - 自动文件合并
  - 实时进度监控
  - 密钥解密支持

### 📊 数据模型 (`models/`)

#### OperationItem
定义单个操作的数据结构

#### Metadata
视频元数据模型，包含：
- 视频代码
- 标题
- 演员
- 制作商
- 发布日期
- 等级/分类
- 标签
- 自定义字段

#### ProgressInfo
进度信息模型，包含：
- 当前进度百分比
- 已下载大小
- 总大小
- 下载速度
- 剩余时间

### 🔌 插件系统 (`plugins/`)

#### BasePlugin
所有插件的基类

#### 提取器插件 (Extractors)
从不同网站提取视频信息和下载链接
- MissAV 提取器
- 直接 M3U8 提取
- 直接 MP4 链接提取
- 等等

#### 元数据插件
处理元数据的收集、验证、存储等

#### 搜索插件
跨多个网站进行统一搜索

### ⚙️ 配置系统 (`config/`)

#### ConfigManager
管理应用配置的读取、验证和保存
- 配置文件位置: `~/.pavone/config.json`
- 支持配置验证
- 支持配置迁移

### 📋 执行管理 (`manager/`)

#### ExecutionManager
管理操作的执行流程
- 操作队列管理
- 并发执行控制
- 错误处理和恢复

#### ProgressManager
管理和报告操作进度
- 进度聚合
- 回调通知
- 进度持久化

## 架构设计原则

### 1. 插件化架构
- 核心功能与具体实现分离
- 通过插件系统支持新的提取器、搜索源等
- 易于扩展和定制

### 2. 关注点分离
- 下载器只负责文件传输
- 提取器只负责信息提取
- 管理器负责流程编排

### 3. 类型安全
- 完整的类型注解
- Pydantic 模型验证
- Pylance/Pyright 类型检查

### 4. 可配置性
- 灵活的配置系统
- 支持多种工作流程
- 易于集成到其他应用

## 数据流

### 下载流程
```
用户命令
  ↓
CLI 解析
  ↓
执行管理器
  ↓
提取器插件 (获取下载链接)
  ↓
下载器 (HTTP/M3U8)
  ↓
本地文件
  ↓
[可选] 元数据处理
  ↓
[可选] 文件整理
```

### 搜索流程
```
用户搜索
  ↓
搜索管理器
  ↓
多个搜索插件 (并发)
  ↓
结果聚合和排序
  ↓
返回结果
```

## 扩展点

### 添加新的提取器
1. 继承 `BaseExtractor`
2. 实现 `extract()` 方法
3. 在插件管理器中注册

### 添加新的搜索源
1. 继承 `BaseSearcher`
2. 实现 `search()` 方法
3. 在搜索管理器中注册

### 添加新的下载协议
1. 继承 `BaseDownloader`
2. 实现下载逻辑
3. 在下载管理器中注册

## 依赖关系

核心依赖：
- **Pydantic**: 数据验证和模型
- **Click**: 命令行框架
- **requests**: HTTP 请求
- **aiohttp**: 异步 HTTP 请求
- **lxml**: HTML 解析
- **m3u8**: M3U8 解析

开发依赖：
- **pytest**: 单元测试
- **black**: 代码格式化
- **pylance/pyright**: 类型检查
- **flake8**: 代码风格检查

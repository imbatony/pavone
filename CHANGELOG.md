# Changelog

本文档记录 PAVOne 项目的所有重要变更。

格式基于 [Keep a Changelog](https://keepachangelog.com/zh-CN/1.0.0/)，
版本号遵循 [语义化版本](https://semver.org/lang/zh-CN/)。

## [0.3.5] - 2026-04-21

### 新增
- `jellyfin list` 命令新增「质量」列，显示视频分辨率标签（4K/1080p/720p 等）
- 新增 `--sort-by quality` 排序选项，支持按视频分辨率排序
- `ItemMetadata` 新增 `video_quality` / `video_height` 属性

### 改进
- `get_library_items` API 请求增加 MediaSources 字段
- 元数据插件改进：fanza GraphQL、javbus 解析、supfc2 描述提取

### 修复
- 修复 pyright 错误：supfc2_metadata.py BeautifulSoup find 类型重载
- 修复 flake8 F401：移除未使用的 import
- 修复 flake8 E741：重命名模糊变量名 `l` → `line`

## [0.3.4] - 2026-04-15

### 新增
- 自动发布工作流（gh-aw auto-release），PR 合并后自动 bump 版本并创建 GitHub Release
- 每日 CI 测试工作流和元数据插件测试脚本

### 改进
- 移除失败的插件，清理代码
- auto-release 使用 `grep -m1` 精确匹配项目版本号

### 修复
- 修复 daily workflow 中 discussion 创建使用 GraphQL node ID
- 修复 gcolle 和 javfree 的 2 个 pyright 类型错误

## [0.3.3] - 2026-04-14

### 修复
- TokyoHot: 支持日文和英文双语字段 key（Model/出演者、Release Date/配信開始日等）
- Kin8tengoku: URL 解析支持不带末尾 `/` 的格式
- Gcolle: 自动通过年龄认证页面，正确获取商品详情
- Javfree: 支持非 FC2 格式 URL，从标题提取 `[CODE-123]` 番号
- Muramura: MOVIE_ID_PATTERN 兼容 3-4 位数字后缀（如 `040826_1229`）

## [0.3.2] - 2026-04-14

### 新增
- `HtmlMetadataPlugin` 中间基类 — HTML 解析类插件的通用流程封装（resolve → fetch → parse + 统一错误处理）
- `ApiMetadataPlugin` 中间基类 — API/JSON 类插件的通用流程封装
- `JsonLdMetadataPlugin` 中间基类 — JSON-LD 解析类插件的通用流程封装（继承 HtmlMetadataPlugin）
- `_get_tag_attr` 类型安全工具方法 — 安全获取 BeautifulSoup 标签属性，返回 `Optional[str]`

### 改进
- 统一 `_abs` 方法至基类（原 16 份独立实现 → 1 份）
- 统一 `_parse_runtime` 方法至基类，超集合并 3 种变体（原 14 份 → 1 份）
- 统一 `_parse_date` 方法至基类，超集合并 4 种分隔符格式（原 23 份 → 1 份）
- 统一 `_parse_iso_duration` 方法至基类（原 5 份 → 1 份）
- 34 个元数据插件分 8 批迁移至新基类，每批独立验证
- `FC2BaseMetadata` 改为继承 `HtmlMetadataPlugin`，自动获得模板方法和工具方法
- 插件总代码行数从 7,148 行降至 6,357 行（减少 11%）

## [0.2.2] - 2026-03-17

### 新增
- JavratePlugin v2.1.0 - 支持 javrate.com，使用浏览器自动化绕过 Cloudflare
- JellyfinSearch 插件 - 支持在本地 Jellyfin 媒体库中搜索视频
- `organize` 命令 - 实现文件整理功能
- 搜索结果去重优化
- 搜索命令输出美化

### 改进
- 新增 `missav.ws` 域名支持
- 优化 MissAV 搜索重试次数
- 修正 `retry_times` 语义为总尝试次数
- 修复元数据增强时覆盖已有 actors/directors 的问题
- 重构 logger 初始化，统一所有基类和派生类
- 代码质量优化和技术债务清理

### 构建 & 配置
- 修复 setuptools 包发现配置，支持所有子包
- 新增 `uv tool install` 安装方式
- 更新 pyrightconfig.json 排除列表
- 更新 README：补全所有插件信息、安装方式

**完全向后兼容，无需迁移。**

## [0.2.1] - 2025-12-29

### 新增
- HTMLMetadataExtractor - 统一的 HTML 元数据提取工具类
- MetadataBuilder - 元数据构建器，支持链式调用
- OperationItemBuilder - 操作项构建器，支持链式调用
- FC2BaseMetadata - FC2 系列视频元数据插件基类
- CLI 公共命令选项装饰器（@common_download_options 等）
- BasePlugin.can_handle_domain() - 统一的 URL 域名验证方法

### 改进
- 重构 6 个核心插件（missav, av01, jtable, memojav, ppvdatabank, supfc2）
- 减少代码约 400 行，消除 15+ 处重复代码
- 代码重复度从 30% 降至 < 5%
- 所有代码通过 pyright 类型检查（0 errors）
- 新插件开发时间减少 40-50%

### 文档
- 新增详细的更新文档（docs/update/0.2.1.md）
- 完善所有新增类和方法的文档字符串

**完全向后兼容，无需迁移。**

详见：[docs/update/0.2.1.md](docs/update/0.2.1.md)

## [0.2.0] - 2024-12-XX

### 新增
- Jellyfin 集成支持（连接、搜索、移动文件）
- AV01 元数据提取器
- MemoJav、JTable 等多个元数据提取器
- `metadata enrich` 命令 - 从多个数据源增强元数据
- `jellyfin move` 命令 - 移动文件到 Jellyfin 库并刷新

### 改进
- 大幅改进 M3U8 下载器性能和稳定性
- 重构日志系统，统一日志配置
- 整合 AV01 和 MissAV 插件功能
- 优化 GitHub Actions 工作流

### 修复
- 修复 Jellyfin 库文件夹获取逻辑
- 修复 MissAV 搜索插件正则表达式
- 修复元数据提取器 JavaScript 执行问题

详见：[docs/update/0.2.0.md](docs/update/0.2.0.md)

## [0.1.1] - 2024-XX-XX

### 新增
- 初始稳定版本
- 基础插件系统
- CLI 命令实现

---

[0.3.5]: https://github.com/imbatony/pavone/compare/v0.3.4...v0.3.5
[0.3.4]: https://github.com/imbatony/pavone/compare/v0.3.3...v0.3.4
[0.3.3]: https://github.com/imbatony/pavone/compare/v0.3.2...v0.3.3
[0.3.2]: https://github.com/imbatony/pavone/compare/v0.2.2...v0.3.2
[0.2.2]: https://github.com/imbatony/pavone/compare/v0.2.1...v0.2.2
[0.2.1]: https://github.com/imbatony/pavone/compare/v0.2.0...v0.2.1
[0.2.0]: https://github.com/imbatony/pavone/compare/v0.1.1...v0.2.0
[0.1.1]: https://github.com/imbatony/pavone/releases/tag/v0.1.1

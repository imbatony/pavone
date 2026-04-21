# 数据模型: Jellyfin 媒体库视频列表

**功能**: 005-jellyfin-library-listing
**日期**: 2026-04-17

## 实体

### 1. LibraryInfo（已有，无修改）

Jellyfin 媒体库的基本信息，用于交互式选择和列表展示。

| 字段 | 类型 | 说明 |
|------|------|------|
| name | str | 媒体库名称 |
| id | str | 唯一标识符 |
| type | str | 类型 (movies, tvshows 等) |
| item_count | int | 库中项目总数 |

### 2. JellyfinItem（已有，无修改）

媒体库中的视频条目，承载 API 原始数据。

| 字段 | 类型 | 说明 |
|------|------|------|
| id | str | 唯一标识符 |
| name | str | 视频名称 |
| type | str | 项目类型 (Movie, Video 等) |
| container | Optional[str] | 容器格式 (mkv, mp4 等) |
| path | Optional[str] | 文件系统路径 |
| metadata | Dict[str, Any] | 完整 API 响应数据 |

### 3. ItemMetadata（已有，扩展）

对 JellyfinItem.metadata 的结构化访问封装。新增 `metadata_score` 计算属性。

**新增属性**:

| 属性 | 类型 | 说明 |
|------|------|------|
| metadata_score | int | 元数据丰富度评分 (0-100)，基于加权模型计算 |

**评分计算模型**:

```
metadata_score = sum(
    weight  if  dimension_has_value
    else  0
    for dimension, weight in SCORE_WEIGHTS.items()
)
```

**权重常量** (`METADATA_SCORE_WEIGHTS`):

| 维度 | 属性访问 | 权重 | 判定条件 |
|------|----------|------|----------|
| 标题 | `self._data.get("Name")` | 5 | 非空字符串 |
| 简介 | `self.overview` | 20 | 非空字符串 |
| 类型 | `self.genres` | 10 | 列表非空 |
| 年份 | `self.year` | 5 | 非 None |
| 演员 | `self.actors` | 15 | 列表非空 |
| 导演 | `self.directors` | 10 | 列表非空 |
| 封面图 | `self.has_primary_image` | 15 | 为 True |
| 评分 | `self.rating` | 5 | 非 None 且 > 0 |
| 标签 | `self.tags` | 10 | 列表非空 |
| 工作室 | `self.studio_names` | 5 | 列表非空 |

### 4. VideoListItem（新增，展示层数据传输对象）

用于将各来源的数据整合为表格展示所需的扁平结构。非持久化，仅在 list 命令内部使用。

| 字段 | 类型 | 来源 | 说明 |
|------|------|------|------|
| index | int | 枚举生成 | 序号 (1-based) |
| name | str | JellyfinItem.name | 视频名称，过长截断 |
| date_added | str | ItemMetadata.added_date | 加入时间，格式化为日期字符串 |
| metadata_score | int | ItemMetadata.metadata_score | 元数据丰富度评分 |
| path | str | JellyfinItem.path | 视频文件路径，过长截断 |

## 关系

```
LibraryInfo  1 ──── * JellyfinItem
JellyfinItem 1 ──── 1 ItemMetadata (通过 metadata dict 构造)
JellyfinItem 1 ──── 1 VideoListItem (list 命令展示转换)
```

## 状态转换

本功能不涉及状态转换。所有数据为只读查询展示。

## 验证规则

- `metadata_score` 值域: [0, 100]，类型 int
- `date_added` 为 None 时展示为 "N/A"
- `path` 为 None 时展示为 "N/A"
- 名称截断长度上限: 30 个显示宽度字符
- 路径截断长度上限: 50 个显示宽度字符

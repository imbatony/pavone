## Enrich 功能 - Jellyfin 字段映射修复总结

### 1. 支持的字段列表

Enrich 功能对比和更新的字段（Jellyfin 支持的）：

```
title, premiere_date, runtime, director, studio, actors, genres, tags, 
rating, official_rating, plot, year
```

**排除的字段**（Jellyfin 不支持）：
- ❌ `code` - Jellyfin 不支持视频代码/番号字段
- ❌ `serial` - Jellyfin 的 SeriesName 仅用于电视剧，不适用于电影

---

### 2. Title 字段映射修复

#### 问题
用户反馈在 enrich 功能中，title 字段显示的是 Jellyfin 中的 `Name` 字段，但在初始版本中，代码使用了错误的参数。

#### 解决方案
- 添加 `ItemMetadata.name` 属性，从元数据的 `Name` 字段读取
- 更新字段映射，确保 `'title'` → `ItemMetadata.name`

---

### 3. Year 字段映射修复

#### 问题
在 enrich 对比中，Jellyfin 的年份信息没有正确显示，始终显示为 `(无)`。

#### 根本原因
`ItemMetadata.year` 属性读取的是 `Year` 字段，但 Jellyfin API 实际返回的是 `ProductionYear` 字段。

#### 解决方案
**文件**: `pavone/models/jellyfin_item.py`

```python
@property
def year(self) -> Optional[int]:
    """发行年份"""
    # Jellyfin API 返回 ProductionYear，而不是 Year
    return self._data.get('ProductionYear') or self._data.get('Year')
```

现在会优先读取 `ProductionYear`，如果不存在则 fallback 到 `Year`。

#### 修复验证
对于 SDMT-415：
- **之前**: year = None
- **之后**: year = 2011 ✅

---

### 4. Jellyfin 支持的元数据字段完整映射

| 字段名 | Jellyfin 字段 | 类型 | 说明 |
|--------|--------------|------|------|
| title | Name | string | 视频标题 |
| premiere_date | PremiereDate | date | 首映日期 |
| runtime | RunTimeTicks | long | 时长（单位：ticks） |
| director | People (Type=Director) | list | 导演列表 |
| studio | Studios | list | 制作公司列表 |
| actors | People (Type=Actor) | list | 演员列表 |
| genres | Genres | list | 类型列表 |
| tags | Tags | list | 标签列表 |
| rating | CommunityRating | float | 社区评分 |
| official_rating | OfficialRating | string | 官方分级（如 JP-18+） |
| plot | Overview | string | 描述/简介 |
| year | ProductionYear | int | 发行年份 |

**不支持的字段**（排除于 Enrich）：
| 字段名 | 原因 |
|--------|------|
| code | Jellyfin 没有代码/番号字段 |
| serial | Jellyfin 的 SeriesName 仅用于电视剧 |

---

### 参数顺序调整

为了让代码逻辑更清晰，调整了方法的参数顺序：

**before**:
```python
compare_metadata(remote_metadata, local_metadata, force)
merge_metadata(remote_metadata, local_metadata, comparison, force)
```

**after**:
```python
compare_metadata(local_metadata, remote_metadata, force)  # local first
merge_metadata(local_metadata, remote_metadata, comparison, force)  # local first
```

这样在 `display_comparison` 中：
- 左列 (local) = Jellyfin
- 右列 (remote) = 数据源

---

### 修改文件列表

1. **pavone/models/jellyfin_item.py**
   - 修复 `year` 属性，从 `ProductionYear` 读取

2. **pavone/cli/commands/enrich_helper.py**
   - 从 METADATA_FIELDS 移除 `code` 和 `serial`
   - 更新字段映射，移除不适用的字段
   - 调整 `compare_metadata` 和 `merge_metadata` 的参数顺序

3. **pavone/cli/commands/metadata.py**
   - 更新方法调用的参数顺序

---

### 测试验证

✅ 所有测试通过：129 passed, 2 xfailed

**修复效果示例**:

对于 SDMT-415：
```
字段               │ Jellyfin (本地)              │ Remote (远程)
────────────────────┼──────────────────────────────┼──────────────────────────────
title              │ SDMT-415                    │ 男子の格好をしているオンナ... 
year               │ 2011                        │ 2023                  [覆盖]
rating             │ 7.4                         │ 7.4
official_rating    │ JP-18+                      │ JP-18+
premiere_date      │ 2011-04-21T00:00:00.0000000Z│ 2023-04-19T00:00:00Z  [覆盖]
director           │ Keita★No.1                  │ Keita★No.1             [合并]
studio             │ SODクリエイト                  │ SODクリエイト               [合并]
actors             │ さとう遥希                     │ さとう遥希, 南佳也...    [合并]
```

**注意**：
- ❌ `code` 不再显示（Jellyfin 不支持）
- ❌ `serial` 不再显示（电影类型无此字段）

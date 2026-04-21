# CLI 命令合同: jellyfin list

**功能**: 005-jellyfin-library-listing
**日期**: 2026-04-17

## 命令签名

```
pavone jellyfin list [LIBRARY_NAME] [OPTIONS]
```

## 参数

| 参数 | 类型 | 必需 | 默认值 | 说明 |
|------|------|------|--------|------|
| `LIBRARY_NAME` | str | 否 | None | 媒体库名称。未指定时进入交互式选择 |

## 选项

| 选项 | 短选项 | 类型 | 默认值 | 说明 |
|------|--------|------|--------|------|
| `--sort-by` | `-s` | Choice: name, date_added, metadata_score | `date_added` | 排序字段 |
| `--order` | `-o` | Choice: asc, desc | `desc` | 排序方向 |
| `--limit` | `-n` | int (1-10000) | `50` | 显示记录数上限 |

## 输出格式

### 成功输出 (stdout)

```
媒体库: 我的视频 (共 128 个视频, 显示前 50 条, 按加入时间降序)

  #  名称                            加入时间      评分  路径
---  ------------------------------  ----------  ------  --------------------------------------------------
  1  示例视频标题                    2026-04-15      85  /media/videos/example.mkv
  2  另一个视频                      2026-04-14      60  /media/videos/another.mp4
  3  仅有标题的视频                  2026-04-10      25  /media/videos/minimal.avi
 ...
```

### 空结果输出 (stdout)

```
媒体库 "我的视频" 为空，没有视频内容。
```

### 交互式选择输出 (stdout)

```
请选择媒体库:
  1. 我的视频 (128 项)
  2. 电影收藏 (56 项)
  3. 纪录片 (23 项)

请选择库 [1-3]:
```

### 错误输出 (stderr)

| 场景 | 错误信息 |
|------|----------|
| 媒体库不存在 | `[ERROR] 媒体库 "xxx" 不存在。可用的媒体库: 我的视频, 电影收藏` |
| 连接失败 | `[ERROR] 无法连接到 Jellyfin 服务器: <错误详情>` |
| 认证失败 | `[ERROR] Jellyfin 认证失败，请检查配置` |

## 退出码

| 退出码 | 含义 |
|--------|------|
| 0 | 成功列取并展示 |
| ExitCode.NETWORK_ERROR | 网络连接或超时错误 |
| ExitCode.CONFIG_ERROR | 配置缺失或认证失败 |
| ExitCode.GENERAL_ERROR | 其他未预期错误 |

## 使用示例

```bash
# 列取指定媒体库的视频（默认按加入时间降序）
pavone jellyfin list "我的视频"

# 按名称升序排列
pavone jellyfin list "我的视频" --sort-by name --order asc

# 按元数据评分升序排列（评分低的在前，方便找到需要补充元数据的视频）
pavone jellyfin list "我的视频" -s metadata_score -o asc

# 限制显示数量
pavone jellyfin list "我的视频" -n 20

# 不指定媒体库，交互式选择
pavone jellyfin list

# 组合选项
pavone jellyfin list -s metadata_score -o asc -n 100
```

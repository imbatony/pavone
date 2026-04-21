# 快速入门: Jellyfin 媒体库视频列表

**功能**: 005-jellyfin-library-listing

## 前提条件

1. 已安装 PAVOne (`uv sync`)
2. 已配置 Jellyfin 连接（`pavone config` 中设置 server_url 和认证信息）
3. Jellyfin 服务器上至少有一个媒体库包含视频

## 基础用法

### 1. 列取指定媒体库的视频

```bash
pavone jellyfin list "我的视频"
```

输出含名称、加入时间、元数据评分和路径的表格。

### 2. 交互式选择媒体库

```bash
pavone jellyfin list
```

系统展示编号列表，输入编号选择。

### 3. 按元数据评分排序（找出元数据缺失的视频）

```bash
pavone jellyfin list "我的视频" --sort-by metadata_score --order asc
```

评分低的视频排在前面，方便逐一补充元数据。

### 4. 控制显示数量

```bash
pavone jellyfin list "我的视频" --limit 20
```

## 开发验证

```bash
# 运行评分计算单元测试
uv run pytest tests/test_metadata_score.py -v

# 运行列表命令测试
uv run pytest tests/test_jellyfin_list.py -v

# 代码格式和类型检查
uv run black pavone/models/jellyfin_item.py pavone/cli/commands/jellyfin.py pavone/jellyfin/client.py
uv run pyright pavone/models/jellyfin_item.py pavone/cli/commands/jellyfin.py pavone/jellyfin/client.py
```

# 实施计划: MetaTube 元数据提取器移植 (v0.4.0)

**分支**: `003-metatube-metadata-extractor` | **日期**: 2026-04-13 | **规范**: [spec.md](spec.md)
**输入**: 来自 `/specs/003-metatube-metadata-extractor/spec.md` 的功能规范

## 摘要

本计划将 MetaTube SDK Go 源码（`D:\code\metatube-sdk-go-main\provider\`）中的元数据提取器，
以 Python 重写的方式移植到 pavone 插件系统中，目标为：

- 全量移植 provider 目录下所有尚未支持的站点（共 32 个新站点）
- 严格保留现有 4 个提取器实现：caribbeancom、caribbeancompr、1pondo/onepondo、fc2/supfc2
- 新提取器继承现有 `MetadataPlugin` 基类，通过 `pkgutil` 自动发现机制接入
- 元数据字段严格对齐现有 `MovieMetadata` 模型，缺失字段填 `None`

## 技术背景

**语言/版本**: Python 3.10+
**主要依赖**: requests（HTTP 请求）、BeautifulSoup4（HTML 解析）、lxml（解析器）、Pydantic 2.x（数据模型）
**参考源码**: Go → `D:\code\metatube-sdk-go-main\provider\<site>\<site>.go`
**插件架构**: `MetadataPlugin` 基类 + `pkgutil` 自动发现（`PluginManager._load_builtin_plugins()`）
**测试**: pytest + unittest.mock（Mock HTTP 响应，纳入 CI）；集成测试可选

## 现有提取器（保留，不修改）

| 插件文件 | 对应 MetaTube provider | 说明 |
|---|---|---|
| `caribbeancom_metadata.py` | caribbeancom / caribbeancompr | 保留现有，跳过移植 |
| `onepondo_metadata.py` | 1pondo | 保留现有，跳过移植 |
| `fc2_base.py` + `supfc2_metadata.py` | fc2 | 保留现有，跳过移植 |
| `ppvdatabank_metadata.py` | — | 非 MetaTube provider，保留 |

## 需要移植的站点（32 个）

按字母顺序分组为 4 批，便于并行实施：

### 批次 A（8 个）
| 目标文件 | MetaTube provider | 站点域名 |
|---|---|---|
| `tenmusume_metadata.py` | 10musume/ | 10musume.com |
| `avleague_metadata.py` | av-league/ | av-league.com |
| `avbase_metadata.py` | avbase/ | avbase.one |
| `aventertainments_metadata.py` | aventertainments/ | aventertainments.com |
| `c0930_metadata.py` | c0930/ | c0930.com |
| `dahlia_metadata.py` | dahlia/ | dahlia-av.com |
| `duga_metadata.py` | duga/ | duga.jp |
| `faleno_metadata.py` | faleno/ | faleno.jp |

### 批次 B（8 个）
| 目标文件 | MetaTube provider | 站点域名 |
|---|---|---|
| `fanza_metadata.py` | fanza/ | dmm.co.jp / fanza.com |
| `fc2hub_metadata.py` | fc2hub/ | fc2hub.com |
| `fc2ppvdb_metadata.py` | fc2ppvdb/ | fc2ppvdb.com |
| `gcolle_metadata.py` | gcolle/ | gcolle.com |
| `getchu_metadata.py` | getchu/ | getchu.com |
| `gfriends_metadata.py` | gfriends/ | gfriends.io |
| `h0930_metadata.py` | h0930/ | h0930.com |
| `h4610_metadata.py` | h4610/ | h4610.com |

### 批次 C（8 个）
| 目标文件 | MetaTube provider | 站点域名 |
|---|---|---|
| `heydouga_metadata.py` | heydouga/ | heydouga.com |
| `heyzo_metadata.py` | heyzo/ | heyzo.com |
| `jav321_metadata.py` | jav321/ | jav321.com |
| `javbus_metadata.py` | javbus/ | javbus.com |
| `javfree_metadata.py` | javfree/ | javfree.sh |
| `kin8tengoku_metadata.py` | kin8tengoku/ | kin8tengoku.com |
| `madouqu_metadata.py` | madouqu/ | madouqu.com |
| `mgstage_metadata.py` | mgstage/ | mgstage.com |

### 批次 D（8 个）
| 目标文件 | MetaTube provider | 站点域名 |
|---|---|---|
| `modelmediaasia_metadata.py` | modelmediaasia/ | modelmediaasia.com |
| `muramura_metadata.py` | muramura/ | muramura.tv |
| `mywife_metadata.py` | mywife/ | mywife.co.jp |
| `pacopacomama_metadata.py` | pacopacomama/ | pacopacomama.com |
| `pcolle_metadata.py` | pcolle/ | pcolle.com |
| `sod_metadata.py` | sod/ | sod.com |
| `theporndb_metadata.py` | theporndb/ | theporndb.net |
| `tokyohot_metadata.py` | tokyo-hot/ | tokyo-hot.com |

## 项目结构

### 文档（此功能）

```
specs/003-metatube-metadata-extractor/
├── plan.md              # 此文件
├── spec.md              # 功能规范
└── tasks.md             # 任务列表
```

### 源代码（变更范围）

```
pavone/plugins/metadata/             # 元数据提取器插件目录
├── base.py                          # [不修改] MetadataPlugin 基类
├── caribbeancom_metadata.py         # [不修改] 现有提取器
├── onepondo_metadata.py             # [不修改] 现有提取器
├── fc2_base.py                      # [不修改] 现有提取器
├── supfc2_metadata.py               # [不修改] 现有提取器
├── ppvdatabank_metadata.py          # [不修改] 现有提取器
│
│   # === 新增文件（按批次） ===
├── tenmusume_metadata.py            # 批次 A
├── avleague_metadata.py             # 批次 A
├── avbase_metadata.py               # 批次 A
├── aventertainments_metadata.py     # 批次 A
├── c0930_metadata.py                # 批次 A
├── dahlia_metadata.py               # 批次 A
├── duga_metadata.py                 # 批次 A
├── faleno_metadata.py               # 批次 A
│
├── fanza_metadata.py                # 批次 B
├── fc2hub_metadata.py               # 批次 B
├── fc2ppvdb_metadata.py             # 批次 B
├── gcolle_metadata.py               # 批次 B
├── getchu_metadata.py               # 批次 B
├── gfriends_metadata.py             # 批次 B
├── h0930_metadata.py                # 批次 B
├── h4610_metadata.py                # 批次 B
│
├── heydouga_metadata.py             # 批次 C
├── heyzo_metadata.py                # 批次 C
├── jav321_metadata.py               # 批次 C
├── javbus_metadata.py               # 批次 C
├── javfree_metadata.py              # 批次 C
├── kin8tengoku_metadata.py          # 批次 C
├── madouqu_metadata.py              # 批次 C
├── mgstage_metadata.py              # 批次 C
│
├── modelmediaasia_metadata.py       # 批次 D
├── muramura_metadata.py             # 批次 D
├── mywife_metadata.py               # 批次 D
├── pacopacomama_metadata.py         # 批次 D
├── pcolle_metadata.py               # 批次 D
├── sod_metadata.py                  # 批次 D
├── theporndb_metadata.py            # 批次 D
├── tokyohot_metadata.py             # 批次 D
└── __init__.py                      # [修改] 导出新提取器

tests/metadata/                      # 新增测试目录
├── conftest.py                      # 共享 Mock fixtures
├── test_tenmusume.py                # 批次 A 测试
├── test_avleague.py
├── ...（每个提取器一个测试文件）
└── test_tokyohot.py                 # 批次 D 测试
```

## 每个提取器的实现模式

所有新提取器遵循如下标准模式（参考 `caribbeancom_metadata.py`）：

```python
class XxxMetadata(MetadataPlugin):
    def __init__(self): ...
    def can_extract(self, identifier: str) -> bool:
        # 检查域名或 ID 格式
    def extract_metadata(self, identifier: str) -> Optional[MovieMetadata]:
        # 1. 解析 URL/ID → 标准化 movie_id
        # 2. 构造目标 URL
        # 3. HTTP GET + BeautifulSoup 解析（或 JSON API）
        # 4. 填充 MovieMetadata 字段，缺失字段填 None
        # 5. 返回 MovieMetadata
```

**字段映射原则（来自 Go model.MovieInfo）**：
| Go 字段 | Python 字段 | 类型 |
|---|---|---|
| Title | title | str |
| Actors | actors | list[str] |
| Tags / Genres | tags / genres | list[str] |
| Duration | runtime | int（分钟）|
| ReleaseDate | premiered | str（YYYY-MM-DD）|
| Director | director | str |
| Maker / Studio | studio | str |
| Series | serial | str |
| CoverURL | cover | str |
| ThumbURL | thumbnail | str |
| PreviewImages | backdrops | list[str] |
| Score | rating | float |

## 实施策略

1. **MVP（最小可用集）**: 阶段 3（批次 A，8 个站点）— 验证流程跑通后再扩展
2. **增量交付**: 每批次（A→B→C→D）独立可测试，可单独合并
3. **并行友好**: 同一批次内的提取器彼此独立，可由不同开发者同时实现
4. **零回归保证**: 批次 A 实施完成后必须运行全测试套件（`pytest tests/ -v`）

## 依赖关系

```
[设置] → [基础] → [批次 A] → [批次 B] → [批次 C] → [批次 D] → [完善]
                       ↓
                  运行全测试 + 确认现有提取器无回归
```

批次内部任务可并行；批次之间建议顺序执行（验证上一批次后推进下一批次）。

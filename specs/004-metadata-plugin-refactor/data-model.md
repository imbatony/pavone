# 数据模型: 元数据插件架构重构

**功能**: 004-metadata-plugin-refactor | **日期**: 2025-07-18

## 实体概览

```
┌─────────────────────────────────────────────────────────────┐
│                      BasePlugin                             │
│  (plugins/base.py)                                          │
│  + name, version, description, author, priority             │
│  + logger, config                                           │
│  + fetch(url, headers, timeout, ...) → Response             │
│  + can_handle_domain(url, domains) → bool                   │
│  + initialize() → bool  [abstract]                          │
│  + cleanup()                                                │
└─────────────────────┬───────────────────────────────────────┘
                      │
┌─────────────────────▼───────────────────────────────────────┐
│                  MetadataPlugin                              │
│  (plugins/metadata/base.py) — 接口不变                       │
│  + can_extract(identifier) → bool  [abstract]               │
│  + extract_metadata(identifier) → Optional[BaseMetadata]    │
│    [abstract]                                                │
│  + select_portrait_image(urls, timeout) → Optional[str]     │
└───┬──────────────────┬─────────────────────┬────────────────┘
    │                  │                     │
    ▼                  ▼                     ▼
 HtmlMeta          ApiMeta            (Direct: 特殊插件)
 dataPlugin        dataPlugin         FanzaMetadata
                                      AvbaseMetadata
```

## 实体定义

### MetadataPlugin (已有, 不变)

```
MetadataPlugin(BasePlugin)
├── 字段: 继承自 BasePlugin
├── 方法:
│   ├── can_extract(identifier: str) → bool              [abstract]
│   ├── extract_metadata(identifier: str) → Optional[BaseMetadata]  [abstract]
│   └── select_portrait_image(urls: List[str], timeout: int) → Optional[str]
└── 约束:
    ├── 公开接口零变更 (FR-017)
    └── 所有现有测试保持通过 (SC-010)
```

### HtmlMetadataPlugin (新增)

```
HtmlMetadataPlugin(MetadataPlugin)
├── 职责: HTML 页面类插件的通用流程封装
├── 模板方法:
│   └── extract_metadata(identifier: str) → Optional[BaseMetadata]
│       流程: _resolve → _fetch_page → BeautifulSoup parse → _parse
│       错误处理: RequestException → log + return None
│                 Exception → log(exc_info) + return None
├── 钩子方法:
│   └── _fetch_page(url: str) → requests.Response
│       默认: self.fetch(url, timeout=30)
│       子类覆写场景: 自定义 cookies/headers/timeout/verify_ssl
├── 抽象方法:
│   ├── _resolve(identifier: str) → Tuple[Optional[str], Optional[str]]
│   │   返回: (movie_id, page_url), 失败返回 (None, None)
│   └── _parse(soup: BeautifulSoup, movie_id: str, page_url: str) → Optional[BaseMetadata]
│       返回: 填充好的 BaseMetadata 对象, 失败返回 None
├── 静态工具方法:
│   ├── _abs(url: str, base: str) → str
│   │   规则: http开头→原样; //开头→补scheme; 其他→补scheme+netloc
│   ├── _parse_runtime(text: str) → Optional[int]
│   │   格式优先级: 日文分 > 英文Min > HH:MM(:SS)
│   ├── _parse_date(s: str) → Optional[str]
│   │   输入: '2023/01/02' | '2023-01-02' | '2023年1月2日' | '2023.01.02'
│   │   输出: 'YYYY-MM-DD'
│   ├── _parse_iso_duration(s: str) → Optional[int]
│   │   输入: 'PT1H30M' | 'PT30M' | 'PT1H' | '120分'
│   │   输出: 分钟数
│   └── _get_tag_attr(tag: Optional[Any], attr: str) → Optional[str]
│       规则: tag为None→None; val为str→str(val); 否则→None
└── 约束:
    ├── 子类仅需实现 can_extract + _resolve + _parse (FR-004, SC-007)
    └── 模板方法中 try/except 必须与现有各插件行为一致 (FR-015, FR-016)
```

### ApiMetadataPlugin (新增)

```
ApiMetadataPlugin(MetadataPlugin)
├── 职责: API/JSON 类插件的通用流程封装
├── 模板方法:
│   └── extract_metadata(identifier: str) → Optional[BaseMetadata]
│       流程: _resolve → _build_api_url → _fetch_api → json() → _parse
│       错误处理: 同 HtmlMetadataPlugin
├── 钩子方法:
│   └── _fetch_api(url: str) → requests.Response
│       默认: self.fetch(url, timeout=30)
│       子类覆写场景: 自定义 headers (Referer/Auth), Content-Type
├── 抽象方法:
│   ├── _build_api_url(movie_id: str) → str
│   ├── _resolve(identifier: str) → Tuple[Optional[str], Optional[str]]
│   └── _parse(data: Dict[str, Any], movie_id: str, page_url: str) → Optional[BaseMetadata]
└── 约束:
    ├── 子类仅需实现 can_extract + _resolve + _build_api_url + _parse
    └── 不继承 HtmlMetadataPlugin 的静态工具方法 (API 插件通常不需要)
```

### JsonLdMetadataPlugin (新增)

```
JsonLdMetadataPlugin(HtmlMetadataPlugin)
├── 职责: JSON-LD 数据提取 + HTML fallback
├── 模板方法 (覆写):
│   └── extract_metadata(identifier: str) → Optional[BaseMetadata]
│       流程: _resolve → _fetch_page → BeautifulSoup → _extract_jsonld → _parse_with_jsonld
├── 新增方法:
│   ├── _extract_jsonld(soup: BeautifulSoup) → Optional[Dict[str, Any]]
│   │   解析 <script type="application/ld+json"> 标签
│   │   处理: JSON 数组→取第一个; 换行符清理; 异常跳过
│   └── _parse_with_jsonld(soup, jsonld, movie_id, page_url) → Optional[BaseMetadata]
│       [abstract] 子类实现, 接收 JSON-LD 数据 + soup 作为 fallback
├── 兼容层:
│   └── _parse(soup, movie_id, page_url) → Optional[BaseMetadata]
│       实现: 调用 _extract_jsonld + _parse_with_jsonld
└── 继承工具方法:
    └── _abs, _parse_runtime, _parse_date, _parse_iso_duration, _get_tag_attr (来自 HtmlMetadataPlugin)
```

### FC2BaseMetadata (已有, 修改继承)

```
FC2BaseMetadata(HtmlMetadataPlugin)  ← 原: FC2BaseMetadata(MetadataPlugin)
├── 职责: FC2 系列视频的通用 ID 处理逻辑
├── FC2 专属方法 (保留不变):
│   ├── _extract_fc2_id(identifier: str) → Optional[str]
│   ├── _build_fc2_code(fc2_id: str) → str
│   ├── _build_fc2_ppv_code(fc2_id: str) → str
│   ├── _validate_fc2_identifier(identifier: str) → bool
│   ├── _is_fc2_url(url: str) → bool
│   └── _normalize_fc2_code(code: str) → str
├── 继承:
│   └── 自动获得 HtmlMetadataPlugin 的模板方法 + 工具方法
└── 约束:
    └── 子类 (supfc2, ppvdatabank) 可能需覆写 _fetch_page 设置 verify_ssl=False
```

## 关系图

```
BasePlugin
  └─ MetadataPlugin [接口不变]
       ├─ HtmlMetadataPlugin [新增]
       │    ├─ JsonLdMetadataPlugin [新增, 继承 HtmlMetadataPlugin]
       │    │    ├─ C0930Metadata
       │    │    ├─ H0930Metadata
       │    │    ├─ H4610Metadata
       │    │    ├─ Fc2HubMetadata
       │    │    └─ HeyzoMetadata
       │    ├─ FC2BaseMetadata [已有, 改继承 HtmlMetadataPlugin]
       │    │    ├─ SupFc2Metadata
       │    │    └─ PpvDataBankMetadata (+ SearchPlugin 多重继承)
       │    ├─ DahliaMetadata
       │    ├─ FalenoMetadata
       │    ├─ MywifMetadata
       │    ├─ SodMetadata
       │    ├─ MgstageMetadata
       │    ├─ GetchuMetadata
       │    ├─ Kin8tengokuMetadata
       │    ├─ MadouquMetadata
       │    ├─ DugaMetadata
       │    ├─ Jav321Metadata
       │    ├─ JavbusMetadata
       │    ├─ TokyohotMetadata
       │    ├─ HeydougaMetadata
       │    ├─ AventertainmentsMetadata
       │    ├─ GcolleMetadata
       │    ├─ JavfreeMetadata
       │    ├─ PcolleMetadata
       │    ├─ Fc2PpvDbMetadata
       │    └─ CaribBeanComMetadata (评估后决定)
       ├─ ApiMetadataPlugin [新增]
       │    ├─ TenmusumeMetadata
       │    ├─ ModelMediaAsiaMetadata
       │    ├─ MuramuraMetadata
       │    ├─ OnePondoMetadata
       │    ├─ PacopacomamaMetadata
       │    └─ ThePornDbMetadata
       └─ (直接继承 MetadataPlugin)
            ├─ FanzaMetadata (混合: __NEXT_DATA__ + HTML + JSON-LD)
            └─ AvbaseMetadata (混合: Next.js API + HTML)
```

## 验证规则

| 规则 | 来源 | 验证方式 |
|------|------|---------|
| MetadataPlugin 公开接口不变 | FR-017 | Pyright 类型检查, 现有测试通过 |
| 子类必须实现 can_extract + _resolve + _parse | FR-004 | @abstractmethod 强制, 实例化时报错 |
| extract_metadata 返回同样结果 | FR-015 | 30 个现有 Mock 测试 |
| 错误时返回 None 不抛异常 | FR-016 | 测试中的 network_error 测试用例 |
| _fetch_page 可被覆写 | FR-005, FR-019 | dahlia/javbus 等覆写验证 |
| _get_tag_attr 返回 Optional[str] | FR-010 | Pyright 类型检查 |

## 状态转换

本功能无状态机，所有插件为无状态函数式调用：
```
identifier → can_extract(bool) → extract_metadata → Optional[BaseMetadata]
```

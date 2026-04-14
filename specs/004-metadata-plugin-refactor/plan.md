# 实施计划: 元数据插件架构重构 (PAVOne v0.3.2)

**分支**: `004-metadata-plugin-refactor` | **日期**: 2025-07-18 | **规范**: [spec.md](spec.md)
**输入**: 来自 `/specs/004-metadata-plugin-refactor/spec.md` 的功能规范

## 摘要

本计划实施 PAVOne v0.3.2 元数据插件架构重构，聚焦三个核心目标：

1. **基类提取**: 在 `MetadataPlugin` 和具体插件之间引入 `HtmlMetadataPlugin`、`ApiMetadataPlugin`、`JsonLdMetadataPlugin` 三个中间基类，封装 resolve → fetch → parse 模板方法和统一错误处理
2. **工具方法统一**: 将分散在 34 个插件中的 `_abs`（17 份）、`_parse_runtime`（14 份）、`_parse_date`（23 份）等重复实现，以超集策略合并至基类（合并所有已知格式变体，互不冲突）
3. **全量插件迁移**: 分 8 批将 34 个插件迁移至对应基类，每批独立提交，全量测试通过后推进下一批

技术方法：模板方法模式 + 钩子方法覆写；渐进式迁移，每批独立可验证；行为兼容性通过现有 Mock 测试保障。

## 技术背景

**语言/版本**: Python 3.10+
**主要依赖**: requests 2.x (HTTP), BeautifulSoup4 + lxml (HTML 解析), Pydantic 2.x (数据模型), Click 8.x (CLI)
**存储**: N/A（元数据提取为纯计算型操作，无持久化）
**测试**: pytest + unittest.TestCase + unittest.mock, 661 个测试函数, 62 个测试文件, conftest.py 共享 fixtures
**目标平台**: 跨平台 CLI (Windows 主要, Linux/macOS 次要)
**项目类型**: CLI 工具 + 插件系统
**性能目标**: N/A（元数据提取为网络 I/O 密集型，无特定性能基线）
**约束条件**: 迁移后行为完全兼容（同输入同输出）；`MetadataPlugin` 公开接口不变；现有 661 个测试全部通过
**规模/范围**: 34 个元数据插件, 7,148 行代码, 30 个专属测试文件 + 33 个 HTML fixture

## 章程检查

*门控: 必须在阶段 0 研究前通过. 阶段 1 设计后重新检查.*

### 阶段 0 前检查

| 章程原则 | 合规状态 | 说明 |
|----------|---------|------|
| I. 代码质量与类型安全 | ✅ 一致 | 新增 `_get_tag_attr` 提供类型安全的标签属性访问；基类方法含完整类型注解；`MetadataPlugin` 抽象契约保持不变 |
| II. 测试标准 | ✅ 一致 | 行为兼容性通过现有 Mock 测试验证，每批迁移后全量测试通过；无需新增测试基础设施 |
| III. 用户体验一致性 | ✅ 无影响 | 纯内部架构重构，不涉及 CLI 命令、输出格式或用户可见行为的变更 |
| IV. 性能要求 | ✅ 无影响 | 模板方法模式引入的方法调用开销可忽略不计（ns 级），网络 I/O 仍为主要瓶颈 |
| 技术栈与质量门控 | ✅ 一致 | 使用 Python 标准库 + 现有依赖，无新增依赖；代码通过 Pyright standard + Black + isort |
| CI 流水线质量门 | ✅ 一致 | 每批迁移后 CI 全绿为合并前提，符合章程流水线质量门要求 |

**门控结果**: ✅ 全部通过, 无违规, 可进入阶段 0

## 项目结构

### 文档(此功能)

```
specs/004-metadata-plugin-refactor/
├── plan.md              # 此文件
├── research.md          # 阶段 0 输出
├── data-model.md        # 阶段 1 输出
├── quickstart.md        # 阶段 1 输出
├── contracts/           # 阶段 1 输出 (基类公共 API 合同)
│   ├── html-metadata-plugin.md
│   ├── api-metadata-plugin.md
│   └── jsonld-metadata-plugin.md
└── tasks.md             # 阶段 2 输出 (/speckit.tasks 命令)
```

### 源代码(仓库根目录)

```
pavone/plugins/metadata/              # 元数据提取器插件目录
├── base.py                            # [修改] MetadataPlugin 基类 + 新增中间基类
│   ├── MetadataPlugin                 # [不变] 已有抽象基类
│   ├── HtmlMetadataPlugin             # [新增] HTML 解析通用基类
│   ├── ApiMetadataPlugin              # [新增] API/JSON 通用基类
│   └── JsonLdMetadataPlugin           # [新增] JSON-LD 解析通用基类
├── fc2_base.py                        # [修改] FC2BaseMetadata 改继承 HtmlMetadataPlugin
│
│   # === 阶段一新增完成后，阶段二分批迁移 ===
├── dahlia_metadata.py                 # [修改] 批次 1 - 改继承 HtmlMetadataPlugin
├── faleno_metadata.py                 # [修改] 批次 1
├── mywife_metadata.py                 # [修改] 批次 1
├── tenmusume_metadata.py              # [修改] 批次 1 - 改继承 ApiMetadataPlugin
├── sod_metadata.py                    # [修改] 批次 2
├── mgstage_metadata.py                # [修改] 批次 2
├── getchu_metadata.py                 # [修改] 批次 2
├── kin8tengoku_metadata.py            # [修改] 批次 2
├── madouqu_metadata.py                # [修改] 批次 2
├── modelmediaasia_metadata.py         # [修改] 批次 3 - 改继承 ApiMetadataPlugin
├── muramura_metadata.py               # [修改] 批次 3 - 改继承 ApiMetadataPlugin
├── pacopacomama_metadata.py           # [修改] 批次 3 - 改继承 ApiMetadataPlugin
├── onepondo_metadata.py               # [修改] 批次 3 - 改继承 ApiMetadataPlugin
├── theporndb_metadata.py              # [修改] 批次 3 - 改继承 ApiMetadataPlugin
├── c0930_metadata.py                  # [修改] 批次 4 - 改继承 JsonLdMetadataPlugin
├── h0930_metadata.py                  # [修改] 批次 4 - 改继承 JsonLdMetadataPlugin
├── h4610_metadata.py                  # [修改] 批次 4 - 改继承 JsonLdMetadataPlugin
├── fc2hub_metadata.py                 # [修改] 批次 4 - 改继承 JsonLdMetadataPlugin
├── heyzo_metadata.py                  # [修改] 批次 4 - 改继承 JsonLdMetadataPlugin
├── duga_metadata.py                   # [修改] 批次 5
├── jav321_metadata.py                 # [修改] 批次 5
├── javbus_metadata.py                 # [修改] 批次 5
├── tokyohot_metadata.py               # [修改] 批次 5
├── heydouga_metadata.py               # [修改] 批次 5
├── aventertainments_metadata.py       # [修改] 批次 6
├── gcolle_metadata.py                 # [修改] 批次 6
├── javfree_metadata.py                # [修改] 批次 6
├── pcolle_metadata.py                 # [修改] 批次 6
├── fc2ppvdb_metadata.py               # [修改] 批次 7 - FC2 家族迁移
├── supfc2_metadata.py                 # [修改] 批次 7
├── ppvdatabank_metadata.py            # [修改] 批次 7
├── fanza_metadata.py                  # [修改] 批次 8 - 最复杂
├── caribbeancom_metadata.py           # [修改] 批次 8
├── avbase_metadata.py                 # [修改] 批次 8
└── __init__.py                        # [不修改] pkgutil 自动发现无需改动

tests/
├── conftest.py                        # [不修改] 根级 fixtures
├── metadata/
│   ├── conftest.py                    # [不修改] mock_html_response / mock_json_response fixtures
│   └── test_*.py                      # [不修改] 30 个插件测试文件 — 迁移后原测试不变
└── sites/                             # [不修改] 33 个 HTML fixture 文件
```

**结构决策**: 所有变更在已有目录体系内进行。新增基类放在现有 `base.py` 文件中（与 `MetadataPlugin` 同文件），保持导入路径一致。不新增顶层目录或重组文件结构。

---

## 阶段一：基类提取与公共方法统一

### 1.1 目标架构（继承层次）

```
BasePlugin (plugins/base.py)
  └─ MetadataPlugin (plugins/metadata/base.py) ← 接口不变
       ├─ HtmlMetadataPlugin (新增, 同文件)
       │    ├─ JsonLdMetadataPlugin (新增, 同文件, 继承 HtmlMetadataPlugin)
       │    │    ├─ C0930Metadata
       │    │    ├─ H0930Metadata
       │    │    ├─ H4610Metadata
       │    │    ├─ Fc2HubMetadata
       │    │    └─ HeyzoMetadata
       │    ├─ FC2BaseMetadata (已有, 改继承 HtmlMetadataPlugin)
       │    │    ├─ SupFc2Metadata
       │    │    └─ PpvDataBankMetadata
       │    ├─ DahliaMetadata
       │    ├─ FalenoMetadata
       │    ├─ SodMetadata
       │    ├─ JavbusMetadata
       │    └─ ... (20 个 HTML 解析插件)
       ├─ ApiMetadataPlugin (新增, 同文件)
       │    ├─ TenmusumeMetadata
       │    ├─ ModelMediaAsiaMetadata
       │    ├─ MuramuraMetadata
       │    ├─ OnePondoMetadata
       │    ├─ PacopacomamaMetadata
       │    └─ ThePornDbMetadata
       └─ (特殊插件保持直接继承 MetadataPlugin)
            ├─ FanzaMetadata (混合: __NEXT_DATA__ + HTML + JSON-LD)
            ├─ AvbaseMetadata (混合: Next.js API + HTML)
            └─ CaribBeanComMetadata (复杂 HTML, 可选迁移)
```

### 1.2 HtmlMetadataPlugin 核心设计

```python
class HtmlMetadataPlugin(MetadataPlugin):
    """HTML 解析类元数据插件的公共基类。

    子类仅需实现: can_extract, _resolve, _parse
    可选覆写: _fetch_page (自定义 HTTP 行为)
    """

    # ── 模板方法 ──

    def extract_metadata(self, identifier: str) -> Optional[BaseMetadata]:
        try:
            movie_id, page_url = self._resolve(identifier)
            if not movie_id or not page_url:
                self.logger.error(f"无法解析 identifier: {identifier}")
                return None
            resp = self._fetch_page(page_url)
            soup = BeautifulSoup(resp.text, "lxml")
            return self._parse(soup, movie_id, page_url)
        except requests.RequestException as e:
            self.logger.error(f"HTTP 请求失败: {e}")
            return None
        except Exception as e:
            self.logger.error(f"提取元数据失败: {e}", exc_info=True)
            return None

    def _fetch_page(self, url: str) -> requests.Response:
        """获取页面, 子类可覆写以添加 cookies/headers/特殊超时"""
        return self.fetch(url, timeout=30)

    # ── 抽象方法 ──

    @abstractmethod
    def _resolve(self, identifier: str) -> Tuple[Optional[str], Optional[str]]:
        """将 identifier 解析为 (movie_id, page_url)"""
        ...

    @abstractmethod
    def _parse(self, soup: BeautifulSoup, movie_id: str, page_url: str) -> Optional[BaseMetadata]:
        """从 BeautifulSoup 对象解析元数据"""
        ...

    # ── 公共工具方法 (超集策略) ──

    @staticmethod
    def _abs(url: str, base: str) -> str:
        """相对 URL 转绝对 URL (统一 16 份实现)"""
        if url.startswith("http"):
            return url
        parsed = urlparse(base)
        if url.startswith("//"):
            return f"{parsed.scheme}:{url}"
        return f"{parsed.scheme}://{parsed.netloc}{url}"

    @staticmethod
    def _parse_runtime(text: str) -> Optional[int]:
        """解析时长文本 → 分钟数 (超集: 合并 3 种变体)
        支持: '120分', '1:30:00', '02:15', 'Apx. 122 Min.'
        """
        # Variant 1: Japanese minutes
        m = re.search(r"(\d+)\s*分", text)
        if m:
            return int(m.group(1))
        # Variant 3: English minutes
        m = re.search(r"(\d+)\s*[Mm]in", text)
        if m:
            return int(m.group(1))
        # Variant 2: HH:MM:SS or HH:MM
        m = re.match(r"(\d+):(\d+)(?::(\d+))?", text.strip())
        if m:
            hours = int(m.group(1))
            mins = int(m.group(2))
            return hours * 60 + mins
        return None

    @staticmethod
    def _parse_date(s: str) -> Optional[str]:
        """解析日期文本 → 'YYYY-MM-DD' (超集: 合并 3 种变体)
        支持: '2023/01/02', '2023-01-02', '2023年1月2日', '2023.01.02'
        """
        m = re.match(r"(\d{4})[年/\-.](\d{1,2})[月/\-.](\d{1,2})", s.strip())
        if m:
            return f"{m.group(1)}-{int(m.group(2)):02d}-{int(m.group(3)):02d}"
        return None

    @staticmethod
    def _parse_iso_duration(s: str) -> Optional[int]:
        """解析 ISO 8601 duration (PT1H30M) → 分钟数"""
        if not s:
            return None
        m = re.match(r"PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?", s)
        if m:
            h = int(m.group(1) or 0)
            mi = int(m.group(2) or 0)
            return h * 60 + mi or None
        m2 = re.search(r"(\d+)\s*分", s)
        if m2:
            return int(m2.group(1))
        return None

    @staticmethod
    def _get_tag_attr(tag: Optional[Any], attr: str) -> Optional[str]:
        """安全获取 BS4 tag 属性, 返回 Optional[str] (消除 _AttributeValue 类型问题)"""
        if tag is None:
            return None
        val = tag.get(attr)
        return str(val) if isinstance(val, str) else None
```

### 1.3 ApiMetadataPlugin 核心设计

```python
class ApiMetadataPlugin(MetadataPlugin):
    """API/JSON 类元数据插件的公共基类。

    子类仅需实现: can_extract, _resolve, _parse
    可选覆写: _fetch_api (自定义 HTTP 行为), _build_api_url (API URL 构建)
    """

    def extract_metadata(self, identifier: str) -> Optional[BaseMetadata]:
        try:
            movie_id, page_url = self._resolve(identifier)
            if not movie_id or not page_url:
                self.logger.error(f"无法解析 identifier: {identifier}")
                return None
            api_url = self._build_api_url(movie_id)
            resp = self._fetch_api(api_url)
            data = resp.json()
            return self._parse(data, movie_id, page_url)
        except requests.RequestException as e:
            self.logger.error(f"HTTP 请求失败: {e}")
            return None
        except Exception as e:
            self.logger.error(f"提取元数据失败: {e}", exc_info=True)
            return None

    def _fetch_api(self, url: str) -> requests.Response:
        """获取 API 响应, 子类可覆写以添加 headers/认证"""
        return self.fetch(url, timeout=30)

    @abstractmethod
    def _build_api_url(self, movie_id: str) -> str:
        """构建 API 请求 URL"""
        ...

    @abstractmethod
    def _resolve(self, identifier: str) -> Tuple[Optional[str], Optional[str]]:
        ...

    @abstractmethod
    def _parse(self, data: Dict[str, Any], movie_id: str, page_url: str) -> Optional[BaseMetadata]:
        ...

    # 继承 HtmlMetadataPlugin 的静态工具方法? 不, ApiMetadataPlugin 直接继承 MetadataPlugin
    # API 插件通常不需要 _abs, _parse_runtime, _parse_date
    # 如个别 API 插件需要, 可单独导入或直接使用
```

### 1.4 JsonLdMetadataPlugin 核心设计

```python
class JsonLdMetadataPlugin(HtmlMetadataPlugin):
    """JSON-LD 解析类元数据插件的公共基类。

    继承 HtmlMetadataPlugin, 在 HTML 解析基础上增加 JSON-LD 自动提取。
    子类仅需实现: can_extract, _resolve, _parse
    _parse 方法接收 soup + JSON-LD 数据, 子类可使用 JSON-LD 数据填充字段, HTML 作为 fallback。
    """

    def extract_metadata(self, identifier: str) -> Optional[BaseMetadata]:
        try:
            movie_id, page_url = self._resolve(identifier)
            if not movie_id or not page_url:
                self.logger.error(f"无法解析 identifier: {identifier}")
                return None
            resp = self._fetch_page(page_url)
            soup = BeautifulSoup(resp.text, "lxml")
            jsonld_data = self._extract_jsonld(soup)
            return self._parse_with_jsonld(soup, jsonld_data, movie_id, page_url)
        except requests.RequestException as e:
            self.logger.error(f"HTTP 请求失败: {e}")
            return None
        except Exception as e:
            self.logger.error(f"提取元数据失败: {e}", exc_info=True)
            return None

    def _extract_jsonld(self, soup: BeautifulSoup) -> Optional[Dict[str, Any]]:
        """从 HTML 中提取 JSON-LD 数据"""
        for script in soup.find_all("script", type="application/ld+json"):
            try:
                text = (script.string or "").replace("\n", "")
                data = json.loads(text)
                if isinstance(data, list):
                    data = data[0]
                return data
            except Exception:
                continue
        return None

    @abstractmethod
    def _parse_with_jsonld(
        self,
        soup: BeautifulSoup,
        jsonld: Optional[Dict[str, Any]],
        movie_id: str,
        page_url: str,
    ) -> Optional[BaseMetadata]:
        """从 JSON-LD + HTML soup 解析元数据"""
        ...

    def _parse(self, soup: BeautifulSoup, movie_id: str, page_url: str) -> Optional[BaseMetadata]:
        """重定向到 _parse_with_jsonld, 保持 HtmlMetadataPlugin 兼容"""
        jsonld_data = self._extract_jsonld(soup)
        return self._parse_with_jsonld(soup, jsonld_data, movie_id, page_url)
```

### 1.5 FC2BaseMetadata 改造

```python
# 修改前:
class FC2BaseMetadata(MetadataPlugin):
    ...

# 修改后:
class FC2BaseMetadata(HtmlMetadataPlugin):
    """FC2 元数据提取器基类 — 继承链: MetadataPlugin → HtmlMetadataPlugin → FC2BaseMetadata"""
    # 保留所有 FC2 专属方法: _extract_fc2_id, _build_fc2_code, _validate_fc2_identifier 等
    # 自动获得 HtmlMetadataPlugin 的模板方法和公共工具方法
    ...
```

---

## 阶段二：分批迁移策略

### 迁移批次总览

| 批次 | 插件数 | 目标基类 | 插件列表 | 风险等级 |
|------|--------|---------|---------|---------|
| 1 | 4 | Html + Api | dahlia, faleno, mywife, tenmusume | 🟢 低 |
| 2 | 5 | Html | sod, mgstage, getchu, kin8tengoku, madouqu | 🟢 低 |
| 3 | 5 | Api | modelmediaasia, muramura, pacopacomama, onepondo, theporndb | 🟢 低 |
| 4 | 5 | JsonLd | c0930, h0930, h4610, fc2hub, heyzo | 🟡 中 |
| 5 | 5 | Html | duga, jav321, javbus, tokyohot, heydouga | 🟡 中 |
| 6 | 4 | Html | aventertainments, gcolle, javfree, pcolle | 🟢 低 |
| 7 | 3 | Html (FC2) | fc2ppvdb, supfc2, ppvdatabank | 🟡 中 |
| 8 | 3 | 特殊 | fanza, caribbeancom, avbase | 🔴 高 |

**合计**: 34 个插件, 8 个批次

### 批次 1 — 基础验证 (4 插件)

最简单的插件，验证 `HtmlMetadataPlugin` 和 `ApiMetadataPlugin` 基类的正确性。

| 插件 | 行数 | 目标基类 | 有 _abs | 有 _parse_runtime | 有 _parse_date | 自定义 fetch |
|------|------|---------|---------|-------------------|---------------|-------------|
| dahlia | 175 | HtmlMetadataPlugin | ✓ | ✓ | ✓ | Cookie: modal=off |
| faleno | 173 | HtmlMetadataPlugin | ✓ | ✓ | ✓ | Cookie: modal=off |
| mywife | 137 | HtmlMetadataPlugin | ✓ | ✗ | ✗ | ✗ |
| tenmusume | 113 | ApiMetadataPlugin | ✗ | ✗ | ✗ | ✗ |

**迁移步骤** (每个插件通用):
1. 修改 `from .base import MetadataPlugin` → `from .base import HtmlMetadataPlugin` (或 ApiMetadataPlugin)
2. 修改 `class XxxMetadata(MetadataPlugin)` → `class XxxMetadata(HtmlMetadataPlugin)`
3. 删除本地 `extract_metadata` 模板方法（使用基类的模板）
4. 删除本地 `_abs`、`_parse_runtime`、`_parse_date` 方法（使用基类的）
5. 如有自定义 HTTP 逻辑，覆写 `_fetch_page` 方法
6. 运行该插件的测试: `uv run pytest tests/metadata/test_<name>.py -v`
7. 运行全量测试: `uv run pytest tests/ -v -m "not integration"`

**dahlia 迁移示例** (预计: 175 → ~130 行, 节省 ~45 行):

```python
# 修改前:
class DahliaMetadata(MetadataPlugin):
    def extract_metadata(self, identifier):  # 16 行 → 删除
        ...
    def _abs(url, base):                     #  5 行 → 删除
        ...
    def _parse_runtime(text):                #  7 行 → 删除
        ...
    def _parse_date(s):                      #  4 行 → 删除
        ...

# 修改后:
class DahliaMetadata(HtmlMetadataPlugin):
    def _fetch_page(self, url):              # 新增 2 行
        return self.fetch(url, headers={"Cookie": "modal=off"}, timeout=30)
    # can_extract, _resolve, _parse 保留不变
```

### 批次 2 — 标准 HTML (5 插件)

| 插件 | 行数 | 有 _abs | 有 _parse_runtime | 有 _parse_date | 自定义 fetch |
|------|------|---------|-------------------|---------------|-------------|
| sod | 204 | ✓ | ✓ | ✓ | ✗ |
| mgstage | 204 | ✓ | ✓ | ✓ | Cookie |
| getchu | 151 | ✓ | ✗ | ✓ | ✗ |
| kin8tengoku | 184 | ✓ | ✓ | ✓ | ✗ |
| madouqu | 160 | ✗ | ✗ | ✓ | ✗ |

### 批次 3 — API/JSON (5 插件)

| 插件 | 行数 | 目标基类 | 自定义 fetch |
|------|------|---------|-------------|
| modelmediaasia | 134 | ApiMetadataPlugin | Referer header |
| muramura | 140 | ApiMetadataPlugin | Content-Type header |
| pacopacomama | 144 | ApiMetadataPlugin | ✗ |
| onepondo | 203 | ApiMetadataPlugin | ✗ |
| theporndb | 177 | ApiMetadataPlugin | Bearer token auth |

### 批次 4 — JSON-LD (5 插件)

| 插件 | 行数 | 有 _parse_iso_duration | 有 _parse_date | 自定义 fetch |
|------|------|----------------------|---------------|-------------|
| c0930 | 193 | ✓ | ✓ | ✗ |
| h0930 | 181 | ✓ | ✗ | ✗ |
| h4610 | 181 | ✓ | ✗ | ✗ |
| fc2hub | 188 | ✓ | ✓ | ✗ |
| heyzo | 230 | ✓ | ✓ | ✗ |

### 批次 5 — 复杂 HTML (5 插件)

| 插件 | 行数 | 有 _abs | 有 _parse_runtime | 有 _parse_date | 自定义 fetch |
|------|------|---------|-------------------|---------------|-------------|
| duga | 241 | ✓ | ✓ | ✓ | ✗ |
| jav321 | 235 | ✓ | ✓ | ✓ | ✗ |
| javbus | 213 | ✓ | ✓ | ✓ | Cookie + Referer |
| tokyohot | 216 | ✓ | ✓ | ✓ | ✗ |
| heydouga | 198 | ✓ | ✓ | ✓ | ✗ |

### 批次 6 — 中等 HTML (4 插件)

| 插件 | 行数 | 有 _abs | 有 _parse_date | 自定义 fetch |
|------|------|---------|---------------|-------------|
| aventertainments | 202 | ✓ | ✓ | ✗ |
| gcolle | 170 | ✓ | ✓ | ✗ |
| javfree | 153 | ✗ | ✓ | ✗ |
| pcolle | 179 | ✓ | ✓ | Cookie |

### 批次 7 — FC2 家族 (3 插件)

**特殊处理**: FC2BaseMetadata 先改为继承 HtmlMetadataPlugin，再迁移子类。

| 插件 | 行数 | 当前基类 | 特殊点 |
|------|------|---------|--------|
| fc2ppvdb | 166 | FC2BaseMetadata | verify_ssl=False |
| supfc2 | 330 | FC2BaseMetadata | verify_ssl=False, max_retry=2 |
| ppvdatabank | 386 | FC2BaseMetadata | 最大插件, SearchPlugin 混入 |

**迁移步骤**:
1. 先修改 `fc2_base.py`: `FC2BaseMetadata(MetadataPlugin)` → `FC2BaseMetadata(HtmlMetadataPlugin)`
2. FC2BaseMetadata 自动获得模板方法和工具方法
3. 子类可能需要覆写 `_fetch_page` 以设置 `verify_ssl=False`
4. ppvdatabank 同时继承 SearchPlugin, 需保持多重继承不变

### 批次 8 — 混合/特殊 (3 插件)

| 插件 | 行数 | 解析策略 | 处理方式 |
|------|------|---------|---------|
| fanza | 309 | __NEXT_DATA__ + HTML + JSON-LD | 评估后决定: 可选迁移至 HtmlMetadataPlugin 并覆写 extract_metadata，或保留 MetadataPlugin |
| caribbeancom | 364 | 复杂 HTML | 迁移至 HtmlMetadataPlugin，删除重复方法 |
| avbase | 222 | Next.js API + HTML fallback | 评估后决定: 可选迁移至 ApiMetadataPlugin 并覆写 extract_metadata，或保留 MetadataPlugin |

**决策原则**: 如果迁移后代码比原有代码更简洁，则迁移；否则保留直接继承 `MetadataPlugin`，符合 FR-018 灵活性保留要求。

---

## 预期成果

| 指标 | 重构前 | 重构后 | 改善 |
|------|--------|--------|------|
| 插件总代码行数 | ~7,148 行 | ≤5,700 行 | ≥-20% |
| 新插件开发成本 | ~180 行 | ~100 行 | -44% |
| `_abs` 实现数 | 16 份 | 1 份 | -94% |
| `_parse_runtime` 实现数 | 14 份 | 1 份 | -93% |
| `_parse_date` 实现数 | 23 份 | 1 份 | -96% |
| `extract_metadata` 模板数 | 34 份 | ≤3 份 | -91% |
| 新插件需实现方法数 | 6-7 个 | 3 个 | -57% |
| 全量测试通过率 | 100% | 100% | 无回归 |

---

## 风险与缓解

| 风险 | 影响 | 概率 | 缓解措施 |
|------|------|------|---------|
| 工具方法超集策略引入解析歧义 | 高 | 低 | 各变体已验证互不冲突；分析确认无正则冲突 |
| 多重继承冲突 (ppvdatabank 的 SearchPlugin) | 中 | 低 | 保持 MRO 不变，仅修改 MetadataPlugin → HtmlMetadataPlugin 一环 |
| `resp.text` vs `resp.content` 不一致 | 中 | 中 | 模板方法统一使用 `resp.text`；个别需 `resp.content` 的插件覆写 `_fetch_page` |
| `_parse_runtime` 变体细微差异 | 低 | 低 | 超集合并覆盖所有格式；迁移时逐一对比确认 |
| 批次 8 特殊插件迁移困难 | 低 | 中 | FR-018 允许保留直接继承 MetadataPlugin |

---

## 章程检查 — 阶段 1 设计后重新评估

| 章程原则 | 合规状态 | 说明 |
|----------|---------|------|
| I. 代码质量与类型安全 | ✅ 一致 | 新增 `_get_tag_attr` 消除 `_AttributeValue` 类型问题；所有新增基类方法含完整类型注解；`MetadataPlugin` 抽象契约零变更 |
| II. 测试标准 | ✅ 一致 | 30 个插件测试文件 + 33 个 HTML fixture 提供行为兼容性保障；每批迁移后全量测试通过；符合 Mock 边界原则（仅在网络请求处 Mock） |
| III. 用户体验一致性 | ✅ 无影响 | 纯内部架构重构，CLI 命令、输出格式、错误处理行为均不变 |
| IV. 性能要求 | ✅ 无影响 | 模板方法引入的虚方法调用开销 ≤10ns，远低于网络 I/O（~100ms+） |
| 技术栈与质量门控 | ✅ 一致 | 无新增依赖；代码通过 Pyright standard + Black (127) + isort (black profile) |
| CI 流水线质量门 | ✅ 一致 | 每批次 PR 须通过 CI 全绿（格式+类型+测试+安全扫描）才能合并 |

**设计后门控结果**: ✅ 全部通过, 无复杂度违规, 可进入阶段 2 (tasks)

## 复杂度跟踪

> **无需填写**: 章程检查未发现需要正当理由的违规项。

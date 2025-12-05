# Jellyfin 集成功能详细开发计划

## 一、技术栈选择

### 核心库：`jellyfin-apiclient-python`
- **版本**：最新稳定版本
- **许可证**：GPL-3.0
- **优势**：
  - 官方维护，与 Jellyfin 服务器完全兼容
  - 提供完整的 API 封装
  - 支持多种认证方式（用户名密码、API Key）
  - 支持搜索、元数据更新、库管理等核心功能
  - 从 Jellyfin Kodi 项目提取，经过大规模验证

### 主要 API 方法
```python
# 认证
client.auth.connect_to_address(server_url)
client.auth.login(server_url, username, password)
client.authenticate(credentials)

# 搜索
client.jellyfin.search_media_items(term, media="Videos")

# 库操作
client.jellyfin.get_items()
client.jellyfin.get_item(item_id)
client.jellyfin.get_libraries()  # 获取库列表

# 元数据更新
client.jellyfin.update_item(item_id, metadata_dict)
client.jellyfin.item_played(item_id)
client.jellyfin.get_userdata_for_item(user_id, item_id)
client.jellyfin.update_userdata_for_item(user_id, item_id, data)
```

---

## 二、架构设计

### 模块结构
```
pavone/jellyfin/
├── __init__.py
├── client.py              # Jellyfin 客户端包装器
├── models.py              # 数据模型
├── library_manager.py     # 库管理
├── metadata_matcher.py    # 元数据匹配
└── exceptions.py          # 异常定义
```

### 设计原则
1. **轻量封装**：在 `jellyfin-apiclient-python` 基础上做最小化包装
2. **解耦集成**：独立模块，不直接修改插件系统
3. **配置驱动**：所有配置集中在 `config.json`
4. **错误处理**：统一的异常处理和日志记录

---

## 三、分阶段开发计划

### Phase 1: 基础设施搭建（3-4 天）

#### 1.1 添加依赖
- [ ] 在 `pyproject.toml` 中添加 `jellyfin-apiclient-python>=0.12.0`
- [ ] 运行 `uv sync` 安装依赖

#### 1.2 配置模块扩展
**文件**：`pavone/config/configs.py`

新增 `JellyfinConfig` 数据类：
```python
@dataclass
class JellyfinConfig:
    """Jellyfin 配置"""
    enabled: bool = False
    server_url: str = ""
    username: Optional[str] = None
    password: Optional[str] = None
    api_key: Optional[str] = None
    libraries: List[str] = field(default_factory=list)
    verify_ssl: bool = True
    timeout: int = 30
    auto_match: bool = True  # 是否自动匹配元数据
```

修改 `Config` 类，添加 `jellyfin: JellyfinConfig` 字段

#### 1.3 异常定义
**文件**：`pavone/jellyfin/exceptions.py`

```python
class JellyfinException(Exception):
    """Jellyfin 异常基类"""
    pass

class JellyfinConnectionError(JellyfinException):
    """连接错误"""
    pass

class JellyfinAuthenticationError(JellyfinException):
    """认证错误"""
    pass

class JellyfinAPIError(JellyfinException):
    """API 调用错误"""
    pass

class JellyfinVideoMatchError(JellyfinException):
    """视频匹配错误"""
    pass
```

#### 1.4 数据模型
**文件**：`pavone/jellyfin/models.py`

```python
from typing import Optional, List, Dict, Any
from dataclasses import dataclass

@dataclass
class JellyfinItem:
    """Jellyfin 库项"""
    id: str
    name: str
    type: str  # "Movie", "Series", "Episode", etc.
    container: Optional[str]  # 文件格式
    path: Optional[str]  # 文件路径
    metadata: Dict[str, Any]

@dataclass
class JellyfinMetadata:
    """Jellyfin 元数据"""
    title: str
    year: Optional[int]
    genres: List[str]
    overview: str
    runtime_minutes: Optional[int]
    premiere_date: Optional[str]
```

---

### Phase 2: Jellyfin 客户端集成（3-4 天）

#### 2.1 客户端包装器
**文件**：`pavone/jellyfin/client.py`

```python
from jellyfin_apiclient_python import JellyfinClient
from .exceptions import *
from .models import *

class JellyfinClientWrapper:
    """Jellyfin 客户端包装器"""
    
    def __init__(self, config: JellyfinConfig):
        self.config = config
        self.client = JellyfinClient()
        self._setup_config()
        self._authenticated = False
    
    def _setup_config(self):
        """配置客户端"""
        self.client.config.app("PAVOne", "0.2.0", "pavone-client", "pavone-unique-id")
        self.client.config.data["auth.ssl"] = "https" in self.config.server_url
    
    def authenticate(self) -> bool:
        """认证"""
        try:
            if self.config.api_key:
                # 使用 API Key 认证
                self.client.authenticate(
                    {"Servers": [{
                        "AccessToken": self.config.api_key,
                        "address": self.config.server_url
                    }]},
                    discover=False
                )
            else:
                # 使用用户名密码认证
                self.client.auth.connect_to_address(self.config.server_url)
                self.client.auth.login(
                    self.config.server_url,
                    self.config.username,
                    self.config.password
                )
            self._authenticated = True
            return True
        except Exception as e:
            raise JellyfinAuthenticationError(f"认证失败: {e}")
    
    def get_libraries(self) -> List[str]:
        """获取库列表"""
        try:
            libs = self.client.jellyfin.get_libraries()
            return [lib["Name"] for lib in libs.get("Items", [])]
        except Exception as e:
            raise JellyfinAPIError(f"获取库列表失败: {e}")
    
    def search_items(self, keyword: str, limit: int = 20) -> List[JellyfinItem]:
        """搜索视频"""
        try:
            result = self.client.jellyfin.search_media_items(
                term=keyword,
                media="Videos",
                limit=limit
            )
            return [self._parse_item(item) for item in result.get("Items", [])]
        except Exception as e:
            raise JellyfinAPIError(f"搜索失败: {e}")
    
    def get_library_items(self, library_names: Optional[List[str]] = None) -> List[JellyfinItem]:
        """获取库中的所有项"""
        try:
            libraries = library_names or self.config.libraries
            items = []
            for lib_name in libraries:
                # 获取库中的所有视频
                result = self.client.jellyfin.get_items(
                    filters="IsNotFolder",
                    includeItemTypes="Video",
                    searchTerm=None,
                    # 更多参数...
                )
                items.extend([self._parse_item(item) for item in result.get("Items", [])])
            return items
        except Exception as e:
            raise JellyfinAPIError(f"获取库项失败: {e}")
    
    def _parse_item(self, item_data: Dict) -> JellyfinItem:
        """解析 API 返回的项数据"""
        return JellyfinItem(
            id=item_data.get("Id"),
            name=item_data.get("Name"),
            type=item_data.get("Type"),
            container=item_data.get("Container"),
            path=item_data.get("Path"),
            metadata=item_data
        )
```

---

### Phase 3: 库管理功能（3-4 天）

#### 3.1 库管理器
**文件**：`pavone/jellyfin/library_manager.py`

```python
from typing import Optional, List, Dict
from .client import JellyfinClientWrapper
from .models import JellyfinItem

class LibraryManager:
    """Jellyfin 库管理器"""
    
    def __init__(self, client_wrapper: JellyfinClientWrapper):
        self.client = client_wrapper
        self._cache: Dict[str, List[JellyfinItem]] = {}
    
    def initialize(self) -> bool:
        """初始化并验证连接"""
        try:
            self.client.authenticate()
            return True
        except Exception as e:
            raise
    
    def get_monitored_libraries(self) -> List[str]:
        """获取要监控的库"""
        return self.client.config.libraries
    
    def scan_library(self, force_refresh: bool = False) -> Dict[str, List[JellyfinItem]]:
        """扫描库中的所有视频"""
        if not force_refresh and self._cache:
            return self._cache
        
        libraries = self.get_monitored_libraries()
        result = {}
        
        for lib_name in libraries:
            items = self.client.get_library_items([lib_name])
            result[lib_name] = items
        
        self._cache = result
        return result
    
    def find_item_by_code(self, code: str) -> Optional[JellyfinItem]:
        """按视频番号查找项"""
        # 需要匹配逻辑
        pass
    
    def find_item_by_title(self, title: str, threshold: float = 0.8) -> Optional[JellyfinItem]:
        """按标题查找项（模糊匹配）"""
        # 需要模糊匹配逻辑
        pass
```

#### 3.2 集成到下载流程 - 下载前重复检测
**修改文件**：`pavone/manager/execution.py`

在 `_extract_items()` 方法中添加 Jellyfin 重复检测与质量对比：
```python
def _extract_items(self, url: str) -> List[OperationItem]:
    # ... 现有代码 ...
    
    # 添加 Jellyfin 检查 - 检测重复并获取现有视频质量
    if self.config.jellyfin.enabled:
        jellyfin_check = self._check_jellyfin_duplicate(video_title)
        if jellyfin_check:
            self.logger.warning(f"视频已在 Jellyfin 中存在!")
            # 显示 Jellyfin 中的视频质量信息
            self._display_existing_video_quality(jellyfin_check)
            # 询问用户是否继续下载或跳过
            user_choice = self._prompt_user_duplicate_action(jellyfin_check)
            if user_choice == 'skip':
                return []  # 跳过下载
    
    # ... 继续下载流程 ...

def _check_jellyfin_duplicate(self, video_title: str) -> Optional[JellyfinItem]:
    """检查 Jellyfin 是否已有该视频"""
    # 按番号或标题在 Jellyfin 中搜索
    # 返回匹配的 JellyfinItem 或 None

def _display_existing_video_quality(self, item: JellyfinItem) -> None:
    """显示 Jellyfin 中已有视频的质量信息"""
    # 显示信息：
    # - 文件路径
    # - 文件大小
    # - 分辨率（如果可用）
    # - 比特率（如果可用）
    # - 添加时间
    # - 播放状态

def _prompt_user_duplicate_action(self, item: JellyfinItem) -> str:
    """提示用户是否跳过或重新下载"""
    # 返回: 'skip' / 'download' / 'cancel'
```

**质量信息字段**：
- 文件路径：`item.path`
- 文件大小：`item.metadata.get('Size')`
- 分辨率：`item.metadata.get('Width')x${item.metadata.get('Height')}`
- 比特率：`item.metadata.get('VideoBitrate')`
- 编码格式：`item.metadata.get('VideoCodec')`
- 添加时间：`item.metadata.get('DateCreated')`

#### 3.3 集成到下载流程 - 下载完成后的文件管理
**修改文件**：`pavone/manager/execution.py`

在下载完成后添加 Jellyfin 库移动交互流程：
```python
def _on_download_complete(self, operation: OperationItem) -> None:
    """下载完成后的处理"""
    # ... 现有代码 ...
    
    # 添加 Jellyfin 库移动流程
    if self.config.jellyfin.enabled:
        self._handle_jellyfin_library_import(operation)

def _handle_jellyfin_library_import(self, operation: OperationItem) -> None:
    """处理下载完成后的 Jellyfin 库导入"""
    
    # Step 1: 询问用户是否移动文件到 Jellyfin 库
    move_to_library = self._prompt_move_to_jellyfin_library()
    if not move_to_library:
        return
    
    # Step 2: 获取 Jellyfin 库列表和对应的本地文件夹
    library_folders = self._get_jellyfin_library_folders()
    
    # Step 3: 让用户选择目标库
    target_library = self._select_jellyfin_library(library_folders)
    if not target_library:
        return
    
    # Step 4: 如果库有多个文件夹，让用户选择具体文件夹
    target_folder = self._select_library_folder(target_library)
    if not target_folder:
        return
    
    # Step 5: 执行文件移动
    success = self._move_downloaded_files(
        source=operation.output_path,
        destination=target_folder
    )
    
    if success:
        # Step 6: 询问是否刷新 Jellyfin 库元数据
        refresh_metadata = self._prompt_refresh_jellyfin_metadata()
        if refresh_metadata:
            self._refresh_jellyfin_library(target_library)

def _prompt_move_to_jellyfin_library(self) -> bool:
    """询问用户是否移动文件到 Jellyfin 库"""
    # 返回 True/False

def _get_jellyfin_library_folders(self) -> Dict[str, List[str]]:
    """获取 Jellyfin 库及其对应的本地文件夹"""
    # 返回格式:
    # {
    #     "电影": ["/media/movies", "/mnt/films"],
    #     "电视剧": ["/media/tv"],
    #     "其他": ["/media/other"]
    # }
    libraries = self.jellyfin_client.get_libraries_with_paths()
    result = {}
    for lib in libraries:
        lib_name = lib['Name']
        lib_paths = lib['CollectionFolders']  # 库可能有多个文件夹
        result[lib_name] = lib_paths
    return result

def _select_jellyfin_library(self, library_folders: Dict[str, List[str]]) -> Optional[str]:
    """让用户选择目标库"""
    # 显示所有库及其文件夹信息
    # 返回选中的库名称或 None

def _select_library_folder(self, library_name: str) -> Optional[str]:
    """如果库有多个文件夹，让用户选择具体文件夹"""
    # 如果只有一个文件夹，直接返回
    # 如果有多个文件夹，显示列表让用户选择
    # 返回选中的文件夹路径或 None

def _move_downloaded_files(self, source: str, destination: str) -> bool:
    """执行文件移动操作"""
    # 将下载的文件移动到 Jellyfin 库文件夹
    # 注意：Windows 和 Linux 路径处理
    # 返回 True 成功，False 失败

def _prompt_refresh_jellyfin_metadata(self) -> bool:
    """询问用户是否刷新 Jellyfin 库的元数据"""
    # 返回 True/False

def _refresh_jellyfin_library(self, library_name: str) -> None:
    """刷新 Jellyfin 库的元数据"""
    # 调用 Jellyfin API 刷新指定库
    # 显示刷新进度/完成提示
```

**用户交互流程示意**：
```
下载完成
    ↓
询问: "是否将文件移动到 Jellyfin 库中? (Y/n)"
    ↓ (Yes)
显示 Jellyfin 库列表:
  1. 电影 → /media/movies, /mnt/films
  2. 电视剧 → /media/tv
  3. 其他 → /media/other
询问: "选择目标库 (1-3):"
    ↓ (选择 1)
电影库有多个文件夹，选择具体文件夹:
  1. /media/movies
  2. /mnt/films
询问: "选择文件夹 (1-2):"
    ↓ (选择 1)
移动文件: /downloads/video.mkv → /media/movies/video.mkv
    ↓
询问: "文件已移动，是否刷新 Jellyfin 库元数据? (Y/n)"
    ↓ (Yes)
刷新 Jellyfin 库元数据...
完成！
```

**关键考虑**：
- 文件系统与程序一致性：确保本地文件系统路径与 Jellyfin 中配置的路径对应
- 跨平台支持：处理 Windows (`C:\`) 和 Linux (`/mnt/`) 路径差异
- 安全移动：检查目标文件夹权限，确保文件移动不会失败
- 原子性：如果移动失败，需要清晰的错误提示和回滚选项

---

### Phase 4: 搜索插件扩展（2-3 天）

#### 4.1 Jellyfin 搜索插件
**文件**：`pavone/plugins/search/jellyfin_search.py`

```python
from typing import List
from pavone.models import SearchResult
from pavone.jellyfin import JellyfinClientWrapper, LibraryManager
from .base import SearchPlugin

class JellyfinSearchPlugin(SearchPlugin):
    """Jellyfin 搜索插件"""
    
    def __init__(self):
        super().__init__(site="jellyfin", name="JellyfinSearch")
        self.client = None
        self.library_manager = None
    
    def initialize(self) -> bool:
        """初始化搜索插件"""
        try:
            if not self.config.jellyfin.enabled:
                return False
            
            self.client = JellyfinClientWrapper(self.config.jellyfin)
            self.library_manager = LibraryManager(self.client)
            self.library_manager.initialize()
            return True
        except Exception as e:
            self.logger.error(f"初始化 Jellyfin 搜索插件失败: {e}")
            return False
    
    def search(self, keyword: str, limit: int = 20) -> List[SearchResult]:
        """搜索视频"""
        if not self.client:
            return []
        
        try:
            items = self.client.search_items(keyword, limit)
            results = []
            for item in items:
                result = SearchResult(
                    title=item.name,
                    url=f"jellyfin://{item.id}",
                    site="jellyfin",
                    code=self._extract_code(item),
                    metadata=item.metadata
                )
                results.append(result)
            return results
        except Exception as e:
            self.logger.error(f"Jellyfin 搜索失败: {e}")
            return []
    
    def _extract_code(self, item) -> str:
        """从 Jellyfin 项中提取视频番号"""
        # 需要实现提取逻辑
        return item.metadata.get("ExternalUrls", {}).get("imdb", "")
```

---

### Phase 5: CLI 命令扩展（1-2 天）

#### 5.1 Jellyfin 命令
**文件**：`pavone/cli/commands/jellyfin.py`

```python
import click
from pavone.jellyfin import JellyfinClientWrapper, LibraryManager
from pavone.config.settings import get_config_manager

@click.group()
def jellyfin():
    """Jellyfin 相关命令"""
    pass

@jellyfin.command()
def status():
    """查看 Jellyfin 连接状态"""
    config = get_config_manager().get_config()
    if not config.jellyfin.enabled:
        click.echo("Jellyfin 未启用")
        return
    
    try:
        client = JellyfinClientWrapper(config.jellyfin)
        client.authenticate()
        click.echo("✓ 连接成功")
    except Exception as e:
        click.echo(f"✗ 连接失败: {e}")

@jellyfin.command()
def libraries():
    """列出 Jellyfin 库"""
    # 实现列出库的逻辑
    pass

@jellyfin.command()
def scan():
    """扫描 Jellyfin 库"""
    # 实现扫描逻辑
    pass
```

---

### Phase 6: 测试和文档（2-3 天）

#### 6.1 单元测试
- [ ] `tests/test_jellyfin_client.py` - 客户端测试
- [ ] `tests/test_jellyfin_library_manager.py` - 库管理测试
- [ ] `tests/test_jellyfin_search_plugin.py` - 搜索插件测试

#### 6.2 集成测试
- [ ] Mock Jellyfin 服务器响应
- [ ] 测试完整工作流

#### 6.3 文档
- [ ] `docs/jellyfin-setup.md` - 配置指南
- [ ] 更新 `README.md`

---

## 四、实现要点

### 4.1 认证处理
```
优先级：API Key > 用户名密码
配置检验：确保 server_url 有效
错误处理：捕获认证异常，提供清晰错误消息
```

### 4.2 视频匹配策略
```
1. 精确匹配（按番号）
2. 标题相似度匹配（使用 difflib 或 fuzzywuzzy）
3. 手动确认
```

### 4.3 缓存策略
```
- 定期刷新库缓存（可配置时间间隔）
- 按库名称缓存结果
- 提供手动清除缓存的命令
```

---

## 五、时间估计

| 阶段 | 任务 | 估计时间 |
|------|------|--------|
| Phase 1 | 基础设施 | 3-4 天 |
| Phase 2 | 客户端集成 | 3-4 天 |
| Phase 3 | 库管理 | 3-4 天 |
| Phase 4 | 搜索插件 | 2-3 天 |
| Phase 5 | CLI 命令 | 1-2 天 |
| Phase 6 | 测试和文档 | 2-3 天 |
| **总计** | | **14-20 天** |

---

## 六、风险和缓解

| 风险 | 影响 | 缓解措施 |
|------|------|--------|
| Jellyfin 版本兼容性 | 中 | 使用稳定版 API，多版本测试 |
| 网络连接不稳定 | 中 | 实现重试机制和超时处理 |
| 大库性能 | 高 | 增量同步，分页获取，后台线程 |
| 元数据冲突 | 低 | 定义明确的合并策略 |


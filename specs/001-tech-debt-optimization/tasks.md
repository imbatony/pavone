# 任务: 技术欠债清理与体验优化

**输入**: 来自 `/specs/001-tech-debt-optimization/` 的设计文档
**前置条件**: plan.md(必需), spec.md(用户故事必需)

**测试**: 本迭代包含测试任务, 遵循章程 II. 测试标准 (AAA 模式, Mock 仅限系统边界).

**组织结构**: 任务按用户故事分组, 以便每个故事能够独立实施和测试.

## 格式: `[ID] [P?] [Story] 描述`
- **[P]**: 可以并行运行(不同文件, 无依赖关系)
- **[Story]**: 此任务属于哪个用户故事(例如: US1, US2, US3)
- 在描述中包含确切的文件路径

## 路径约定
- 源代码: `pavone/`
- 测试: `tests/`

---

## 阶段 1: 设置

**目的**: 创建本次迭代需要的基础模块和共享类型定义

- [x] T001 在 pavone/utils/signal_handler.py 中创建全局中断管理模块, 包含 `InterruptHandler` 类: threading.Event 作为中断标志, `register()` 注册 SIGINT/SIGTERM 信号处理器, `is_interrupted()` 检查中断状态, `reset()` 重置标志
- [x] T002 在 pavone/models/progress_info.py 中扩展 `ProgressInfo` 数据类, 新增可选字段: `total_segments: int = 0` (总分片数), `completed_segments: int = 0` (已完成分片数), `segment_speed: float = 0.0` (分片/秒); 保持现有字段向后兼容
- [x] T002a [P] 在 pavone/models/progress_info.py 或 pavone/models/segment_result.py 中定义 `SegmentResult` 数据类: 包含 index (分片索引), success (bool), error_message (可选失败原因). 供 US2 的 T014 使用
- [x] T003 在 tests/test_signal_handler.py 中为 InterruptHandler 编写单元测试: 测试注册/重置/中断状态检查, 测试多次调用 is_interrupted() 的幂等性

---

## 阶段 2: 基础 (阻塞前置条件)

**目的**: 将中断机制集成到下载器基类, 所有用户故事都依赖此基础

**⚠️ 关键**: 在此阶段完成之前, 无法开始 US1/US2/US3 的用户故事工作

- [x] T004 在 pavone/core/downloader/base.py 中集成 InterruptHandler: BaseDownloader.__init__() 获取全局 InterruptHandler 实例, 暴露 `self._interrupt_handler` 供子类使用
- [x] T005 在 pavone/manager/execution.py 中集成 InterruptHandler: 在 download_from_url() 和 execute_operation() 入口处初始化并注册信号处理器, 在操作完成/异常时重置

**检查点**: 基础就绪 — 中断标志可被所有下载器和执行管理器访问

---

## 阶段 3: 用户故事 1 - Ctrl+C 优雅终止下载 (优先级: P1) 🎯 MVP

**目标**: 用户按 Ctrl+C 后程序在 3 秒内优雅退出, 保留已下载的缓存分片和 .part 文件

**独立测试**: 启动 M3U8/HTTP 下载, 按 Ctrl+C, 验证 3 秒内退出且缓存文件保留

### 用户故事 1 的实施

- [x] T006 [US1] 在 pavone/core/downloader/m3u8_downloader.py 中改造 execute() 方法: ThreadPoolExecutor 提交任务前检查中断标志; as_completed() 循环中每次迭代检查中断标志, 若中断则调用 executor.shutdown(wait=False, cancel_futures=True) 并跳出循环
- [x] T007 [US1] 在 pavone/core/downloader/m3u8_downloader.py 中改造 _download_segment() 方法: 每个 chunk 写入后检查中断标志, 若中断则立即返回失败; 已完整写入的分片文件保留不删除
- [x] T008 [US1] 在 pavone/core/downloader/http_downloader.py 中改造 _download_multithreaded() 方法: 同 T006 模式, ThreadPoolExecutor 循环中检查中断标志, 中断时 shutdown 并保留 .part 文件
- [x] T009 [US1] 在 pavone/core/downloader/http_downloader.py 中改造 _download_chunk() 方法: 每个 chunk 写入后检查中断标志, 中断时保留已写入的 .part 文件并返回
- [x] T010 [US1] 在 pavone/core/downloader/http_downloader.py 中改造 _download_single_threaded() 方法: 流式读取循环中检查中断标志, 中断时保留已写入数据
- [x] T011 [US1] 在 pavone/manager/execution.py 中添加中断退出处理: 捕获 InterruptHandler 的中断状态, 输出"⚠️ 下载已中断, 已保存的缓存可用于断点续传"消息到 stderr, 以 exit code 130 退出
- [x] T012 [US1] 在 pavone/core/downloader/http_downloader.py 中实现 .part 文件续传验证: _download_multithreaded() 启动时检查已有 .part 文件, 获取文件大小并发送 Range 请求验证, 可续传则从断点继续, 否则删除重下
- [x] T012a [US1] 在 pavone/core/downloader/m3u8_downloader.py 中增强中断后分片完整性验证: _check_segment_exists() 除检查文件 >0 字节外, 还需验证分片未被截断 (如比较已知 Content-Length 或最小合理大小阈值); 中断时正在写入的分片标记为不完整, 下次启动时重新下载
- [x] T013 [US1] 在 tests/test_signal_handler.py 中补充集成测试: 模拟 M3U8Downloader 在中断标志设置后停止下载的行为; 验证已完成分片保留、未完成分片状态正确

**检查点**: Ctrl+C 可在 M3U8 和 HTTP 下载中优雅终止, 缓存保留

---

## 阶段 4: 用户故事 2 - M3U8 分段失败可跳过 (优先级: P1)

**目标**: M3U8 部分分片失败时, 用户可选择跳过失败分片并合并剩余分片

**独立测试**: 模拟分片失败, 验证交互式提示和跳过后合并产出可用文件

### 用户故事 2 的实施

- [x] T013a [US2] 验证 ffmpeg concat demuxer 对非连续分片的支持: 使用一组 M3U8 分片手动删除其中 2 个, 生成仅包含剩余分片的 filelist.txt, 运行 `ffmpeg -f concat -safe 0 -i filelist.txt -c copy output.mp4` 确认输出可播放. 若不可行则在 T016 中实现分片重新编号策略
- [x] T014 [US2] 在 pavone/core/downloader/m3u8_downloader.py 中重构 execute() 的失败处理逻辑: 下载完成后不再直接 return False, 改为收集 SegmentResult 列表 (成功/失败/索引/原因, 使用 T002a 定义的数据类), 返回给调用方决策
- [x] T015 [US2] 在 pavone/core/downloader/m3u8_downloader.py 中实现仅重试失败分片的方法 `_retry_failed_segments(failed_segments)`: 接受失败分片列表, 仅下载这些分片, 复用已有的 _download_segment() 和缓存机制
- [x] T016 [US2] 在 pavone/core/downloader/m3u8_downloader.py 中修改合并逻辑 `_merge_segments()` / `_merge_with_ffmpeg()`: 支持接受实际已下载的分片索引列表 (非连续), 生成仅包含已有分片的 ffmpeg concat 文件列表, 跳过缺失索引
- [x] T017 [US2] 在 pavone/manager/execution.py 中实现分片失败交互流程: 检测到失败分片后显示 "X/Y 段下载失败" 摘要, 提供 Rich 交互式选择菜单 (重试/跳过并合并/取消); 检测 stdin 是否可用, 不可用时根据 --skip-failed 标志决定行为 (跳过或取消); Rich 交互提示必须包裹 KeyboardInterrupt 处理, 确保 Ctrl+C 在等待输入时也能优雅退出
- [x] T018 [US2] 在 pavone/cli/__init__.py 和 pavone/cli/commands/download.py 中添加 `--skip-failed` 全局 CLI 选项: 传递到 execution.py 的下载流程, 控制非交互式环境的默认行为
- [x] T019 [US2] 在 tests/test_m3u8_segment_failure.py 中编写测试: 模拟部分分片失败场景, 验证失败汇总信息正确; 验证 --skip-failed 标志下自动跳过并合并; 验证全部失败时直接报告失败不提供跳过选项

**检查点**: M3U8 分片失败时用户可交互式选择, --skip-failed 可自动跳过

---

## 阶段 5: 用户故事 3 - M3U8 进度条优化 (优先级: P2)

**目标**: M3U8 下载进度条显示分片计数、百分比、分片/秒速度和预估剩余时间

**独立测试**: 下载多分片 M3U8, 验证进度条显示"完成/总数"格式和 ETA

### 用户故事 3 的实施

- [x] T020 [P] [US3] 在 pavone/manager/progress.py 中创建 `create_segment_progress_callback()` 函数: 使用 Rich Progress 显示分片级进度, 列配置为 TextColumn("M3U8") + BarColumn + "[{completed}/{total} 段]" + "{percentage:.0f}%" + "{speed} 段/秒" + TimeRemainingColumn; verbose 模式下额外显示字节/秒
- [x] T021 [US3] 在 pavone/core/downloader/m3u8_downloader.py 中改造进度回调调用: 使用 ProgressInfo 的新字段 total_segments 和 completed_segments 替代 total_size=0 模式; 每完成一个分片时更新 completed_segments 和 segment_speed; 从缓存恢复的分片计入 completed_segments 初始值
- [x] T022 [US3] 在 pavone/manager/execution.py 中修改 _set_progress_callback(): 当操作类型为 STREAM (M3U8) 时选择 create_segment_progress_callback(), 其他类型保持使用 create_console_progress_callback()
- [x] T023 [US3] 在 tests/test_m3u8_progress.py 中编写测试: 验证 ProgressInfo 的 segment 字段正确填充; 验证 create_segment_progress_callback 回调函数正确接收和显示分片级进度; 模拟 Ctrl+C 中断后重启场景 (部分分片已在缓存), 验证进度条从正确的恢复点 (非零) 开始

**检查点**: M3U8 下载进度条显示分片计数/百分比/速度/ETA

---

## 阶段 6: 用户故事 4 - 插件自动发现与加载 (优先级: P2)

**目标**: 新增插件仅需创建类文件并继承基类, 系统自动发现加载, 移除硬编码注册

**独立测试**: 在插件目录新增测试插件文件, 不修改注册代码, 验证自动加载

### 用户故事 4 的实施

- [x] T024 [US4] 在 pavone/manager/plugin_manager.py 中重构 _load_builtin_plugins(): 删除 builtin_plugins 硬编码字典和对应的 10 个手动 import 语句; 改为调用 _load_plugins_from_package() 扫描 pavone.plugins 包下的所有模块, 自动发现 ExtractorPlugin/MetadataPlugin/SearchPlugin 子类
- [x] T025 [US4] 在 pavone/manager/plugin_manager.py 中增强 _discover_plugins_in_module(): 添加类名冲突检测 — 若发现同名已注册插件, 记录警告并保留优先级更高的; 添加加载异常隔离 — 单个模块的 ImportError/SyntaxError 记录 warning 但不影响其他模块
- [x] T026 [US4] 在 pavone/plugins/__init__.py 中清理延迟导入 __getattr__() 机制: 移除手动维护的插件名 → 模块路径映射; 保留类型导出 (ExtractorPlugin, MetadataPlugin, SearchPlugin, BasePlugin) 用于外部引用
- [x] T027 [US4] 在 tests/test_plugin_autodiscovery.py 中编写测试: 使用临时目录创建测试插件文件, 验证 PluginManager 自动发现并加载; 验证禁用列表中的插件被跳过且有日志; 验证语法错误的插件文件不影响其他插件; 验证类名冲突时优先级高的被保留

**检查点**: 硬编码注册已移除, 插件纯自动发现, 所有现有插件正常加载

---

## 阶段 7: 用户故事 5 - 消除重复代码, 抽取公共工具类 (优先级: P3)

**目标**: 将各插件中重复的 HTML 元数据提取逻辑提炼为独立工具函数, 减少 60%+ 重复代码

**独立测试**: 运行完整插件测试套件, 验证提取结果与重构前一致

### 用户故事 5 的实施

- [x] T028 [P] [US5] 在 pavone/utils/html_metadata_utils.py 中新增独立提取函数: `extract_title(html, selectors=None, patterns=None)` 支持 OG 标签、CSS 选择器和正则; `extract_code(html, patterns=None)` 提取番号; `extract_cover(html, selectors=None)` 提取封面 URL; `extract_date(html, patterns=None, formats=None)` 解析多种日期格式; `extract_actors(html, selectors=None, patterns=None)` 提取演员列表; `extract_genres(html, selectors=None)` 提取类型标签; `extract_m3u8_url(html, patterns=None)` 提取 M3U8 链接. 每个函数接受 HTML 字符串和可选的站点特定参数
- [x] T029 [P] [US5] 在 tests/test_extract_utils.py 中为每个新增的独立提取函数编写单元测试: 使用各站点的真实 HTML 样本 (从 tests/sites/ 获取) 验证提取结果; 测试默认参数和自定义参数两种模式; 测试 HTML 不包含目标内容时的 None 返回值
- [x] T030 [US5] 在 pavone/plugins/missav_plugin.py 中将内联 _extract_* 方法替换为调用共享提取函数: 保留站点特定的选择器/正则作为参数传入; 对于非标准提取逻辑保留自定义方法覆盖
- [x] T031 [US5] 在 pavone/plugins/javrate_plugin.py 中将内联 _extract_* 方法替换为调用共享提取函数: 同 T030 模式
- [x] T032 [US5] 在 pavone/plugins/jtable_plugin.py 中将内联 _extract_* 方法替换为调用共享提取函数: 同 T030 模式
- [x] T033 [US5] 在 pavone/plugins/memojav_plugin.py 中将内联 _extract_* 方法替换为调用共享提取函数: 同 T030 模式
- [x] T034 [US5] 在 pavone/plugins/av01_plugin.py 中评估并替换可复用的提取逻辑: AV01 使用 JSON-LD 和 API, 与 HTML 提取模式不同; 仅替换确有重叠的部分 (如 OG 标签提取), 保留 API 特有逻辑
- [x] T035 [US5] 运行完整测试套件 (pytest tests/ -v) 验证所有现有插件测试无回归

**检查点**: 5 个插件的重复提取代码减少 60%+, 所有测试通过

---

## 阶段 8: 完善与横切关注点

**目的**: 跨故事的质量保障和文档更新

- [x] T036 [P] 运行 Black + isort 格式化所有修改文件, 确保零格式错误
- [x] T037 [P] 运行 Pyright standard 检查所有修改文件, 修复新增类型错误至零
- [x] T038 [P] 运行 flake8 检查所有修改文件, 修复关键错误 (E9, F63, F7, F82)
- [x] T039 在 docs/usage.md 中更新 download 命令文档: 新增 --skip-failed 标志说明, 更新 Ctrl+C 中断行为描述
- [x] T040 运行完整测试套件 pytest tests/ -v --cov=pavone, 确认整体测试通过率和覆盖率

---

## 依赖关系与执行顺序

### 阶段依赖关系

- **设置 (阶段 1)**: 无依赖 — 可立即开始
- **基础 (阶段 2)**: 依赖于阶段 1 (InterruptHandler 和 ProgressInfo) — 阻塞所有用户故事
- **US1 Ctrl+C (阶段 3)**: 依赖于阶段 2 — P1 最高优先级
- **US2 分段失败 (阶段 4)**: 依赖于阶段 2 + 部分依赖 US1 的中断集成 (T006/T007 中的中断检查) — P1
- **US3 进度条 (阶段 5)**: 依赖于阶段 1 (ProgressInfo 扩展) 和阶段 2 (T021 修改的 m3u8_downloader.py 已被阶段 2 改动) — 建议在阶段 2 后开始
- **US4 插件自动发现 (阶段 6)**: 仅依赖于阶段 1 — 可与 US1/US2/US3 并行
- **US5 代码去重 (阶段 7)**: 仅依赖于阶段 1 — 可与其他故事并行, 但建议在 US4 后执行 (自动发现改变了插件加载方式)
- **完善 (阶段 8)**: 依赖于所有故事完成

### 用户故事依赖关系

- **US1 (P1)**: 可在基础 (阶段 2) 后开始 — 无其他故事依赖
- **US2 (P1)**: 可在基础 (阶段 2) 后开始 — 与 US1 有轻度耦合 (中断标志在 m3u8_downloader.py 中共用), 建议 US1 先完成或同步进行
- **US3 (P2)**: 可在阶段 2 后开始 — T021 修改的 m3u8_downloader.py 在阶段 2 已引入 interrupt_handler, 需基于该版本开发
- **US4 (P2)**: 可在阶段 1 后开始 — 完全独立于 US1/US2/US3
- **US5 (P3)**: 可在阶段 1 后开始 — 建议在 US4 后执行以避免合并冲突

### 每个用户故事内部

- 模型/工具在业务逻辑之前
- 核心实施在集成之前
- 测试与实施同阶段

### 并行机会

- 阶段 1: T001/T002/T003 全部可并行
- 阶段 3 (US1): T006+T008 可并行 (M3U8/HTTP 分别修改)
- 阶段 5 (US3): T020 可与阶段 3/4 并行 (独立模块)
- 阶段 6 (US4): 整个阶段可与阶段 3/4/5 并行
- 阶段 7 (US5): T028+T029 可并行; T030/T031/T032/T033 全部可并行 (不同文件)
- 阶段 8: T036+T037+T038 可并行

---

## 并行示例: 最大并行度执行

```
时间线 →
─────────────────────────────────────────────────────────
轨道 A: T001 → T004 → T006 → T007 → T011 → T014 → T015 → T016 → T017 → T018
轨道 B: T002 → T005 → T008 → T009 → T010 → T012 → T013 → T019
轨道 C: T003 ─────→ T020 → T021 → T022 → T023
轨道 D: ──────────→ T024 → T025 → T026 → T027
轨道 E: ──────────────────────────→ T028 → T030 → T031 → T032 → T033 → T034 → T035
轨道 F: ──────────────────────────→ T029
最终: T036 + T037 + T038 → T039 → T040
```

---

## 实施策略

- **MVP 范围**: US1 (Ctrl+C 优雅终止) — 解决最关键的可用性阻塞
- **增量交付顺序**: US1 → US2 → US3 → US4 → US5
- **风险缓解**: US4 (纯自动发现) 是最高风险项 — 建议早期开始并在独立测试中验证, 避免阻塞其他故事
- **回归防护**: US5 (代码去重) 必须在最后执行完整测试套件, 任何回归立即回退

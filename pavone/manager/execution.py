import os
from typing import List, Optional, Tuple

import click

from ..config.logging_config import get_logger
from ..config.settings import Config
from ..core import (
    DummyOperator,
    FileMover,
    HTTPDownloader,
    M3U8Downloader,
    MetadataSaver,
    Operator,
)
from ..models import ItemType, OperationItem, OperationType
from ..utils.signal_handler import get_interrupt_handler
from .plugin_manager import PluginManager, get_plugin_manager
from .progress import (
    create_console_progress_callback,
    create_segment_progress_callback,
    create_silent_progress_callback,
)

# Jellyfin 集成
try:
    from ..jellyfin import JellyfinDownloadHelper
except ImportError:
    JellyfinDownloadHelper = None


class ExecutionManager:
    """
    执行管理器
    负责处理下载和组织的执行逻辑

    提供统一的下载接口，自动处理URL提取、用户选择和下载器选择
    也可在整理文件时使用
    """

    def __init__(self, config: Config, plugin_manager: Optional[PluginManager] = None):
        """
        初始化执行管理器
        Args:
            config: 配置对象
            plugin_manager: 可选的插件管理器实例
        """

        self.config: Config = config
        self.plugin_manager = plugin_manager or get_plugin_manager()
        self.logger = get_logger(__name__)
        # 初始化下载器
        self.http_downloader = HTTPDownloader(config)
        self.m3u8_downloader = M3U8Downloader(config)
        self.metadata_saver = MetadataSaver(config)
        self.file_mover = FileMover(config)
        # 初始化 Jellyfin 助手
        self.jellyfin_helper = None
        if JellyfinDownloadHelper and config.jellyfin.enabled:
            try:
                self.jellyfin_helper = JellyfinDownloadHelper(config.jellyfin)
            except Exception as e:
                self.logger.warning(f"Jellyfin 助手初始化失败: {e}")
        # 确保插件已加载
        if not self.plugin_manager.extractor_plugins:
            self.plugin_manager.load_plugins()

    def _extract_items(self, url: str) -> List[OperationItem]:
        """
        从URL提取下载选项

        Args:
            url: 要处理的URL

        Returns:
            可用的下载选项列表

        Raises:
            ValueError: 如果找不到合适的提取器
        """
        # 获取合适的提取器
        extractor = self.plugin_manager.get_extractor_for_url(url)
        if not extractor:
            raise ValueError(f"没有找到能处理URL的提取器: {url}")
        # 提取下载选项
        if hasattr(extractor, "extract") and callable(getattr(extractor, "extract")):
            options = extractor.extract(url)  # type: ignore
            if not options:
                raise ValueError(f"提取器 {extractor.name} 没有找到下载选项")
            return options
        else:
            raise ValueError(f"提取器 {extractor.name} 缺少extract方法")

    def _select_download_item(self, items: List[OperationItem]) -> OperationItem:
        """
        让用户选择下载选项

        Args:
            options: 可用的下载选项列表

        Returns:
            用户选择的下载选项
              Raises:
            ValueError: 如果用户输入无效或取消选择
        """
        if len(items) == 1:
            click.echo(f"找到1个下载选项: {items[0].get_description()}")
            return items[0]

        click.echo(f"找到 {len(items)} 个下载选项:")
        for i, opt in enumerate(items, 1):
            click.echo(f"  {i}. {opt.get_description()}")

        while True:
            try:
                choice = input(f"请选择下载选项 (1-{len(items)}, 0取消): ").strip()

                if choice == "0":
                    raise ValueError("用户取消了下载")

                choice_num = int(choice)
                if 1 <= choice_num <= len(items):
                    selected = items[choice_num - 1]
                    click.echo(f"已选择: {selected.get_description()}")
                    return selected
                else:
                    click.echo(f"请输入1到{len(items)}之间的数字")

            except ValueError as e:
                if "用户取消了下载" in str(e):
                    raise
                click.echo("输入无效，请输入数字")
            except KeyboardInterrupt:
                click.echo("\n已取消")
                raise ValueError("用户取消了下载")

    def _handle_jellyfin_duplicate_check(self, item: OperationItem) -> bool:
        """
        检查 Jellyfin 中是否已有该视频，如果有则询问用户是否继续

        Args:
            item: 操作项

        Returns:
            True 表示继续下载，False 表示跳过
        """
        try:
            if not self.jellyfin_helper:
                self.logger.debug("Jellyfin helper 未初始化")
                return True

            if not self.jellyfin_helper.is_available():
                self.logger.debug("Jellyfin 不可用")
                return True

            video_title = item.get_description()
            video_code = item.get_code()  # 尝试获取代码而不是文件名前缀

            # 如果代码为空，尝试从标题中提取番号
            if not video_code:
                # 尝试从标题开头提取番号（通常格式为：CODE-XXXX）
                import re

                match = re.match(r"^([A-Z0-9]+-\d+)", video_title)
                if match:
                    video_code = match.group(1)

            self.logger.info(f"检查 Jellyfin 重复: {video_title} (代码: {video_code})")

            duplicate_info = self.jellyfin_helper.check_duplicate(video_title, video_code)

            if duplicate_info and duplicate_info.exists:
                # 用黄色显示警告信息
                click.secho("\n! 警告: 视频已在 Jellyfin 中存在", fg="yellow", bold=True)
                if duplicate_info.item:
                    click.secho(f"  项目: {duplicate_info.item.name}\n", fg="yellow")

                # 显示质量信息
                if duplicate_info.quality_info:
                    self.jellyfin_helper.display_existing_video_quality(duplicate_info.quality_info)

                    # 比较质量
                    new_quality = item.get_quality_info()
                    existing_quality = duplicate_info.quality_info.resolution

                    # 智能建议
                    suggestion = self._compare_quality_and_suggest(new_quality, existing_quality)
                    if suggestion:
                        click.echo(f"\n{suggestion}\n")  # 询问用户是否继续
                while True:
                    try:
                        choice = input("是否继续下载? (y/n/s - 是/否/跳过其他): ").strip().lower()
                        if choice in ("y", "yes", "是"):
                            self.logger.info("用户选择继续下载")
                            return True
                        elif choice in ("n", "no", "否"):
                            self.logger.info("用户选择取消下载")
                            return False
                        elif choice in ("s", "skip", "跳过"):
                            self.logger.info("用户选择跳过")
                            return False
                        else:
                            click.echo("请输入 y/n/s 中的一个")
                    except KeyboardInterrupt:
                        click.echo("\n已取消")
                        raise

            return True

        except KeyboardInterrupt:
            raise
        except Exception as e:
            self.logger.warning(f"Jellyfin 重复检查失败: {e}")
            return True  # 检查失败时继续下载

    def _compare_quality_and_suggest(self, new_quality: str, existing_quality: str) -> str:
        """
        比较新下载的质量和现有质量，给出建议

        Args:
            new_quality: 新下载的质量信息（如 "360p", "480p", "1080p"）
            existing_quality: 现有视频的分辨率（如 "720x410"）

        Returns:
            建议文本，如果相同或更好则返回空字符串
        """
        try:
            # 从新质量中提取分辨率数字
            import re

            new_match = re.search(r"(\d+)p", str(new_quality))
            new_res = int(new_match.group(1)) if new_match else 0

            # 从现有分辨率中提取高度
            existing_match = re.search(r"x(\d+)", str(existing_quality))
            existing_res = int(existing_match.group(1)) if existing_match else 0

            if new_res <= 0 or existing_res <= 0:
                return ""

            # 比较并给出建议
            if new_res < existing_res:
                click.secho(
                    f"建议: 新下载的质量 ({new_quality}) 低于现有视频 ({existing_quality})，建议不下载。",
                    fg="red",
                )
                return ""
            elif new_res == existing_res:
                return f"提示: 新下载的质量 ({new_quality}) 与现有视频相同。"
            else:
                return f"提示: 新下载的质量 ({new_quality}) 高于现有视频 ({existing_quality})，可以考虑更新。"
        except Exception as e:
            self.logger.debug(f"质量比较失败: {e}")
            return ""

    def _handle_jellyfin_post_download(self, item: OperationItem) -> None:  # noqa: C901
        """
        下载完成后处理 Jellyfin 集成

        移动整个下载文件夹到 Jellyfin 库（而不是单个文件）

        Args:
            item: 操作项（根项）
        """
        try:
            target_path = item.get_target_path()
            if not target_path:
                self.logger.warning("无法获取下载文件的目标路径")
                return

            # 获取源文件夹（下载的所有文件都在这个文件夹下）
            source_folder = os.path.dirname(target_path)
            if not os.path.isdir(source_folder):
                self.logger.warning(f"源文件夹不存在: {source_folder}")
                return

            source_folder_name = os.path.basename(source_folder)

            # 显示待移动的源文件夹信息
            click.secho("\n" + "=" * 60, fg="cyan")
            click.secho("准备移动下载文件夹到 Jellyfin", fg="cyan", bold=True)
            click.secho("=" * 60, fg="cyan")
            click.secho("📁 源文件夹:", fg="yellow", bold=True)
            click.secho(f"   {source_folder}", fg="yellow")
            click.echo()

            # 询问是否移动文件到 Jellyfin 库
            if not click.confirm("是否将此文件夹移动到 Jellyfin 库中?", default=True):
                return

            # 获取库列表
            if self.jellyfin_helper is None:
                self.logger.warning("Jellyfin helper 未初始化")
                click.secho("\n❌ Jellyfin helper 未初始化，无法继续操作。", fg="red", bold=True)
                return
            library_folders = self.jellyfin_helper.get_library_folders()
            if not library_folders:
                self.logger.warning("无法获取 Jellyfin 库信息")
                click.secho(
                    "\n❌ 无法获取 Jellyfin 库信息，请检查服务器连接。",
                    fg="red",
                    bold=True,
                )
                return

            # 过滤出有有效文件夹路径的库
            valid_libraries = {
                lib_name: folders for lib_name, folders in library_folders.items() if folders  # 只保留非空的文件夹列表
            }

            if not valid_libraries:
                click.secho("\n❌ 没有找到任何配置了文件夹路径的库", fg="red", bold=True)
                click.secho(f"已检查的库: {list(library_folders.keys())}", fg="yellow")
                click.secho("请在 Jellyfin 服务器中检查库的配置。", fg="yellow")
                return

            # 显示库列表
            click.secho("\n可用的 Jellyfin 库:", fg="cyan", bold=True)
            libraries_list = list(valid_libraries.items())
            for i, (lib_name, folders) in enumerate(libraries_list, 1):
                click.secho(f"  {i}. ", fg="cyan", nl=False)
                click.secho(f"{lib_name}", fg="green", bold=True, nl=False)
                click.echo()
                for folder in folders:
                    click.echo(f"     📁 {folder}")

            # 让用户选择库
            while True:
                try:
                    lib_choice = input(f"\n请选择库 (1-{len(libraries_list)}): ").strip()
                    lib_choice_num = int(lib_choice)
                    if 1 <= lib_choice_num <= len(libraries_list):
                        selected_lib_name, selected_folders = libraries_list[lib_choice_num - 1]
                        click.secho("✓ 已选择库: ", fg="green", nl=False)
                        click.secho(f"{selected_lib_name}", fg="green", bold=True)
                        break
                    else:
                        click.secho(f"❌ 请输入 1 到 {len(libraries_list)} 之间的数字", fg="red")
                except KeyboardInterrupt:
                    click.echo("\n已取消")
                    raise
                except ValueError:
                    click.secho("❌ 输入无效，请输入数字", fg="red")

            # 如果库有多个文件夹，让用户选择
            if len(selected_folders) > 1:
                click.secho(f"\n库 '{selected_lib_name}' 有多个文件夹:", fg="cyan", bold=True)
                for i, folder in enumerate(selected_folders, 1):
                    click.echo(f"  {i}. 📁 {folder}")

                while True:
                    try:
                        folder_choice = input(f"\n请选择文件夹 (1-{len(selected_folders)}): ").strip()
                        folder_choice_num = int(folder_choice)
                        if 1 <= folder_choice_num <= len(selected_folders):
                            target_folder = selected_folders[folder_choice_num - 1]
                            click.secho("✓ 已选择文件夹: ", fg="green", nl=False)
                            click.secho(f"{target_folder}", fg="green", bold=True)
                            break
                        else:
                            click.secho(
                                f"❌ 请输入 1 到 {len(selected_folders)} 之间的数字",
                                fg="red",
                            )
                    except KeyboardInterrupt:
                        click.echo("\n已取消")
                        raise
                    except ValueError:
                        click.secho("❌ 输入无效，请输入数字", fg="red")
            else:
                # 单个文件夹的情况
                if selected_folders:
                    target_folder = selected_folders[0]
                    click.secho("✓ 已选择文件夹: ", fg="green", nl=False)
                    click.secho(f"{target_folder}", fg="green", bold=True)
                else:
                    # 这种情况不应该发生，因为我们已经过滤出了有效的库
                    click.secho(
                        f"\n❌ 错误: 库 '{selected_lib_name}' 的文件夹为空",
                        fg="red",
                        bold=True,
                    )
                    return

            # 最终确认 - 显示源和目标
            if not target_folder:
                click.secho("\n❌ 未选择有效的目标文件夹", fg="red", bold=True)
                return

            target_location = os.path.join(target_folder, source_folder_name)

            click.secho("\n" + "=" * 60, fg="yellow")
            click.secho("移动确认:", fg="yellow", bold=True)
            click.secho("=" * 60, fg="yellow")
            click.secho("📁 源位置:", fg="yellow", bold=True)
            click.secho(f"   {source_folder}", fg="yellow")
            click.secho("\n📁 目标位置:", fg="yellow", bold=True)
            click.secho(f"   {target_location}", fg="yellow")
            click.echo()

            if not click.confirm("确认移动?", default=True):
                click.secho("已取消移动", fg="yellow")
                return

            # 执行文件夹移动
            if self.jellyfin_helper is None:
                click.secho("\n❌ Jellyfin helper 未初始化", fg="red", bold=True)
                return
            if self.jellyfin_helper.move_to_library(source_folder, target_folder):
                click.secho("\n✓ 文件夹移动成功!", fg="green", bold=True)
                self.logger.info(f"文件夹移动成功: {source_folder} -> {target_location}")

                # 询问是否刷新元数据
                if click.confirm("\n是否增量刷新 Jellyfin 库的元数据?", default=True):
                    if self.jellyfin_helper and self.jellyfin_helper.refresh_library(selected_lib_name):
                        click.secho("✓ 元数据增量刷新成功!", fg="green", bold=True)
                        self.logger.info("元数据增量刷新成功")
                    else:
                        click.secho("❌ 元数据刷新失败", fg="red", bold=True)
                        self.logger.warning("元数据刷新失败")
            else:
                click.secho("\n❌ 文件夹移动失败", fg="red", bold=True)
                self.logger.error("文件夹移动失败")

        except KeyboardInterrupt:
            click.echo("\n已取消")
            raise
        except Exception as e:
            self.logger.warning(f"Jellyfin 后下载处理失败: {e}")

    def _get_operator_for_item(self, item: OperationItem) -> Operator:
        """
        跟据操作项获取合适的执行器
        Args:
            item: 操作项
        """
        # TODO: 未来可能支持更多执行器类型，需要用户进行配置或者选择
        # M3U8Downloader只适用于stream类型
        if item.opt_type == OperationType.DOWNLOAD:
            if item.item_type == ItemType.STREAM:
                # 如果是M3U8类型，使用M3U8Downloader
                return self.m3u8_downloader
            elif item.item_type in (ItemType.VIDEO, ItemType.IMAGE):
                # 如果是视频或图片类型，使用HTTPDownloader
                return self.http_downloader
            else:
                # 对于其他类型, 暂时不支持
                return DummyOperator(self.config)
        elif item.opt_type == OperationType.SAVE_METADATA:
            # 如果是元数据类型，使用MetadataSaver
            return self.metadata_saver
        elif item.opt_type == OperationType.MOVE:
            # 如果是移动操作，使用FileMover
            return self.file_mover
        else:
            self.logger.warning(f"未找到合适的执行器，使用DummyOperator作为占位符: {item.get_description()}")
            return DummyOperator(self.config)

    def _execute_operation(
        self,
        selected_item: OperationItem,
        silent: bool = False,
        parent: Optional[OperationItem] = None,
    ) -> bool:
        """
        执行操作项（下载、文件移动等）

        Args:
            selected_item: 用户选择的选项
            silent: 是否静默模式（不显示进度）
            parent: 父项（用于递归调用）

        Returns:
            是否成功
        """

        success = True
        is_root_item = parent is None  # 判断是否是根项

        # 在下载前检查 Jellyfin 中是否已有该视频（仅在非静默模式和根项时提示用户）
        if (
            self.jellyfin_helper
            and self.jellyfin_helper.is_available()
            and selected_item.opt_type == OperationType.DOWNLOAD
            and not silent
            and is_root_item
        ):
            if not self._handle_jellyfin_duplicate_check(selected_item):
                return False

        # 设置目标路径
        # 对于 MOVE 操作，如果已经设置了 target_path 且没有父项（根项），则不覆盖
        # 这样可以保留 organize 命令通过 build_operation 设置的路径
        if selected_item.opt_type == OperationType.MOVE and parent is None and selected_item.get_target_path():
            # 根 MOVE 项已有 target_path，不覆盖，但仍需设置 custom_filename_prefix
            naming_pattern = self.config.organize.naming_pattern
            name_prefix = selected_item.get_filename_prefix(file_name_pattern=naming_pattern)
            selected_item.set_custom_filename_prefix(name_prefix)
        else:
            # 其他情况正常设置目标路径
            self._set_target_path_for_item(selected_item, parent)
        # 设置进度回调函数
        self._set_progress_callback(silent, selected_item)
        # 找到合适的执行器
        operator = self._get_operator_for_item(selected_item)
        # 执行
        success = operator.execute(selected_item)
        if not success:
            # T017: M3U8 分片失败交互处理
            from ..core import M3U8Downloader

            if isinstance(operator, M3U8Downloader):
                segment_results = operator.get_last_segment_results()
                if segment_results:
                    success = self._handle_m3u8_segment_failure(operator, segment_results)
            if not success:
                self.logger.error(f"执行失败: {selected_item.get_description()}")
                return False

        # 注意：不在这里处理 Jellyfin 移动，改为在所有子项完成后再处理

        if not selected_item.has_children():
            # 如果没有子项，立即返回
            return success

        if not self.config.organize.auto_organize:
            self.logger.warning(f"选项 {selected_item.get_description()} 包含子项，但自动整理未启用，子项将不会被处理")
            return success

        # 如果包含子选项，则依次执行子选项
        for child in selected_item.get_children():
            # 根据配置判断是否需要执行子项
            if child.item_type == ItemType.META_DATA and not self.config.organize.create_nfo:
                self.logger.info(f"跳过NFO文件创建: {child.get_description()}")
                continue
            if child.item_type == ItemType.IMAGE and not self.config.organize.download_cover:
                self.logger.info(f"跳过图片下载: {child.get_description()}")
                continue
            # 递归执行子选项
            if not self._execute_operation(child, silent, selected_item):
                self.logger.error(f"子选项执行失败: {child.get_description()}")
                success = False

        # 所有子项完成后，如果是根项且下载成功，处理 Jellyfin 集成
        if is_root_item and success and selected_item.opt_type == OperationType.DOWNLOAD:
            if self.jellyfin_helper and self.jellyfin_helper.is_available():
                self._handle_jellyfin_post_download(selected_item)

        return success

    def _handle_m3u8_segment_failure(
        self,
        downloader: "M3U8Downloader",
        segment_results: list,
    ) -> bool:
        """处理 M3U8 分片部分失败: 交互式选择重试/跳过/取消.

        Args:
            downloader: M3U8下载器实例
            segment_results: SegmentResult 列表

        Returns:
            bool: 是否最终成功 (合并完成)
        """
        failed = [r for r in segment_results if not r.success]
        total = len(segment_results)
        failed_count = len(failed)

        # 全部失败 — 直接报告失败, 不提供跳过选项 (FR-009)
        if failed_count == total:
            click.echo(f"\n❌ 所有 {total} 个分片均下载失败, 无法继续", err=True)
            return False

        click.echo(f"\n⚠️  {failed_count}/{total} 个分片下载失败", err=True)
        for r in failed[:5]:
            click.echo(f"   - 分片 {r.index}: {r.error_message or '未知错误'}", err=True)
        if failed_count > 5:
            click.echo(f"   ... 及其他 {failed_count - 5} 个", err=True)

        # 检查是否有 --skip-failed 标志 (通过 click context)
        skip_failed = False
        try:
            ctx = click.get_current_context(silent=True)
            if ctx and ctx.obj:
                skip_failed = ctx.obj.get("skip_failed", False)
        except RuntimeError:
            pass

        # 检测 stdin 是否可用
        import sys

        is_interactive = sys.stdin.isatty() and not skip_failed

        if skip_failed:
            click.echo("ℹ️  --skip-failed 已启用, 自动跳过失败分片并合并", err=True)
            return downloader.merge_available_segments()

        if not is_interactive:
            click.echo("ℹ️  非交互式环境, 自动取消下载 (使用 --skip-failed 可自动跳过)", err=True)
            return False

        # 交互式选择
        while True:
            try:
                click.echo("\n请选择操作:", err=True)
                click.echo("  [R] 重试失败分片", err=True)
                click.echo("  [S] 跳过失败分片并合并", err=True)
                click.echo("  [C] 取消下载", err=True)
                choice = click.prompt("选择", type=click.Choice(["R", "S", "C", "r", "s", "c"]), err=True)
                choice = choice.upper()
            except (KeyboardInterrupt, EOFError):
                click.echo("\n已取消", err=True)
                return False

            if choice == "R":
                retry_success = downloader.retry_failed_segments()
                if retry_success:
                    # 所有分片现在都成功了, 走正常合并流程
                    return downloader.merge_available_segments()
                else:
                    # 仍有失败, 更新结果并重新询问
                    segment_results = downloader.get_last_segment_results() or []
                    failed = [r for r in segment_results if not r.success]
                    failed_count = len(failed)
                    if failed_count == 0:
                        return downloader.merge_available_segments()
                    click.echo(f"\n仍有 {failed_count}/{total} 个分片失败", err=True)
                    continue
            elif choice == "S":
                return downloader.merge_available_segments()
            else:  # C
                click.echo("已取消下载", err=True)
                return False

    def _execute_download(
        self, selected_item: OperationItem, silent: bool = False, parent: Optional[OperationItem] = None
    ) -> bool:
        """执行下载或处理操作（已废弃，请使用 _execute_operation）

        为了向后兼容保留此方法，实际调用 _execute_operation
        """
        return self._execute_operation(selected_item, silent, parent)

    def _set_progress_callback(self, silent: bool, selected_item: OperationItem) -> None:
        """
        获取进度回调函数

        Args:
            progress_callback: 可选的进度回调函数

        Returns:
            处理后的进度回调函数
        """
        # 只有当下载类型为STREAM或者VIDEO时才传递进度回调
        if selected_item.item_type in (ItemType.STREAM, ItemType.VIDEO):
            if selected_item.item_type == ItemType.STREAM:
                # M3U8: 使用分片级进度回调
                callback = create_segment_progress_callback() if not silent else create_silent_progress_callback()
            else:
                # HTTP: 使用字节级进度回调
                callback = create_console_progress_callback() if not silent else create_silent_progress_callback()
            selected_item.set_progress_callback(callback)

    def _set_target_path_for_item(self, item: OperationItem, parent_item: Optional[OperationItem]) -> None:
        """
        获取操作项的目标路径
        Args:
            item: 操作项
            parent_item: 父操作项（如果有的话）
        """
        # 如果没有父项
        if parent_item is None:
            target_path, name_prefix = self._get_target_path_for_item(item)
            item.set_target_path(target_path)
            item.set_custom_filename_prefix(name_prefix)  # 设置自定义文件名前缀
        else:
            # 如果有父项，则使用父项的目标路径作为基础
            parent_target_path = parent_item.get_target_path()
            if not parent_target_path:
                raise ValueError(f"父项 {parent_item.get_description()} 没有设置目标路径")
            # 沿用父项的文件名前缀
            custom_filename_prefix = parent_item.get_custom_filename_prefix()
            # 获取父项的目标文件夹
            target_folder = os.path.dirname(parent_target_path)
            target_path, _ = self._get_target_path_for_item(item, target_folder, custom_filename_prefix)
            item.set_target_path(target_path)

    def _get_target_path_for_item(
        self,
        item: OperationItem,
        target_folder: Optional[str] = None,
        custom_filename_prefix: Optional[str] = None,
    ) -> Tuple[str, str]:
        """
        获取操作项的目标路径
        Args:
            item: 操作项
            target_folder: 可选的目标文件夹，如果未指定则使用配置中的输出目录
            custom_filename_prefix: 可选的自定义文件名前缀，如果未指定则使用配置中的命名模式
        Returns:
            目标路径字符串
        """
        naming_pattern = self.config.organize.naming_pattern
        # 如果没有指定目标文件夹，则使用配置中的输出目录
        if not target_folder:
            output_dir = self.config.download.output_dir
            if custom_filename_prefix is not None:
                # 如果有自定义文件名前缀，则不使用自动整理
                target_folder = output_dir
            elif self.config.organize.auto_organize:
                folder_pattern = self.config.organize.folder_structure
                target_sub_folder = item.get_target_subfolder(
                    output_dir=output_dir, folder_name_pattern=folder_pattern
                )  # 获取子文件夹名称
                # 确保路径和文件名有效
                if target_sub_folder is None:
                    target_folder = output_dir  # 如果没有子文件夹，则使用输出目录
                else:
                    target_folder = os.path.join(output_dir, target_sub_folder)  # 拼接输出目录和子文件夹
            else:
                # 如果不整理则直接使用输出目录
                target_folder = output_dir
        # 生成目标文件名

        if custom_filename_prefix:
            name_prefix = custom_filename_prefix
        elif self.config.organize.auto_organize:
            name_prefix = item.get_filename_prefix(file_name_pattern=naming_pattern)  # 获取文件名
        else:
            name_prefix = item.get_filename_prefix()
        file_name_suffix = item.get_file_suffix()
        if name_prefix is None:
            raise ValueError("生成的文件名为None，无法继续。")

        if file_name_suffix:
            file_name = f"{name_prefix}{file_name_suffix}"
        else:
            file_name = f"{name_prefix}"

        target_path = os.path.join(target_folder, file_name)

        # 对于 MOVE 操作，检查源文件和目标文件是否相同
        if item.opt_type == OperationType.MOVE:
            source_path = item.get_source_path()
            if source_path:
                from pathlib import Path

                source_resolved = Path(source_path).resolve()
                target_resolved = Path(target_path).resolve()
                if source_resolved == target_resolved:
                    self.logger.info(f"文件已在目标位置，无需移动: {target_path}")
                    return (target_path, name_prefix)

        # 检查文件是否已存在
        if os.path.exists(target_path) and not self.config.download.overwrite_existing:
            raise FileExistsError(f"文件已存在: {target_path}. 请检查配置或选择覆盖选项。")
        # 确保目标目录存在
        os.makedirs(os.path.dirname(target_path), exist_ok=True)
        return (target_path, name_prefix)

    def download_from_url(
        self,
        url: str,
        silent: bool = False,
        auto_select: bool = False,
        file_name: Optional[str] = None,
    ) -> bool:
        """
        从URL下载内容
        Args:
            url: 要下载的URL
            silent: 是否静默模式（不显示进度）
            auto_select: 是否自动选择第一个下载选项
            file_name: 可选的文件名（如果需要覆盖默认名称）
        """

        try:
            click.echo(f"正在分析URL: {url}")

            # 注册中断处理器
            interrupt_handler = get_interrupt_handler()
            interrupt_handler.register()

            # 1. 提取下载选项
            items = self._extract_items(url)

            # 2. 选择下载选项
            if auto_select:
                selected_item = items[0]
                click.echo(f"自动选择: {selected_item.get_description()}")
            else:
                selected_item = self._select_download_item(items)

            # 如果提供了文件名，则覆盖操作项的名称
            if file_name:
                selected_item.set_custom_filename_prefix(file_name)

            # 3. 完成准备
            result = self._execute_operation(selected_item, silent)

            # 检查是否被中断
            if interrupt_handler.is_interrupted():
                click.echo("\n⚠️ 下载已中断, 已保存的缓存可用于断点续传", err=True)
                interrupt_handler.reset()
                return False

            return result

        except Exception as e:
            click.echo(f"下载失败: {e}")
            return False
        finally:
            get_interrupt_handler().reset()

    def execute_operation(
        self,
        operation_item: OperationItem,
        silent: bool = False,
    ) -> bool:
        """执行操作项（公开方法）

        Args:
            operation_item: 操作项（DOWNLOAD, SAVE_METADATA, MOVE 等）
            silent: 是否静默模式（不显示进度）

        Returns:
            是否成功

        说明:
            这是对外公开的接口，用于执行任意类型的操作项。
            内部会自动选择合适的执行器（HTTPDownloader, MetadataSaver, FileMover 等）
            并递归处理所有子项（元数据、图片等）。
        """
        try:
            # 注册中断处理器
            interrupt_handler = get_interrupt_handler()
            interrupt_handler.register()

            result = self._execute_operation(operation_item, silent=silent, parent=None)

            if interrupt_handler.is_interrupted():
                click.echo("\n⚠️ 下载已中断, 已保存的缓存可用于断点续传", err=True)
                interrupt_handler.reset()
                return False

            return result
        except Exception as e:
            self.logger.error(f"执行操作失败: {e}", exc_info=True)
            return False
        finally:
            get_interrupt_handler().reset()

    def batch_download(self, urls: List[str], slient: bool = True) -> List[Tuple[str, bool]]:
        """
        批量下载多个URL

        Args:
            urls: URL列表
            progress_callback: 进度回调函数
            auto_select: 是否自动选择第一个选项
              Returns:
            (URL, 成功状态) 的列表
        """
        results: List[Tuple[str, bool]] = []
        # TODO: 实现批量下载逻辑
        return results


def create_exe_manager(config: Config, plugin_manager: Optional[PluginManager] = None) -> ExecutionManager:
    """
    创建执行管理器实例的便利函数
    Args:
        config: 配置对象
        plugin_manager: 可选的插件管理器实例
    """
    return ExecutionManager(config=config, plugin_manager=plugin_manager)

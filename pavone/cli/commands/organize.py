"""
Organize command - 整理命令
"""

from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional

import click

from ...config.settings import get_config
from ...manager.execution import create_exe_manager
from ...manager.metadata_manager import get_metadata_manager
from ...manager.plugin_manager import get_plugin_manager
from ...manager.search_manager import get_search_manager
from ...utils.file_operation_builder import FileOperationBuilder
from ...utils.filename_parser import FilenameParser
from ...utils.format_utils import FormatUtils
from .utils import confirm_action, echo_error, echo_info, echo_success, echo_warning

# 支持的视频扩展名
VIDEO_EXTENSIONS = {
    ".mp4",
    ".mkv",
    ".avi",
    ".wmv",
    ".flv",
    ".mov",
    ".rmvb",
    ".m4v",
    ".mpg",
    ".mpeg",
    ".ts",
    ".webm",
    ".3gp",
}


@dataclass
class LocalVideoQuality:
    """本地视频文件质量信息"""

    path: str
    filename: str
    size: str
    size_bytes: int
    resolution: str
    height: int
    bitrate: str
    bitrate_raw: int
    codec: str
    duration: str


@click.command()
@click.argument("path", type=click.Path(exists=True))
@click.option("--keyword", "-k", type=str, help="手动指定搜索关键词（仅单文件时有效，跳过从文件名提取）")
@click.option("--pattern", "-p", type=str, help="文件名模板 (如: {code} - {title})")
@click.option("--structure", "-s", type=str, help="目录结构模板 (如: {studio}/{code})")
@click.option("--output-dir", "-o", type=click.Path(), help="输出目录")
@click.option("--conflict", "-c", type=click.Choice(["rename", "skip", "overwrite"]), help="文件冲突处理策略")
@click.option("--dry-run", is_flag=True, help="模拟运行，不实际移动文件")
@click.option("--recursive", "-r", is_flag=True, help="递归处理子目录")
@click.option("--auto", "-a", is_flag=True, help="自动模式，不提示确认")
@click.option("--no-nfo", is_flag=True, help="不创建 NFO 文件")
@click.option("--no-cover", is_flag=True, help="不下载封面图片")
@click.option("--jellyfin", "-j", is_flag=True, help="使用 Jellyfin 库文件夹作为目标目录")
def organize(
    path: str,
    keyword: Optional[str],
    pattern: Optional[str],
    structure: Optional[str],
    output_dir: Optional[str],
    conflict: Optional[str],
    dry_run: bool,
    recursive: bool,
    auto: bool,
    no_nfo: bool,
    no_cover: bool,
    jellyfin: bool,
):
    """整理指定路径下的视频文件

    自动识别视频文件中的番号，获取元数据，并整理文件到指定目录结构。

    示例：
        pavone organize /downloads --pattern "{code} - {title}" --structure "{studio}/{code}"
        pavone organize /downloads -r --dry-run  # 递归模拟运行
        pavone organize /downloads -o /videos --auto  # 自动模式
        pavone organize video.mp4 --keyword "SSIS-001"  # 手动指定搜索关键词
        pavone organize /downloads -j  # 整理到 Jellyfin 库文件夹
    """
    try:
        # 获取配置
        config = get_config()
        organize_config = config.organize

        # 应用命令行参数覆盖配置
        if pattern:
            organize_config.naming_pattern = pattern
        if structure:
            organize_config.folder_structure = structure
        if conflict:
            organize_config.on_conflict = conflict
        if no_nfo:
            organize_config.create_nfo = False
        if no_cover:
            organize_config.download_cover = False

        # 确定输出目录
        base_dir = output_dir or config.download.output_dir

        # 如果指定了 --jellyfin，从 Jellyfin 库选择目标文件夹
        if jellyfin:
            selected_dir = _select_jellyfin_library_folder(config)
            if not selected_dir:
                return 1
            base_dir = selected_dir

        echo_info(f"开始整理: {path}")
        echo_info(f"文件名模板: {organize_config.naming_pattern}")
        echo_info(f"目录结构模板: {organize_config.folder_structure}")
        echo_info(f"输出基础目录: {base_dir}")
        echo_info(f"冲突策略: {organize_config.on_conflict}")

        if dry_run:
            echo_warning("【模拟运行模式】不会实际移动文件")

        # 扫描视频文件
        echo_info("扫描视频文件...")
        video_files = _scan_video_files(path, recursive)

        if not video_files:
            echo_warning("未找到视频文件")
            return 0

        echo_success(f"找到 {len(video_files)} 个视频文件")

        # 如果指定了关键词但不是单个文件，给出警告
        if keyword and len(video_files) > 1:
            echo_warning("--keyword 选项仅在处理单个文件时有效，将忽略该选项")
            keyword = None

        # 创建管理器
        plugin_manager = get_plugin_manager()
        search_manager = get_search_manager(plugin_manager)
        metadata_manager = get_metadata_manager(plugin_manager)  # type: ignore
        exe_manager = create_exe_manager(config=config, plugin_manager=plugin_manager)

        # 创建文件操作构建器
        file_operation_builder = FileOperationBuilder()

        # 处理每个文件
        success_count = 0
        failed_count = 0
        skipped_count = 0

        for i, video_file in enumerate(video_files, 1):
            echo_info(f"\n[{i}/{len(video_files)}] 处理: {video_file.name}")

            try:
                # 1. 确定搜索关键词
                if keyword and len(video_files) == 1:
                    # 使用手动指定的关键词
                    search_keyword = keyword
                    echo_info(f"  使用指定关键词: {search_keyword}")
                else:
                    # 从文件名提取代码
                    hints = FilenameParser.extract_metadata_hints(str(video_file))
                    code = hints.get("code")

                    if not code:
                        echo_warning("  无法从文件名提取番号，跳过")
                        skipped_count += 1
                        continue

                    search_keyword = code
                    echo_info(f"  识别番号: {search_keyword}")

                # 2. 搜索获取 URL
                echo_info("  搜索元数据源...")
                search_results = search_manager.search(search_keyword)

                if not search_results:
                    echo_warning("  未找到搜索结果，跳过")
                    skipped_count += 1
                    continue

                # 使用第一个搜索结果
                search_result = search_results[0]
                source_name = getattr(search_result, "source", "unknown")
                echo_info(f"  找到: {search_result.title or search_result.code} ({source_name})")

                # 3. 从搜索结果获取完整元数据
                echo_info("  获取详细元数据...")
                metadata = metadata_manager.get_metadata_from_search_result(search_result)

                if not metadata:
                    echo_warning("  未能获取元数据，跳过")
                    skipped_count += 1
                    continue

                echo_success(f"  获取到元数据: {metadata.title or '无标题'}")

                # 4. 构建文件操作
                try:
                    operation = file_operation_builder.build_operation(
                        source_path=video_file, metadata=metadata, config=organize_config, base_dir=Path(base_dir)
                    )
                except ValueError as e:
                    echo_error(f"  构建操作失败: {e}")
                    failed_count += 1
                    continue

                if not operation:
                    echo_error("  构建操作失败")
                    failed_count += 1
                    continue

                target_path = operation.get_target_path()
                if not target_path:
                    echo_error("  无法确定目标路径")
                    failed_count += 1
                    continue
                echo_info(f"  目标路径: {target_path}")

                # 4.5 检查目标文件夹是否已有同番号视频
                target_path_obj = Path(target_path)
                target_dir = target_path_obj.parent
                existing_videos = _find_existing_videos(target_dir, exclude=video_file)

                if existing_videos:
                    echo_warning(f"  目标文件夹已存在 {len(existing_videos)} 个视频文件:")

                    source_quality = _probe_video_quality(video_file)
                    existing_qualities = [_probe_video_quality(v) for v in existing_videos]
                    _display_quality_comparison(source_quality, existing_qualities)

                    if auto:
                        echo_warning("  自动模式: 跳过已存在的番号")
                        skipped_count += 1
                        continue

                    action = _prompt_duplicate_action()

                    if action == "skip":
                        echo_warning("  跳过")
                        skipped_count += 1
                        continue
                    elif action == "extra":
                        # 移动到 extras 子文件夹（Jellyfin 支持的 extras 目录）
                        # 保留源文件原始文件名
                        extras_dir = target_dir / "extras"
                        new_target = extras_dir / video_file.name
                        operation.set_target_path(str(new_target))
                        # extras 不需要 NFO/封面等子操作
                        operation._children.clear()
                        echo_info(f"  将作为 Extra 移动到: {new_target}")
                    else:
                        # overwrite: 目标路径使用原始无后缀路径
                        original_target = target_dir / (target_path_obj.stem.split(" (")[0] + target_path_obj.suffix)
                        operation.set_target_path(str(original_target))

                        # 删除已有视频文件
                        for existing in existing_videos:
                            if not dry_run:
                                existing.unlink()
                                echo_info(f"  已删除旧文件: {existing.name}")
                            else:
                                echo_info(f"  [模拟] 将删除: {existing.name}")

                        # 询问是否重新生成元信息文件
                        if operation.has_children():
                            if not confirm_action("  目标已有元信息文件，是否重新生成 NFO/封面等？", default=False):
                                operation._children.clear()
                                echo_info("  保留已有元信息文件")

                # 5. 显示操作详情
                if operation.has_children():
                    echo_info("  额外操作:")
                    for child in operation.get_children():
                        echo_info(f"    - {child.get_description()}")

                # 6. 确认执行（非自动模式）
                if not auto and not dry_run and not existing_videos:
                    if not confirm_action("  是否执行整理？", default=True):
                        echo_warning("  跳过")
                        skipped_count += 1
                        continue

                # 7. 执行操作
                if dry_run:
                    echo_success(f"  [模拟] 将移动到: {target_path}")
                    success_count += 1
                else:
                    echo_info("  执行整理...")
                    success = exe_manager.execute_operation(operation)

                    if success:
                        echo_success("  整理完成")
                        success_count += 1
                    else:
                        echo_error("  整理失败")
                        failed_count += 1

            except Exception as e:
                echo_error(f"  处理失败: {e}")
                failed_count += 1
                continue

        # 显示汇总信息
        echo_info("\n" + "=" * 50)
        echo_info("整理完成！")
        echo_success(f"成功: {success_count}")
        if failed_count > 0:
            echo_error(f"失败: {failed_count}")
        if skipped_count > 0:
            echo_warning(f"跳过: {skipped_count}")
        echo_info(f"总计: {len(video_files)}")

        return 0 if failed_count == 0 else 1

    except Exception as e:
        echo_error(f"整理出错: {e}")
        import traceback

        traceback.print_exc()
        return 1


def _select_jellyfin_library_folder(config: object) -> Optional[str]:
    """连接 Jellyfin 并让用户选择库文件夹作为输出目录

    Returns:
        选择的文件夹路径，取消或失败返回 None
    """
    from ...jellyfin.client import JellyfinClientWrapper
    from ...jellyfin.library_manager import LibraryManager

    jellyfin_config = config.jellyfin  # type: ignore
    if not jellyfin_config.enabled or not jellyfin_config.server_url:
        echo_error("Jellyfin 未配置或未启用，请先运行: pavone jellyfin config")
        return None

    try:
        client = JellyfinClientWrapper(jellyfin_config)
        client.authenticate()
        lib_manager = LibraryManager(client)
        lib_manager.initialize()
        folders = lib_manager.get_library_folders()
    except Exception as e:
        echo_error(f"连接 Jellyfin 失败: {e}")
        return None

    valid_libraries = {name: paths for name, paths in folders.items() if paths}
    if not valid_libraries:
        echo_error("没有找到任何配置了文件夹路径的 Jellyfin 库")
        return None

    # 展示库列表
    echo_info("\n可用的 Jellyfin 库:")
    libraries_list = list(valid_libraries.items())
    for i, (lib_name, lib_folders) in enumerate(libraries_list, 1):
        echo_info(f"  {i}. {lib_name}")
        for f in lib_folders:
            echo_info(f"     📁 {f}")

    # 选择库
    from .utils import prompt_int

    try:
        lib_choice = prompt_int(f"请选择库 (1-{len(libraries_list)})", default=1)
    except click.Abort:
        echo_info("已取消")
        return None

    if lib_choice < 1 or lib_choice > len(libraries_list):
        echo_error("选择无效")
        return None

    selected_name, selected_folders = libraries_list[lib_choice - 1]

    # 如果库有多个文件夹，让用户选择
    if len(selected_folders) > 1:
        echo_info(f"\n库 '{selected_name}' 有多个文件夹:")
        for i, f in enumerate(selected_folders, 1):
            echo_info(f"  {i}. 📁 {f}")

        try:
            folder_choice = prompt_int(f"请选择文件夹 (1-{len(selected_folders)})", default=1)
        except click.Abort:
            echo_info("已取消")
            return None

        if folder_choice < 1 or folder_choice > len(selected_folders):
            echo_error("选择无效")
            return None

        target = selected_folders[folder_choice - 1]
    else:
        target = selected_folders[0]

    echo_success(f"已选择: {selected_name} → {target}")
    return target


def _scan_video_files(path: str, recursive: bool) -> List[Path]:
    """扫描视频文件

    Args:
        path: 扫描路径（文件或目录）
        recursive: 是否递归扫描子目录

    Returns:
        视频文件路径列表
    """
    path_obj = Path(path)
    video_files: List[Path] = []

    if path_obj.is_file():
        # 单个文件
        if path_obj.suffix.lower() in VIDEO_EXTENSIONS:
            video_files.append(path_obj)
    else:
        # 目录
        if recursive:
            for ext in VIDEO_EXTENSIONS:
                video_files.extend(path_obj.rglob(f"*{ext}"))
                video_files.extend(path_obj.rglob(f"*{ext.upper()}"))
        else:
            for ext in VIDEO_EXTENSIONS:
                video_files.extend(path_obj.glob(f"*{ext}"))
                video_files.extend(path_obj.glob(f"*{ext.upper()}"))

    # 排序并去重
    video_files = sorted(set(video_files))

    return video_files


def _find_existing_videos(target_dir: Path, exclude: Optional[Path] = None) -> List[Path]:
    """检查目标文件夹中是否已有视频文件

    Args:
        target_dir: 目标目录
        exclude: 排除的文件路径（避免把源文件自身当作重复）

    Returns:
        已存在的视频文件列表
    """
    if not target_dir.exists():
        return []

    existing: List[Path] = []
    exclude_resolved = exclude.resolve() if exclude else None

    for f in target_dir.iterdir():
        if f.is_file() and f.suffix.lower() in VIDEO_EXTENSIONS:
            if exclude_resolved and f.resolve() == exclude_resolved:
                continue
            existing.append(f)

    return sorted(existing)


def _probe_video_quality(file_path: Path) -> LocalVideoQuality:
    """探测本地视频文件质量信息

    优先使用 ffprobe 获取详细信息，不可用时回退到仅文件大小。

    Args:
        file_path: 视频文件路径

    Returns:
        LocalVideoQuality 对象
    """
    import json
    import shutil
    import subprocess

    size_bytes = file_path.stat().st_size

    # 尝试 ffprobe
    if shutil.which("ffprobe"):
        try:
            result = subprocess.run(
                [
                    "ffprobe",
                    "-v",
                    "quiet",
                    "-print_format",
                    "json",
                    "-show_streams",
                    "-show_format",
                    str(file_path),
                ],
                capture_output=True,
                text=True,
                encoding="utf-8",
                timeout=30,
            )
            if result.returncode == 0:
                data = json.loads(result.stdout)
                video_stream = next(
                    (s for s in data.get("streams", []) if s.get("codec_type") == "video"),
                    None,
                )
                fmt = data.get("format", {})

                if video_stream:
                    width = int(video_stream.get("width", 0))
                    height = int(video_stream.get("height", 0))
                    codec = video_stream.get("codec_name", "未知")
                    bitrate_raw = int(video_stream.get("bit_rate", 0) or fmt.get("bit_rate", 0) or 0)
                    duration_sec = float(fmt.get("duration", 0))

                    return LocalVideoQuality(
                        path=str(file_path),
                        filename=file_path.name,
                        size=FormatUtils.format_size(size_bytes),
                        size_bytes=size_bytes,
                        resolution=f"{width}x{height}" if width and height else "未知",
                        height=height,
                        bitrate=FormatUtils.format_bitrate(bitrate_raw) if bitrate_raw else "未知",
                        bitrate_raw=bitrate_raw,
                        codec=codec,
                        duration=f"{int(duration_sec // 60)} 分钟" if duration_sec else "未知",
                    )
        except Exception:
            pass

    # 回退：仅文件大小
    return LocalVideoQuality(
        path=str(file_path),
        filename=file_path.name,
        size=FormatUtils.format_size(size_bytes),
        size_bytes=size_bytes,
        resolution="未知 (需要 ffprobe)",
        height=0,
        bitrate="未知",
        bitrate_raw=0,
        codec="未知",
        duration="未知",
    )


def _display_quality_comparison(
    source: LocalVideoQuality,
    existing_list: List[LocalVideoQuality],
) -> None:
    """显示新文件与已有文件的质量对比

    Args:
        source: 新文件的质量信息
        existing_list: 已有文件的质量信息列表
    """
    click.echo()
    click.echo("  " + "─" * 56)

    # 新文件信息
    click.secho("  【新文件】", fg="cyan", bold=True)
    click.echo(f"    文件名:  {source.filename}")
    click.echo(f"    大小:    {source.size}")
    click.echo(f"    分辨率:  {source.resolution}")
    click.echo(f"    编码:    {source.codec}")
    click.echo(f"    码率:    {source.bitrate}")
    click.echo(f"    时长:    {source.duration}")

    click.echo("  " + "─" * 56)

    # 已有文件信息
    for i, existing in enumerate(existing_list):
        label = "【已有文件】" if len(existing_list) == 1 else f"【已有文件 {i + 1}】"
        click.secho(f"  {label}", fg="yellow", bold=True)
        click.echo(f"    文件名:  {existing.filename}")
        click.echo(f"    大小:    {existing.size}")
        click.echo(f"    分辨率:  {existing.resolution}")
        click.echo(f"    编码:    {existing.codec}")
        click.echo(f"    码率:    {existing.bitrate}")
        click.echo(f"    时长:    {existing.duration}")

    click.echo("  " + "─" * 56)

    # 质量建议
    best_existing_height = max(e.height for e in existing_list)
    if source.height > 0 and best_existing_height > 0:
        if source.height > best_existing_height:
            click.secho("  建议: 新文件质量更高", fg="green", bold=True)
        elif source.height < best_existing_height:
            click.secho("  建议: 已有文件质量更高", fg="red", bold=True)
        else:
            # 分辨率相同，比较文件大小（通常更大 = 更高码率）
            best_existing_size = max(e.size_bytes for e in existing_list)
            if source.size_bytes > best_existing_size * 1.1:
                click.secho("  建议: 分辨率相同，新文件码率可能更高", fg="green")
            elif source.size_bytes < best_existing_size * 0.9:
                click.secho("  建议: 分辨率相同，已有文件码率可能更高", fg="yellow")
            else:
                click.secho("  建议: 质量基本相同", fg="white")
    elif source.height == 0 and best_existing_height == 0:
        # 都无法获取分辨率，比较文件大小
        best_existing_size = max(e.size_bytes for e in existing_list)
        if source.size_bytes > best_existing_size:
            click.secho(f"  提示: 新文件更大 ({source.size} vs {FormatUtils.format_size(best_existing_size)})", fg="cyan")
        else:
            click.secho(f"  提示: 已有文件更大 ({FormatUtils.format_size(best_existing_size)} vs {source.size})", fg="cyan")

    click.echo()


def _prompt_duplicate_action() -> str:
    """提示用户选择同番号冲突的处理方式

    Returns:
        "skip" / "overwrite" / "extra"
    """
    click.echo("  请选择处理方式:")
    click.echo("    [S] 跳过 - 不处理此文件")
    click.echo("    [O] 覆盖 - 删除已有文件，移入新文件")
    click.echo("    [E] Extra - 作为 Jellyfin Extra 移入 extras/ 子文件夹")

    while True:
        choice = click.prompt("  请输入", type=str, default="S").strip().upper()
        if choice in ("S", "SKIP"):
            return "skip"
        elif choice in ("O", "OVERWRITE"):
            return "overwrite"
        elif choice in ("E", "EXTRA"):
            return "extra"
        else:
            click.echo("  无效输入，请输入 S / O / E")

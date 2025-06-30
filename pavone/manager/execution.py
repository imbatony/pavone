import os
from typing import List, Optional, Tuple

from ..config.logging_config import get_logger
from ..config.settings import Config
from ..core import DummyOperator, HTTPDownloader, M3U8Downloader, MetadataSaver, Operator
from ..models import ItemType, OperationItem, OperationType
from ..plugins.manager import PluginManager, get_plugin_manager
from .progress import create_console_progress_callback, create_silent_progress_callback


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
            print(f"找到1个下载选项: {items[0].get_description()}")
            return items[0]

        print(f"找到 {len(items)} 个下载选项:")
        for i, opt in enumerate(items, 1):
            print(f"  {i}. {opt.get_description()}")

        while True:
            try:
                choice = input(f"请选择下载选项 (1-{len(items)}, 0取消): ").strip()

                if choice == "0":
                    raise ValueError("用户取消了下载")

                choice_num = int(choice)
                if 1 <= choice_num <= len(items):
                    selected = items[choice_num - 1]
                    print(f"已选择: {selected.get_description()}")
                    return selected
                else:
                    print(f"请输入1到{len(items)}之间的数字")

            except ValueError as e:
                if "用户取消了下载" in str(e):
                    raise
                print("输入无效，请输入数字")
            except KeyboardInterrupt:
                raise ValueError("用户取消了下载")

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
        else:
            self.logger.warning(f"未找到合适的执行器，使用DummyOperator作为占位符: {item.get_description()}")
            return DummyOperator(self.config)

    def _execute_download(
        self, selected_item: OperationItem, silent: bool = False, parent: Optional[OperationItem] = None
    ) -> bool:
        """
        执行下载或处理操作

        Args:
            selected_item: 用户选择的选项
            silent: 是否静默模式（不显示进度）

        Returns:
            是否成功
        """

        success = True

        # 设置目标
        self._set_target_path_for_item(selected_item, parent)
        # 设置进度回调函数
        self._set_progress_callback(silent, selected_item)
        # 找到合适的执行器
        operator = self._get_operator_for_item(selected_item)
        # 执行
        success = operator.execute(selected_item)
        if not success:
            self.logger.error(f"执行失败: {selected_item.get_description()}")
            return False

        if not selected_item.has_children():
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
            if not self._execute_download(child, silent, selected_item):
                self.logger.error(f"子选项执行失败: {child.get_description()}")
                success = False
        return success

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
        self, item: OperationItem, target_folder: Optional[str] = None, custom_filename_prefix: Optional[str] = None
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
            if self.config.organize.auto_organize:
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

        # 检查文件是否已存在
        if os.path.exists(target_path) and not self.config.download.overwrite_existing:
            raise FileExistsError(f"文件已存在: {target_path}. 请检查配置或选择覆盖选项。")
        # 确保目标目录存在
        os.makedirs(os.path.dirname(target_path), exist_ok=True)
        return (target_path, name_prefix)

    def download_from_url(
        self, url: str, silent: bool = False, auto_select: bool = False, file_name: Optional[str] = None
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
            print(f"正在分析URL: {url}")

            # 1. 提取下载选项
            items = self._extract_items(url)

            # 2. 选择下载选项
            if auto_select:
                selected_item = items[0]
                print(f"自动选择: {selected_item.get_description()}")
            else:
                selected_item = self._select_download_item(items)

            # 如果提供了文件名，则覆盖操作项的名称
            if file_name:
                selected_item.set_custom_filename_prefix(file_name)

            # 3. 完成准备
            return self._execute_download(selected_item, silent)

        except Exception as e:
            print(f"下载失败: {e}")
            return False

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

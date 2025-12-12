"""
Jellyfin 下载集成助手

提供与下载流程集成的功能，包括重复检测、文件移动等
"""

import logging
import os
import shutil
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional

from ..config.configs import JellyfinConfig
from ..utils import FormatUtils
from .client import JellyfinClientWrapper
from .library_manager import LibraryManager
from ..models import OperationItem, ItemMetadata


@dataclass
class VideoQualityInfo:
    """视频质量信息"""
    path: str
    size: str
    resolution: str
    bitrate: str
    codec: str
    added_date: str
    runtime: str


@dataclass
class DuplicateCheckResult:
    """重复检查结果"""
    exists: bool
    item: Optional[object] = None
    quality_info: Optional[VideoQualityInfo] = None


class JellyfinDownloadHelper:
    """Jellyfin 下载集成助手"""

    def __init__(self, config: JellyfinConfig):
        """
        初始化助手

        Args:
            config: Jellyfin 配置对象
        """
        self.config = config
        self.logger = logging.getLogger(__name__)

        self.client: Optional[JellyfinClientWrapper] = None
        self.library_manager: Optional[LibraryManager] = None

        if config.enabled:
            try:
                self.client = JellyfinClientWrapper(config)
                self.client.authenticate()
                self.library_manager = LibraryManager(self.client)
                self.library_manager.initialize()
                self.logger.info("Jellyfin 下载助手初始化成功")
            except Exception as e:
                self.logger.warning(f"Jellyfin 下载助手初始化失败: {e}")
                self.client = None
                self.library_manager = None

    def is_available(self) -> bool:
        """
        检查 Jellyfin 集成是否可用

        Returns:
            可用返回 True
        """
        return self.client is not None and self.library_manager is not None

    def check_duplicate(self, video_title: str, video_code: Optional[str] = None) -> Optional[DuplicateCheckResult]:
        """
        检查 Jellyfin 中是否已有该视频

        Args:
            video_title: 视频标题
            video_code: 视频番号（可选）

        Returns:
            DuplicateCheckResult 对象，包含存在标志、项目和质量信息
            如果未找到则返回 None
        """
        if not self.is_available():
            return None

        try:
            # 优先按视频番号通过 API 搜索（更快）
            item = None
            search_key = video_code or video_title
            
            if not search_key:
                self.logger.warning("没有提供搜索关键词")
                return None
            
            self.logger.info(f"搜索: {search_key}")
            
            # 直接使用 API 搜索
            if self.client is None:
                return None
            items = self.client.search_items(search_key, limit=10)
            
            if not items:
                self.logger.info(f"未在 Jellyfin 中找到: {search_key}")
                return None
            
            # 如果提供了视频番号，优先查找完全匹配或包含番号的项
            if video_code:
                for candidate in items:
                    candidate_name = candidate.name.upper()
                    code_upper = video_code.upper()
                    if code_upper in candidate_name or candidate_name.startswith(code_upper):
                        item = candidate
                        self.logger.info(f"按番号精确匹配: {item.name}")
                        break
                
                # 如果番号没有精确匹配，使用第一个结果
                if not item:
                    item = items[0]
                    self.logger.info(f"按番号模糊匹配: {item.name}")
            else:
                # 没有番号时，使用第一个搜索结果
                item = items[0]
                self.logger.info(f"搜索匹配: {item.name}")

            # 获取完整的项信息以获得更详细的元数据
            try:
                if self.client is None:
                    return DuplicateCheckResult(exists=True, item=item)
                item = self.client.get_item(item.id)
            except Exception as e:
                self.logger.debug(f"获取完整项信息失败，使用基本信息: {e}")

            # 提取质量信息
            quality_info = self._extract_quality_info(item)

            self.logger.info(f"在 Jellyfin 中找到重复项: {item.name}")

            return DuplicateCheckResult(
                exists=True,
                item=item,
                quality_info=quality_info
            )

        except Exception as e:
            self.logger.warning(f"检查重复时出错: {e}")
            import traceback
            self.logger.debug(traceback.format_exc())
            return None

    def _extract_quality_info(self, item) -> VideoQualityInfo:
        """
        从项中提取质量信息

        Args:
            item: JellyfinItem 对象

        Returns:
            VideoQualityInfo 对象
        """
        metadata = ItemMetadata(item.metadata or {})

        # 提取视频信息
        video_stream = None
        for stream in metadata.video_streams:
            video_stream = stream
            break

        width = video_stream.get("Width") if video_stream else None
        height = video_stream.get("Height") if video_stream else None
        resolution = f"{width}x{height}" if width and height else "未知"
        
        bitrate = video_stream.get("BitRate") if video_stream else metadata.video_bitrate or 0
        codec = video_stream.get("Codec") if video_stream else metadata.video_codec or "未知"
        
        # 获取文件大小（字节）
        file_size = 0
        if item.path:
            try:
                import os
                if os.path.exists(item.path):
                    file_size = os.path.getsize(item.path)
            except Exception:
                pass

        return VideoQualityInfo(
            path=item.path or "未知",
            size=FormatUtils.format_size(file_size),
            resolution=resolution,
            bitrate=FormatUtils.format_bitrate(bitrate) if bitrate else "未知",
            codec=codec if codec else "未知",
            added_date=metadata.added_date or "未知",
            runtime=f"{metadata.runtime_minutes} 分钟"
        )

    def display_existing_video_quality(self, quality_info: VideoQualityInfo) -> None:
        """
        显示已有视频的质量信息

        Args:
            quality_info: VideoQualityInfo 对象
        """
        print("\n视频质量信息:")
        print("-" * 60)
        print(f"路径: {quality_info.path}")
        print(f"大小: {quality_info.size}")
        print(f"分辨率: {quality_info.resolution}")
        print(f"比特率: {quality_info.bitrate}")
        print(f"编码: {quality_info.codec}")
        print(f"时长: {quality_info.runtime}")
        print(f"添加时间: {quality_info.added_date}")

    def get_library_folders(self) -> Dict[str, List[str]]:
        """
        获取所有库及其对应的本地文件夹

        Returns:
            {库名: 文件夹路径列表} 的字典
        """
        if not self.is_available():
            # 尝试重新初始化连接
            self.logger.warning("Jellyfin 助手不可用，尝试重新初始化...")
            try:
                self.client = JellyfinClientWrapper(self.config)
                self.client.authenticate()
                self.library_manager = LibraryManager(self.client)
                self.library_manager.initialize()
                self.logger.info("Jellyfin 重新初始化成功")
            except Exception as e:
                self.logger.error(f"Jellyfin 重新初始化失败: {e}")
                return {}

        try:
            if self.library_manager is None:
                return {}
            folders = self.library_manager.get_library_folders()
            self.logger.info(f"成功获取 {len(folders)} 个库的文件夹信息")
            return folders
        except Exception as e:
            self.logger.error(f"获取库文件夹失败: {e}", exc_info=True)
            return {}

    def move_to_library(
        self,
        source_path: str,
        destination_folder: str,
    ) -> bool:
        """
        将下载的文件移动到 Jellyfin 库文件夹

        Args:
            source_path: 源文件/文件夹路径
            destination_folder: 目标库文件夹路径

        Returns:
            成功返回 True
        """
        try:
            source = Path(source_path)
            dest = Path(destination_folder)

            if not source.exists():
                self.logger.error(f"源路径不存在: {source}")
                return False

            if not dest.exists():
                self.logger.error(f"目标路径不存在: {dest}")
                return False

            if not dest.is_dir():
                self.logger.error(f"目标路径不是文件夹: {dest}")
                return False

            # 检查权限
            if not os.access(dest, os.W_OK):
                self.logger.error(f"无写权限: {dest}")
                return False

            self.logger.info(f"移动文件: {source} -> {dest}")

            if source.is_file():
                # 移动单个文件
                dest_file = dest / source.name
                shutil.move(str(source), str(dest_file))
                self.logger.info(f"文件移动成功: {dest_file}")
            elif source.is_dir():
                # 移动整个文件夹
                dest_folder = dest / source.name
                shutil.move(str(source), str(dest_folder))
                self.logger.info(f"文件夹移动成功: {dest_folder}")

            return True

        except Exception as e:
            self.logger.error(f"文件移动失败: {e}")
            return False

    def refresh_library(self, library_name: str) -> bool:
        """
        增量刷新 Jellyfin 库的元数据
        
        仅扫描库目录中的新增或修改文件，不进行全量扫描

        Args:
            library_name: 库名称

        Returns:
            成功返回 True
        """
        if not self.is_available() or self.client is None:
            return False

        try:
            libraries = self.client.get_libraries()
            target_lib = None

            for lib in libraries:
                if lib.name == library_name:
                    target_lib = lib
                    break

            if not target_lib:
                self.logger.warning(f"未找到库: {library_name}")
                return False

            self.logger.info(f"增量刷新库元数据: {library_name}")
            if self.library_manager is None:
                return False
            self.library_manager.refresh_library_metadata(target_lib.id)
            return True

        except Exception as e:
            self.logger.error(f"刷新库元数据失败: {e}")
            return False

    def __repr__(self) -> str:
        status = "可用" if self.is_available() else "不可用"
        return f"JellyfinDownloadHelper(status={status})"

"""
配置验证器
"""

from pathlib import Path
from .configs import Config


class ConfigValidator:
    """配置验证器"""
    
    def __init__(self, config_dir: Path):
        self.config_dir = config_dir
    
    def validate_and_fix_config(self, config: Config) -> bool:
        """验证并修复配置"""
        try:
            self._validate_download_config(config)
            self._validate_search_config(config)
            self._validate_organize_config(config)
            self._validate_logging_config(config)
            self._validate_plugin_config(config)        
            return True
            
        except Exception as e:
            print(f"配置验证失败: {e}")
            return False
    
    def _validate_download_config(self, config: Config):
        """验证下载配置"""
        # 验证下载目录
        output_dir = Path(config.download.output_dir)
        if not output_dir.is_absolute():
            # 如果是相对路径，转换为基于配置目录的绝对路径
            config.download.output_dir = str(self.config_dir / "downloads")
        
        # 验证并发下载数
        if config.download.max_concurrent_downloads <= 0:
            config.download.max_concurrent_downloads = 3
          # 验证重试次数
        if config.download.retry_times < 0:
            config.download.retry_times = 3
        
        # 验证重试间隔
        if config.download.retry_interval <= 0:
            config.download.retry_interval = 3000
        
        # 验证超时时间
        if config.download.timeout <= 0:
            config.download.timeout = 30

        # 验证缓存目录
        if config.download.cache_dir:
            cache_dir = Path(config.download.cache_dir)
            if not cache_dir.is_absolute():
                # 如果是相对路径，转换为基于配置目录的绝对路径
                config.download.cache_dir = str(self.config_dir / "cache")
            if not cache_dir.exists():
                cache_dir.mkdir(parents=True, exist_ok=True)
        else:
            # 如果没有设置缓存目录，使用默认路径
            config.download.cache_dir = str(self.config_dir / "cache")

        # 验证请求头
        if not isinstance(config.download.headers, dict):
            config.download.headers = {"User-Agent": "Pavone/1.0"}
        
        # 验证是否覆盖已存在的文件
        if not isinstance(config.download.overwrite_existing, bool):
            config.download.overwrite_existing = False
    
    def _validate_search_config(self, config: Config):
        """验证搜索配置"""
        # 验证搜索结果数
        if config.search.max_results_per_site <= 0:
            config.search.max_results_per_site = 20
        
        # 验证启用的网站列表
        if not config.search.enabled_sites:
            config.search.enabled_sites = ["javbus", "javlibrary", "pornhub"]
    
    def _validate_organize_config(self, config: Config):
        """验证整理配置"""
        # 验证自动整理设置
        if not isinstance(config.organize.auto_organize, bool):
            config.organize.auto_organize = True
        # 验证文件夹结构
        if not config.organize.folder_structure:
            config.organize.folder_structure = "{code}"
        # 验证命名模式
        if not config.organize.naming_pattern:
            config.organize.naming_pattern = "{code}"

    
    def _validate_logging_config(self, config: Config):
        """验证日志配置"""
        # 验证日志级别
        valid_log_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if config.logging.level.upper() not in valid_log_levels:
            config.logging.level = "INFO"
        
        # 验证日志文件大小
        if config.logging.max_file_size <= 0:
            config.logging.max_file_size = 10 * 1024 * 1024  # 10MB
        
        # 验证备份文件数
        if config.logging.backup_count < 0:
            config.logging.backup_count = 5
        
        # 验证日志文件路径
        log_path = Path(config.logging.file_path)
        if not log_path.is_absolute():
            config.logging.file_path = str(self.config_dir / "logs" / "pavone.log")
    
    def _validate_plugin_config(self, config: Config):
        """验证插件配置"""
        # 验证插件目录
        plugin_dir = Path(config.plugin.plugin_dir)
        if not plugin_dir.is_absolute():
            config.plugin.plugin_dir = str(self.config_dir.parent / "pavone" / "plugins")
        
        # 验证插件配置目录
        plugin_config_dir = Path(config.plugin.plugin_config_dir)
        if not plugin_config_dir.is_absolute():
            config.plugin.plugin_config_dir = str(self.config_dir / "plugins_config")
        
        # 确保禁用插件列表是列表类型
        if not isinstance(config.plugin.disabled_plugins, list):
            config.plugin.disabled_plugins = []
        
        # 验证插件加载超时时间
        if config.plugin.load_timeout <= 0:
            config.plugin.load_timeout = 30
        
        # 确保插件优先级设置是字典类型
        if not isinstance(config.plugin.plugin_priorities, dict):
            config.plugin.plugin_priorities = {}

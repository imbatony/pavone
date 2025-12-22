"""
配置管理器
"""

import json
from dataclasses import asdict
from pathlib import Path
from typing import Optional

from .configs import (
    Config,
    DownloadConfig,
    JellyfinConfig,
    OrganizeConfig,
    PluginConfig,
    ProxyConfig,
    SearchConfig,
)
from .logging_config import LoggingConfig, get_log_manager, init_log_manager
from .validator import ConfigValidator


class ConfigManager:
    """配置管理器"""

    def __init__(self, config_dir: Optional[str] = None):
        if config_dir is None:
            self.config_dir = Path.home() / ".pavone"
        else:
            self.config_dir = Path(config_dir)

        self.config_dir.mkdir(exist_ok=True)
        self.config_file = self.config_dir / "config.json"
        self.config = Config()
        self.validator = ConfigValidator(self.config_dir)

        self.load_config()
        # 初始化日志管理器
        self._init_logging()

    def _init_logging(self):
        """初始化日志系统"""
        init_log_manager(self.config.logging)

    def load_config(self):
        """加载配置"""
        if self.config_file.exists():
            try:
                with open(self.config_file, "r", encoding="utf-8") as f:
                    data = json.load(f)

                # 更新配置
                self._load_config_data(data)

            except Exception as e:
                print(f"ERROR: 加载配置失败: {e}")
                # 使用默认配置
                self.config = Config()

        # 验证并修复配置
        if not self.validator.validate_and_fix_config(self.config):
            print("WARNING: 配置验证失败，使用默认配置")
            self.config = Config()
            self.save_config()

    def _load_config_data(self, data: dict):
        """从字典数据加载配置"""
        if "download" in data:
            self.config.download = DownloadConfig(**data["download"])
        if "organize" in data:
            self.config.organize = OrganizeConfig(**data["organize"])
        if "search" in data:
            self.config.search = SearchConfig(**data["search"])
        if "proxy" in data:
            self.config.proxy = ProxyConfig(**data["proxy"])
        if "logging" in data:
            self.config.logging = LoggingConfig(**data["logging"])
        if "plugin" in data:
            self.config.plugin = PluginConfig(**data["plugin"])
        if "jellyfin" in data:
            self.config.jellyfin = JellyfinConfig(**data["jellyfin"])

    def save_config(self):
        """保存配置"""
        try:
            config_dict = {
                "download": asdict(self.config.download),
                "organize": asdict(self.config.organize),
                "search": asdict(self.config.search),
                "proxy": asdict(self.config.proxy),
                "logging": asdict(self.config.logging),
                "plugin": asdict(self.config.plugin),
                "jellyfin": asdict(self.config.jellyfin),
            }

            with open(self.config_file, "w", encoding="utf-8") as f:
                json.dump(config_dict, f, indent=2, ensure_ascii=False)

        except Exception as e:
            print(f"ERROR: 保存配置失败: {e}")

    def get_config(self) -> Config:
        """获取配置"""
        return self.config

    def update_config(self, **kwargs):
        """更新配置"""
        for key, value in kwargs.items():
            if hasattr(self.config, key):
                setattr(self.config, key, value)

        self.save_config()

    def reset_config(self):
        """重置配置为默认值"""
        self.config = Config()
        self.save_config()

    def get_logger(self, name: str):
        """获取日志器"""
        return get_log_manager().get_logger(name)

    # 日志配置管理方法
    def update_logging_config(self, **kwargs):
        """更新日志配置"""
        for key, value in kwargs.items():
            if hasattr(self.config.logging, key):
                setattr(self.config.logging, key, value)

        # 更新日志管理器配置
        get_log_manager().update_config(self.config.logging)
        self.save_config()

    def set_log_level(self, level: str):
        """设置日志级别"""
        self.config.logging.level = level
        get_log_manager().set_level(level)
        self.save_config()

    def enable_console_logging(self):
        """启用控制台日志"""
        self.config.logging.console_enabled = True
        get_log_manager().enable_console_logging()
        self.save_config()

    def disable_console_logging(self):
        """禁用控制台日志"""
        self.config.logging.console_enabled = False
        get_log_manager().disable_console_logging()
        self.save_config()

    def enable_file_logging(self):
        """启用文件日志"""
        self.config.logging.file_enabled = True
        get_log_manager().enable_file_logging()
        self.save_config()

    def disable_file_logging(self):
        """禁用文件日志"""
        self.config.logging.file_enabled = False
        get_log_manager().disable_file_logging()
        self.save_config()

    # 插件配置管理方法
    def disable_plugin(self, plugin_name: str):
        """禁用指定插件"""
        if plugin_name not in self.config.plugin.disabled_plugins:
            self.config.plugin.disabled_plugins.append(plugin_name)
            self.save_config()

    def enable_plugin(self, plugin_name: str):
        """启用指定插件"""
        if plugin_name in self.config.plugin.disabled_plugins:
            self.config.plugin.disabled_plugins.remove(plugin_name)
            self.save_config()

    def is_plugin_disabled(self, plugin_name: str) -> bool:
        """检查插件是否被禁用"""
        return plugin_name in self.config.plugin.disabled_plugins

    def set_plugin_priority(self, plugin_name: str, priority: int):
        """设置插件优先级"""
        self.config.plugin.plugin_priorities[plugin_name] = priority
        self.save_config()

    def get_plugin_priority(self, plugin_name: str, default: int = 50) -> int:
        """获取插件优先级"""
        return self.config.plugin.plugin_priorities.get(plugin_name, default)

    def get_plugin_dir(self) -> Path:
        """获取插件目录路径"""
        return Path(self.config.plugin.plugin_dir)

    def get_plugin_config_dir(self) -> Path:
        """获取插件配置目录路径"""
        return Path(self.config.plugin.plugin_config_dir)

    def ensure_plugin_dirs(self):
        """确保插件相关目录存在"""
        plugin_dir = self.get_plugin_dir()
        plugin_config_dir = self.get_plugin_config_dir()

        plugin_dir.mkdir(parents=True, exist_ok=True)
        plugin_config_dir.mkdir(parents=True, exist_ok=True)

    def update_plugin_config(self, **kwargs):
        """更新插件配置"""
        for key, value in kwargs.items():
            if hasattr(self.config.plugin, key):
                setattr(self.config.plugin, key, value)
        self.save_config()

    def validate_and_fix_config(self) -> bool:
        """验证并修复配置（兼容性方法）"""
        return self.validator.validate_and_fix_config(self.config)

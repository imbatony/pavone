"""
日志使用示例
演示如何在pavone项目中使用日志系统
"""

from pavone.config.settings import config_manager
from pavone.config.logging_config import get_logger

def main():
    """主函数演示日志使用"""
    
    # 获取当前配置
    config = config_manager.get_config()
    print(f"当前日志级别: {config.logging.level}")
    print(f"日志文件路径: {config.logging.file_path}")
    print(f"控制台日志启用: {config.logging.console_enabled}")
    print(f"文件日志启用: {config.logging.file_enabled}")
    
    # 获取不同模块的日志器
    main_logger = get_logger("pavone.main")
    downloader_logger = get_logger("pavone.downloader")
    extractor_logger = get_logger("pavone.extractor")
    
    # 演示不同级别的日志
    main_logger.debug("这是一条调试信息")
    main_logger.info("应用程序启动")
    main_logger.warning("这是一条警告信息")
    
    downloader_logger.info("开始下载文件")
    downloader_logger.error("下载失败，正在重试")
    
    extractor_logger.info("开始解析页面")
    extractor_logger.warning("页面解析可能不完整")
    
    # 动态修改日志配置
    print("\n--- 修改日志配置 ---")
    
    # 修改日志级别为DEBUG
    config_manager.set_log_level("DEBUG")
    main_logger.debug("现在可以看到调试信息了")
    
    # 禁用控制台日志
    print("禁用控制台日志...")
    config_manager.disable_console_logging()
    main_logger.info("这条信息只会写入文件")
    
    # 重新启用控制台日志
    print("重新启用控制台日志...")
    config_manager.enable_console_logging()
    main_logger.info("控制台日志已恢复")
    
    # 修改日志配置
    config_manager.update_logging_config(
        level="WARNING",
        max_file_size=20 * 1024 * 1024,  # 20MB
        backup_count=10
    )
    
    main_logger.info("这条INFO信息不会显示，因为级别改为WARNING了")
    main_logger.warning("这条警告信息会显示")
    
    print("\n--- 配置管理演示完成 ---")


if __name__ == "__main__":
    main()

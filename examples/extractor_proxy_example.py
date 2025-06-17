"""
提取器代理集成示例

演示如何在提取器子类中使用统一的网页获取方法
"""

from typing import List
from pavone.plugins.extractors.base import ExtractorPlugin
from pavone.core.downloader.options import DownloadOpt


class ExampleExtractor(ExtractorPlugin):
    """示例提取器，展示如何使用基类的代理功能"""
    
    def __init__(self):
        super().__init__()
        self.name = "ExampleExtractor"
        self.version = "1.0.0"
        self.description = "演示代理功能的示例提取器"
        self.priority = 40
    
    def initialize(self):
        """初始化插件"""
        print(f"[{self.name}] 初始化示例提取器")
        return True
    
    def cleanup(self):
        """清理插件资源"""
        print(f"[{self.name}] 清理示例提取器")
    
    def execute(self, *args, **kwargs):
        """执行插件功能"""
        if args and isinstance(args[0], str):
            return self.extract(args[0])
        return []
    
    def can_handle(self, url: str) -> bool:
        """检查是否能处理该URL"""
        return "example.com" in url
    
    def extract(self, url: str) -> List[DownloadOpt]:
        """从URL提取下载选项"""
        try:
            # 使用基类的统一网页获取方法
            # 自动处理代理配置、SSL验证和默认请求头
            response = self.fetch_webpage(url)
            html_content = response.text
            
            # 解析HTML内容...
            # (这里只是示例，实际实现需要根据网站结构来解析)
            
            download_options = []
            # 创建下载选项...
            
            return download_options
            
        except Exception as e:
            print(f"提取失败: {e}")
            return []
    
    def extract_with_custom_headers(self, url: str) -> List[DownloadOpt]:
        """展示如何使用自定义请求头"""
        try:
            # 使用自定义请求头
            custom_headers = {
                'User-Agent': 'CustomBot/1.0',
                'Referer': 'https://example.com',
                'Authorization': 'Bearer token123'
            }
            
            # 调用基类方法，传入自定义头部
            response = self.fetch_webpage(
                url, 
                headers=custom_headers,
                timeout=60,  # 自定义超时时间
                verify_ssl=True  # 如果需要验证SSL证书
            )
            
            html_content = response.text
            # 处理响应...
            
            return []
            
        except Exception as e:
            print(f"自定义头部提取失败: {e}")
            return []


# 使用示例
if __name__ == "__main__":
    extractor = ExampleExtractor()
    
    # 基本用法 - 自动使用全局代理配置
    options1 = extractor.extract("https://example.com/video1")
    
    # 高级用法 - 使用自定义请求头
    options2 = extractor.extract_with_custom_headers("https://example.com/video2")
    
    print("示例完成！")

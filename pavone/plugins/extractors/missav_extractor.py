"""
MissAV视频提取器插件

支持从 missav.ai 和 missav.com 网站提取视频下载链接。
该提取器能够解析JavaScript混淆代码来获取真实的视频URL。
"""

import re
import json
from typing import List, Dict, Any
from urllib.parse import urlparse

from ...core.downloader.options import DownloadOpt, LinkType
from .base import ExtractorPlugin


class MissAVExtractor(ExtractorPlugin):
    """MissAV视频提取器"""
    
    def __init__(self):
        """初始化MissAV提取器"""
        super().__init__()
        self.name = "MissAVExtractor"
        self.version = "1.0.0"
        self.description = "提取 missav.ai 和 missav.com 的视频下载链接"
        self.priority = 30
        
        # 支持的域名
        self.supported_domains = [
            'missav.ai',
            'www.missav.ai', 
            'missav.com',
            'www.missav.com'
        ]
    
    def initialize(self):
        """初始化插件"""
        print(f"[{self.name}] 初始化 MissAV 视频提取器")
        return True
    
    def can_handle(self, url: str) -> bool:
        """检查是否能处理给定的URL"""
        try:
            parsed_url = urlparse(url)
            return any(parsed_url.netloc.lower() == domain.lower() 
                      for domain in self.supported_domains)
        except Exception:
            return False
    
    def extract(self, url: str) -> List[DownloadOpt]:
        """从 MissAV 页面提取视频下载选项"""
        try:
            # 使用基类的统一网页获取方法，自动处理代理和SSL
            response = self.fetch_webpage(url, timeout=30, verify_ssl=False)
            html_content = response.text
            
            # 定义默认的User-Agent，用于后续的下载请求
            default_user_agent = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
            
            download_options = []
            
            # 提取视频标题
            title_match = re.search(r'<title[^>]*>([^<]+)</title>', html_content, re.IGNORECASE)
            video_title = "Unknown"
            if title_match:
                video_title = title_match.group(1).strip()
                # 清理标题，移除网站名称
                video_title = re.sub(r'\s*-\s*MissAV.*$', '', video_title)
                video_title = self._sanitize_filename(video_title)
            
            # 主要方法：解析JavaScript混淆代码中的视频链接
            video_urls = self._extract_obfuscated_urls(html_content)
            
            if video_urls:                # 添加M3U8播放列表链接（最高优先级）
                if 'source' in video_urls:
                    download_opt = DownloadOpt(
                        url=video_urls['source'],
                        filename=f"{video_title}.mp4",
                        custom_headers={
                            "User-Agent": default_user_agent,
                            "Referer": url,
                            "Accept": "application/vnd.apple.mpegurl,application/x-mpegurl,video/*;q=0.9,*/*;q=0.8"
                        },
                        link_type=LinkType.STREAM,
                        display_name=f"M3U8播放列表 - {video_title}",
                        quality="自适应"
                    )
                    download_options.append(download_opt)
                # 添加720p视频链接
                if 'source1280' in video_urls:
                    download_opt = DownloadOpt(
                        url=video_urls['source1280'],
                        filename=f"{video_title}_720p.mp4",
                        custom_headers={
                            "User-Agent": default_user_agent,
                            "Referer": url,
                            "Accept": "application/vnd.apple.mpegurl,application/x-mpegurl,video/*;q=0.9,*/*;q=0.8"
                        },
                        link_type=LinkType.STREAM,
                        display_name=f"720p M3U8 - {video_title}",
                        quality="720p"
                    )
                    download_options.append(download_opt)                # 添加480p视频链接
                if 'source842' in video_urls:
                    download_opt = DownloadOpt(
                        url=video_urls['source842'],
                        filename=f"{video_title}_480p.mp4",
                        custom_headers={
                            "User-Agent": default_user_agent,
                            "Referer": url,
                            "Accept": "application/vnd.apple.mpegurl,application/x-mpegurl,video/*;q=0.9,*/*;q=0.8"
                        },
                        link_type=LinkType.STREAM,
                        display_name=f"480p M3U8 - {video_title}",
                        quality="480p"
                    )
                    download_options.append(download_opt)
            
            return download_options
            
        except ImportError:
            print("MissAV提取器需要 requests 库支持")
            return []
        except Exception as e:
            print(f"提取视频链接时出错: {e}")
            return []
    
    def _extract_obfuscated_urls(self, html_content: str) -> Dict[str, str]:
        """
        从JavaScript混淆代码中提取视频URL
        
        Args:
            html_content: HTML页面内容
            
        Returns:
            包含video URLs的字典        """
        try:            # 查找JavaScript混淆代码
            # 直接匹配参数部分
            eval_pattern = r"'([^']*f=.*?)',\s*(\d+),\s*(\d+),\s*'([^']+)'\.split\('\|'\)"
            
            match = re.search(eval_pattern, html_content)
            if not match:
                return {}
            
            encoded_string = match.group(1)
            base = int(match.group(2))
            count = int(match.group(3))
            keywords = match.group(4).split('|')
            
            # 解码混淆字符串
            decoded_js = self._decode_obfuscated_string(encoded_string, keywords)
            
            # 提取视频URL变量
            video_urls = {}
            
            # 查找各种source变量的定义
            patterns = {
                'source': r"([a-z]+)\s*=\s*'([^']+)'",
            }
            
            # 提取所有变量
            var_matches = re.findall(r"([a-z]+)\s*=\s*'([^']+)'", decoded_js)
            for var_name, url in var_matches:
                video_urls[var_name] = url
            
            # 如果没有找到完整的URL，尝试手动构建
            if not video_urls:
                video_urls = self._manual_decode_urls(encoded_string, keywords)
            
            return video_urls
            
        except Exception as e:
            print(f"解析混淆JavaScript时出错: {e}")
            return {}
    
    def _decode_obfuscated_string(self, encoded_string: str, keywords: list) -> str:
        """
        解码JavaScript混淆字符串
        
        Args:
            encoded_string: 编码后的字符串
            keywords: 关键词列表
            
        Returns:
            解码后的字符串
        """
        result = encoded_string
        
        # 基于JavaScript的36进制解码算法
        # 0-9 对应 keywords[0]-keywords[9]
        # a-z 对应 keywords[10]-keywords[35]
        
        # 先创建映射字典避免重复替换问题
        mapping = {}
        
        # 数字 0-9
        for i in range(min(10, len(keywords))):
            if keywords[i]:
                mapping[str(i)] = keywords[i]
        
        # 字母 a-z (对应10-35)
        for i in range(26):  # a-z
            idx = 10 + i
            if idx < len(keywords) and keywords[idx]:
                letter = chr(ord('a') + i)
                mapping[letter] = keywords[idx]
        
        # 按长度排序，先替换长的，避免子字符串问题
        for char in sorted(mapping.keys(), key=len, reverse=True):
            result = result.replace(char, mapping[char])
        
        return result
    
    def _manual_decode_urls(self, encoded_string: str, keywords: list) -> Dict[str, str]:
        """
        手动解码视频URL（当自动解码失败时）
        
        Args:
            encoded_string: 编码后的字符串
            keywords: 关键词列表
            
        Returns:
            包含video URLs的字典
        """
        try:
            # 基于已知的MissAV URL结构手动构建
            # 从关键词中查找UUID和域名
            uuid_parts = []
            for keyword in keywords:
                if re.match(r'^[0-9a-f]+$', keyword) and len(keyword) >= 4:
                    uuid_parts.append(keyword)
            
            # 构建UUID
            if len(uuid_parts) >= 5:
                # 典型格式：b8e4c00d-0a85-4dc5-badd-024a7765d391
                uuid = f"{uuid_parts[0]}-{uuid_parts[1]}-{uuid_parts[2]}-{uuid_parts[3]}-{uuid_parts[4]}"
                  # 查找域名
                domain = None
                for keyword in keywords:
                    if 'surrit' in keyword.lower():
                        domain = keyword + '.com'  # 添加.com后缀
                        break
                
                if not domain:
                    domain = 'surrit.com'  # 默认域名
                
                # 构建视频URL
                base_url = f"https://{domain}/{uuid}"
                
                return {
                    'source': f"{base_url}/playlist.m3u8",
                    'source842': f"{base_url}/842x480/video.m3u8",
                    'source1280': f"{base_url}/1280x720/video.m3u8"                }
            
            return {}
            
        except Exception as e:
            print(f"手动解码URL时出错: {e}")
            return {}
    
    def _sanitize_filename(self, filename: str) -> str:
        """
        清理文件名，移除非法字符
        
        Args:
            filename: 原始文件名
            
        Returns:
            清理后的文件名
        """
        if not filename or not filename.strip():
            return "video"
        
        # 移除或替换非法字符
        illegal_chars = ['<', '>', ':', '"', '/', '\\', '|', '?', '*']
        sanitized = filename
        for char in illegal_chars:
            sanitized = sanitized.replace(char, '_')
        
        # 限制文件名长度
        if len(sanitized) > 200:
            sanitized = sanitized[:200]
        
        return sanitized.strip()
    
    def cleanup(self):
        """清理插件资源"""
        print(f"[{self.name}] 清理 MissAV 视频提取器")
    
    def execute(self, *args, **kwargs) -> Any:
        """执行插件功能（为了兼容基类接口）"""
        if args and isinstance(args[0], str):
            return self.extract(args[0])
        return []

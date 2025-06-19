"""
MissAV视频提取器插件

支持从 missav.ai 和 missav.com 网站提取视频下载链接。
该提取器只依赖dukpy来执行JavaScript混淆代码，获取真实的视频URL。
如果dukpy执行失败，直接返回空结果。
"""

import json
import re
from typing import List, Dict, Any
from urllib.parse import urlparse

from ...core.downloader.options import DownloadOpt, LinkType
from .base import ExtractorPlugin

# 使用日志
from ...config.logging_config import get_logger
logger = get_logger("pavone.extractor.missav_extractor")

# dukpy引用
try:
    import dukpy
    _dukpy_available = True
except ImportError:
    logger.error("dukpy库未安装，无法执行JavaScript代码。请安装dukpy库以支持MissAV提取器。")
    dukpy = None
    _dukpy_available = False


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
            'www.missav.com'        ]
    
    def initialize(self):
        """初始化插件"""
        logger.info(f"[{self.name}] 初始化 MissAV 视频提取器")
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
            if not html_content:
                logger.error(f"获取页面内容失败: {url}")
                return []
                
            # 提取混淆的JavaScript代码
            video_urls = self._extract_obfuscated_urls(html_content)
            if not video_urls:
                logger.error(f"未能从页面提取视频链接: {url}")
                return []
            # 提取视频标题
            title_match = re.search(r'<title[^>]*>([^<]+)</title>', html_content, re.IGNORECASE)
            video_title = "Unknown"
            if title_match:
                video_title = title_match.group(1).strip()
                # 清理标题，移除网站名称
                video_title = re.sub(r'\s*-\s*MissAV.*$', '', video_title)
                video_title = self.sanitize_filename(video_title)
            
            # 生成下载选项
            download_options: List[DownloadOpt] = []
            for _, video_url in video_urls.items():
                if not video_url:
                    continue
                    
                # 清理文件名
                filename = self.sanitize_filename(video_title)
                quality = "未知"
                
                # 如果有质量信息，可以从video_url中提取
                if '720p' in video_url.lower():
                    quality = '720p'
                elif '1080p' in video_url.lower():
                    quality = '1080p'
                elif '4k' in video_url.lower():
                    quality = '4K'
                elif '480p' in video_url.lower():
                    quality = '480p'
                
                
                # filename应该以视频名称为基础,同事包括视频质量，并且应该处理一下
                filename = f"{filename} - {quality}" if quality != "未知" else filename
                # 以mp4结尾
                if not filename.endswith('.mp4'):
                    filename += '.mp4'

                download_options.append(DownloadOpt(
                    url=video_url,
                    filename=filename,
                    link_type=LinkType.STREAM,
                    custom_headers={"Referrer": url},
                    display_name=f"{filename}",
                    quality=quality
                ))
            
            
            return download_options
  
        except Exception as e:
            logger.error(f"获取页面失败: {e}")
            return []
    
    def _extract_obfuscated_urls(self, html_content: str) -> Dict[str, str]:
        """
        从JavaScript混淆代码中提取视频URL - 只依赖dukpy执行JavaScript
        如果dukpy执行失败，直接返回空结果
        
        Args:
            html_content: HTML页面内容
            
        Returns:
            包含video URLs的字典，失败时返回空字典        
        """        # 检查dukpy是否可用
        if not _dukpy_available or dukpy is None:
            logger.error("dukpy库不可用，无法执行JavaScript代码")
            return {}
        
        try:
            # 使用Python直接查找包含eval的行
            lines = html_content.splitlines()
            eval_code = ''
            
            # 从最后一行开始查找包含eval的行
            for line in reversed(lines):
                if 'eval(' in line and 'm3u8' in line:
                    eval_code = line
                    break
            # 如果没有找到eval代码，返回空字典
            if not eval_code:
                logger.warning("提取的eval代码为空")
                return {}
            #不需要提取eval括号内的内容，直接使用整行代码
            eval_code = eval_code.strip()
            
            logger.debug("使用Python成功提取eval代码")
            logger.debug(f"找到eval代码: {eval_code[:100]}...")

            # 尝试执行JavaScript代码并提取视频URL
            js_execution_code = """
            var source, source842, source1280;
            """ + eval_code + """;
            var result = {
                'source': source,
                'source842': source842,
                'source1280': source1280
            };
            // 返回一个对象，包含所有提取到的视频URL
            result;
            """
            
            logger.debug("使用dukpy执行混淆代码并提取视频URL")
            result = dukpy.evaljs(js_execution_code)
            logger.debug("dukpy执行结果: " + str(result))
            
            if result and isinstance(result, dict) and len(result) > 0:
                logger.debug(f"成功提取到 {len(result)} 个视频URL")
                video_urls = {}
                for key, url in result.items():
                    if url and isinstance(url, str):
                        # 确保URL是完整的
                        if url.startswith('//'):
                            url = 'https:' + url
                        elif url.startswith('/'):
                            url = 'https://missav.ai' + url
                        video_urls[key] = url
                        logger.debug(f"提取到视频URL: {key} = {url}")
                # 获取最终的视频URL列表
                finial_video_urls = self._get_final_urls(video_urls)

                return finial_video_urls
            else:
                logger.warning("dukpy执行后未获取到有效的视频URL")
                return {}
                
        except Exception as e:
            logger.error(f"使用dukpy执行JavaScript时出错: {e}")
            return {}
        
        # 如果到达这里，说明所有尝试都失败了        return {}
    
    def cleanup(self):
        """清理插件资源"""
        logger.info(f"[{self.name}] 清理 MissAV 视频提取器")
    
    def execute(self, *args, **kwargs) -> Any:
        """执行插件功能（为了兼容基类接口）"""
        if args and isinstance(args[0], str):
            return self.extract(args[0])
        return []

    def _get_final_urls(self, video_urls: Dict[str,str]) -> Dict[str, str]:
        """
        获取最终的视频URL列表
        主要用于在下载前获取所有可用的URL
        """
        finial_video_urls = {}
        # 尝试找到大师链接,这个链接一般是以playlist.m3u8结尾
        master_urls = {k: v for k, v in video_urls.items() if v.endswith('playlist.m3u8')}
        #如果找到大师链接，则进行继续处理，否则，将所有url进行去重处理
        if not master_urls or len(master_urls) == 0:
            logger.debug("未找到大师链接，使用所有视频URL")
            # 需要对video_urls进行清理，移除空值
            # 只保留非空的URL,同时需要去处相同的URL
            video_urls = {k: v for k, v in video_urls.items() if v and isinstance(v, str)}
            # 移除重复的URL
            for key, url in video_urls.items():
                if url not in finial_video_urls.values():
                    # TODO: 这里需要进一步处理URL，确保是有效的，并且有些情况m3u8链接可能是大师链接,内嵌多个子链接，需要进一步处理
                    finial_video_urls[key] = url
            logger.debug(f"最终提取到 {len(finial_video_urls)} 个有效视频URL")
        else:
            mater_url = list(master_urls.values())[0]
            logger.debug(f"找到大师链接: {mater_url}")
            finial_video_urls = self._extract_master_playlist(mater_url)
        return finial_video_urls

    def _extract_master_playlist(self, master_url: str) -> Dict[str, str]:

        """
        从大师链接中提取所有子链接
        主要用于处理.m3u8链接，获取所有可用的子链接
        """
        try:
            # 获取大师链接内容
            response = self.fetch_webpage(master_url, timeout=30, verify_ssl=False)
            if response.status_code != 200:
                logger.info(f"获取大师链接失败: {master_url} - 状态码: {response.status_code}")
                return {}
            # 基准为去除playlist.m3u8的一部分
            base_url = master_url.rsplit('/', 1)[0] + '/'
            # 解析.m3u8内容，提取所有子链接
            lines = response.text.splitlines()
            sub_urls = {}
            for line in lines:
                line = line.strip()
                if line and not line.startswith('#'):
                    #找到以m3u8结尾的链接
                    if line.endswith('.m3u8'):
                        if line.startswith('http'):
                            key = self._get_key_for_url(line)
                            if key:
                                sub_urls[key] = line
                        else:
                            # 如果是相对链接，拼接基准URL
                            full_url = base_url + line
                            key = self._get_key_for_url(full_url)
                            if key:
                                sub_urls[key] = full_url
            
            logger.debug(f"从大师链接提取到 {len(sub_urls)} 个子链接")
            return sub_urls
        
        except Exception as e:
            logger.error(f"处理大师链接时出错: {e}")
            return {}
    
    def _get_key_for_url(self, url: str) -> str:
        """
        获取视频URL的唯一键
        用于在下载选项中标识不同的视频链接
        """
        # 如果包含360p或720p等质量信息，使用这些信息作为键
        if '360p' in url:
            return '360p'
        elif '480p' in url:
            return '480p'
        elif '720p' in url:
            return '720p'
        elif '1080p' in url:
            return '1080p'
        elif '4k' in url:
            return '4k'
        else:
            return ''

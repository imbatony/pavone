"""
Caribbeancom元数据提取器插件

支持从 caribbeancom.com 和 caribbeancompr.com 网站提取视频元数据。
通过解析HTML页面获取结构化数据。
"""

import re
from typing import List, Optional

from ...models import MovieMetadata
from ...utils.metadata_builder import MetadataBuilder
from .base import MetadataPlugin

# 定义插件名称和版本
PLUGIN_NAME = "CaribbeancomMetadata"
PLUGIN_VERSION = "1.1.0"
PLUGIN_DESCRIPTION = "提取 caribbeancom.com 和 caribbeancompr.com 的视频元数据"
PLUGIN_AUTHOR = "PAVOne"

# 定义插件优先级
PLUGIN_PRIORITY = 20

# 定义支持的域名
SUPPORTED_DOMAINS = [
    "caribbeancom.com",
    "www.caribbeancom.com",
    "en.caribbeancom.com",
    "caribbeancompr.com",
    "www.caribbeancompr.com",
    "en.caribbeancompr.com",
]

# Premium 域名
PREMIUM_DOMAINS = ["caribbeancompr.com", "www.caribbeancompr.com", "en.caribbeancompr.com"]

SITE_NAME = "Caribbeancom"
SITE_NAME_PREMIUM = "CaribbeancomPR"

# 番号格式: caribbeancom 用 dash, caribbeancompr 用 underscore
MOVIE_ID_PATTERN = r"\d{6}-\d{3}"
MOVIE_ID_PATTERN_PR = r"\d{6}_\d{3}"

# 影片页面 URL 模板
MOVIE_URL_TEMPLATE = "https://www.caribbeancom.com/moviepages/{movie_id}/index.html"
MOVIE_URL_TEMPLATE_PR = "https://www.caribbeancompr.com/moviepages/{movie_id}/index.html"


class CaribbeancomMetadata(MetadataPlugin):
    """
    Caribbeancom元数据提取器
    通过解析HTML页面提取 caribbeancom.com 视频元数据。
    """

    def __init__(self):
        """初始化Caribbeancom元数据提取器"""
        super().__init__(
            name=PLUGIN_NAME,
            version=PLUGIN_VERSION,
            description=PLUGIN_DESCRIPTION,
            author=PLUGIN_AUTHOR,
            priority=PLUGIN_PRIORITY,
        )
        self.supported_domains = SUPPORTED_DOMAINS
        self.site_name = SITE_NAME

    def can_extract(self, identifier: str) -> bool:
        """检查是否能处理给定的identifier

        支持两种格式：
        1. URL: https://www.caribbeancom.com/moviepages/033026-001/index.html
              https://www.caribbeancompr.com/moviepages/050815_203/index.html
        2. 番号: 033026-001 或 050815_203
        """
        if identifier.startswith("http://") or identifier.startswith("https://"):
            return self.can_handle_domain(identifier, self.supported_domains)

        identifier_stripped = identifier.strip()
        return bool(
            re.match(rf"^{MOVIE_ID_PATTERN}$", identifier_stripped)
            or re.match(rf"^{MOVIE_ID_PATTERN_PR}$", identifier_stripped)
        )

    def extract_metadata(self, identifier: str) -> Optional[MovieMetadata]:
        """从给定的identifier提取元数据"""
        try:
            is_premium = self._is_premium(identifier)
            movie_id = self._extract_movie_id(identifier, is_premium)
            if not movie_id:
                self.logger.error(f"无法从identifier提取番号: {identifier}")
                return None

            if is_premium:
                url = MOVIE_URL_TEMPLATE_PR.format(movie_id=movie_id)
            else:
                url = MOVIE_URL_TEMPLATE.format(movie_id=movie_id)

            response = self.fetch(url, timeout=30)
            # caribbeancompr 使用 EUC-JP 编码
            if is_premium:
                response.encoding = "euc-jp"
            html = response.text
            if not html:
                self.logger.error(f"获取页面内容失败: {url}")
                return None

            return self._build_metadata_from_html(html, movie_id, is_premium)

        except Exception as e:
            self.logger.error(f"提取元数据失败: {str(e)}", exc_info=True)
            return None

    def _is_premium(self, identifier: str) -> bool:
        """判断是否为 caribbeancompr (Premium) 链接"""
        if identifier.startswith("http://") or identifier.startswith("https://"):
            from urllib.parse import urlparse

            host = urlparse(identifier).netloc.lower()
            return any(host == d for d in PREMIUM_DOMAINS)
        # 番号格式区分：underscore 为 premium
        return bool(re.match(rf"^{MOVIE_ID_PATTERN_PR}$", identifier.strip()))

    def _extract_movie_id(self, identifier: str, is_premium: bool = False) -> Optional[str]:
        """从identifier中提取番号"""
        if identifier.startswith("http://") or identifier.startswith("https://"):
            return self._extract_movie_id_from_url(identifier, is_premium)
        identifier_stripped = identifier.strip()
        pattern = MOVIE_ID_PATTERN_PR if is_premium else MOVIE_ID_PATTERN
        if re.match(rf"^{pattern}$", identifier_stripped):
            return identifier_stripped
        return None

    def _extract_movie_id_from_url(self, url: str, is_premium: bool = False) -> Optional[str]:
        """从URL中提取番号"""
        pattern = MOVIE_ID_PATTERN_PR if is_premium else MOVIE_ID_PATTERN
        match = re.search(rf"/moviepages/({pattern})/", url)
        return match.group(1) if match else None

    def _build_metadata_from_html(self, html: str, movie_id: str, is_premium: bool = False) -> Optional[MovieMetadata]:
        """从HTML页面构建MovieMetadata对象"""
        try:
            if is_premium:
                url = MOVIE_URL_TEMPLATE_PR.format(movie_id=movie_id)
                site_name = SITE_NAME_PREMIUM
                base_domain = "https://www.caribbeancompr.com"
                studio = "カリビアンコムプレミアム"
            else:
                url = MOVIE_URL_TEMPLATE.format(movie_id=movie_id)
                site_name = SITE_NAME
                base_domain = "https://www.caribbeancom.com"
                studio = "カリビアンコム"

            code = movie_id

            title = self._extract_title(html)
            actors = self._extract_actors(html)
            release_date = self._extract_release_date(html)
            runtime = self._extract_duration(html)
            tags = self._extract_tags(html)
            rating = self._extract_rating(html)
            desc = self._extract_description(html)

            # 从 HTML 画像ギャラリー区域提取图片链接
            gallery_images = self._extract_gallery_images(html, movie_id, base_domain)
            # l_l.jpg 作为 poster
            poster = f"{base_domain}/moviepages/{movie_id}/images/l_l.jpg"
            # 从背景图中选择高度最大的作为 cover
            cover = self._select_tallest_image(gallery_images)
            # 所有图片作为背景图（Jellyfin支持多张）
            backdrops = gallery_images

            display_title = title or "Unknown"

            builder = (
                MetadataBuilder()
                .set_title(display_title, code)
                .set_identifier(site_name, code, url)
                .set_actors(actors)
                .set_runtime(runtime)
                .set_release_date(release_date)
                .set_tags(tags)
                .set_rating(rating)
                .set_plot(desc)
                .set_backdrops(backdrops)
                .set_cover(cover)
                .set_poster(poster)
                .set_studio(studio)
            )
            metadata = builder.build()
            metadata.official_rating = "JP-18+"

            self.logger.info(f"成功提取元数据: {code}")
            return metadata

        except Exception as e:
            self.logger.error(f"构建元数据失败: {str(e)}", exc_info=True)
            return None

    def _select_tallest_image(self, image_urls: List[str]) -> Optional[str]:
        """从图片列表中选择高度最大的竖图（宽<高）作为 cover

        如果没有竖图则返回 None。
        """
        import io

        from PIL import Image

        best_url: Optional[str] = None
        max_height = 0

        for url in image_urls:
            try:
                resp = self.fetch(url, timeout=15, no_exceptions=True)
                if resp.status_code != 200:
                    continue
                img = Image.open(io.BytesIO(resp.content))
                width, height = img.size
                if width < height and height > max_height:
                    max_height = height
                    best_url = url
            except Exception:
                continue

        if best_url:
            self.logger.debug(f"选择 cover: {best_url} (高度 {max_height})")
        return best_url

    def _extract_gallery_images(
        self, html: str, movie_id: str, base_domain: str = "https://www.caribbeancom.com"
    ) -> List[str]:
        """从 HTML 的画像ギャラリー区域提取大图 URL

        支持不同格式的图片链接：
        - 新版: /moviepages/{id}/images/l/001.jpg (相对路径)
        - 旧版: /moviepages/{id}/images/g_big001.jpg (相对路径)
        - Premium: https://www.caribbeancompr.com/moviepages/{id}/images/l/001.jpg (绝对路径)
        """
        movie_path = f"/moviepages/{movie_id}/images/"
        # 匹配相对路径
        pattern_rel = rf'href="({re.escape(movie_path)}[^"]+\.jpg)"'
        paths_rel = re.findall(pattern_rel, html)
        # 匹配绝对路径
        pattern_abs = rf'href="(https?://[^"]*{re.escape(movie_path)}[^"]+\.jpg)"'
        paths_abs = re.findall(pattern_abs, html)

        # 合并：绝对路径直接使用，相对路径加 base_domain
        all_urls = paths_abs + [base_domain + p for p in paths_rel]
        # 过滤：只保留大图（l/ 或 g_big 或 g_samp），排除缩略图（s/ 或 g_t）和会员限定（/member/）
        big_urls = [u for u in all_urls if ("/l/" in u or "g_big" in u or "g_samp" in u) and "/member/" not in u]
        # 去重保序
        seen: set[str] = set()
        result: List[str] = []
        for u in big_urls:
            if u not in seen:
                seen.add(u)
                result.append(u)
        return result

    def _extract_title(self, html: str) -> Optional[str]:
        """从<title>标签提取影片标题"""
        match = re.search(r"<title>(.*?)\s*\|", html)
        if match:
            return match.group(1).strip()
        return None

    def _extract_actors(self, html: str) -> List[str]:
        """从出演区域提取演员列表

        caribbeancom 使用 itemprop="name"，caribbeancompr 使用 spec-item 链接文本
        """
        section = re.search(
            r'<span class="spec-title">出演</span>\s*<span[^>]*>(.*?)</span>\s*</li>',
            html,
            re.S,
        )
        if section:
            content = section.group(1)
            # 优先尝试 itemprop="name" (caribbeancom)
            actors = re.findall(r'itemprop="name">([^<]+)</', content)
            if not actors:
                # caribbeancompr: 从 spec-item 链接提取
                actors = re.findall(r'class="spec-item"[^>]*>([^<]+)</a>', content)
            return actors
        return []

    def _extract_release_date(self, html: str) -> Optional[str]:
        """提取配信日，转换为YYYY-MM-DD格式"""
        match = re.search(r'itemprop="uploadDate"[^>]*class="spec-content">(\d{4}/\d{2}/\d{2})', html)
        if match:
            return match.group(1).replace("/", "-")
        return None

    def _extract_duration(self, html: str) -> Optional[int]:
        """提取再生時間，返回分钟数

        caribbeancom: itemprop="duration" content="T00H51M31S"
        caribbeancompr: 纯文本 "02:01:27"
        """
        # itemprop 格式
        match = re.search(r'itemprop="duration"\s+content="T(\d+)H(\d+)M(\d+)S"', html)
        if match:
            hours = int(match.group(1))
            minutes = int(match.group(2))
            seconds = int(match.group(3))
            return hours * 60 + minutes + (1 if seconds >= 30 else 0)
        # 纯文本 HH:MM:SS 格式
        section = re.search(
            r'<span class="spec-title">再生時間</span>\s*<span[^>]*>\s*(\d{1,2}):(\d{2}):(\d{2})',
            html,
            re.S,
        )
        if section:
            hours = int(section.group(1))
            minutes = int(section.group(2))
            seconds = int(section.group(3))
            return hours * 60 + minutes + (1 if seconds >= 30 else 0)
        return None

    def _extract_tags(self, html: str) -> List[str]:
        """提取标签列表"""
        section = re.search(
            r'<span class="spec-title">タグ</span>\s*<span class="spec-content">(.*?)</span>\s*</li>',
            html,
            re.S,
        )
        if section:
            return re.findall(r'class="spec-item"[^>]*>([^<]+)</a>', section.group(1))
        return []

    def _extract_rating(self, html: str) -> Optional[float]:
        """提取评分（星数转换为10分制）"""
        # 第一个 meta-rating 是当前影片的评分
        match = re.search(r'meta-rating">(★+)', html)
        if match:
            stars = len(match.group(1))
            return round(stars * 2.0, 1)  # 5星制 → 10分制
        return None

    def _extract_description(self, html: str) -> Optional[str]:
        """提取影片描述

        caribbeancom: itemprop="description"
        caribbeancompr: movie-info 区域的 <p> 或 <meta name="description">
        """
        # itemprop 格式
        match = re.search(r'itemprop="description"[^>]*>(.*?)</p>', html, re.S)
        if match:
            desc = re.sub(r"<[^>]+>", "", match.group(1)).strip()
            if desc:
                return desc
        # movie-info 区域内的 <p>
        section = re.search(r"movie-info(.*?)</section>", html, re.S)
        if section:
            p_match = re.search(r"<p[^>]*>(.*?)</p>", section.group(1), re.S)
            if p_match:
                desc = re.sub(r"<[^>]+>", "", p_match.group(1)).strip()
                if desc:
                    return desc
        # meta description 兜底
        match = re.search(r'<meta\s+name="description"\s+content="([^"]+)"', html)
        if match:
            return match.group(1).strip()
        return None

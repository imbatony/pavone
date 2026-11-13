"""M3U8 播放列表认证参数继承测试。"""

from pavone.config.configs import Config
from pavone.core.downloader.m3u8_downloader import M3U8Downloader


def _downloader(tmp_path) -> M3U8Downloader:
    config = Config()
    config.download.output_dir = str(tmp_path)
    return M3U8Downloader(config)


def test_absolute_segment_inherits_access_token(tmp_path) -> None:
    downloader = _downloader(tmp_path)
    playlist_url = "https://customers.iw01.xyz/api/v1/videos/1/manifest/index.m3u8?hb=abc&access_token=cdn%2Ftoken"
    content = """#EXTM3U
#EXT-X-MAP:URI="https://customers.iw01.xyz/fmp4/init.mp4?ro=0"
#EXTINF:9.0,
https://customers.iw01.xyz/fmp4/file-1.m4s?ro=0
https://other.example/file-2.m4s
"""

    urls = downloader._parse_m3u8_playlist(content, "https://customers.iw01.xyz/api/v1/videos/1/manifest/", playlist_url)

    assert urls[0] == "https://customers.iw01.xyz/fmp4/file-1.m4s?ro=0&access_token=cdn%2Ftoken"
    assert urls[1] == "https://other.example/file-2.m4s"
    assert downloader._init_segment_url == "https://customers.iw01.xyz/fmp4/init.mp4?ro=0&access_token=cdn%2Ftoken"


def test_relative_segment_inherits_access_token(tmp_path) -> None:
    downloader = _downloader(tmp_path)
    playlist_url = "https://cdn.example/v/pl.m3u8?access_token=abc"
    urls = downloader._parse_m3u8_playlist("#EXTM3U\nseg-1.ts\n", "https://cdn.example/v/", playlist_url)

    assert urls == ["https://cdn.example/v/seg-1.ts?access_token=abc"]


def test_playlist_without_token_is_unchanged(tmp_path) -> None:
    downloader = _downloader(tmp_path)
    urls = downloader._parse_m3u8_playlist(
        "#EXTM3U\nhttps://cdn.example/seg.ts\n",
        "https://cdn.example/",
        "https://cdn.example/pl.m3u8",
    )

    assert urls == ["https://cdn.example/seg.ts"]
    assert downloader._init_segment_url is None


def test_existing_access_token_is_not_duplicated(tmp_path) -> None:
    downloader = _downloader(tmp_path)
    playlist_url = "https://cdn.example/pl.m3u8?access_token=abc"
    content = "#EXTM3U\nhttps://cdn.example/seg.ts?access_token=abc\n"

    urls = downloader._parse_m3u8_playlist(content, "https://cdn.example/", playlist_url)

    assert urls == ["https://cdn.example/seg.ts?access_token=abc"]

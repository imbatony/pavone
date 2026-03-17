"""共享提取函数单元测试"""

import unittest

from pavone.utils.html_metadata_utils import (
    extract_actors,
    extract_code,
    extract_cover,
    extract_date,
    extract_genres,
    extract_m3u8_url,
    extract_title,
)

SAMPLE_HTML = """
<html>
<head>
<title>ABC-123 Sample Video Title</title>
<meta property="og:title" content="ABC-123 Sample Video Title" />
<meta property="og:image" content="https://example.com/cover.jpg" />
<meta property="og:description" content="A sample video" />
</head>
<body>
<span class="code">ABC-123</span>
<span class="date">2024-06-15</span>
<a href="/actor/alice">Alice</a>
<a href="/actor/bob">Bob</a>
<a href="/genre/drama">Drama</a>
<a href="/genre/action">Action</a>
<script>var m3u8_url = "https://cdn.example.com/stream/playlist.m3u8?token=abc123";</script>
</body>
</html>
"""


class TestExtractTitle(unittest.TestCase):
    def test_extract_og_title(self) -> None:
        result = extract_title(SAMPLE_HTML)
        self.assertEqual(result, "ABC-123 Sample Video Title")

    def test_extract_title_with_custom_pattern(self) -> None:
        html = "<div class='title'>Custom Title Here</div>"
        result = extract_title(html, patterns=[r"class='title'>([^<]+)</div>"])
        self.assertEqual(result, "Custom Title Here")

    def test_extract_title_fallback_to_title_tag(self) -> None:
        html = "<html><head><title>Fallback Title</title></head></html>"
        result = extract_title(html)
        self.assertEqual(result, "Fallback Title")

    def test_extract_title_returns_none_for_empty(self) -> None:
        result = extract_title("<html></html>")
        self.assertIsNone(result)


class TestExtractCode(unittest.TestCase):
    def test_extract_code_with_pattern(self) -> None:
        result = extract_code(SAMPLE_HTML, patterns=[r'class="code">([A-Z]+-\d+)<'])
        self.assertEqual(result, "ABC-123")

    def test_extract_code_returns_none_without_pattern(self) -> None:
        result = extract_code(SAMPLE_HTML)
        self.assertIsNone(result)

    def test_extract_code_uppercase(self) -> None:
        html = "<span>abc-456</span>"
        result = extract_code(html, patterns=[r"<span>([a-z]+-\d+)</span>"])
        self.assertEqual(result, "ABC-456")


class TestExtractCover(unittest.TestCase):
    def test_extract_og_cover(self) -> None:
        result = extract_cover(SAMPLE_HTML)
        self.assertEqual(result, "https://example.com/cover.jpg")

    def test_extract_cover_with_pattern(self) -> None:
        html = '<img data-src="https://img.example.com/thumb.jpg">'
        result = extract_cover(html, patterns=[r'data-src="([^"]+)"'])
        self.assertEqual(result, "https://img.example.com/thumb.jpg")

    def test_extract_cover_returns_none(self) -> None:
        result = extract_cover("<html></html>")
        self.assertIsNone(result)


class TestExtractDate(unittest.TestCase):
    def test_extract_iso_date(self) -> None:
        result = extract_date(SAMPLE_HTML)
        self.assertEqual(result, "2024-06-15")

    def test_extract_date_with_custom_pattern(self) -> None:
        html = '<span class="release">Release: 2023/12/01</span>'
        result = extract_date(html, patterns=[r"Release:\s*(\d{4}/\d{2}/\d{2})"])
        self.assertEqual(result, "2023/12/01")

    def test_extract_date_returns_none(self) -> None:
        result = extract_date("<html>no date</html>")
        self.assertIsNone(result)

    def test_extract_jp_date(self) -> None:
        html = "<span>2024年3月15日</span>"
        result = extract_date(html)
        self.assertEqual(result, "2024年3月15日")


class TestExtractActors(unittest.TestCase):
    def test_extract_actors_with_pattern(self) -> None:
        result = extract_actors(SAMPLE_HTML, patterns=[r'href="/actor/([^"]+)"'])
        self.assertEqual(result, ["alice", "bob"])

    def test_extract_actors_returns_empty(self) -> None:
        result = extract_actors("<html></html>")
        self.assertEqual(result, [])


class TestExtractGenres(unittest.TestCase):
    def test_extract_genres_with_pattern(self) -> None:
        result = extract_genres(SAMPLE_HTML, patterns=[r'href="/genre/([^"]+)"'])
        self.assertEqual(result, ["drama", "action"])

    def test_extract_genres_returns_empty(self) -> None:
        result = extract_genres("<html></html>")
        self.assertEqual(result, [])


class TestExtractM3U8Url(unittest.TestCase):
    def test_extract_m3u8_default(self) -> None:
        result = extract_m3u8_url(SAMPLE_HTML)
        self.assertIsNotNone(result)
        self.assertIn(".m3u8", result or "")

    def test_extract_m3u8_with_pattern(self) -> None:
        html = 'source: "https://cdn.example.com/v.m3u8"'
        result = extract_m3u8_url(html, patterns=[r'source:\s*"([^"]+\.m3u8[^"]*)"'])
        self.assertEqual(result, "https://cdn.example.com/v.m3u8")

    def test_extract_m3u8_returns_none(self) -> None:
        result = extract_m3u8_url("<html>no m3u8 here</html>")
        self.assertIsNone(result)


if __name__ == "__main__":
    unittest.main()

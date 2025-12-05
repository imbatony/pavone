import os

from pavone.models.search_result import SearchResult
from pavone.plugins.search.missav_search import MissavSearch


class TestMissavSearch:
    """Test the MissavSearch plugin"""

    def test_parse_search_results(self):
        """Test the _parse_search_results method"""
        # Initialize the plugin
        plugin = MissavSearch()

        # Read the sample search results HTML file
        html_path = os.path.join(os.path.dirname(__file__), "sites", "missav_search.html")
        with open(html_path, "r", encoding="utf-8") as f:
            html_content = f.read()

        # Parse the search results
        results = plugin._parse_search_results(html_content, 5, "优等生")

        # Assert that we have the expected number of results
        assert len(results) == 5

        # 检查第一个结果
        first_result = results[0]
        assert isinstance(first_result, SearchResult)
        assert first_result.site == "MissAV"
        assert first_result.keyword == "优等生"
        # code 可能为 None，需要处理
        if first_result.code is not None:
            assert "GOAL-052" in first_result.code.upper()
        assert "優等生" in first_result.title

        # Verify URLs are correctly extracted
        for result in results:
            assert result.url.startswith("https://missav.ai/")
            assert result.code is not None and result.code != ""

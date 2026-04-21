"""ItemMetadata.metadata_score 单元测试"""

from pavone.models.constants import METADATA_SCORE_WEIGHTS
from pavone.models.jellyfin_item import ItemMetadata


class TestMetadataScore:
    """元数据丰富度评分测试"""

    def test_empty_metadata_score_is_zero(self) -> None:
        """全部元数据为空时评分为 0"""
        metadata = ItemMetadata({})
        assert metadata.metadata_score == 0

    def test_title_only_score(self) -> None:
        """仅有标题时评分为 title 权重"""
        metadata = ItemMetadata({"Name": "测试视频"})
        assert metadata.metadata_score == METADATA_SCORE_WEIGHTS["title"]

    def test_full_metadata_score_is_100(self) -> None:
        """全部元数据齐全时评分为 100"""
        data = {
            "Name": "测试视频",
            "ExternalId": "ABC-123",
            "Overview": "这是一个测试视频的描述",
            "Genres": ["动作", "科幻"],
            "PremiereDate": "2026-01-01",
            "RunTimeTicks": 36000000000,
            "People": [
                {"Name": "张三", "Type": "Actor"},
                {"Name": "李四", "Type": "Director"},
            ],
            "ImageTags": {"Primary": "abc123", "Thumb": "def456"},
            "CommunityRating": 8.5,
            "Tags": ["精选", "推荐"],
            "Studios": [{"Name": "测试工作室"}],
        }
        metadata = ItemMetadata(data)
        assert metadata.metadata_score == 100

    def test_partial_metadata_score(self) -> None:
        """部分元数据存在时评分为对应权重之和"""
        # title + plot + genres
        data = {
            "Name": "测试视频",
            "Overview": "描述内容",
            "Genres": ["动作"],
        }
        metadata = ItemMetadata(data)
        expected = METADATA_SCORE_WEIGHTS["title"] + METADATA_SCORE_WEIGHTS["plot"] + METADATA_SCORE_WEIGHTS["genres"]
        assert metadata.metadata_score == expected

    def test_score_type_is_int(self) -> None:
        """验证返回类型为 int"""
        metadata = ItemMetadata({"Name": "测试"})
        assert isinstance(metadata.metadata_score, int)

    def test_score_range(self) -> None:
        """验证评分值域 [0, 100]"""
        assert ItemMetadata({}).metadata_score >= 0
        assert ItemMetadata({}).metadata_score <= 100

        full_data = {
            "Name": "测试",
            "ExternalId": "X-1",
            "Overview": "描述",
            "Genres": ["动作"],
            "PremiereDate": "2026-01-01",
            "RunTimeTicks": 36000000000,
            "People": [{"Name": "A", "Type": "Actor"}, {"Name": "B", "Type": "Director"}],
            "ImageTags": {"Primary": "x", "Thumb": "y"},
            "CommunityRating": 7.0,
            "Tags": ["标签"],
            "Studios": [{"Name": "工作室"}],
        }
        assert ItemMetadata(full_data).metadata_score >= 0
        assert ItemMetadata(full_data).metadata_score <= 100

    def test_zero_rating_not_counted(self) -> None:
        """评分为 0 时不计入"""
        data = {"CommunityRating": 0.0}
        metadata = ItemMetadata(data)
        assert metadata.metadata_score == 0

    def test_none_rating_not_counted(self) -> None:
        """评分为 None 时不计入"""
        data = {"CommunityRating": None}
        metadata = ItemMetadata(data)
        assert metadata.metadata_score == 0

    def test_weights_sum_to_100(self) -> None:
        """权重总和为 100"""
        assert sum(METADATA_SCORE_WEIGHTS.values()) == 100

    def test_cover_without_primary_not_counted(self) -> None:
        """有图片标签但无 Primary 时不计入封面图分数"""
        data = {"ImageTags": {"Thumb": "xyz"}}
        metadata = ItemMetadata(data)
        # Thumb 算 thumbnail 分数，但不算 cover
        assert metadata.metadata_score == METADATA_SCORE_WEIGHTS["thumbnail"]

    def test_actors_and_directors_separate(self) -> None:
        """演员和导演分别计分"""
        data_actors = {"People": [{"Name": "A", "Type": "Actor"}]}
        assert ItemMetadata(data_actors).metadata_score == METADATA_SCORE_WEIGHTS["actors"]

        data_directors = {"People": [{"Name": "B", "Type": "Director"}]}
        assert ItemMetadata(data_directors).metadata_score == METADATA_SCORE_WEIGHTS["director"]

        data_both = {"People": [{"Name": "A", "Type": "Actor"}, {"Name": "B", "Type": "Director"}]}
        assert ItemMetadata(data_both).metadata_score == METADATA_SCORE_WEIGHTS["actors"] + METADATA_SCORE_WEIGHTS["director"]

    def test_premiered_from_year_fallback(self) -> None:
        """有 ProductionYear 但无 PremiereDate 时仍计入 premiered 分数"""
        data = {"ProductionYear": 2026}
        metadata = ItemMetadata(data)
        assert metadata.metadata_score == METADATA_SCORE_WEIGHTS["premiered"]

    def test_runtime_scored(self) -> None:
        """有时长时计入 runtime 分数"""
        data = {"RunTimeTicks": 36000000000}
        metadata = ItemMetadata(data)
        assert metadata.metadata_score == METADATA_SCORE_WEIGHTS["runtime"]

    def test_code_scored(self) -> None:
        """有 ExternalId 时计入 code 分数"""
        data = {"ExternalId": "ABC-123"}
        metadata = ItemMetadata(data)
        assert metadata.metadata_score == METADATA_SCORE_WEIGHTS["code"]

    def test_thumbnail_scored(self) -> None:
        """有 Thumb 图片时计入 thumbnail 分数"""
        data = {"ImageTags": {"Thumb": "abc"}}
        metadata = ItemMetadata(data)
        assert metadata.metadata_score == METADATA_SCORE_WEIGHTS["thumbnail"]

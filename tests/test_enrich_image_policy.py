"""enrich 命令的图片策略 (ImagePolicy) 与 should_upload_image 单元测试"""

from typing import Any, Dict

import pytest

from pavone.cli.commands.enrich_helper import (
    IMAGE_KIND_BACKDROP,
    IMAGE_KIND_PRIMARY,
    IMAGE_KIND_THUMB,
    ImagePolicy,
    should_upload_image,
)
from pavone.models.jellyfin_item import ItemMetadata


def _make_item(
    has_primary: bool = False,
    has_thumb: bool = False,
    backdrop_count: int = 0,
) -> ItemMetadata:
    """构造一个 ItemMetadata 测试夹具，按需要标记是否已有各类图片"""
    image_tags: Dict[str, str] = {}
    if has_primary:
        image_tags["Primary"] = "tag-p"
    if has_thumb:
        image_tags["Thumb"] = "tag-t"
    data: Dict[str, Any] = {
        "ImageTags": image_tags,
        "BackdropImageTags": [f"bd-{i}" for i in range(backdrop_count)],
    }
    return ItemMetadata(data)


class TestShouldUploadImageNone:
    """policy=NONE 时所有类型都跳过"""

    @pytest.mark.parametrize("kind", [IMAGE_KIND_PRIMARY, IMAGE_KIND_THUMB, IMAGE_KIND_BACKDROP])
    def test_none_policy_skips_all(self, kind: str) -> None:
        item = _make_item(has_primary=False, has_thumb=False, backdrop_count=0)
        assert should_upload_image(kind, item, ImagePolicy.NONE) is False

    @pytest.mark.parametrize("kind", [IMAGE_KIND_PRIMARY, IMAGE_KIND_THUMB, IMAGE_KIND_BACKDROP])
    def test_none_policy_skips_even_when_missing(self, kind: str) -> None:
        item = _make_item(has_primary=True, has_thumb=True, backdrop_count=3)
        assert should_upload_image(kind, item, ImagePolicy.NONE) is False


class TestShouldUploadImageAll:
    """policy=ALL 时所有类型都下载，无视当前是否已存在"""

    @pytest.mark.parametrize("kind", [IMAGE_KIND_PRIMARY, IMAGE_KIND_THUMB, IMAGE_KIND_BACKDROP])
    def test_all_policy_when_missing(self, kind: str) -> None:
        item = _make_item()
        assert should_upload_image(kind, item, ImagePolicy.ALL) is True

    @pytest.mark.parametrize("kind", [IMAGE_KIND_PRIMARY, IMAGE_KIND_THUMB, IMAGE_KIND_BACKDROP])
    def test_all_policy_when_present(self, kind: str) -> None:
        item = _make_item(has_primary=True, has_thumb=True, backdrop_count=2)
        assert should_upload_image(kind, item, ImagePolicy.ALL) is True


class TestShouldUploadImageMissingOnly:
    """policy=MISSING_ONLY 时仅在对应类型缺失时下载"""

    def test_primary_missing(self) -> None:
        item = _make_item(has_primary=False)
        assert should_upload_image(IMAGE_KIND_PRIMARY, item, ImagePolicy.MISSING_ONLY) is True

    def test_primary_present(self) -> None:
        item = _make_item(has_primary=True)
        assert should_upload_image(IMAGE_KIND_PRIMARY, item, ImagePolicy.MISSING_ONLY) is False

    def test_thumb_missing(self) -> None:
        item = _make_item(has_thumb=False)
        assert should_upload_image(IMAGE_KIND_THUMB, item, ImagePolicy.MISSING_ONLY) is True

    def test_thumb_present(self) -> None:
        item = _make_item(has_thumb=True)
        assert should_upload_image(IMAGE_KIND_THUMB, item, ImagePolicy.MISSING_ONLY) is False

    def test_backdrop_missing(self) -> None:
        item = _make_item(backdrop_count=0)
        assert should_upload_image(IMAGE_KIND_BACKDROP, item, ImagePolicy.MISSING_ONLY) is True

    def test_backdrop_present(self) -> None:
        item = _make_item(backdrop_count=1)
        assert should_upload_image(IMAGE_KIND_BACKDROP, item, ImagePolicy.MISSING_ONLY) is False

    def test_independent_per_kind(self) -> None:
        # 仅有封面，缩略图 / 背景图缺失：只跳过封面
        item = _make_item(has_primary=True, has_thumb=False, backdrop_count=0)
        assert should_upload_image(IMAGE_KIND_PRIMARY, item, ImagePolicy.MISSING_ONLY) is False
        assert should_upload_image(IMAGE_KIND_THUMB, item, ImagePolicy.MISSING_ONLY) is True
        assert should_upload_image(IMAGE_KIND_BACKDROP, item, ImagePolicy.MISSING_ONLY) is True

    def test_unknown_kind_returns_false(self) -> None:
        # 未知图片类型在 MISSING_ONLY 策略下保守返回 False
        item = _make_item()
        assert should_upload_image("Logo", item, ImagePolicy.MISSING_ONLY) is False


class TestImagePolicyEnum:
    def test_enum_values(self) -> None:
        assert ImagePolicy.ASK.value == "ask"
        assert ImagePolicy.NONE.value == "none"
        assert ImagePolicy.MISSING_ONLY.value == "missing-only"
        assert ImagePolicy.ALL.value == "all"

    def test_enum_from_string(self) -> None:
        assert ImagePolicy("missing-only") == ImagePolicy.MISSING_ONLY

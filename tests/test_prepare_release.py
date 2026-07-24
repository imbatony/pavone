import json
from pathlib import Path

import pytest

from scripts.prepare_release import (
    BumpType,
    PullRequest,
    bump_version,
    determine_bump_type,
    extract_release_notes,
    main,
    prepare_release,
    validate_pull_request,
)
from scripts.validate_pull_request import main as validate_main

VALID_RELEASE_NOTES = """\
<!-- release-notes:start -->
### 新增
- 支持不依赖 AI 的确定性发布
### 改进
- 发布失败后可安全重试
<!-- release-notes:end -->
"""


@pytest.mark.parametrize(
    ("title", "labels"),
    [
        ("refactor!: replace public API", []),
        ("chore: migrate API", ["breaking-change"]),
        ("feat: migrate API", ["release:major"]),
        ("chore: BREAKING CHANGE in configuration", []),
    ],
)
def test_determine_major_bump(title: str, labels: list[str]) -> None:
    assert determine_bump_type(title, labels) == "major"


@pytest.mark.parametrize(
    ("title", "labels"),
    [
        ("feat: add downloader", []),
        ("feat(metadata): add provider", []),
        ("chore: improve downloader", ["enhancement"]),
    ],
)
def test_determine_minor_bump(title: str, labels: list[str]) -> None:
    assert determine_bump_type(title, labels) == "minor"


def test_determine_patch_bump_by_default() -> None:
    assert determine_bump_type("fix: handle timeout", ["bug"]) == "patch"


def test_release_label_overrides_title_bump() -> None:
    assert determine_bump_type("feat!: replace API", ["release:patch"]) == "patch"


@pytest.mark.parametrize(
    ("current", "bump_type", "expected"),
    [
        ("1.2.3", "major", "2.0.0"),
        ("1.2.3", "minor", "1.3.0"),
        ("1.2.3", "patch", "1.2.4"),
    ],
)
def test_bump_version(current: str, bump_type: BumpType, expected: str) -> None:
    assert bump_version(current, bump_type) == expected


def _event(
    title: str = "feat: add deterministic releases",
    body: str = VALID_RELEASE_NOTES,
    labels: list[str] | None = None,
) -> dict[str, object]:
    return {
        "pull_request": {
            "merged": True,
            "number": 123,
            "title": title,
            "body": body,
            "html_url": "https://github.com/owner/repo/pull/123",
            "labels": [{"name": label} for label in labels or []],
        }
    }


def test_prepare_release_updates_versions_and_changelog(tmp_path: Path) -> None:
    (tmp_path / "pavone").mkdir()
    (tmp_path / "pyproject.toml").write_text('[project]\nversion = "1.2.3"\n', encoding="utf-8")
    (tmp_path / "pavone" / "__init__.py").write_text('__version__ = "1.2.3"\n', encoding="utf-8")
    (tmp_path / "CHANGELOG.md").write_text("# Changelog\n\n简介\n\n## [1.2.3] - 2026-01-01\n", encoding="utf-8")

    release = prepare_release(_event(), tmp_path, "2026-07-24")

    assert release.version == "1.3.0"
    assert release.bump_type == "minor"
    assert "<!-- release-pr: 123 -->" in release.notes
    assert 'version = "1.3.0"' in (tmp_path / "pyproject.toml").read_text(encoding="utf-8")
    assert '__version__ = "1.3.0"' in (tmp_path / "pavone" / "__init__.py").read_text(encoding="utf-8")
    changelog = (tmp_path / "CHANGELOG.md").read_text(encoding="utf-8")
    assert "## [1.3.0] - 2026-07-24" in changelog
    assert "### 新增" in changelog
    assert "发布失败后可安全重试" in changelog
    assert "完整变更见 [#123]" in release.notes


def test_prepare_release_existing_version_does_not_modify_files(tmp_path: Path) -> None:
    release = prepare_release(
        _event("fix: recover release creation", body=""),
        tmp_path,
        "2026-07-24",
        existing_version="1.2.4",
    )

    assert release.version == "1.2.4"
    assert release.bump_type == "patch"
    assert "### 修复" in release.notes


def test_prepare_release_rejects_unmerged_event(tmp_path: Path) -> None:
    event = json.loads(json.dumps(_event()))
    event["pull_request"]["merged"] = False

    with pytest.raises(ValueError, match="已合并"):
        prepare_release(event, tmp_path, "2026-07-24")


def test_extract_release_notes() -> None:
    notes = extract_release_notes(f"前言\n{VALID_RELEASE_NOTES}\n结尾")

    assert notes is not None
    assert notes.startswith("### 新增")
    assert "确定性发布" in notes


def test_validate_pull_request_accepts_structured_notes() -> None:
    pull_request = PullRequest(
        number=123,
        title="feat(release): 添加确定性发布",
        body=VALID_RELEASE_NOTES,
        url="https://github.com/owner/repo/pull/123",
        labels=(),
    )

    assert validate_pull_request(pull_request) == []


def test_validate_pull_request_allows_empty_notes_when_skipped() -> None:
    pull_request = PullRequest(
        number=123,
        title="chore: 整理内部配置",
        body="",
        url="https://github.com/owner/repo/pull/123",
        labels=("release:skip",),
    )

    assert validate_pull_request(pull_request) == []


def test_validate_pull_request_rejects_invalid_contract() -> None:
    pull_request = PullRequest(
        number=123,
        title="Add release workflow",
        body="<!-- release-notes:start -->\n### Details\nNo bullet\n<!-- release-notes:end -->",
        url="https://github.com/owner/repo/pull/123",
        labels=("release:major", "release:minor"),
    )

    errors = validate_pull_request(pull_request)

    assert any("Conventional Commits" in error for error in errors)
    assert any("只能使用一个 release 标签" in error for error in errors)
    assert any("不支持的内容" in error for error in errors)
    assert any("至少需要一个" in error for error in errors)
    assert any("重大变更" in error for error in errors)


def test_validate_pull_request_rejects_content_outside_headings_and_bullets() -> None:
    pull_request = PullRequest(
        number=123,
        title="fix: 修复发布日志",
        body="""\
<!-- release-notes:start -->
## [999.0.0] - 2099-01-01
伪造版本内容
### 修复
- 正常列表项
<!-- release-notes:end -->
""",
        url="https://github.com/owner/repo/pull/123",
        labels=(),
    )

    errors = validate_pull_request(pull_request)

    assert any("## [999.0.0]" in error for error in errors)
    assert any("伪造版本内容" in error for error in errors)


def test_validate_cli_reports_errors(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    event_path = tmp_path / "event.json"
    event_path.write_text(json.dumps(_event(title="Invalid title", body="")), encoding="utf-8")

    result = validate_main(["--event", str(event_path)])

    assert result == 1
    assert "::error::PR 标题必须符合 Conventional Commits" in capsys.readouterr().out


def test_main_writes_release_notes_and_github_outputs(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    (tmp_path / "pavone").mkdir()
    (tmp_path / "pyproject.toml").write_text('[project]\nversion = "1.2.3"\n', encoding="utf-8")
    (tmp_path / "pavone" / "__init__.py").write_text('__version__ = "1.2.3"\n', encoding="utf-8")
    (tmp_path / "CHANGELOG.md").write_text("# Changelog\n\n简介\n\n## [1.2.3] - 2026-01-01\n", encoding="utf-8")
    event_path = tmp_path / "event.json"
    event_path.write_text(json.dumps(_event()), encoding="utf-8")
    notes_path = tmp_path / "release-notes.md"
    output_path = tmp_path / "github-output.txt"
    monkeypatch.setenv("GITHUB_OUTPUT", str(output_path))

    result = main(
        [
            "--event",
            str(event_path),
            "--notes-output",
            str(notes_path),
            "--root",
            str(tmp_path),
            "--date",
            "2026-07-24",
        ]
    )

    assert result == 0
    assert "<!-- release-pr: 123 -->" in notes_path.read_text(encoding="utf-8")
    outputs = output_path.read_text(encoding="utf-8")
    assert "new_version=1.3.0" in outputs
    assert "bump_type=minor" in outputs
    assert "release_title=v1.3.0" in outputs

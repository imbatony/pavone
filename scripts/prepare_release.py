"""根据合并 PR 的固定规则准备版本发布。"""

from __future__ import annotations

import argparse
import json
import os
import re
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Iterable, Literal, Mapping, Sequence, cast

BumpType = Literal["major", "minor", "patch"]

_VERSION_PATTERN = re.compile(r"^\d+\.\d+\.\d+$")
_PYPROJECT_VERSION_PATTERN = re.compile(r'(?m)^version = "([^"]+)"$')
_PACKAGE_VERSION_PATTERN = re.compile(r'(?m)^__version__ = "([^"]+)"$')
_CONVENTIONAL_FEATURE_PATTERN = re.compile(r"^feat(?:\([^)]*\))?:", re.IGNORECASE)
_CONVENTIONAL_FIX_PATTERN = re.compile(r"^fix(?:\([^)]*\))?:", re.IGNORECASE)
_CONVENTIONAL_BREAKING_PATTERN = re.compile(r"^[a-z]+(?:\([^)]*\))?!:", re.IGNORECASE)
_CONVENTIONAL_TITLE_PATTERN = re.compile(
    r"^(feat|fix|docs|refactor|perf|test|build|ci|chore|style|revert)(?:\([^()\r\n]+\))?!?:\s+\S.+$",
    re.IGNORECASE,
)
_RELEASE_NOTES_START = "<!-- release-notes:start -->"
_RELEASE_NOTES_END = "<!-- release-notes:end -->"
_RELEASE_LABELS = {"release:major", "release:minor", "release:patch", "release:skip"}
_RELEASE_HEADINGS = {"### 新增", "### 修复", "### 改进", "### 重大变更", "### 变更"}


@dataclass(frozen=True)
class PullRequest:
    number: int
    title: str
    body: str
    url: str
    labels: tuple[str, ...]


@dataclass(frozen=True)
class Release:
    version: str
    bump_type: BumpType
    title: str
    notes: str


def determine_bump_type(title: str, labels: Iterable[str]) -> BumpType:
    """按显式标签和 Conventional Commit 标题确定 SemVer 级别。"""
    normalized_labels = {label.casefold() for label in labels}
    if "release:major" in normalized_labels:
        return "major"
    if "release:minor" in normalized_labels:
        return "minor"
    if "release:patch" in normalized_labels:
        return "patch"
    if "breaking-change" in normalized_labels or "breaking" in title.casefold() or _CONVENTIONAL_BREAKING_PATTERN.match(title):
        return "major"
    if normalized_labels.intersection({"feature", "enhancement"}) or _CONVENTIONAL_FEATURE_PATTERN.match(title):
        return "minor"
    return "patch"


def bump_version(version: str, bump_type: BumpType) -> str:
    """递增三段式 SemVer 版本号。"""
    if not _VERSION_PATTERN.fullmatch(version):
        raise ValueError(f"不支持的版本格式: {version}")
    major, minor, patch = (int(part) for part in version.split("."))
    if bump_type == "major":
        return f"{major + 1}.0.0"
    if bump_type == "minor":
        return f"{major}.{minor + 1}.0"
    return f"{major}.{minor}.{patch + 1}"


def _read_single_version(path: Path, pattern: re.Pattern[str]) -> str:
    content = path.read_text(encoding="utf-8")
    matches = pattern.findall(content)
    if len(matches) != 1:
        raise ValueError(f"{path} 中应恰好包含一个版本号，实际为 {len(matches)} 个")
    return matches[0]


def _replace_version(path: Path, pattern: re.Pattern[str], old_version: str, new_version: str) -> None:
    content = path.read_text(encoding="utf-8")
    updated, count = pattern.subn(lambda match: match.group(0).replace(old_version, new_version), content)
    if count != 1 or updated == content:
        raise ValueError(f"无法在 {path} 中将版本 {old_version} 更新为 {new_version}")
    path.write_text(updated, encoding="utf-8")


def update_versions(root: Path, bump_type: BumpType) -> str:
    """同步更新 pyproject.toml 和包版本。"""
    pyproject = root / "pyproject.toml"
    package_init = root / "pavone" / "__init__.py"
    current_version = _read_single_version(pyproject, _PYPROJECT_VERSION_PATTERN)
    package_version = _read_single_version(package_init, _PACKAGE_VERSION_PATTERN)
    if current_version != package_version:
        raise ValueError(f"版本不一致: pyproject.toml={current_version}, pavone/__init__.py={package_version}")

    new_version = bump_version(current_version, bump_type)
    _replace_version(pyproject, _PYPROJECT_VERSION_PATTERN, current_version, new_version)
    _replace_version(package_init, _PACKAGE_VERSION_PATTERN, current_version, new_version)
    return new_version


def parse_pull_request(event: Mapping[str, object], require_merged: bool = True) -> PullRequest:
    """从 GitHub pull_request 事件中读取受控字段。"""
    pull_request_value = event.get("pull_request")
    if not isinstance(pull_request_value, dict):
        raise ValueError("事件不包含已合并的 pull request")
    pull_request = cast(Mapping[str, object], pull_request_value)
    if require_merged and pull_request.get("merged") is not True:
        raise ValueError("事件不包含已合并的 pull request")

    labels_value = pull_request.get("labels", [])
    labels: list[str] = []
    if isinstance(labels_value, list):
        for label_value in cast(list[object], labels_value):
            if isinstance(label_value, dict):
                label = cast(Mapping[str, object], label_value)
                name = label.get("name")
                if isinstance(name, str):
                    labels.append(name)

    number = pull_request.get("number")
    title = pull_request.get("title")
    body = pull_request.get("body")
    url = pull_request.get("html_url")
    if not isinstance(number, int) or not isinstance(title, str) or not isinstance(url, str):
        raise ValueError("pull request 事件缺少 number、title 或 html_url")
    return PullRequest(
        number=number,
        title=" ".join(title.split()),
        body=body if isinstance(body, str) else "",
        url=url,
        labels=tuple(labels),
    )


def extract_release_notes(body: str) -> str | None:
    """提取 PR 正文中的结构化 Release Notes 区块。"""
    start = body.find(_RELEASE_NOTES_START)
    end = body.find(_RELEASE_NOTES_END)
    if start < 0 or end < 0 or end <= start:
        return None
    start += len(_RELEASE_NOTES_START)
    return body[start:end].strip()


def validate_pull_request(pull_request: PullRequest) -> list[str]:
    """校验 PR 标题、版本标签和结构化 Release Notes。"""
    errors: list[str] = []
    if not _CONVENTIONAL_TITLE_PATTERN.fullmatch(pull_request.title):
        errors.append("PR 标题必须符合 Conventional Commits，例如 `feat(cli): 添加批量下载`。")

    normalized_labels = {label.casefold() for label in pull_request.labels}
    release_labels = sorted(normalized_labels.intersection(_RELEASE_LABELS))
    if len(release_labels) > 1:
        errors.append(f"只能使用一个 release 标签，当前为: {', '.join(release_labels)}。")
    if "release:skip" in release_labels:
        return errors

    if pull_request.body.count(_RELEASE_NOTES_START) != 1 or pull_request.body.count(_RELEASE_NOTES_END) != 1:
        errors.append("PR 正文必须包含且仅包含一组 release-notes 标记。")
        return errors

    release_notes = extract_release_notes(pull_request.body)
    if not release_notes:
        errors.append("Release Notes 不能为空；若无需发布，请添加 `release:skip` 标签。")
        return errors

    visible_lines = [
        line.strip() for line in release_notes.splitlines() if line.strip() and not line.strip().startswith("<!--")
    ]
    heading_counts: dict[str, int] = {}
    current_heading: str | None = None
    for line in visible_lines:
        if line in _RELEASE_HEADINGS:
            current_heading = line
            heading_counts.setdefault(line, 0)
        elif line.startswith("- ") and len(line) > 2 and current_heading is not None:
            heading_counts[current_heading] += 1
        else:
            errors.append(f"Release Notes 包含不支持的内容: `{line}`。")

    headings = set(heading_counts)
    if not headings:
        errors.append("Release Notes 至少需要一个 `###` 分类标题。")
    empty_headings = sorted(heading for heading, item_count in heading_counts.items() if item_count == 0)
    if empty_headings:
        errors.append(f"Release Notes 分类下至少需要一条 `- ` 列表项: {', '.join(empty_headings)}。")
    if determine_bump_type(pull_request.title, pull_request.labels) == "major" and "### 重大变更" not in headings:
        errors.append("major 版本变更必须包含 `### 重大变更` 小节。")
    return errors


def render_notes(pull_request: PullRequest, bump_type: BumpType) -> tuple[str, str]:
    """生成固定格式的变更日志正文和带幂等标记的 Release Notes。"""
    structured_notes = extract_release_notes(pull_request.body)
    if structured_notes:
        body = structured_notes
    else:
        if bump_type == "major":
            heading = "### 重大变更"
        elif bump_type == "minor":
            heading = "### 新增"
        elif _CONVENTIONAL_FIX_PATTERN.match(pull_request.title) or "bug" in {
            label.casefold() for label in pull_request.labels
        }:
            heading = "### 修复"
        else:
            heading = "### 变更"
        body = f"{heading}\n- {pull_request.title} ([#{pull_request.number}]({pull_request.url}))"

    notes = (
        f"<!-- release-pr: {pull_request.number} -->\n\n{body}\n\n完整变更见 [#{pull_request.number}]({pull_request.url})。\n"
    )
    return body, notes


def prepend_changelog(path: Path, version: str, release_date: str, body: str) -> None:
    """将新版本条目插入现有 Keep a Changelog 头部之后。"""
    content = path.read_text(encoding="utf-8")
    first_release = content.find("\n## [")
    if first_release < 0:
        raise ValueError(f"{path} 中未找到版本条目")
    entry = f"\n## [{version}] - {release_date}\n\n{body}\n"
    path.write_text(content[:first_release] + entry + content[first_release:], encoding="utf-8")


def prepare_release(
    event: Mapping[str, object],
    root: Path,
    release_date: str,
    existing_version: str | None = None,
) -> Release:
    """准备发布文件；已有版本仅重新生成 Release Notes，用于失败重跑恢复。"""
    pull_request = parse_pull_request(event)
    bump_type = determine_bump_type(pull_request.title, pull_request.labels)
    body, notes = render_notes(pull_request, bump_type)

    if existing_version is not None:
        if not _VERSION_PATTERN.fullmatch(existing_version):
            raise ValueError(f"不支持的已有版本格式: {existing_version}")
        version = existing_version
    else:
        version = update_versions(root, bump_type)
        prepend_changelog(root / "CHANGELOG.md", version, release_date, body)

    return Release(version=version, bump_type=bump_type, title=f"v{version}", notes=notes)


def _write_github_outputs(path: Path, release: Release) -> None:
    with path.open("a", encoding="utf-8") as output:
        output.write(f"new_version={release.version}\n")
        output.write(f"bump_type={release.bump_type}\n")
        output.write(f"release_title={release.title}\n")


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--event", type=Path, required=True, help="GitHub pull_request 事件 JSON")
    parser.add_argument("--notes-output", type=Path, required=True, help="Release Notes 输出路径")
    parser.add_argument("--root", type=Path, default=Path.cwd(), help="仓库根目录")
    parser.add_argument("--date", default=date.today().isoformat(), help="发布日期，格式为 YYYY-MM-DD")
    parser.add_argument("--existing-version", help="已提交的版本；提供后不再修改版本和 CHANGELOG")
    args = parser.parse_args(argv)

    event_value: object = json.loads(args.event.read_text(encoding="utf-8"))
    if not isinstance(event_value, dict):
        raise ValueError("GitHub 事件必须是 JSON 对象")
    event = cast(Mapping[str, object], event_value)
    release = prepare_release(event, args.root, args.date, args.existing_version)
    args.notes_output.write_text(release.notes, encoding="utf-8")

    github_output = os.environ.get("GITHUB_OUTPUT")
    if github_output:
        _write_github_outputs(Path(github_output), release)
    else:
        print(json.dumps(release.__dict__, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

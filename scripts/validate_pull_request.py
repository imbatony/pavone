"""校验 PR 是否符合项目的发布约定。"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Mapping, Sequence, cast

from scripts.prepare_release import parse_pull_request, validate_pull_request


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--event", type=Path, required=True, help="GitHub pull_request 事件 JSON")
    args = parser.parse_args(argv)

    event_value: object = json.loads(args.event.read_text(encoding="utf-8"))
    if not isinstance(event_value, dict):
        raise ValueError("GitHub 事件必须是 JSON 对象")
    pull_request = parse_pull_request(cast(Mapping[str, object], event_value), require_merged=False)
    errors = validate_pull_request(pull_request)
    for error in errors:
        print(f"::error::{error}")
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())

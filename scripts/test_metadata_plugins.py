#!/usr/bin/env python3
"""
PAVOne 元数据插件全量集成测试

通过真实网络请求验证所有元数据插件的功能和数据完整度。
使用方法:
    uv run python scripts/test_metadata_plugins.py
    uv run python scripts/test_metadata_plugins.py --output-dir /tmp
    uv run python scripts/test_metadata_plugins.py --format json
    uv run python scripts/test_metadata_plugins.py --format markdown
"""

import argparse
import json
import logging
import re
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple, cast

# Ensure pavone is importable
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

TEST_CASES: List[Tuple[str, str, str]] = [
    # (plugin_class_name, base_class, test_identifier)
    # === HtmlMetadataPlugin ===
    ("DahliaMetadata", "Html", "https://dahlia-av.jp/works/dldss339/"),
    ("FalenoMetadata", "Html", "https://faleno.jp/top/works/fns196/"),
    ("MyWifeMetadata", "Html", "https://mywife.cc/teigaku/model/no/1894"),
    ("MgstageMetadata", "Html", "https://www.mgstage.com/product/product_detail/200GANA-3191/"),
    ("GetchuMetadata", "Html", "https://dl.getchu.com/i/item4043542"),
    ("DugaMetadata", "Html", "https://duga.jp/ppv/mousouzoku2-1275/"),
    ("Jav321Metadata", "Html", "https://www.jav321.com/video/snos00115"),
    ("JavbusMetadata", "Html", "https://www.javbus.com/ja/SSIS-001"),
    ("TokyoHotMetadata", "Html", "https://my.tokyo-hot.com/product/n0697/?lang=ja"),
    ("HeydougaMetadata", "Html", "https://www.heydouga.com/moviepages/4386/088/index.html"),
    ("AvEntertainmentsMetadata", "Html", "https://www.aventertainments.com/dvd/detail?pro=95843&lang=2&culture=ja-JP&cat=29"),
    ("GcolleMetadata", "Html", "https://gcolle.net/product_info.php/products_id/847256"),
    ("JavfreeMetadata", "Html", "https://javfree.me/384459/venx-281"),
    ("PcolleMetadata", "Html", "https://www.pcolle.com/product/detail/?product_id=27567069de31e4f23ce"),
    ("CaribbeancomMetadata", "Html", "https://www.caribbeancom.com/moviepages/033026-001/index.html"),
    ("FanzaMetadata", "Html", "https://www.dmm.co.jp/digital/videoa/-/detail/=/cid=midv00047/"),
    ("AvBaseMetadata", "Html", "https://www.avbase.net/works/SSIS-001"),
    # === ApiMetadataPlugin ===
    ("MuramuraMetadata", "Api", "https://www.muramura.tv/movies/040826_1229/"),
    ("PacopacomamaMetadata", "Api", "https://www.pacopacomama.com/movies/040726_100/"),
    ("OnePondoMetadata", "Api", "https://www.1pondo.tv/movies/032417_504/"),
    ("TenMusumeMetadata", "Api", "https://www.10musume.com/movies/040726_01/"),
    # === JsonLdMetadataPlugin ===
    ("C0930Metadata", "JsonLd", "https://www.c0930.com/moviepages/ki220913/index.html"),
    ("H0930Metadata", "JsonLd", "https://www.h0930.com/moviepages/ori1234/index.html"),
    ("H4610Metadata", "JsonLd", "https://www.h4610.com/moviepages/gol123/index.html"),
    ("HeyzoMetadata", "JsonLd", "https://www.heyzo.com/moviepages/3456/index.html"),
    # === FC2 Family (Html via FC2BaseMetadata) ===
    ("Fc2ppvDbMetadata", "Html/FC2", "https://fc2ppv-db.com/ja/videos/4778286"),
    ("SupFC2Metadata", "Html/FC2", "FC2-PPV-1482027"),
    ("PPVDataBankMetadata", "Html/FC2", "FC2-2941579"),
]


def _load_field_weights() -> Dict[str, int]:
    try:
        from pavone.models.constants import METADATA_SCORE_WEIGHTS

        return dict(METADATA_SCORE_WEIGHTS)
    except ImportError:
        return {
            "title": 1,
            "actors": 13,
            "cover": 11,
            "plot": 16,
            "premiered": 9,
            "genres": 9,
            "tags": 11,
            "studio": 11,
            "runtime": 1,
            "rating": 5,
            "director": 5,
            "thumbnail": 8,
        }


FIELD_WEIGHTS = _load_field_weights()

QUALITY_GATES: Dict[str, Dict[str, Any]] = {
    "TokyoHotMetadata": {
        "min_score": 70,
        "required_fields": ("title", "cover", "premiered", "studio"),
    },
    "JavfreeMetadata": {
        "min_score": 25,
        "required_fields": ("title", "cover", "premiered", "director"),
    },
    "PPVDataBankMetadata": {
        "min_score": 30,
        "required_fields": ("title", "cover", "premiered", "studio"),
    },
    "MyWifeMetadata": {
        "min_score": 45,
        "required_fields": ("title", "cover", "studio"),
    },
    "PcolleMetadata": {
        "min_score": 50,
        "required_fields": ("title", "cover", "premiered", "studio", "plot"),
    },
}
SIGNIFICANT_SCORE_DROP = 10
TRACKING_ISSUE_URL = "https://github.com/imbatony/pavone/issues/126"
STATUS_SEVERITY = {
    "OK": 0,
    "DEGRADED": 1,
    "SKIP": 2,
    "FAIL": 3,
    "NOT_FOUND": 3,
    "ERROR": 4,
}


def classify_failure(diagnostic: Dict[str, Any]) -> str:
    """将提取失败归类为可操作的故障类型。"""
    stage = str(diagnostic.get("stage") or "")
    error = str(diagnostic.get("error") or "").casefold()
    status = diagnostic.get("http_status")
    if not isinstance(status, int):
        status_match = re.search(r"\b([45]\d{2})\b", error)
        status = int(status_match.group(1)) if status_match else None

    if status in (401, 403, 429) or any(marker in error for marker in ("cloudflare", "forbidden", "access denied")):
        return "BLOCKED"
    if status in (404, 410) or stage == "resolve":
        return "STALE_CASE"
    if (
        isinstance(status, int)
        and status >= 500
        or any(
            marker in error
            for marker in (
                "timeout",
                "timed out",
                "connection",
                "dns",
                "name resolution",
                "network",
                "proxy",
                "ssl",
            )
        )
    ):
        return "NETWORK"
    if stage == "parse":
        return "PARSE"
    return "EMPTY_RESULT"


def score_metadata(metadata_obj: Any) -> Tuple[int, Dict[str, bool]]:
    """根据元数据丰富度打分 (0-100)"""
    if metadata_obj is None:
        return 0, {}
    fields: Dict[str, bool] = {}
    score = 0
    for field, weight in FIELD_WEIGHTS.items():
        val = getattr(metadata_obj, field, None)
        has_value = val is not None and val != "" and val != [] and val != 0
        if isinstance(val, list) and not val:
            has_value = False
        fields[field] = has_value
        if has_value:
            score += weight
    return score, fields


def _has_meaningful_title(metadata_obj: Any) -> bool:
    """标题必须包含代码以外的有效内容。"""
    title = str(getattr(metadata_obj, "title", "") or "").strip()
    code = str(getattr(metadata_obj, "code", "") or "").strip()
    if not title:
        return False

    def normalize(value: str) -> str:
        return re.sub(r"[\W_]+", "", value.casefold())

    normalized_code = normalize(code)
    if not normalized_code:
        return True
    return bool(normalize(title).replace(normalized_code, ""))


def evaluate_quality_gate(plugin_name: str, metadata_obj: Any, score: int, fields: Dict[str, bool]) -> Dict[str, Any]:
    """评估插件的最低分和关键字段门禁。"""
    gate = QUALITY_GATES.get(plugin_name)
    if gate is None:
        return {}

    required_fields = cast(Tuple[str, ...], gate["required_fields"])
    missing_fields = [field for field in required_fields if not fields.get(field, False)]
    if "title" in required_fields and not _has_meaningful_title(metadata_obj) and "title" not in missing_fields:
        missing_fields.append("title")
    min_score = cast(int, gate["min_score"])
    return {
        "min_score": min_score,
        "required_fields": list(required_fields),
        "missing_fields": missing_fields,
        "passed": score >= min_score and not missing_fields,
    }


def apply_previous_results(results: List[Dict[str, Any]], previous_data: Dict[str, Any]) -> None:
    """把上一份结果的状态和评分变化附加到当前结果。"""
    previous_by_plugin: Dict[str, Dict[str, Any]] = {}
    previous_results = previous_data.get("results")
    if isinstance(previous_results, list):
        for result_value in cast(List[object], previous_results):
            if not isinstance(result_value, dict):
                continue
            previous_result = cast(Dict[str, Any], result_value)
            plugin_name = previous_result.get("plugin")
            if plugin_name:
                previous_by_plugin[str(plugin_name)] = previous_result
    for result in results:
        previous = previous_by_plugin.get(str(result["plugin"]))
        if previous is None:
            result.update(
                {
                    "previous_status": None,
                    "previous_score": None,
                    "status_change": "NEW",
                    "score_change": None,
                }
            )
            continue

        previous_status = str(previous.get("status") or "")
        previous_score_value = previous.get("score")
        previous_score = previous_score_value if isinstance(previous_score_value, int) else None
        current_status = str(result["status"])
        previous_severity = STATUS_SEVERITY.get(previous_status, 4)
        current_severity = STATUS_SEVERITY.get(current_status, 4)
        if current_severity > previous_severity:
            status_change = "REGRESSED"
        elif current_status == "OK" and previous_status != "OK":
            status_change = "RECOVERED"
        elif previous_status != current_status:
            status_change = "CHANGED"
        else:
            status_change = "UNCHANGED"
        result.update(
            {
                "previous_status": previous_status,
                "previous_score": previous_score,
                "status_change": status_change,
                "score_change": result["score"] - previous_score if previous_score is not None else None,
            }
        )


def load_previous_results(path: Path) -> Dict[str, Any]:
    """读取并校验上一份 JSON 测试结果。"""
    with path.open("r", encoding="utf-8") as file:
        data: object = json.load(file)
    if not isinstance(data, dict):
        raise ValueError(f"上一份结果格式无效: {path}")
    typed_data = cast(Dict[str, Any], data)
    if not isinstance(typed_data.get("results"), list):
        raise ValueError(f"上一份结果格式无效: {path}")
    return typed_data


def select_test_cases(plugin_names: Optional[Set[str]]) -> List[Tuple[str, str, str]]:
    """按插件名筛选测试样例，并拒绝拼写错误。"""
    if not plugin_names:
        return TEST_CASES
    known_plugins = {case[0] for case in TEST_CASES}
    unknown_plugins = sorted(plugin_names - known_plugins)
    if unknown_plugins:
        raise ValueError(f"未知插件: {', '.join(unknown_plugins)}")
    return [case for case in TEST_CASES if case[0] in plugin_names]


def _get_diagnostic(plugin: Any) -> Dict[str, Any]:
    getter = getattr(plugin, "get_last_diagnostic", None)
    if callable(getter):
        diagnostic = getter()
        if isinstance(diagnostic, dict):
            return cast(Dict[str, Any], diagnostic)
    return {}


def _failed_result(
    plugin_name: str,
    base_class: str,
    identifier: str,
    elapsed: float,
    attempts: int,
    diagnostic: Dict[str, Any],
    status: str = "FAIL",
) -> Dict[str, Any]:
    error = str(diagnostic.get("error") or "extract_metadata returned None")
    return {
        "plugin": plugin_name,
        "base_class": base_class,
        "identifier": identifier,
        "status": status,
        "score": 0,
        "time_ms": round(elapsed),
        "fields": {},
        "error": error[:240],
        "failure_type": classify_failure(diagnostic),
        "failure_stage": diagnostic.get("stage") or "unknown",
        "exception_type": diagnostic.get("exception_type"),
        "http_status": diagnostic.get("http_status"),
        "final_url": diagnostic.get("final_url"),
        "attempts": attempts,
    }


def run_tests(plugin_names: Optional[Set[str]] = None, retries: int = 0) -> List[Dict[str, Any]]:
    logging.getLogger("pavone").setLevel(logging.ERROR)

    from pavone.manager.plugin_manager import PluginManager

    pm = PluginManager()
    pm.load_plugins()
    plugin_map = {p.__class__.__name__: p for p in pm.metadata_plugins}

    results: List[Dict[str, Any]] = []
    for plugin_name, base_class, identifier in select_test_cases(plugin_names):
        plugin = plugin_map.get(plugin_name)
        if not plugin:
            results.append(
                {
                    "plugin": plugin_name,
                    "base_class": base_class,
                    "identifier": identifier,
                    "status": "NOT_FOUND",
                    "score": 0,
                    "time_ms": 0,
                    "fields": {},
                    "error": "Plugin not loaded",
                    "failure_type": "EMPTY_RESULT",
                    "failure_stage": "load",
                    "attempts": 0,
                }
            )
            continue

        if not plugin.can_extract(identifier):
            results.append(
                {
                    "plugin": plugin_name,
                    "base_class": base_class,
                    "identifier": identifier,
                    "status": "SKIP",
                    "score": 0,
                    "time_ms": 0,
                    "fields": {},
                    "error": "can_extract returned False",
                    "failure_type": "STALE_CASE",
                    "failure_stage": "resolve",
                    "attempts": 0,
                }
            )
            continue

        start = time.time()
        attempts = 0
        metadata_obj = None
        diagnostic: Dict[str, Any] = {}
        runner_error: Optional[Exception] = None
        while attempts <= retries and metadata_obj is None:
            attempts += 1
            try:
                metadata_obj = plugin.extract_metadata(identifier)
                diagnostic = _get_diagnostic(plugin)
            except Exception as e:
                runner_error = e
                diagnostic = {
                    "stage": "runner",
                    "error": str(e),
                    "exception_type": type(e).__name__,
                }
                break

        elapsed = (time.time() - start) * 1000
        if runner_error is not None:
            results.append(
                _failed_result(
                    plugin_name,
                    base_class,
                    identifier,
                    elapsed,
                    attempts,
                    diagnostic,
                    status="ERROR",
                )
            )
        elif metadata_obj is None:
            results.append(_failed_result(plugin_name, base_class, identifier, elapsed, attempts, diagnostic))
        else:
            score, fields = score_metadata(metadata_obj)
            quality_gate = evaluate_quality_gate(plugin_name, metadata_obj, score, fields)
            gate_passed = quality_gate.get("passed", True)
            missing_fields = quality_gate.get("missing_fields", [])
            gate_error_parts: List[str] = []
            if quality_gate and score < quality_gate["min_score"]:
                gate_error_parts.append(f"评分 {score} 低于最低分 {quality_gate['min_score']}")
            if missing_fields:
                gate_error_parts.append(f"缺少关键字段: {', '.join(missing_fields)}")
            results.append(
                {
                    "plugin": plugin_name,
                    "base_class": base_class,
                    "identifier": identifier,
                    "status": "OK" if gate_passed else "DEGRADED",
                    "score": score,
                    "time_ms": round(elapsed),
                    "fields": fields,
                    "error": None if gate_passed else "；".join(gate_error_parts),
                    "title": getattr(metadata_obj, "title", ""),
                    "failure_type": None if gate_passed else "QUALITY_GATE",
                    "failure_stage": None if gate_passed else "quality",
                    "attempts": attempts,
                    "quality_gate": quality_gate or None,
                }
            )

        r = results[-1]
        status_map = {
            "OK": "  OK",
            "DEGRADED": " DEG",
            "FAIL": "FAIL",
            "ERROR": " ERR",
            "SKIP": "SKIP",
            "NOT_FOUND": " N/A",
        }
        diagnostic_suffix = f" {r.get('failure_type', '')}/{r.get('failure_stage', '')}" if r["status"] != "OK" else ""
        console_line = (
            f"  [{status_map.get(r['status'], '????')}] [{r['time_ms']:>5}ms] "
            + f"{r['plugin']:30s} score={r['score']:>3}{diagnostic_suffix}"
        )
        print(
            console_line,
            flush=True,
        )

    return results


def generate_markdown(data: Dict[str, Any]) -> str:
    results = data["results"]
    ok = [r for r in results if r["status"] == "OK"]
    degraded = [r for r in results if r["status"] == "DEGRADED"]
    fail = [r for r in results if r["status"] == "FAIL"]
    error = [r for r in results if r["status"] == "ERROR"]
    skip = [r for r in results if r["status"] == "SKIP"]

    lines = [
        f"# PAVOne v{data['version']} — 元数据插件每日测试报告",
        f"\n**测试时间**: {data['timestamp']}",
        f"**总耗时**: {data['total_time_s']}s",
        f"**测试插件数**: {len(results)}",
        f"**跟踪 Issue**: [#{TRACKING_ISSUE_URL.rsplit('/', 1)[-1]}]({TRACKING_ISSUE_URL})",
        "",
        "## 概览",
        "",
        "| 状态 | 数量 |",
        "|------|------|",
        f"| ✅ 成功 | {len(ok)} |",
        f"| ⚠️ 质量降级 | {len(degraded)} |",
        f"| ❌ 提取失败 | {len(fail)} |",
        f"| 💥 异常 | {len(error)} |",
        f"| ⏭️ 跳过 | {len(skip)} |",
    ]

    if ok:
        avg_score = sum(r["score"] for r in ok) / len(ok)
        avg_time = sum(r["time_ms"] for r in ok) / len(ok)
        lines.append(f"\n**成功插件平均完整度评分**: {avg_score:.1f}/100")
        lines.append(f"**成功插件平均响应时间**: {avg_time:.0f}ms")

    has_previous = any("previous_status" in result for result in results)
    if has_previous:
        regressions = [result for result in results if result.get("status_change") == "REGRESSED"]
        recoveries = [result for result in results if result.get("status_change") == "RECOVERED"]
        score_drops = [
            result
            for result in results
            if isinstance(result.get("score_change"), int) and result["score_change"] <= -SIGNIFICANT_SCORE_DROP
        ]
        lines += ["", "## 趋势", ""]
        if not regressions and not recoveries and not score_drops:
            lines.append("- 无新增失败、恢复或显著降分。")
        for result in regressions:
            lines.append(f"- 🚨 **新增失败/降级**: {result['plugin']} ({result['previous_status']} → {result['status']})")
        for result in recoveries:
            lines.append(f"- 🎉 **恢复**: {result['plugin']} ({result['previous_status']} → {result['status']})")
        for result in score_drops:
            lines.append(
                "- 📉 **显著降分**: {} ({} → {}, {:+d})".format(
                    result["plugin"],
                    result["previous_score"],
                    result["score"],
                    result["score_change"],
                )
            )

    lines += [
        "",
        "## 详细结果",
        "",
        "| # | 插件 | 基类 | 状态 | 分类/阶段 | 评分 | 耗时 | 说明 |",
        "|---|------|------|------|-----------|------|------|------|",
    ]

    for i, r in enumerate(results, 1):
        icon = {"OK": "✅", "DEGRADED": "⚠️", "FAIL": "❌", "ERROR": "💥", "SKIP": "⏭️", "NOT_FOUND": "❓"}[r["status"]]
        note = r.get("title", "")[:40] if r["status"] == "OK" else (r.get("error", "")[:50] or "")
        failure = f"{r.get('failure_type', '')}/{r.get('failure_stage', '')}" if r["status"] != "OK" else "-"
        lines.append(
            "| {} | {} | {} | {} | {} | {} | {}ms | {} |".format(
                i,
                r["plugin"],
                r["base_class"],
                icon,
                failure,
                r["score"],
                r["time_ms"],
                note,
            )
        )

    if ok:
        lines += [
            "",
            "## 字段覆盖率（成功插件）",
            "",
            "| 字段 | 权重 | 覆盖数 | 覆盖率 |",
            "|------|------|--------|--------|",
        ]
        for field in FIELD_WEIGHTS:
            count = sum(1 for r in ok if r["fields"].get(field, False))
            pct = count / len(ok) * 100
            lines.append(f"| {field} | {FIELD_WEIGHTS[field]} | {count}/{len(ok)} | {pct:.0f}% |")

        lines += ["", "## 评分排名（成功插件）", "", "| # | 插件 | 基类 | 评分 | 耗时 |", "|---|------|------|------|------|"]
        for i, r in enumerate(sorted(ok, key=lambda x: (-x["score"], x["time_ms"])), 1):
            lines.append(f"| {i} | {r['plugin']} | {r['base_class']} | {r['score']}/100 | {r['time_ms']}ms |")

    if degraded or fail or error:
        lines += ["", "## 降级/失败/异常插件", ""]
        for r in degraded + fail + error:
            context: List[str] = []
            if r.get("http_status") is not None:
                context.append(f"HTTP {r['http_status']}")
            if r.get("final_url"):
                context.append(str(r["final_url"]))
            context_text = f"；{'；'.join(context)}" if context else ""
            lines.append(
                "- **{}** ({}): `{}/{}` {}{}".format(
                    r["plugin"],
                    r["base_class"],
                    r.get("failure_type", "UNKNOWN"),
                    r.get("failure_stage", "unknown"),
                    r["error"],
                    context_text,
                )
            )

    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(description="PAVOne 元数据插件全量集成测试")
    parser.add_argument("--output-dir", type=str, default=None, help="输出目录 (默认: 当前目录)")
    parser.add_argument("--format", type=str, choices=["json", "markdown", "both"], default="both", help="输出格式")
    parser.add_argument("--plugin", action="append", dest="plugins", help="仅运行指定插件，可重复提供")
    parser.add_argument("--retries", type=int, choices=range(0, 3), default=0, help="失败重试次数（0-2）")
    parser.add_argument("--previous-results", type=Path, default=None, help="上一份 JSON 结果，用于生成趋势")
    args = parser.parse_args()

    output_dir = Path(args.output_dir) if args.output_dir else Path.cwd()
    output_dir.mkdir(parents=True, exist_ok=True)

    # Get version
    try:
        from pavone import __version__

        version = __version__
    except Exception:
        version = "unknown"

    print(f"PAVOne v{version} — 元数据插件全量测试")
    print("=" * 60)

    total_start = time.time()
    try:
        results = run_tests(set(args.plugins) if args.plugins else None, retries=args.retries)
    except ValueError as e:
        parser.error(str(e))
    total_elapsed = time.time() - total_start
    if args.previous_results is not None:
        try:
            apply_previous_results(results, load_previous_results(args.previous_results))
        except (OSError, ValueError, json.JSONDecodeError) as error:
            print(f"警告: 无法读取上一份结果，跳过趋势比较: {error}", file=sys.stderr)

    data: Dict[str, Any] = {
        "version": version,
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "total_time_s": round(total_elapsed, 1),
        "results": results,
    }

    ok = [r for r in results if r["status"] == "OK"]
    degraded = [r for r in results if r["status"] == "DEGRADED"]
    fail = [r for r in results if r["status"] == "FAIL"]
    error = [r for r in results if r["status"] == "ERROR"]

    print()
    print("=" * 60)
    print(f"总计: {len(results)} | 成功: {len(ok)} | 降级: {len(degraded)} | 失败: {len(fail)} | 异常: {len(error)}")
    print(f"总耗时: {total_elapsed:.1f}s")
    if ok:
        avg_score = sum(r["score"] for r in ok) / len(ok)
        print(f"平均评分: {avg_score:.1f}/100")
    print("=" * 60)

    if args.format in ("json", "both"):
        json_path = output_dir / "metadata_test_results.json"
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print(f"JSON: {json_path}")

    if args.format in ("markdown", "both"):
        md_path = output_dir / "metadata_test_report.md"
        with open(md_path, "w", encoding="utf-8") as f:
            f.write(generate_markdown(data))
        print(f"Markdown: {md_path}")

    # Exit with failure if any errors
    sys.exit(1 if error else 0)


if __name__ == "__main__":
    main()

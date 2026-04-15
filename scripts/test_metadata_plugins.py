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
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

# Ensure pavone is importable
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

# fmt: off
TEST_CASES: List[Tuple[str, str, str]] = [
    # (plugin_class_name, base_class, test_identifier)
    # === HtmlMetadataPlugin ===
    ("DahliaMetadata",              "Html",     "https://dahlia-av.jp/works/dldss339/"),
    ("FalenoMetadata",              "Html",     "https://faleno.jp/top/works/fns196/"),
    ("MyWifeMetadata",              "Html",     "https://mywife.cc/teigaku/model/no/1894"),
    ("MgstageMetadata",             "Html",     "https://www.mgstage.com/product/product_detail/200GANA-3191/"),
    ("GetchuMetadata",              "Html",     "https://dl.getchu.com/i/item4043542"),
    ("MadouquMetadata",             "Html",     "https://madouqu.com/video/mm-103/"),
    ("DugaMetadata",                "Html",     "https://duga.jp/ppv/mousouzoku2-1275/"),
    ("Jav321Metadata",              "Html",     "https://www.jav321.com/video/snos00115"),
    ("JavbusMetadata",              "Html",     "https://www.javbus.com/ja/SSIS-001"),
    ("TokyoHotMetadata",            "Html",     "https://my.tokyo-hot.com/product/20032/?lang=ja"),
    ("HeydougaMetadata",            "Html",     "https://www.heydouga.com/moviepages/4030/2826/index.html"),
    ("AvEntertainmentsMetadata",    "Html",     "https://www.aventertainments.com/dvd/detail?pro=95843&lang=2&culture=ja-JP&cat=29"),
    ("GcolleMetadata",              "Html",     "https://gcolle.net/product_info.php/products_id/1001529"),
    ("JavfreeMetadata",             "Html",     "https://javfree.me/384459/venx-281"),
    ("PcolleMetadata",              "Html",     "https://www.pcolle.com/product/detail/?product_id=27567069de31e4f23ce"),
    ("CaribbeancomMetadata",        "Html",     "https://www.caribbeancom.com/moviepages/033026-001/index.html"),
    ("FanzaMetadata",               "Html",     "https://www.dmm.co.jp/digital/videoa/-/detail/=/cid=midv00047/"),
    ("AvBaseMetadata",              "Html",     "https://www.avbase.net/works/SSIS-001"),
    # === ApiMetadataPlugin ===
    ("MuramuraMetadata",            "Api",      "https://www.muramura.tv/movies/040826_1229/"),
    ("PacopacomamaMetadata",        "Api",      "https://www.pacopacomama.com/movies/040726_100/"),
    ("OnePondoMetadata",            "Api",      "https://www.1pondo.tv/movies/032417_504/"),
    ("TenMusumeMetadata",           "Api",      "https://www.10musume.com/movies/040726_01/"),
    # === JsonLdMetadataPlugin ===
    ("C0930Metadata",               "JsonLd",   "https://www.c0930.com/moviepages/ki220913/index.html"),
    ("H0930Metadata",               "JsonLd",   "https://www.h0930.com/moviepages/ori1234/index.html"),
    ("H4610Metadata",               "JsonLd",   "https://www.h4610.com/moviepages/gol123/index.html"),
    ("Fc2HubMetadata",              "JsonLd",   "https://javten.com/video/2045529/id4848768/%E3%80%90%E3%83%90%E3%83%AC%E3%83%B3%E3%82%BF%E3%82%A4%E3%83%B3%E3%82%BB%E3%83%BC%E3%83%AB%E2%91%A1%E3%80%91"),
    ("HeyzoMetadata",               "JsonLd",   "https://www.heyzo.com/moviepages/3456/index.html"),
    # === FC2 Family (Html via FC2BaseMetadata) ===
    ("Fc2PpvdbMetadata",            "Html/FC2", "https://fc2ppvdb.com/articles/1482027"),
    ("SupFC2Metadata",              "Html/FC2", "FC2-PPV-1482027"),
    ("PPVDataBankMetadata",         "Html/FC2", "FC2-2941579"),
]
# fmt: on

FIELD_WEIGHTS: Dict[str, int] = {
    "title": 15,
    "code": 10,
    "actors": 12,
    "studio": 8,
    "tags": 8,
    "premiered": 10,
    "runtime": 8,
    "cover": 10,
    "plot": 8,
    "rating": 5,
    "director": 3,
    "thumbnail": 3,
}


def score_metadata(metadata_obj: Any) -> Tuple[int, Dict[str, bool]]:
    """根据元数据丰富度打分 (0-100)"""
    if metadata_obj is None:
        return 0, {}
    fields: Dict[str, bool] = {}
    score = 0
    for field, weight in FIELD_WEIGHTS.items():
        val = getattr(metadata_obj, field, None)
        has_value = val is not None and val != "" and val != [] and val != 0
        if isinstance(val, list) and len(val) == 0:
            has_value = False
        fields[field] = has_value
        if has_value:
            score += weight
    return score, fields


def run_tests() -> List[Dict[str, Any]]:
    logging.getLogger("pavone").setLevel(logging.ERROR)

    from pavone.manager.plugin_manager import PluginManager

    pm = PluginManager()
    pm.load_plugins()
    plugin_map = {p.__class__.__name__: p for p in pm.metadata_plugins}

    results: List[Dict[str, Any]] = []
    for plugin_name, base_class, identifier in TEST_CASES:
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
                }
            )
            continue

        start = time.time()
        try:
            metadata_obj = plugin.extract_metadata(identifier)
            elapsed = (time.time() - start) * 1000
            if metadata_obj is None:
                results.append(
                    {
                        "plugin": plugin_name,
                        "base_class": base_class,
                        "identifier": identifier,
                        "status": "FAIL",
                        "score": 0,
                        "time_ms": round(elapsed),
                        "fields": {},
                        "error": "extract_metadata returned None",
                    }
                )
            else:
                score, fields = score_metadata(metadata_obj)
                results.append(
                    {
                        "plugin": plugin_name,
                        "base_class": base_class,
                        "identifier": identifier,
                        "status": "OK",
                        "score": score,
                        "time_ms": round(elapsed),
                        "fields": fields,
                        "error": None,
                        "title": getattr(metadata_obj, "title", ""),
                    }
                )
        except Exception as e:
            elapsed = (time.time() - start) * 1000
            results.append(
                {
                    "plugin": plugin_name,
                    "base_class": base_class,
                    "identifier": identifier,
                    "status": "ERROR",
                    "score": 0,
                    "time_ms": round(elapsed),
                    "fields": {},
                    "error": str(e)[:120],
                }
            )

        r = results[-1]
        status_map = {"OK": "  OK", "FAIL": "FAIL", "ERROR": " ERR", "SKIP": "SKIP", "NOT_FOUND": " N/A"}
        print(
            f"  [{status_map.get(r['status'], '????')}] [{r['time_ms']:>5}ms] "
            f"{r['plugin']:30s} score={r['score']:>3}",
            flush=True,
        )

    return results


def generate_markdown(data: Dict[str, Any]) -> str:
    results = data["results"]
    ok = [r for r in results if r["status"] == "OK"]
    fail = [r for r in results if r["status"] == "FAIL"]
    error = [r for r in results if r["status"] == "ERROR"]
    skip = [r for r in results if r["status"] == "SKIP"]

    lines = [
        f"# PAVOne v{data['version']} — 元数据插件每日测试报告",
        f"\n**测试时间**: {data['timestamp']}",
        f"**总耗时**: {data['total_time_s']}s",
        f"**测试插件数**: {len(results)}",
        "",
        "## 概览",
        "",
        "| 状态 | 数量 |",
        "|------|------|",
        f"| ✅ 成功 | {len(ok)} |",
        f"| ❌ 提取失败 | {len(fail)} |",
        f"| 💥 异常 | {len(error)} |",
        f"| ⏭️ 跳过 | {len(skip)} |",
    ]

    if ok:
        avg_score = sum(r["score"] for r in ok) / len(ok)
        avg_time = sum(r["time_ms"] for r in ok) / len(ok)
        lines.append(f"\n**成功插件平均完整度评分**: {avg_score:.1f}/100")
        lines.append(f"**成功插件平均响应时间**: {avg_time:.0f}ms")

    lines += ["", "## 详细结果", "", "| # | 插件 | 基类 | 状态 | 评分 | 耗时 | 说明 |", "|---|------|------|------|------|------|------|"]

    for i, r in enumerate(results, 1):
        icon = {"OK": "✅", "FAIL": "❌", "ERROR": "💥", "SKIP": "⏭️", "NOT_FOUND": "❓"}[r["status"]]
        note = r.get("title", "")[:40] if r["status"] == "OK" else (r.get("error", "")[:50] or "")
        lines.append(f"| {i} | {r['plugin']} | {r['base_class']} | {icon} | {r['score']} | {r['time_ms']}ms | {note} |")

    if ok:
        lines += ["", "## 字段覆盖率（成功插件）", "", "| 字段 | 权重 | 覆盖数 | 覆盖率 |", "|------|------|--------|--------|"]
        for field in FIELD_WEIGHTS:
            count = sum(1 for r in ok if r["fields"].get(field, False))
            pct = count / len(ok) * 100
            lines.append(f"| {field} | {FIELD_WEIGHTS[field]} | {count}/{len(ok)} | {pct:.0f}% |")

        lines += ["", "## 评分排名（成功插件）", "", "| # | 插件 | 基类 | 评分 | 耗时 |", "|---|------|------|------|------|"]
        for i, r in enumerate(sorted(ok, key=lambda x: (-x["score"], x["time_ms"])), 1):
            lines.append(f"| {i} | {r['plugin']} | {r['base_class']} | {r['score']}/100 | {r['time_ms']}ms |")

    if fail or error:
        lines += ["", "## 失败/异常插件", ""]
        for r in fail + error:
            lines.append(f"- **{r['plugin']}** ({r['base_class']}): {r['error']}")

    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="PAVOne 元数据插件全量集成测试")
    parser.add_argument("--output-dir", type=str, default=None, help="输出目录 (默认: 当前目录)")
    parser.add_argument("--format", type=str, choices=["json", "markdown", "both"], default="both", help="输出格式")
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
    results = run_tests()
    total_elapsed = time.time() - total_start

    data = {
        "version": version,
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "total_time_s": round(total_elapsed, 1),
        "results": results,
    }

    ok = [r for r in results if r["status"] == "OK"]
    fail = [r for r in results if r["status"] == "FAIL"]
    error = [r for r in results if r["status"] == "ERROR"]

    print()
    print("=" * 60)
    print(f"总计: {len(results)} | 成功: {len(ok)} | 失败: {len(fail)} | 异常: {len(error)}")
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

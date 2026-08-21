#!/usr/bin/env python3
"""Schema validation for a Phase 2 daily-panel output pair (marker + CSV).

Pure filesystem + parsing. Makes NO network calls of any kind, which is what
lets the deterministic test suite exercise it with sockets blocked.

Exit codes are the contract the unattended runner depends on:

    0  all checks passed -- output is safe to commit
    6  a required artifact is missing (marker or final CSV)
    7  an artifact exists but failed schema validation

The runner must never stage anything unless this returns 0.

    python phase2_panel_validate.py --marker <path> --csv <path> [--json]
"""
from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path

EXIT_OK, EXIT_MISSING, EXIT_SCHEMA = 0, 6, 7

EXPECTED_ROWS = 24
EXPECTED_COLS = 92
SIX_FIELDS = ("gst_zscore", "wiki_zscore", "implied_volatility",
              "realized_vol", "price", "volume")


def validate(marker_path: Path, csv_path: Path) -> tuple[int, list[tuple[str, bool, str]]]:
    """Return (exit_code, [(check_name, passed, detail), ...])."""
    checks: list[tuple[str, bool, str]] = []

    if not marker_path.is_file():
        return EXIT_MISSING, [("completion marker exists", False, str(marker_path))]
    if not csv_path.is_file():
        # The panel writes the final CSV only on a clean 24/24, so its absence
        # is the normal signal for a PARTIAL run -- missing, not malformed.
        return EXIT_MISSING, [("final CSV exists", False, str(csv_path))]
    checks.append(("completion marker exists", True, marker_path.name))
    checks.append(("final CSV exists", True, csv_path.name))

    try:
        marker = json.loads(marker_path.read_text(encoding="utf-8"))
    except Exception as e:                                        # noqa: BLE001
        return EXIT_SCHEMA, checks + [("marker parses as JSON", False, f"{type(e).__name__}: {e}")]
    checks.append(("marker parses as JSON", True, ""))

    with csv_path.open(newline="", encoding="utf-8") as fh:
        rows = list(csv.DictReader(fh))

    def add(name: str, ok: bool, detail: str = "") -> None:
        checks.append((name, bool(ok), detail))

    add("marker status is COMPLETE", marker.get("status") == "COMPLETE",
        str(marker.get("status")))
    add(f"marker row_count == {EXPECTED_ROWS}", marker.get("row_count") == EXPECTED_ROWS,
        str(marker.get("row_count")))
    add(f"marker unique_ticker_count == {EXPECTED_ROWS}",
        marker.get("unique_ticker_count") == EXPECTED_ROWS, str(marker.get("unique_ticker_count")))
    add(f"marker all_six_fields_clean_count == {EXPECTED_ROWS}",
        marker.get("all_six_fields_clean_count") == EXPECTED_ROWS,
        str(marker.get("all_six_fields_clean_count")))

    failed_sources = marker.get("failed_source_counts") or {}
    add("marker failed_source_counts all zero",
        all(v == 0 for v in failed_sources.values()),
        ", ".join(f"{k}={v}" for k, v in failed_sources.items() if v) or "all zero")

    completeness = marker.get("field_completeness_pct") or {}
    for f in SIX_FIELDS:
        add(f"marker {f} == 100%", completeness.get(f) == 100.0, str(completeness.get(f)))

    add(f"csv data rows == {EXPECTED_ROWS}", len(rows) == EXPECTED_ROWS, str(len(rows)))
    if rows:
        add(f"csv column count == {EXPECTED_COLS}", len(rows[0]) == EXPECTED_COLS, str(len(rows[0])))
        add(f"csv unique tickers == {EXPECTED_ROWS}",
            len({r.get("ticker") for r in rows}) == EXPECTED_ROWS,
            str(len({r.get("ticker") for r in rows})))
        for f in SIX_FIELDS:
            n = sum(1 for r in rows if (r.get(f) or "").strip())
            add(f"csv {f} non-null on all rows", n == len(rows), f"{n}/{len(rows)}")
    else:
        add("csv has rows", False, "0")

    code = EXIT_OK if all(ok for _, ok, _ in checks) else EXIT_SCHEMA
    return code, checks


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="phase2_panel_validate")
    ap.add_argument("--marker", required=True)
    ap.add_argument("--csv", required=True)
    ap.add_argument("--json", action="store_true", help="emit machine-readable result")
    a = ap.parse_args(argv)

    code, checks = validate(Path(a.marker), Path(a.csv))
    if a.json:
        print(json.dumps({
            "exit_code": code,
            "passed": sum(1 for _, ok, _ in checks if ok),
            "total": len(checks),
            "checks": [{"name": n, "passed": ok, "detail": d} for n, ok, d in checks],
        }, indent=2))
    else:
        for name, ok, detail in checks:
            print(f"  {'PASS' if ok else 'FAIL'}  {name}" + (f"  [{detail}]" if detail else ""))
        n_ok = sum(1 for _, ok, _ in checks if ok)
        print(f"{'VALIDATION PASSED' if code == EXIT_OK else 'VALIDATION FAILED'} "
              f"({n_ok}/{len(checks)} checks)")
    return code


if __name__ == "__main__":
    sys.exit(main())

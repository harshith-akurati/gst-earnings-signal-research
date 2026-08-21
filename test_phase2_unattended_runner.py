#!/usr/bin/env python3
# Deterministic tests for the unattended Phase 2 daily-panel runner's schema
# validation contract.
#
# No network, no provider, no financial data retrieval, no outcome access, and
# no panel run. Sockets are blocked BEFORE any project module is imported, the
# same discipline the rest of this repository's test files use. Every fixture is
# synthetic and lives in a temporary directory.
#
# Run directly:  python test_phase2_unattended_runner.py

from __future__ import annotations

import csv
import json
import socket
import sys
import tempfile
from pathlib import Path

# --- blockers installed BEFORE importing any project module ----------------


class NetworkBlocked(RuntimeError):
    pass


def _no_net(*a, **k):
    raise NetworkBlocked("network access attempted")


socket.socket.connect = _no_net
socket.socket.connect_ex = _no_net
socket.create_connection = _no_net
socket.getaddrinfo = _no_net

sys.path.insert(0, str(Path(__file__).resolve().parent / "tools"))
from phase2_panel_validate import (                                # noqa: E402
    EXIT_MISSING, EXIT_OK, EXIT_SCHEMA, EXPECTED_COLS, EXPECTED_ROWS,
    SIX_FIELDS, validate,
)

_failures: list[str] = []


def check(label: str, ok: bool, detail: str = "") -> None:
    if ok:
        print(f"PASS: {label}")
    else:
        print(f"FAIL: {label}" + (f" -- {detail}" if detail else ""))
        _failures.append(label)


# --- fixture builders -------------------------------------------------------

def good_marker() -> dict:
    return {
        "status": "COMPLETE",
        "row_count": EXPECTED_ROWS,
        "unique_ticker_count": EXPECTED_ROWS,
        "all_six_fields_clean_count": EXPECTED_ROWS,
        "field_completeness_pct": {f: 100.0 for f in SIX_FIELDS},
        "failed_source_counts": {"earnings": 0, "price_history": 0, "realized_vol": 0,
                                 "iv": 0, "gst": 0, "wiki": 0},
        "elapsed_s": 272.1,
    }


def write_pair(d: Path, marker: dict, n_rows: int = EXPECTED_ROWS,
               n_cols: int = EXPECTED_COLS, blank_field: str | None = None,
               dup_ticker: bool = False) -> tuple[Path, Path]:
    mp = d / "marker.json"
    mp.write_text(json.dumps(marker), encoding="utf-8")

    cols = ["ticker"] + list(SIX_FIELDS)
    cols += [f"pad_{i}" for i in range(n_cols - len(cols))]
    cp = d / "panel.csv"
    with cp.open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=cols)
        w.writeheader()
        for i in range(n_rows):
            row = {c: "x" for c in cols}
            row["ticker"] = "AAA" if dup_ticker else f"T{i:02d}"
            for f in SIX_FIELDS:
                row[f] = "1.0"
            if blank_field and i == 0:
                row[blank_field] = ""
            w.writerow(row)
    return mp, cp


def run(marker: dict | None = None, **kw) -> int:
    with tempfile.TemporaryDirectory() as td:
        d = Path(td)
        mp, cp = write_pair(d, marker if marker is not None else good_marker(), **kw)
        code, _ = validate(mp, cp)
        return code


# --- 1. sockets are genuinely blocked ---------------------------------------

print("\n=== 1. network isolation ===")
try:
    socket.create_connection(("wikimedia.org", 443), timeout=1)
    check("1a. outbound connection is refused", False, "connection was NOT blocked")
except NetworkBlocked:
    check("1a. outbound connection is refused", True)
except Exception as e:                                             # noqa: BLE001
    check("1a. outbound connection is refused", False, f"unexpected {type(e).__name__}")
try:
    socket.getaddrinfo("wikimedia.org", 443)
    check("1b. DNS resolution is refused", False, "resolution was NOT blocked")
except NetworkBlocked:
    check("1b. DNS resolution is refused", True)
except Exception as e:                                             # noqa: BLE001
    check("1b. DNS resolution is refused", False, f"unexpected {type(e).__name__}")

# --- 2. the positive case ---------------------------------------------------

print("\n=== 2. valid output passes ===")
check("2a. clean 24/24 pair returns EXIT_OK", run() == EXIT_OK)

with tempfile.TemporaryDirectory() as td:
    d = Path(td)
    mp, cp = write_pair(d, good_marker())
    code, checks = validate(mp, cp)
    check("2b. every individual check passed", all(ok for _, ok, _ in checks))
    check("2c. a meaningful number of checks ran", len(checks) >= 20, f"{len(checks)}")

# --- 3. negative: missing artifacts -> EXIT_MISSING -------------------------

print("\n=== 3. missing artifacts ===")
with tempfile.TemporaryDirectory() as td:
    d = Path(td)
    mp, cp = write_pair(d, good_marker())
    mp.unlink()
    check("3a. missing marker returns EXIT_MISSING", validate(mp, cp)[0] == EXIT_MISSING)
with tempfile.TemporaryDirectory() as td:
    d = Path(td)
    mp, cp = write_pair(d, good_marker())
    cp.unlink()
    check("3b. missing final CSV returns EXIT_MISSING (the PARTIAL-run signal)",
          validate(mp, cp)[0] == EXIT_MISSING)

# --- 4. negative: marker says the run was not clean -> EXIT_SCHEMA ----------

print("\n=== 4. marker-level rejections ===")
m = good_marker(); m["status"] = "PARTIAL"
check("4a. status PARTIAL is rejected", run(m) == EXIT_SCHEMA)
m = good_marker(); m["row_count"] = 23
check("4b. row_count 23 is rejected", run(m) == EXIT_SCHEMA)
m = good_marker(); m["all_six_fields_clean_count"] = 23
check("4c. all_six_fields_clean_count 23 is rejected", run(m) == EXIT_SCHEMA)
m = good_marker(); m["unique_ticker_count"] = 23
check("4d. unique_ticker_count 23 is rejected", run(m) == EXIT_SCHEMA)
m = good_marker(); m["failed_source_counts"]["wiki"] = 2
check("4e. any non-zero failed_source_count is rejected", run(m) == EXIT_SCHEMA)
m = good_marker(); m["field_completeness_pct"]["wiki_zscore"] = 91.67
check("4f. wiki_zscore 91.67% is rejected (the 2026-08-03 PARTIAL shape)",
      run(m) == EXIT_SCHEMA)
m = good_marker(); m["field_completeness_pct"]["gst_zscore"] = 87.5
check("4g. gst_zscore 87.5% is rejected (the 2026-08-05 PARTIAL shape)",
      run(m) == EXIT_SCHEMA)
m = good_marker(); m.pop("status")
check("4h. absent status field is rejected", run(m) == EXIT_SCHEMA)

# --- 5. negative: CSV disagrees with the marker -----------------------------

print("\n=== 5. CSV-level rejections ===")
check("5a. 23 data rows is rejected", run(n_rows=23) == EXIT_SCHEMA)
check("5b. 25 data rows is rejected", run(n_rows=25) == EXIT_SCHEMA)
check("5c. wrong column count is rejected", run(n_cols=EXPECTED_COLS - 1) == EXIT_SCHEMA)
check("5d. duplicate tickers rejected even at 24 rows", run(dup_ticker=True) == EXIT_SCHEMA)
for f in ("gst_zscore", "wiki_zscore", "price"):
    check(f"5e. a blank {f} cell is rejected", run(blank_field=f) == EXIT_SCHEMA)

# --- 6. a marker that lies about the CSV is still caught --------------------

print("\n=== 6. marker/CSV disagreement ===")
with tempfile.TemporaryDirectory() as td:
    d = Path(td)
    mp, cp = write_pair(d, good_marker(), n_rows=20)
    code, checks = validate(mp, cp)
    csv_row_check = [ok for n, ok, _ in checks if n.startswith("csv data rows")]
    check("6a. marker claiming 24 while the CSV holds 20 is rejected", code == EXIT_SCHEMA)
    check("6b. the failure is attributed to the CSV row check",
          csv_row_check and not csv_row_check[0])

# --- 7. malformed marker ----------------------------------------------------

print("\n=== 7. malformed marker ===")
with tempfile.TemporaryDirectory() as td:
    d = Path(td)
    mp, cp = write_pair(d, good_marker())
    mp.write_text("{not valid json", encoding="utf-8")
    check("7a. unparseable marker returns EXIT_SCHEMA", validate(mp, cp)[0] == EXIT_SCHEMA)

# --- summary ----------------------------------------------------------------

print()
if _failures:
    print(f"{len(_failures)} CHECK(S) FAILED:")
    for f in _failures:
        print(f"  - {f}")
    sys.exit(1)
print("ALL UNATTENDED RUNNER VALIDATION CHECKS PASSED")

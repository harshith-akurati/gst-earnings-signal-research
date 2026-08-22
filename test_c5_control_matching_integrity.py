#!/usr/bin/env python3
# Offline guards for the 2026-08-22 C5 matched-control correction overlay.
#
# Sockets are blocked before any project import, per this repository's existing
# test convention. Everything is read from committed inputs; no provider, no
# network, no recomputation of any corrected estimate.
#
# Run directly:  python test_c5_control_matching_integrity.py

from __future__ import annotations

import csv
import hashlib
import json
import re
import socket
import sys
from collections import Counter, defaultdict
from pathlib import Path


class NetworkBlocked(RuntimeError):
    pass


def _no_net(*a, **k):
    raise NetworkBlocked("network access attempted")


socket.socket.connect = _no_net
socket.socket.connect_ex = _no_net
socket.create_connection = _no_net
socket.getaddrinfo = _no_net

ROOT = Path(__file__).resolve().parent
OVERLAY_DIR = ROOT / "Correction_Overlays" / "2026-08-22_C5_Control_Matching"
OVERLAY = OVERLAY_DIR / "CORRECTION_OVERLAY_2026-08-22.md"
VERIFIED = OVERLAY_DIR / "verified_counts.json"
POP = ROOT / "Live Signal Engine" / "C5_PostEarnings_Population.csv"
MATCHED = ROOT / "Live Signal Engine" / "MatchedControlGroup_CanonicalRecompute.csv"
RESULTS = ROOT / "RETROSPECTIVE_MARKET_RESPONSE_RESULTS_v1.0.json"

# Hash-lock recorded in the overlay. These must not drift.
LOCKED = {
    "RETROSPECTIVE_MARKET_RESPONSE_RESULTS_v1.0.json":
        "3d8fbb85d9388d1ea1391aa31a98484a4ed1c0f81d63eda416c82a490574590d",
    "Live Signal Engine/C5_PostEarnings_Population.csv":
        "544172488e1836f31db529a80c5971ad2c9a1993ee14914975ddab60bfb95306",
    "Live Signal Engine/MatchedControlGroup_CanonicalRecompute.csv":
        "ec0fdb11e78ab9fa2bc68da185db50ca7d07ade8e6550fa3136c098134b7c4f3",
}

CAVEAT = "DO_NOT_CITE_PENDING_CORRECTION"

_failures: list[str] = []


def check(label: str, ok: bool, detail: str = "") -> None:
    if ok:
        print(f"PASS: {label}")
    else:
        print(f"FAIL: {label}" + (f" -- {detail}" if detail else ""))
        _failures.append(label)


def sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def rows(p: Path) -> list[dict]:
    return list(csv.DictReader(p.open(encoding="utf-8-sig")))


ident = lambda r: (r["ticker"], r["earnings_date"])

# --- 1. isolation -----------------------------------------------------------

print("\n=== 1. network isolation ===")
for lbl, fn in (("connect", lambda: socket.create_connection(("example.org", 443), timeout=1)),
                ("DNS", lambda: socket.getaddrinfo("example.org", 443))):
    try:
        fn(); check(f"1. outbound {lbl} refused", False, "not blocked")
    except NetworkBlocked:
        check(f"1. outbound {lbl} refused", True)
    except Exception as e:                                          # noqa: BLE001
        check(f"1. outbound {lbl} refused", False, type(e).__name__)

# --- 2. originals remain byte-identical -------------------------------------

print("\n=== 2. original artifacts unchanged (hash-lock) ===")
for rel, want in LOCKED.items():
    p = ROOT / rel
    if not p.is_file():
        check(f"2. {rel} present", False, "missing")
        continue
    got = sha(p)
    check(f"2. {rel} hash unchanged", got == want, f"got {got[:16]}… want {want[:16]}…")

# --- 3. defect counts reproduce from committed inputs -----------------------
# Counted on the population rows that survive the tool's coverage filter. The
# filter drops rows whose earnings date lies beyond price coverage; rather than
# re-run price loading offline, the surviving identities are taken from the
# committed verified_counts.json and cross-checked against the raw population.

print("\n=== 3. defect counts reproduce ===")
v = json.loads(VERIFIED.read_text(encoding="utf-8"))
pop = rows(POP)
sig = [r for r in pop if r["role"] == "signal"]
ctl = [r for r in pop if r["role"] == "control"]

check("3a. population holds 304 rows", len(pop) == 304, str(len(pop)))
check("3b. population splits 152 signal / 152 control",
      len(sig) == 152 and len(ctl) == 152, f"{len(sig)}/{len(ctl)}")
check("3c. verified treated rows = 152", v["treated_rows"] == 152, str(v["treated_rows"]))
check("3d. verified control rows = 133", v["control_rows"] == 133, str(v["control_rows"]))
check("3e. verified distinct control identities = 85",
      v["distinct_control_identities"] == 85, str(v["distinct_control_identities"]))
check("3f. verified self-match count = 20", v["self_match_count"] == 20, str(v["self_match_count"]))
check("3g. verified reused identities = 24",
      v["reused_control_identities"] == 24, str(v["reused_control_identities"]))
check("3h. verified redundant rows = 48", v["reused_extra_rows"] == 48, str(v["reused_extra_rows"]))
check("3i. verified max reuse = 6", v["max_reuse"] == 6, str(v["max_reuse"]))
check("3j. treated identities are unique (152 rows, 152 identities)",
      v["distinct_treated_identities"] == v["treated_rows"] == 152)
check("3k. 85 = 61 used-once + 24 reused",
      v["control_identities_used_exactly_once"] + v["reused_control_identities"]
      == v["distinct_control_identities"])
check("3l. the alleged '61 distinct' is really used-once, and '72' is rows-of-reused-identities",
      v["control_identities_used_exactly_once"] == 61 and v["rows_belonging_to_reused_identities"] == 72)
check("3m. no duplicate control row is byte-identical",
      v["byte_identical_duplicate_control_rows"] == 0,
      str(v["byte_identical_duplicate_control_rows"]))
check("3n. self-matched pair list length matches the count",
      len(v["self_matched_pairs"]) == v["self_match_count"])
check("3o. reused-control list length matches the count",
      len(v["reused_controls"]) == v["reused_control_identities"])

# Self-matches must be verifiable directly in the raw population too.
bypair = defaultdict(dict)
for r in pop:
    bypair[r["pair_id"]][r["role"]] = r
raw_self = {(d["signal"]["ticker"], d["signal"]["earnings_date"])
            for d in bypair.values()
            if "signal" in d and "control" in d and ident(d["signal"]) == ident(d["control"])}
listed_self = {(x["ticker"], x["earnings_date"]) for x in v["self_matched_pairs"]}
check("3p. every recorded self-match is present in the raw population",
      listed_self <= raw_self, f"{len(listed_self - raw_self)} not found")

# --- 4. the mechanism claim holds: upstream had no self-matches -------------

print("\n=== 4. root-cause mechanism ===")
mt = rows(MATCHED)
check("4a. upstream matched file holds 152 pairs", len(mt) == 152, str(len(mt)))
up_self = [r for r in mt if r["ticker"] == r["control_ticker"] and r["spike_week"] == r["control_date"]]
check("4b. upstream selected ZERO controls identical to their treated anchor",
      len(up_self) == 0, f"{len(up_self)} found")
up = Counter((r["control_ticker"], r["control_date"]) for r in mt)
check("4c. control reuse is inherited from upstream (with-replacement matching)",
      max(up.values()) > 1, "no upstream reuse found")

# --- 5. the affected statistic cannot appear without its caveat -------------

print("\n=== 5. caveat coupling ===")
text = OVERLAY.read_text(encoding="utf-8")
check("5a. overlay names Q1_abs_move_high_vs_control", "Q1_abs_move_high_vs_control" in text)
check("5b. overlay carries the DO_NOT_CITE label", CAVEAT in text)
check("5c. t = 2.138 is labelled in the same overlay", "2.138" in text and CAVEAT in text)
check("5d. overlay states no corrected result exists",
      "No corrected result has been computed" in text)
check("5e. overlay states originals are unchanged and hash-locked",
      "hash-locked" in text and "No original artifact byte was changed" in text)
check("5f. overlay records the manuscript's 0.0131 / 0.98332 as affected",
      "0.0131" in text and "0.98332" in text)

# Any *new* markdown that cites the affected statistic must carry the caveat.
EXEMPT = {OVERLAY.name}
offenders = []
for md in ROOT.rglob("*.md"):
    if ".git" in md.parts or md.name in EXEMPT:
        continue
    try:
        body = md.read_text(encoding="utf-8", errors="replace")
    except Exception:                                               # noqa: BLE001
        continue
    if "Q1_abs_move_high_vs_control" in body and CAVEAT not in body:
        offenders.append(str(md.relative_to(ROOT)))
check("5g. no markdown cites Q1_abs_move_high_vs_control without the caveat",
      not offenders, "; ".join(offenders[:4]))

# --- 6. unaffected findings are not labelled invalid ------------------------

print("\n=== 6. unaffected findings protected ===")
res = json.loads(RESULTS.read_text(encoding="utf-8"))
check("6a. treated-arm decomposition still present and n=152",
      res["decomposition"]["high_gst"]["open_to_close"]["n"] == 152)
check("6b. Q4 remains reported (treated-arm only)",
      res["Q4_continuation_vs_reversal"]["n"] == 152)
sc = {s["strategy"][0]: s for s in res["scorecard"]}
check("6c. strategy E net return 0.8543 intact (treated-arm only)",
      abs(sc["E"]["mean_net_pct"] - 0.8543) < 1e-9, str(sc["E"]["mean_net_pct"]))
check("6d. overlay lists an explicit UNAFFECTED section", "UNAFFECTED" in text)
check("6e. overlay states 0.8543 is NOT affected",
      "0.8543" in text and "NOT affected" in text)
for name in ("magnitude forecast", "direction signal", "restaurant search pilot"):
    check(f"6f. overlay excludes the {name} from the lineage", name in text)
check("6g. overlay limits scope explicitly",
      "does not automatically invalidate" in text)

# --- 7. ticker clarification is present and explained -----------------------

print("\n=== 7. 28-vs-24 clarification ===")
check("7a. both counts appear", "28" in text and "24" in text)
check("7b. LOCKED_24_TICKER_UNIVERSE is named as the prospective universe",
      "LOCKED_24_TICKER_UNIVERSE" in text)
check("7c. the treated arm's 27 tickers are disclosed", "27" in text and "JBL" in text)
check("7d. neither number is presented as replacing the other",
      "two different universes" in text.lower())
check("7e. artifact still reports 28 for the retrospective population",
      res["sample"]["tickers"] == 28, str(res["sample"]["tickers"]))

# --- 8. forward guards: detect future self-matches / repeated controls ------

print("\n=== 8. forward guards ===")


def audit(population_rows: list[dict]) -> dict:
    c = [r for r in population_rows if r["role"] == "control"]
    bp = defaultdict(dict)
    for r in population_rows:
        bp[r["pair_id"]][r["role"]] = r
    selfm = sum(1 for d in bp.values()
                if "signal" in d and "control" in d and ident(d["signal"]) == ident(d["control"]))
    cnt = Counter(ident(r) for r in c)
    return {"self_matches": selfm,
            "reused_identities": sum(1 for x in cnt.values() if x > 1),
            "redundant_rows": sum(x - 1 for x in cnt.values() if x > 1)}


clean = [
    {"pair_id": "0", "role": "signal", "ticker": "AAA", "earnings_date": "2025-01-01"},
    {"pair_id": "0", "role": "control", "ticker": "AAA", "earnings_date": "2024-01-01"},
    {"pair_id": "1", "role": "signal", "ticker": "BBB", "earnings_date": "2025-02-01"},
    {"pair_id": "1", "role": "control", "ticker": "BBB", "earnings_date": "2024-02-01"},
]
check("8a. a clean population audits to zero defects",
      audit(clean) == {"self_matches": 0, "reused_identities": 0, "redundant_rows": 0},
      str(audit(clean)))

selfm = [dict(r) for r in clean]
selfm[1]["earnings_date"] = "2025-01-01"          # control collapses onto its own treated event
check("8b. an injected self-match is detected", audit(selfm)["self_matches"] == 1)

reuse = [dict(r) for r in clean]
reuse[3] = dict(reuse[3], ticker="AAA", earnings_date="2024-01-01")
a = audit(reuse)
check("8c. an injected reused control is detected",
      a["reused_identities"] == 1 and a["redundant_rows"] == 1, str(a))

live = audit(pop)
check("8d. the guard reproduces the raw-population self-match count (20)",
      live["self_matches"] == 20, str(live["self_matches"]))
check("8e. the guard flags the current population as defective",
      live["self_matches"] > 0 and live["reused_identities"] > 0)

# --- 9. the overlay must not pre-empt Phase 3 -------------------------------

print("\n=== 9. no premature conclusion ===")
check("9a. overlay does not assert a corrected direction",
      "direction is not asserted" in text.lower() or "direction not asserted" in text.lower())
check("9b. overlay records that no matcher code was modified",
      "No matcher code has been modified" in text)
banned = re.findall(r"corrected (?:t|estimate|effect) (?:is|was|becomes)", text, re.I)
check("9c. overlay states no corrected value", not banned, str(banned[:2]))

# --- summary ----------------------------------------------------------------

print()
if _failures:
    print(f"{len(_failures)} CHECK(S) FAILED:")
    for f in _failures:
        print(f"  - {f}")
    sys.exit(1)
print("ALL C5 CONTROL-MATCHING INTEGRITY CHECKS PASSED")

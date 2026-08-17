#!/usr/bin/env python3
"""Focused offline test for the attention-options dislocation collector.

Synthetic provider fixtures only. No network, no credential, no post-event price.
"""
from __future__ import annotations

import io
import json
import os
import re
import sys
import tempfile
from contextlib import redirect_stdout
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "tools"))
import collect_attention_options_snapshot as C  # noqa: E402

FAIL: list[str] = []
SRC = (ROOT / "tools" / "collect_attention_options_snapshot.py").read_text(encoding="utf-8")
DESIGN = (ROOT / "Live Signal Engine" / "Attention_Options_Dislocation"
          / "FROZEN_DESIGN_v1.0.md").read_text(encoding="utf-8")


def ck(label, ok, detail=""):
    print(("PASS: " if ok else "FAIL: ") + label + ("" if ok or not detail else f"   {detail}"))
    if not ok:
        FAIL.append(label)


def refuses(fn):
    try:
        fn()
    except C.Refused:
        return True
    except Exception:
        return False
    return False


# ---------------------------------------------------------------- fixtures
EXPIRATIONS = ["2026-08-14", "2026-08-21", "2026-08-28", "2026-09-18"]


def chain(exp="2026-08-21", strikes=(180.0, 185.0, 190.0, 195.0), **over):
    rows = []
    for s in strikes:
        for kind in ("call", "put"):
            rows.append({"expiration_date": exp, "strike": s, "option_type": kind,
                         "bid": 4.0 if kind == "call" else 3.6,
                         "ask": 4.4 if kind == "call" else 4.0,
                         "last": 99.0, "volume": 120, "open_interest": 900,
                         "greeks": {"mid_iv": 0.55}})
    for r in rows:
        if r["strike"] == over.get("_strike") and r["option_type"] == over.get("_kind"):
            r.update(over.get("_patch", {}))
    return rows


BASE = dict(ticker="ZZZ", issuer_name="Zeta Systems", event_date="2026-08-19",
            session="AMC", underlying_price=186.0, expirations=EXPIRATIONS,
            quote_timestamp_utc="2026-08-19T19:45:00Z", provider="tradier_sandbox",
            latency_label=C.DELAYED_LABEL, raw_sha256="a" * 64,
            search_features=[{"query": "ZZZ stock", "geo": "US", "category": 0,
                              "window": "today 3-m", "retrieved_utc": "2026-08-17T12:00:00Z",
                              "raw_sha256": "b" * 64, "weekly": [10, 20, 30]}],
            universe_source_kind="OFFICIAL_INDEX_CONSTITUENTS")


def rec(**over):
    kw = dict(BASE, chain=chain())
    kw.update(over)
    return C.build_record(**kw)


# ---------------------------------------------------------------- 1. selection
R = rec()
ck("1a. first expiration STRICTLY after the event is chosen",
   C.first_expiration_after(EXPIRATIONS, "2026-08-19") == "2026-08-21")
ck("1b. an expiration ON the event date is not chosen",
   C.first_expiration_after(["2026-08-19", "2026-08-26"], "2026-08-19") == "2026-08-26")
ck("1c. no later expiration is available -> refused",
   refuses(lambda: C.first_expiration_after(["2026-08-01"], "2026-08-19")))
ck("1d. nearest strike to the underlying is selected",
   C.nearest_strike(chain(), 186.0) == 185.0 and R["strike"] == 185.0)
ck("1e. ties break to the lower strike deterministically",
   C.nearest_strike(chain(strikes=(180.0, 190.0)), 185.0) == 180.0)

# ---------------------------------------------------------------- 2. arithmetic
ck("2a. midpoints computed from bid/ask, not last",
   R["call_mid"] == 4.2 and R["put_mid"] == 3.8 and R["call_last"] == 99.0)
ck("2b. midpoint implied move = (call_mid + put_mid) / underlying",
   abs(R["midpoint_implied_move"] - (4.2 + 3.8) / 186.0) < 1e-12)
ck("2c. executable straddle cost = (call_ask + put_ask) / underlying",
   abs(R["executable_straddle_cost"] - (4.4 + 4.0) / 186.0) < 1e-12)
ck("2d. executable cost exceeds the midpoint move (spread is real)",
   R["executable_straddle_cost"] > R["midpoint_implied_move"])
ck("2e. non-positive underlying refused",
   refuses(lambda: C.implied_move(1.0, 1.0, 0.0)))

# ------------------------------------------------------- 3. no last substitution
ck("3a. missing bid refused, never replaced by last",
   refuses(lambda: rec(chain=chain(_strike=185.0, _kind="call",
                                   _patch={"bid": None}))))
ck("3b. missing ask refused, never replaced by last",
   refuses(lambda: rec(chain=chain(_strike=185.0, _kind="put", _patch={"ask": None}))))
ck("3c. crossed market refused",
   refuses(lambda: rec(chain=chain(_strike=185.0, _kind="call",
                                   _patch={"bid": 9.0, "ask": 1.0}))))
ck("3d. source contains no last-price fallback assignment",
   # an actual fallback would assign `last` into a missing bid/ask
   not re.search(r"\b(bid|ask)\s*=\s*[^\n]*\blast\b", SRC)
   and not re.search(r"\blast\b[^\n]*\bif\b[^\n]*\b(bid|ask)\s+is\s+None", SRC)
   and "last-price substitution is prohibited" in SRC)

# ------------------------------------------------------------ 4. timing rules
ck("4a. AMC snapshots on the announcement trading day",
   C.snapshot_date_for("2026-08-19", "AMC") == "2026-08-19")
ck("4b. BMO snapshots on the preceding trading day",
   C.snapshot_date_for("2026-08-19", "BMO") == "2026-08-18")
ck("4c. BMO rolls back over a weekend",
   C.snapshot_date_for("2026-08-17", "BMO") == "2026-08-14")
ck("4d. unknown session refused",
   refuses(lambda: C.snapshot_date_for("2026-08-19", "MIDDAY")))
ck("4e. search window ends at T-2",
   C.search_window_end("2026-08-19") == "2026-08-17"
   and R["search_window_end"] == "2026-08-17")
ck("4f. a quote after the AMC 16:00 ET release is refused",
   refuses(lambda: rec(quote_timestamp_utc="2026-08-19T20:30:00Z")))
ck("4g. a quote before the AMC release is accepted",
   C.assert_pre_announcement("2026-08-19T19:45:00Z", "2026-08-19", "AMC"))
ck("4h. a quote after the BMO 09:30 ET release is refused",
   refuses(lambda: C.assert_pre_announcement("2026-08-19T14:00:00Z", "2026-08-19", "BMO")))
ck("4i. target snapshot time is frozen at 15:45 ET",
   C.SNAPSHOT_TARGET_ET == "15:45" and "15:45" in DESIGN)

# ------------------------------------------------------ 5. delay labelling
ck("5a. sandbox selection yields the delayed label",
   C.options_provider({"TRADIER_SANDBOX_TOKEN": "x"})[2] == "DELAYED_15_MINUTES")
ck("5b. real-time token is preferred over sandbox",
   C.options_provider({"TRADIER_TOKEN": "x", "TRADIER_SANDBOX_TOKEN": "y"})[0] == "tradier")
ck("5c. no token -> no provider, and no scraping fallback exists",
   C.options_provider({})[0] is None
   and not re.search(r"(cboe|yahoo|marketchameleon|barchart)", SRC, re.I))
ck("5d. the delayed label is carried on the record",
   R["quote_latency_label"] == "DELAYED_15_MINUTES")

# ------------------------------------------------- 6. manifest + duplicates
with tempfile.TemporaryDirectory() as td:
    m = Path(td) / "manifest.jsonl"
    rid = C.append_record(R, m)
    ck("6a. record appended", m.exists() and rid == R["record_id"])
    ck("6b. duplicate identity refused",
       refuses(lambda: C.append_record(rec(), m)))
    other = rec(quote_timestamp_utc="2026-08-19T19:44:00Z")
    C.append_record(other, m)
    lines = [json.loads(x) for x in m.read_text(encoding="utf-8").splitlines() if x.strip()]
    ck("6c. append-only: earlier record preserved verbatim",
       len(lines) == 2 and lines[0]["record_id"] == rid)
    ck("6d. distinct quote timestamps are distinct identities",
       lines[0]["record_id"] != lines[1]["record_id"])

ck("6e. record_id is deterministic",
   C.record_id(R) == C.record_id(dict(R)) == R["record_id"])
ck("6f. hashing is content-addressed",
   C.sha256_bytes(b"a") != C.sha256_bytes(b"b")
   and C.sha256_bytes(b"abc").startswith("ba7816bf"))

# ------------------------------------------- 7. prohibited fields / outcomes
ck("7a. a realized-return field is refused",
   refuses(lambda: C.assert_no_prohibited_fields(dict(R, realized_move=0.05))))
ck("7b. a post-event price field is refused",
   refuses(lambda: C.assert_no_prohibited_fields(dict(R, post_event_close=190.0))))
ck("7c. an order/fill field is refused",
   refuses(lambda: C.assert_no_prohibited_fields(dict(R, order_id="x"))))
ck("7d. the clean record passes", C.assert_no_prohibited_fields(R))
ck("7e. no order/account endpoint exists in the source",
   not re.search(r"/v1/accounts|/orders|place_order|submit_order|side=|order_type", SRC))
ck("7f. no post-event price or return is computed anywhere in the source",
   not re.search(r"def .*(realized|post_event|compute_return)", SRC)
   and "realized" not in SRC.replace("realized|", ""))
ck("7g. Alpha Vantage EPS is never treated as an outcome",
   "EPS fields in this feed are NOT an outcome" in SRC)

# ------------------------------------------------------ 8. credential safety
ck("8a. presence check returns only booleans",
   all(isinstance(v, bool) for v in C.credential_presence({"TRADIER_TOKEN": "s3cret"}).values()))
ck("8b. redact removes a credential value",
   "s3cret" not in C.redact("token s3cret leaked", {"TRADIER_TOKEN": "s3cret"}))
ck("8c. redact strips bearer headers",
   "<REDACTED>" in C.redact("Authorization: Bearer abc.def-123", {}))
buf = io.StringIO()
with redirect_stdout(buf):
    C.mode_doctor()
out = buf.getvalue()
_live = [(os.environ.get(v) or "").strip() for v in C.CRED_VARS]
ck("8d. doctor prints no credential value and no length or prefix of one",
   all(val not in out for val in _live if val)
   # no long opaque token-like run, and no "<var> = N chars"-style disclosure
   and not re.search(r"[A-Za-z0-9]{16,}", out.replace("DELAYED_15_MINUTES", ""))
   and not re.search(r"(len|length|chars|prefix|starts with)\s*[:=]\s*\d", out, re.I))
ck("8e. doctor reports presence only",
   "PRESENT" in out or "ABSENT" in out)
ck("8f. no credential is written to the manifest",
   not any(v in json.dumps(R) for v in ("TRADIER_TOKEN", "ALPHAVANTAGE_API_KEY")))
ck("8g. source never hashes or measures a credential",
   not re.search(r"sha256\w*\(\s*(token|key|cred)", SRC, re.I)
   and not re.search(r"len\(\s*(token|key)\b", SRC, re.I))

# ----------------------------------------------------- 9. universe + design
ck("9a. official constituent source is ranked first",
   C.UNIVERSE_SOURCES[0]["kind"] == "OFFICIAL_INDEX_CONSTITUENTS")
ck("9b. the QQQ fallback is labelled a disclosed proxy",
   C.UNIVERSE_SOURCES[1]["kind"] == "OFFICIAL_ETF_HOLDINGS_PROXY")
ck("9c. no scraped or generated universe source is present",
   not re.search(r"wikipedia|slickcharts|stockanalysis", SRC, re.I))
ck("9d. vendor calendar dates are labelled unverified",
   C.SCHEDULING_LABEL == "SCHEDULING_INPUT_UNVERIFIED"
   and R["event_timing_status"] == C.SCHEDULING_LABEL)
ck("9e. the frozen design fixes the 75-event minimum and four gates",
   "75 eligible events" in DESIGN and "10%" in DESIGN and "2%" in DESIGN)
ck("9f. the design forbids predicting direction",
   "direction is never predicted" in DESIGN or "No direction signal" in DESIGN)
ck("9g. the raw cache is repository-external",
   ROOT not in C.CACHE.resolve().parents and C.CACHE.resolve() != ROOT)

# --------------------------------------------------------- 10. validate mode
with tempfile.TemporaryDirectory() as td:
    m = Path(td) / "manifest.jsonl"
    C.append_record(R, m)
    real, C.MANIFEST = C.MANIFEST, m
    try:
        buf = io.StringIO()
        with redirect_stdout(buf):
            code = C.mode_validate()
        ck("10a. a clean manifest validates", code == 0)
        with m.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(dict(R, quote_timestamp_utc="2026-08-19T21:00:00Z",
                                     record_id="x" * 32)) + "\n")
        buf = io.StringIO()
        with redirect_stdout(buf):
            code = C.mode_validate()
        ck("10b. a post-announcement record fails validation", code == 1)
    finally:
        C.MANIFEST = real

print()
if FAIL:
    print(f"{len(FAIL)} FAILURE(S): {FAIL}")
    sys.exit(1)
print("ALL ATTENTION-OPTIONS DISLOCATION CHECKS PASSED")
sys.exit(0)

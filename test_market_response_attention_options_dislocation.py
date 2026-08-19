#!/usr/bin/env python3
"""Focused offline test for the attention-options dislocation collector.

Synthetic provider fixtures only. No network, no credential, no post-event price.

Sections 1-10 cover the original frozen design. Sections 11-21 cover Provider
Amendment 1 (2026-08-17), which replaced Tradier with Alpaca Paper Only's free
`indicative` options feed.

Sockets are blocked for the whole run: every check below is offline by construction,
not by convention.
"""
from __future__ import annotations

import ast
import io
import json
import os
import re
import socket
import subprocess
import sys
import tempfile
from contextlib import redirect_stdout
from datetime import date, datetime, timedelta, timezone
from pathlib import Path


# ---------------------------------------------------------------- sockets off
class NetworkBlocked(RuntimeError):
    """Raised if anything in this suite tries to open a socket."""


def _blocked(*_a, **_k):
    raise NetworkBlocked("the offline suite blocks all sockets")


socket.socket = _blocked                 # type: ignore[assignment]
socket.create_connection = _blocked      # type: ignore[assignment]
socket.getaddrinfo = _blocked            # type: ignore[assignment]

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "tools"))
import collect_attention_options_snapshot as C  # noqa: E402

FAIL: list[str] = []
STUDY_DIR = ROOT / "Live Signal Engine" / "Attention_Options_Dislocation"
SRC = (ROOT / "tools" / "collect_attention_options_snapshot.py").read_text(encoding="utf-8")
DESIGN_PATH = STUDY_DIR / "FROZEN_DESIGN_v1.0.md"
DESIGN_BYTES = DESIGN_PATH.read_bytes()
DESIGN = DESIGN_BYTES.decode("utf-8")
AMEND_REL = ("Live Signal Engine/Attention_Options_Dislocation/"
             "PROVIDER_AMENDMENT_2026-08-17_ALPACA.md")
AMEND_PATH = ROOT / AMEND_REL
AMEND = AMEND_PATH.read_text(encoding="utf-8") if AMEND_PATH.exists() else ""

# The frozen design must stay byte-identical. This is the hash it was frozen with.
FROZEN_DESIGN_SHA256 = "dc270ef0f2d61c6267204bfc15c2f9e54ca7a2b3264b07f2fb749454c106f1a5"


CHECKS = 0


def ck(label, ok, detail=""):
    global CHECKS
    CHECKS += 1
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


def git(*args):
    r = subprocess.run(["git", "-C", str(ROOT), *args], capture_output=True, text=True)
    return r.stdout.strip()


# ------------------------------------------------------------ effective code
# Guard code must NAME the endpoints and terms it forbids in order to forbid them.
# A bare substring scan would therefore flag the very code that enforces the rule.
# These scans run against executable code with docstrings, comments and blocklist
# constants removed, so a prohibition can be declared but never *used*.
BLOCKLIST_NAMES = {"ALPACA_FORBIDDEN_ENDPOINT", "EXECUTABLE_CLAIM_FIELD",
                   "PROHIBITED_FIELD", "ISSUER_NOISE"}


def effective_code(src):
    tree = ast.parse(src)
    drop = set()
    for node in ast.walk(tree):
        if isinstance(node, (ast.Module, ast.ClassDef, ast.FunctionDef,
                             ast.AsyncFunctionDef)):
            body = getattr(node, "body", None)
            if (body and isinstance(body[0], ast.Expr)
                    and isinstance(body[0].value, ast.Constant)
                    and isinstance(body[0].value.value, str)):
                drop |= set(range(body[0].lineno, body[0].end_lineno + 1))
        if isinstance(node, ast.Assign):
            for t in node.targets:
                if isinstance(t, ast.Name) and t.id in BLOCKLIST_NAMES:
                    drop |= set(range(node.lineno, node.end_lineno + 1))
    out = []
    for i, line in enumerate(src.splitlines(), 1):
        if i not in drop:
            out.append(re.sub(r"#.*$", "", line))
    return "\n".join(out)


CODE = effective_code(SRC)


def url_literals(src):
    return [n.value for n in ast.walk(ast.parse(src))
            if isinstance(n, ast.Constant) and isinstance(n.value, str)
            and re.match(r"^https?://", n.value)]


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


# ---- Alpaca fixtures ------------------------------------------------------
QTS = "2026-08-19T19:45:00.123456789Z"          # 15:45:00 ET, before the AMC release
NOW = datetime(2026, 8, 19, 19, 45, 30, tzinfo=timezone.utc)


def occ(root, exp, kind, strike):
    y, m, d = exp.split("-")
    return "%s%s%s%s%s%08d" % (root, y[2:], m, d, "C" if kind == "call" else "P",
                               int(round(strike * 1000)))


def alpaca_payload(exp="2026-08-21", strikes=(180.0, 185.0, 190.0), ts=QTS,
                   patch=None, root="ZZZ"):
    snaps = {}
    for s in strikes:
        for kind in ("call", "put"):
            snaps[occ(root, exp, kind, s)] = {
                "latestQuote": {"bp": 4.0 if kind == "call" else 3.6,
                                "ap": 4.4 if kind == "call" else 4.0, "t": ts},
                "latestTrade": {"p": 99.0, "t": ts},
                "dailyBar": {"v": 120},
                "impliedVolatility": 0.55,
            }
    if patch:
        for sym, upd in patch.items():
            snaps.setdefault(sym, {})
            for k, v in upd.items():
                if isinstance(v, dict):
                    snaps[sym].setdefault(k, {}).update(v)
                else:
                    snaps[sym][k] = v
    return {"snapshots": snaps, "next_page_token": None}


ALPACA_ROWS = C.alpaca_snapshot_rows(alpaca_payload())
ALPACA_EXPS = {r["expiration_date"] for r in ALPACA_ROWS}


def arec(**over):
    kw = dict(BASE, chain=ALPACA_ROWS, expirations=ALPACA_EXPS,
              provider="alpaca", latency_label=C.ALPACA_LABEL,
              feed=C.ALPACA_OPTIONS_FEED, feed_designation=C.ALPACA_LABEL,
              request_timestamp_utc="2026-08-19T19:45:05Z", response_status=200,
              underlying_price_source="alpaca:iex")
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

# ------------------------------------------------------ 5. provider selection
ck("5a. sandbox selection yields the delayed label",
   C.options_provider({"TRADIER_SANDBOX_TOKEN": "x"})[2] == "DELAYED_15_MINUTES")
ck("5b. real-time token is preferred over sandbox",
   C.options_provider({"TRADIER_TOKEN": "x", "TRADIER_SANDBOX_TOKEN": "y"})[0] == "tradier")
ck("5c. no token -> no provider, and no scraped substitute exists",
   C.options_provider({})[0] is None
   and not re.search(r"(yahoo|marketchameleon|barchart|slickcharts)", SRC, re.I)
   # Cboe is permitted ONLY as a human-downloaded local file; no automated access
   and not any("cboe" in u.lower() for u in url_literals(SRC)))
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
ck("7e. no order/account endpoint is CONSTRUCTED in executable code",
   not re.search(r"/v1/accounts|/orders|place_order|submit_order|side=|order_type",
                 CODE)
   and not any(re.search(r"/orders|/positions|/account|api\.alpaca\.markets", u)
               for u in url_literals(SRC)))
ck("7f. no post-event price or return is computed in executable code",
   not re.search(r"def .*(realized|post_event|compute_return)", SRC)
   and not re.search(r"realized", CODE, re.I))
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
   not re.search(r"sha256\w*\(\s*(token|key|cred|kid|sec)", SRC, re.I)
   and not re.search(r"len\(\s*(token|key|kid|sec)\b", SRC, re.I))

# ----------------------------------------------------- 9. universe + design
ck("9a. official constituent source is ranked first",
   C.UNIVERSE_SOURCES[0]["kind"] == "OFFICIAL_INDEX_CONSTITUENTS")
ck("9b. the QQQ fallback is labelled a disclosed proxy",
   C.UNIVERSE_SOURCES[1]["kind"] == "OFFICIAL_ETF_HOLDINGS_PROXY")
ck("9c. every universe source is an official issuer host, and no scraped, "
   "aggregator or generated source can be requested",
   {s["kind"] for s in C.UNIVERSE_SOURCES} <= {"OFFICIAL_INDEX_CONSTITUENTS",
                                               "OFFICIAL_ETF_HOLDINGS_PROXY"}
   and all(re.match(r"^https://(api\.nasdaq\.com|www\.invesco\.com)/", s["url"])
           for s in C.UNIVERSE_SOURCES)
   and not re.search(r"wikipedia|slickcharts|stockanalysis|dividend|zacks", CODE, re.I))
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

# ==========================================================================
# Provider Amendment 1 (2026-08-17) -- Alpaca Paper Only, indicative feed
# ==========================================================================

# ------------------------------------------- 11. the original design is unchanged
import hashlib  # noqa: E402
ck("11a. the frozen design is byte-identical to its frozen hash",
   hashlib.sha256(DESIGN_BYTES).hexdigest() == FROZEN_DESIGN_SHA256)
ck("11b. git reports no modification to the frozen design on this branch",
   git("diff", "--name-only", "HEAD", "--",
       "Live Signal Engine/Attention_Options_Dislocation/FROZEN_DESIGN_v1.0.md") == "")
ck("11c. the frozen design was never rewritten in branch history "
   "(exactly one commit touches it: the freeze)",
   len([x for x in git("log", "--format=%H", "--",
                       "Live Signal Engine/Attention_Options_Dislocation/"
                       "FROZEN_DESIGN_v1.0.md").splitlines() if x.strip()]) == 1)
ck("11d. the amendment is additive: it does not claim to replace the design",
   "Additive only" in AMEND and "not rewritten" in AMEND
   and FROZEN_DESIGN_SHA256 in AMEND)
ck("11e. no statistical rule, feature, event rule, cutoff, selection rule or "
   "primary metric is changed",
   C.SNAPSHOT_TARGET_ET == "15:45" and C.SEARCH_CUTOFF_DAYS == 2
   and C.CALENDAR_HORIZON_DAYS == 90
   and C.STRIKE_SELECTION_METHOD == "NEAREST_STRIKE_TO_CONTEMPORANEOUS_UNDERLYING"
   and abs(C.implied_move(4.2, 3.8, 186.0) - (4.2 + 3.8) / 186.0) < 1e-12)

# ------------------------------- 12. the amendment predates the first request
AMEND_ADD = [x for x in git("log", "--diff-filter=A", "--format=%H", "--",
                            AMEND_REL).splitlines() if x.strip()]
AMEND_SHA = AMEND_ADD[-1] if AMEND_ADD else ""
AMEND_TIME = git("log", "-1", "--format=%cI", AMEND_SHA) if AMEND_SHA else ""
LEDGER = STUDY_DIR / "collection_provenance.jsonl"
LEDGER_RECS = ([json.loads(x) for x in
                LEDGER.read_text(encoding="utf-8").splitlines() if x.strip()]
               if LEDGER.exists() else [])
ALPACA_REQS = sorted(r["request_timestamp_utc"] for r in LEDGER_RECS
                     if r.get("provider") == "alpaca" and r.get("request_timestamp_utc"))
ck("12a. the amendment is committed", bool(AMEND_SHA) and bool(AMEND_TIME))
ck("12b. the amendment commit changed exactly one path",
   git("show", "--name-only", "--format=", AMEND_SHA).split() != []
   and len([x for x in git("show", "--name-only", "--format=",
                           AMEND_SHA).splitlines() if x.strip()]) == 1)
ck("12c. at the amendment commit the collector had no Alpaca code at all",
   "alpaca" not in git("show",
                       f"{AMEND_SHA}:tools/collect_attention_options_snapshot.py").lower())
ck("12d. every recorded Alpaca request happened AFTER the amendment was committed",
   bool(ALPACA_REQS)
   and all(datetime.fromisoformat(t.replace("Z", "+00:00"))
           > datetime.fromisoformat(AMEND_TIME) for t in ALPACA_REQS),
   f"amendment {AMEND_TIME}; first request {ALPACA_REQS[:1]}")
ck("12e. the amendment states the Tradier/identity reason and the deferral",
   "SSN" in AMEND and "brokerage" in AMEND
   and C.DEFERRED_EXECUTION_STATUS in AMEND
   and C.SCHEMA_INCOMPATIBLE_STATUS in AMEND)
ck("12f. the amendment forbids opening a retrospective outcome to justify itself",
   "No retrospective outcome" in AMEND or "no retrospective outcome" in AMEND.lower())

# ------------------------------- 13. credentials cannot appear in any artifact
LIVE = [v for v in ((os.environ.get(k) or "").strip() for k in C.CRED_VARS) if v]
ARTIFACTS = [p for p in [
    SRC, AMEND, DESIGN,
    (STUDY_DIR / "README.md").read_text(encoding="utf-8"),
    (ROOT / "CHANGELOG.md").read_text(encoding="utf-8"),
    Path(__file__).read_text(encoding="utf-8"),
    LEDGER.read_text(encoding="utf-8") if LEDGER.exists() else "",
] if p]
ck("13a. no live credential value appears in any committed artifact",
   not any(v in a for v in LIVE for a in ARTIFACTS),
   "this check is only meaningful with credentials set; "
   f"{len(LIVE)} live value(s) were searched for")
ck("13b. the Alpaca credentials are read ONLY from the two approved variables",
   C.ALPACA_CRED_VARS == ("APCA_API_KEY_ID", "APCA_API_SECRET_KEY")
   and set(re.findall(r"environ\.get\(\"([A-Z_]+)\"\)", SRC))
   <= set(C.CRED_VARS) | {"AOD_CACHE_DIR"})
ck("13c. auth headers are built but never printed, hashed or serialized",
   not re.search(r"print\([^\n]*alpaca_auth_headers", SRC)
   and not re.search(r"(sha256|json\.dumps|append_provenance)\([^\n]*"
                     r"(alpaca_auth_headers|APCA_API)", SRC))
ck("13d. redact strips the Alpaca variables too",
   "zzsecretzz" not in C.redact("leak zzsecretzz here",
                                {"APCA_API_SECRET_KEY": "zzsecretzz"}))
LEDGER_TEXT = LEDGER.read_text(encoding="utf-8") if LEDGER.exists() else ""
ck("13e. the provenance ledger stores no credential value and no derived fingerprint",
   not any(v in LEDGER_TEXT for v in LIVE)
   # a fingerprint would be a hash or truncation OF a credential; the only hashes in
   # the ledger are of provider RESPONSE bodies, which are declared as such
   and all(k.endswith("response_sha256") or "sha" not in k.lower()
           for r in LEDGER_RECS for k in r))
ck("13f. credential presence is reported as a bare boolean only",
   all(isinstance(v, bool) for v in
       C.alpaca_credential_presence({"APCA_API_KEY_ID": "a"}).values()))

# ------------------------- 14. only market-data endpoints; orders fail closed
ALLOWED = ["https://data.alpaca.markets/v1beta1/options/snapshots/AAPL?feed=indicative",
           "https://data.alpaca.markets/v2/stocks/AAPL/trades/latest?feed=iex"]
FORBIDDEN = ["https://paper-api.alpaca.markets/v2/orders",
             "https://api.alpaca.markets/v2/orders",
             "https://api.alpaca.markets/v2/account",
             "https://paper-api.alpaca.markets/v2/positions",
             "https://paper-api.alpaca.markets/v2/options/contracts",
             "https://broker-api.alpaca.markets/v1/accounts",
             "https://data.alpaca.markets/v2/orders",
             "https://data.alpaca.markets/v2/positions",
             "https://data.alpaca.markets/v2/account",
             "https://data.alpaca.markets/v2/clock"]
UNKNOWN = ["https://data.alpaca.markets/v1beta3/anything",
           "https://data.alpaca.markets/",
           "https://evil.example.com/v2/stocks/AAPL/trades/latest",
           "http://data.alpaca.markets/v2/stocks/AAPL/trades/latest"]
ck("14a. permitted market-data endpoints are allowed",
   all(C.assert_market_data_endpoint(u) for u in ALLOWED))
ck("14b. every order / position / account / trading endpoint fails closed",
   all(refuses(lambda u=u: C.assert_market_data_endpoint(u)) for u in FORBIDDEN))
ck("14c. the guard fails CLOSED on unknown paths, hosts and schemes",
   all(refuses(lambda u=u: C.assert_market_data_endpoint(u)) for u in UNKNOWN))
ck("14d. every Alpaca request routes through the guard",
   "assert_market_data_endpoint(url)" in SRC
   and re.search(r"def alpaca_get\([^)]*\):(?:.|\n)*?assert_market_data_endpoint", SRC))
ck("14e. no order code path exists to disable",
   not re.search(r"def .*(place|submit|cancel).*(order|position)", SRC, re.I)
   and 'method="GET"' in SRC and not re.search(r'method="(POST|PUT|DELETE|PATCH)"', SRC))
ck("14f. alpaca_get refuses a forbidden endpoint before any socket is opened",
   refuses(lambda: C.alpaca_get("/v2/orders", env={"APCA_API_KEY_ID": "a",
                                                  "APCA_API_SECRET_KEY": "b"})))

# ----------------------------- 15. every Alpaca record carries the feed label
AR = arec()
ck("15a. an Alpaca record carries ALPACA_INDICATIVE_NON_EXECUTABLE",
   AR["feed_designation"] == "ALPACA_INDICATIVE_NON_EXECUTABLE"
   and AR["feed"] == "indicative")
ck("15b. an Alpaca record with a wrong feed designation is refused",
   refuses(lambda: arec(feed_designation="REALTIME_OPRA")))
ck("15c. an Alpaca record claiming the OPRA feed is refused",
   refuses(lambda: arec(feed="opra")))
ck("15d. an Alpaca record stripped of its label cannot be appended",
   refuses(lambda: C.append_record(dict(AR, feed_designation=""), Path("x.jsonl"))))
ck("15e. the label is mandatory at validate time too",
   refuses(lambda: C.assert_provider_provenance(dict(AR,
                                                     feed_designation="REALTIME"))))
ck("15f. the constant is exactly the amendment's label",
   C.ALPACA_LABEL == "ALPACA_INDICATIVE_NON_EXECUTABLE"
   and C.ALPACA_LABEL in AMEND)

# ------------------- 16. no executable-price / spread-alpha / straddle-P&L claim
ck("16a. an indicative record carries NO executable straddle cost",
   "executable_straddle_cost" not in AR)
ck("16b. an indicative record declares the execution stage deferred",
   AR["execution_economics_status"] == "OPRA_EXECUTION_DATA_UNAVAILABLE")
ck("16c. adding an executable price to an indicative record is refused",
   refuses(lambda: C.assert_no_executable_claim(
       dict(AR, executable_straddle_cost=0.05))))
ck("16d. a spread-aware net-return field is refused",
   refuses(lambda: C.assert_no_executable_claim(dict(AR, spread_aware_net_return=0.1))))
ck("16e. a realized straddle P&L field is refused",
   refuses(lambda: C.assert_no_executable_claim(dict(AR, straddle_pnl=1.0))))
ck("16f. a tradeable-alpha field is refused",
   refuses(lambda: C.assert_no_executable_claim(dict(AR, tradeable_alpha=0.02))))
ck("16g. an indicative record that drops the deferral status is refused",
   refuses(lambda: C.assert_no_executable_claim(
       {k: v for k, v in AR.items() if k != "execution_economics_status"})))
ck("16h. append_record re-applies the executable-claim ban",
   refuses(lambda: C.append_record(dict(AR, straddle_return=0.3), Path("x.jsonl"))))
ck("16i. the non-Alpaca path still computes the executable cost (design intact)",
   "executable_straddle_cost" in R)

# ---------------- 17. system-validation data can never enter the research panel
VREC = {"data_class": C.VALIDATION_CLASS, "label": C.SYSTEM_VALIDATION_LABEL,
        "provider": "alpaca", "feed": "indicative",
        "feed_designation": C.ALPACA_LABEL, "ticker": "AAPL",
        "event_date": "2026-08-19", "quote_timestamp_utc": "2026-08-19T19:45:00Z"}
ck("17a. a SYSTEM_VALIDATION record is refused from the research panel",
   refuses(lambda: C.append_record(VREC, Path("x.jsonl"))))
ck("17b. relabelling data_class alone does not smuggle it in (the label is scanned)",
   refuses(lambda: C.assert_research_grade(
       dict(VREC, data_class=C.RESEARCH_CLASS,
            note=f"captured as {C.SYSTEM_VALIDATION_LABEL}"))))
ck("17c. a research record is accepted", C.assert_research_grade(AR))
ck("17d. build_record only ever emits RESEARCH-class records",
   AR["data_class"] == C.RESEARCH_CLASS and R["data_class"] == C.RESEARCH_CLASS)
ck("17e. the connectivity check writes to the provenance ledger, not the manifest",
   all(r.get("data_class") != C.RESEARCH_CLASS for r in LEDGER_RECS)
   and C.PROVENANCE_LEDGER.name != C.MANIFEST.name)
ck("17f. the provenance ledger refuses a research record",
   refuses(lambda: C.append_provenance(AR, Path("y.jsonl"))))
ck("17g. the provenance ledger may not be aimed at the research manifest",
   refuses(lambda: C.append_provenance(VREC, C.MANIFEST)))
ck("17h. the recorded validation request is flagged non-usable as an observation",
   all(r.get("may_be_used_as_a_study_observation") is False
       and r.get("entered_research_panel") is False
       for r in LEDGER_RECS if r.get("data_class") == C.VALIDATION_CLASS))

# ------------------------ 18. wrong-window and post-announcement snapshots
ET = C.ET
ck("18a. a capture at the frozen 15:45 ET target on the right day is in-window",
   C.assert_in_snapshot_window(datetime(2026, 8, 19, 15, 45, tzinfo=ET),
                               "2026-08-19", "AMC"))
ck("18b. a capture 45 minutes early is refused",
   refuses(lambda: C.assert_in_snapshot_window(
       datetime(2026, 8, 19, 15, 0, tzinfo=ET), "2026-08-19", "AMC")))
ck("18c. a capture after the close is refused",
   refuses(lambda: C.assert_in_snapshot_window(
       datetime(2026, 8, 19, 16, 30, tzinfo=ET), "2026-08-19", "AMC")))
ck("18d. a capture on the wrong DAY is refused",
   refuses(lambda: C.assert_in_snapshot_window(
       datetime(2026, 8, 18, 15, 45, tzinfo=ET), "2026-08-19", "AMC")))
ck("18e. a BMO capture on the announcement day itself is refused "
   "(it belongs on the preceding day)",
   refuses(lambda: C.assert_in_snapshot_window(
       datetime(2026, 8, 19, 15, 45, tzinfo=ET), "2026-08-19", "BMO")))
ck("18f. a BMO capture on the preceding day is in-window",
   C.assert_in_snapshot_window(datetime(2026, 8, 18, 15, 45, tzinfo=ET),
                               "2026-08-19", "BMO"))
ck("18g. a post-announcement Alpaca quote is refused",
   refuses(lambda: arec(quote_timestamp_utc="2026-08-19T20:30:00Z")))
ck("18h. snapshot mode refuses without confirmed issuer/SEC event timing",
   "--timing-confirmed" in SRC and "SCHEDULING_INPUT_UNVERIFIED" in SRC)

# ----------------------------------------- 19. missing / crossed / stale legs
def arow(**over):
    r = dict(ALPACA_ROWS[0])
    r.update(over)
    return r


ck("19a. a missing bid is refused",
   refuses(lambda: C.assert_leg_usable(arow(bid=None), "call", NOW)))
ck("19b. a missing ask is refused",
   refuses(lambda: C.assert_leg_usable(arow(ask=None), "call", NOW)))
ck("19c. an empty two-sided quote (0/0) is MISSING, not a price of zero",
   refuses(lambda: C.assert_leg_usable(arow(bid=0.0, ask=0.0), "call", NOW)))
ck("19d. a crossed market is refused",
   refuses(lambda: C.assert_leg_usable(arow(bid=9.0, ask=1.0), "call", NOW)))
ck("19e. a negative bid is refused",
   refuses(lambda: C.assert_leg_usable(arow(bid=-1.0), "call", NOW)))
ck("19f. a stale quote is refused",
   refuses(lambda: C.assert_leg_usable(
       arow(), "call", NOW + timedelta(seconds=C.MAX_QUOTE_STALENESS_SECONDS + 60))))
ck("19g. a fresh quote is accepted", bool(C.assert_leg_usable(arow(), "call", NOW)))
ck("19h. a future-dated quote is refused as internally inconsistent",
   refuses(lambda: C.assert_leg_usable(
       arow(), "call", NOW - timedelta(seconds=600))))
ck("19i. a missing quote timestamp is refused",
   refuses(lambda: C.assert_leg_usable(arow(quote_timestamp=None), "call", NOW)))
ck("19j. non-contemporaneous call and put quotes are refused",
   refuses(lambda: C.assert_legs_contemporaneous(
       NOW, NOW + timedelta(seconds=C.MAX_LEG_DIVERGENCE_SECONDS + 30))))
ck("19k. contemporaneous legs are accepted",
   C.assert_legs_contemporaneous(NOW, NOW + timedelta(seconds=5)))
ck("19l. an Alpaca chain missing a bid refuses the whole record",
   refuses(lambda: arec(chain=[dict(r, bid=None) if r["strike"] == 185.0 else r
                               for r in ALPACA_ROWS])))
ck("19m. an internally inconsistent implied move is refused",
   refuses(lambda: C.assert_internally_consistent(
       dict(AR, midpoint_implied_move=1.5))))
ck("19n. an expiration not strictly after the event is refused",
   refuses(lambda: C.assert_internally_consistent(
       dict(AR, expiration="2026-08-19"))))
ck("19o. a contract symbol disagreeing with the record strike is refused",
   refuses(lambda: C.assert_internally_consistent(
       dict(AR, contract_symbol_call=occ("ZZZ", "2026-08-21", "call", 999.0)))))

# ------------------------------------- 20. provider / feed provenance mandatory
for field in ("provider", "feed", "feed_designation"):
    ck(f"20a. {field} is mandatory provenance",
       refuses(lambda f=field: C.assert_provider_provenance(dict(AR, **{f: ""}))))
ck("20b. a record with full provenance passes", C.assert_provider_provenance(AR))
ck("20c. request timestamp, response status and strike-selection method are recorded",
   AR["request_timestamp_utc"] == "2026-08-19T19:45:05Z"
   and AR["response_status"] == 200
   and AR["strike_selection_method"] == C.STRIKE_SELECTION_METHOD)
ck("20d. contract identity, expiration and strike are recorded",
   AR["contract_symbol_call"] == occ("ZZZ", "2026-08-21", "call", 185.0)
   and AR["contract_symbol_put"] == occ("ZZZ", "2026-08-21", "put", 185.0)
   and AR["expiration"] == "2026-08-21" and AR["strike"] == 185.0)
ck("20e. field completeness is disclosed, not imputed",
   AR["all_necessary_fields_present"] is True
   and "call_open_interest" in AR["design_fields_absent"]
   and AR["call_open_interest"] is None)
ck("20f. the underlying price source is recorded",
   AR["underlying_price_source"] == "alpaca:iex")
ck("20g. a provider with no feed designation cannot be resolved",
   refuses(lambda: C.resolve_feed("mystery", None)))
ck("20h. the universe snapshot records source, hash, timestamp and byte count",
   any(all(k in r for k in ("source_url", "response_sha256", "retrieved_utc",
                            "response_bytes", "source_kind", "constituent_count_raw"))
       for r in LEDGER_RECS if r.get("record_type") == "universe_snapshot"))
ck("20i. the universe retains identity fields only -- no weights, no market values",
   all(r.get("weights_retained") is False and r.get("market_values_retained") is False
       and all(set(c) == {"ticker", "issuer_name"} for c in r["constituents"])
       for r in LEDGER_RECS if r.get("record_type") == "universe_snapshot"))

# ------------------------------------------- 21. OCC identity + append-only
ck("21a. an OCC symbol yields expiration, type and strike",
   C.parse_occ_symbol("ZZZ260821C00185000") ==
   {"root": "ZZZ", "expiration_date": "2026-08-21", "option_type": "call",
    "strike": 185.0})
ck("21b. a malformed OCC symbol is refused",
   refuses(lambda: C.parse_occ_symbol("NOTASYMBOL")))
ck("21c. an impossible expiration in an OCC symbol is refused",
   refuses(lambda: C.parse_occ_symbol("ZZZ261332C00185000")))
ck("21d. nanosecond RFC3339 timestamps parse",
   C.parse_rfc3339("2026-08-19T19:45:00.123456789Z")
   == datetime(2026, 8, 19, 19, 45, 0, 123456, tzinfo=timezone.utc))
ck("21e. the adapter invents nothing: open interest stays absent",
   all(r["open_interest"] is None for r in ALPACA_ROWS)
   and all(r["bid"] is not None and r["ask"] is not None for r in ALPACA_ROWS))
ck("21f. a payload without a snapshots object is PROVIDER_SCHEMA_INCOMPATIBLE",
   refuses(lambda: C.alpaca_snapshot_rows({"bars": {}})))
ck("21g. the schema report flags whether the frozen arithmetic is implementable",
   C.alpaca_schema_report(ALPACA_ROWS)["frozen_arithmetic_implementable"] is True
   and C.alpaca_schema_report([])["frozen_arithmetic_implementable"] is False)

with tempfile.TemporaryDirectory() as td:
    m = Path(td) / "manifest.jsonl"
    rid1 = C.append_record(AR, m)
    ck("21h. an Alpaca record appends", m.exists() and rid1 == AR["record_id"])
    ck("21i. a duplicate Alpaca observation is refused",
       refuses(lambda: C.append_record(arec(), m)))
    before = m.read_bytes()
    C.append_record(arec(quote_timestamp_utc="2026-08-19T19:44:00Z"), m)
    after = m.read_bytes()
    ck("21j. append-only: the existing bytes are a strict prefix after appending",
       after.startswith(before) and len(after) > len(before))
    ck("21k. every stored Alpaca record still carries the label",
       all(json.loads(x)["feed_designation"] == C.ALPACA_LABEL
           for x in after.decode("utf-8").splitlines() if x.strip()))
    ck("21l. no stored Alpaca record carries an executable price",
       all("executable_straddle_cost" not in json.loads(x)
           for x in after.decode("utf-8").splitlines() if x.strip()))

with tempfile.TemporaryDirectory() as td:
    m = Path(td) / "manifest.jsonl"
    C.append_record(AR, m)
    real, C.MANIFEST = C.MANIFEST, m
    try:
        buf = io.StringIO()
        with redirect_stdout(buf):
            code = C.mode_validate()
        ck("21m. a clean Alpaca manifest validates", code == 0)
        with m.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(dict(AR, feed_designation="REALTIME_OPRA",
                                     record_id="y" * 32)) + "\n")
        buf = io.StringIO()
        with redirect_stdout(buf):
            code = C.mode_validate()
        ck("21n. a relabelled Alpaca record fails validation", code == 1)
    finally:
        C.MANIFEST = real

def _raises_network_block(fn):
    try:
        fn()
    except NetworkBlocked:
        return True
    except Exception:
        return False
    return False


ck("21o. sockets really are blocked: a raw socket cannot be opened",
   _raises_network_block(lambda: socket.socket()))
ck("21p. even a PERMITTED Alpaca request cannot reach the network in this suite",
   _raises_network_block(lambda: C.alpaca_get(
       "/v2/stocks/AAPL/trades/latest", {"feed": "iex"},
       env={"APCA_API_KEY_ID": "a", "APCA_API_SECRET_KEY": "b"})))

# -------------------------------------------------------------- no observation
ck("22a. no research manifest exists -- no observation has been collected",
   not C.MANIFEST.exists())
ck("22b. nothing in the provenance ledger is a study observation",
   all(r.get("data_class") in (C.VALIDATION_CLASS, C.PROVENANCE_CLASS)
       for r in LEDGER_RECS))


# ==========================================================================
# Provider Amendment 2 (2026-08-18) -- manual, official Cboe delayed capture
# ==========================================================================
AMEND2_REL = ("Live Signal Engine/Attention_Options_Dislocation/"
              "PROVIDER_AMENDMENT_2026-08-18_CBOE_MANUAL.md")
AMEND2_PATH = ROOT / AMEND2_REL
AMEND2 = AMEND2_PATH.read_text(encoding="utf-8") if AMEND2_PATH.exists() else ""

CBOE_HEADER = ("Expiration Date,Calls,Last Sale,Net,Bid,Ask,Volume,IV,Delta,Gamma,"
               "Open Interest,Strike,Puts,Last Sale,Net,Bid,Ask,Volume,IV,Delta,"
               "Gamma,Open Interest")


def cboe_csv(ticker="ZZZ", display="2026-08-20 19:40:00", price="186.00",
             exps=("2026-08-14", "2026-08-28", "2026-09-18"),
             strikes=(180.0, 185.0, 190.0), cbid="4.0", cask="4.4",
             pbid="3.6", pask="4.0", dupe=False, extra_rows=()):
    out = [f"{ticker} Zeta Systems Common Stock",
           f"Last Updated: {display}",
           f"Underlying Price: {price}",
           "", CBOE_HEADER]
    for e in exps:
        for k in strikes:
            out.append(f"{e},{ticker}C,99.0,0,{cbid},{cask},120,0.55,0.5,0.01,900,"
                       f"{k},{ticker}P,99.0,0,{pbid},{pask},120,0.55,-0.5,0.01,900")
            if dupe and e == "2026-08-28" and k == 185.0:
                out.append(out[-1])
    out.extend(extra_rows)
    return ("\n".join(out) + "\n").encode("utf-8")


def run_import(tmpdir, raw=None, **over):
    """Invoke the importer exactly as a human would, with sockets blocked."""
    d = Path(tmpdir)
    f = d / "cboe_download.csv"
    f.write_bytes(raw if raw is not None else cboe_csv())
    args = {"--ticker": "ZZZ", "--event-date": "2026-08-20",
            "--event-session": "AMC", "--retrieved-at": "2026-08-20T19:45:00Z",
            "--csv": str(f), "--timing-confirmed": "https://example.invalid/8-K"}
    args.update(over)
    argv = []
    for k, v in args.items():
        if v is not None:
            argv += [k, str(v)]
    real = C.MANIFEST
    C.MANIFEST = d / "manifest.jsonl"
    real_led = C.PROVENANCE_LEDGER
    C.PROVENANCE_LEDGER = d / "prov.jsonl"
    real_cache = C.CACHE
    C.CACHE = d / "cache"
    buf = io.StringIO()
    try:
        with redirect_stdout(buf):
            code = C.mode_cboe_import(argv)
        return code, buf.getvalue(), C.MANIFEST
    finally:
        C.MANIFEST, C.PROVENANCE_LEDGER, C.CACHE = real, real_led, real_cache


# --------------------------------------------- 23. amendment 2 precedence
A2_ADD = [x for x in git("log", "--diff-filter=A", "--format=%H", "--",
                         AMEND2_REL).splitlines() if x.strip()]
A2_SHA = A2_ADD[-1] if A2_ADD else ""
ck("23a. Amendment 2 is committed", bool(A2_SHA) and bool(AMEND2))
ck("23b. its commit changed exactly one path",
   len([x for x in git("show", "--name-only", "--format=", A2_SHA).splitlines()
        if x.strip()]) == 1)
ck("23c. the collector had no cboe-import at that commit",
   "cboe" not in git("show",
                     f"{A2_SHA}:tools/collect_attention_options_snapshot.py").lower())
ck("23d. no observation existed when it was frozen, so no file preceded it",
   not C.MANIFEST.exists())
ck("23e. it states the 401, the manual-only rule and the timestamp rule",
   "401" in AMEND2 and "prohibit" in AMEND2.lower()
   and "Download CSV" in AMEND2 and C.CBOE_LABEL in AMEND2)
ck("23f. it leaves model, features, selection rule and metric unchanged",
   "unchanged" in AMEND2.lower() and "No outcome" in AMEND2)
ck("23g. neither the design nor Amendment 1 was rewritten",
   hashlib.sha256(DESIGN_BYTES).hexdigest() == FROZEN_DESIGN_SHA256
   and len([x for x in git("log", "--format=%H", "--", AMEND_REL).splitlines()
            if x.strip()]) == 1)

# --------------------------------------------------- 24. zero network access
ck("24a. no Cboe URL literal exists anywhere in the collector",
   not any("cboe" in u.lower() for u in url_literals(SRC)))
ck("24b. no browser-automation or scraping dependency is present",
   not re.search(r"selenium|playwright|webdriver|puppeteer|beautifulsoup|bs4|"
                 r"requests_html|mechanize", SRC, re.I))
ck("24c. the import path issues no HTTP call at all",
   not re.search(r"(urlopen|http_json|alpaca_get|requests\.)",
                 SRC.split("def mode_cboe_import")[1].split("\ndef ")[0]))
with tempfile.TemporaryDirectory() as td:
    code, out, man = run_import(td)
    ck("24d. a valid manual file imports with sockets blocked", code == 0, out)
    IMPORTED = [json.loads(x) for x in
                man.read_text(encoding="utf-8").splitlines() if x.strip()]
ck("24e. the importer never printed a network action",
   "http" not in out.lower().replace("https://example.invalid/8-k", ""))

# ------------------------------------------- 25. label, provenance, arithmetic
IR = IMPORTED[0]
ck("25a. the manual-source label is carried",
   IR["feed_designation"] == "CBOE_MANUAL_DELAYED_NON_EXECUTABLE"
   and IR["provider"] == "cboe_manual")
ck("25b. the capture method is recorded as a human download",
   IR["capture_method"] == "HUMAN_MANUAL_DOWNLOAD")
ck("25c. filename, byte count and SHA-256 are recorded",
   IR["source_file_name"] == "cboe_download.csv"
   and IR["source_file_bytes"] == len(cboe_csv())
   and re.fullmatch(r"[0-9a-f]{64}", IR["source_file_sha256"]))
ck("25d. the SHA-256 is deterministic and content-addressed",
   C.sha256_bytes(cboe_csv()) == IR["source_file_sha256"]
   and C.sha256_bytes(cboe_csv()) != C.sha256_bytes(cboe_csv(price="187.00")))
ck("25e. a record stripped of the label is refused",
   refuses(lambda: C.assert_provider_provenance(dict(IR, feed_designation="LIVE"))))
ck("25f. a record without capture provenance is refused",
   refuses(lambda: C.assert_provider_provenance(dict(IR, source_file_sha256=""))))
ck("25g. the frozen implied-move arithmetic is applied unmodified",
   abs(IR["midpoint_implied_move"] - (4.2 + 3.8) / 186.0) < 1e-12
   and IR["call_mid"] == 4.2 and IR["put_mid"] == 3.8)

# ------------------------------------- 26. expiration and ATM selection
ck("26a. the first expiration strictly after the event is selected",
   IR["expiration"] == "2026-08-28")
ck("26b. the nearest strike to the underlying is selected", IR["strike"] == 185.0)
ck("26c. an ambiguous ATM (equidistant strikes) is refused",
   refuses(lambda: C.assert_unambiguous_atm([180.0, 190.0], 185.0)))
ck("26d. an unambiguous ATM resolves",
   C.assert_unambiguous_atm([180.0, 185.0, 190.0], 186.0) == 185.0)
with tempfile.TemporaryDirectory() as td:
    code, out, _ = run_import(td, raw=cboe_csv(strikes=(180.0, 190.0)),
                              **{"--underlying-price": "185.0"})
    ck("26e. the importer refuses an ambiguous ATM file", code == 3)
with tempfile.TemporaryDirectory() as td:
    code, out, _ = run_import(td, raw=cboe_csv(exps=("2026-08-14",)))
    ck("26f. a file with no expiration after the event is refused", code == 3)

# ------------------------------ 27. displayed timestamp vs retrieval timestamp
ck("27a. both timestamps are recorded separately",
   IR["quote_timestamp_utc"] == "2026-08-20T19:40:00Z"
   and IR["retrieved_at_utc"] == "2026-08-20T19:45:00Z"
   and IR["quote_timestamp_utc"] != IR["retrieved_at_utc"])
ck("27b. the underlying timestamp is recorded separately from retrieval",
   "underlying_timestamp_utc" in IR
   and IR["underlying_timestamp_utc"] != IR["retrieved_at_utc"])
ck("27c. a displayed timestamp later than retrieval is refused",
   refuses(lambda: C.assert_delayed_display_timing(
       datetime(2026, 8, 20, 19, 50, tzinfo=timezone.utc),
       datetime(2026, 8, 20, 19, 45, tzinfo=timezone.utc))))
ck("27d. a displayed timestamp equal to retrieval is refused",
   refuses(lambda: C.assert_delayed_display_timing(
       datetime(2026, 8, 20, 19, 45, tzinfo=timezone.utc),
       datetime(2026, 8, 20, 19, 45, tzinfo=timezone.utc))))
ck("27e. a displayed timestamp beyond the staleness bound is refused",
   refuses(lambda: C.assert_delayed_display_timing(
       datetime(2026, 8, 20, 17, 0, tzinfo=timezone.utc),
       datetime(2026, 8, 20, 19, 45, tzinfo=timezone.utc))))
ck("27f. a properly delayed timestamp is accepted",
   C.assert_delayed_display_timing(
       datetime(2026, 8, 20, 19, 30, tzinfo=timezone.utc),
       datetime(2026, 8, 20, 19, 45, tzinfo=timezone.utc)))
with tempfile.TemporaryDirectory() as td:
    code, _, _ = run_import(td, raw=cboe_csv(display="2026-08-20 17:00:00"))
    ck("27g. the importer refuses a stale file", code == 3)
ck("27h. a missing displayed timestamp is refused",
   refuses(lambda: C.parse_display_timestamp("")))

# ------------------------------- 28. wrong ticker / missing / crossed / duplicate
with tempfile.TemporaryDirectory() as td:
    code, _, _ = run_import(td, raw=cboe_csv(ticker="QQQQ"))
    ck("28a. a file for the wrong ticker is refused", code == 3)
with tempfile.TemporaryDirectory() as td:
    code, _, _ = run_import(td, raw=cboe_csv(cbid=""))
    ck("28b. a missing call bid is refused, never replaced by last", code == 3)
with tempfile.TemporaryDirectory() as td:
    code, _, _ = run_import(td, raw=cboe_csv(pask=""))
    ck("28c. a missing put ask is refused", code == 3)
with tempfile.TemporaryDirectory() as td:
    code, _, _ = run_import(td, raw=cboe_csv(cbid="9.0", cask="1.0"))
    ck("28d. a crossed market is refused", code == 3)
with tempfile.TemporaryDirectory() as td:
    code, _, _ = run_import(td, raw=cboe_csv(pbid="-1.0"))
    ck("28e. a negative quote is refused", code == 3)
with tempfile.TemporaryDirectory() as td:
    code, _, _ = run_import(td, raw=cboe_csv(dupe=True))
    ck("28f. duplicate contract rows are refused", code == 3)
with tempfile.TemporaryDirectory() as td:
    code, _, _ = run_import(td, raw=b"not,a,cboe,file\n1,2,3,4\n")
    ck("28g. an unrecognisable layout is refused rather than guessed", code == 3)
with tempfile.TemporaryDirectory() as td:
    code, _, _ = run_import(td, **{"--timing-confirmed": None})
    ck("28h. import without issuer/SEC-confirmed timing is refused", code == 3)

# --------------------------- 29. wrong window / post-announcement / append-only
with tempfile.TemporaryDirectory() as td:
    code, _, _ = run_import(td, **{"--retrieved-at": "2026-08-20T17:00:00Z"})
    ck("29a. a retrieval outside the frozen 15:45 ET window is refused", code == 3)
with tempfile.TemporaryDirectory() as td:
    code, _, _ = run_import(td, **{"--event-date": "2026-08-21"})
    ck("29b. a retrieval on the wrong snapshot day is refused", code == 3)
with tempfile.TemporaryDirectory() as td:
    code, _, _ = run_import(td, raw=cboe_csv(display="2026-08-20 20:30:00"),
                            **{"--retrieved-at": "2026-08-20T20:35:00Z"})
    ck("29c. a post-announcement displayed quote is refused", code == 3)
with tempfile.TemporaryDirectory() as td:
    code, out, man = run_import(td)
    before = man.read_bytes()
    C.MANIFEST, keep = man, C.MANIFEST
    try:
        ck("29d. re-importing the same observation is refused as a duplicate",
           refuses(lambda: C.append_record(IMPORTED[0], man)))
    finally:
        C.MANIFEST = keep
    ck("29e. append-only: the earlier bytes are untouched",
       man.read_bytes() == before and len(before) > 0)

# ------------------------------- 30. no executable price, P&L or trade claim
ck("30a. no executable straddle cost is emitted",
   "executable_straddle_cost" not in IR)
ck("30b. the execution stage stays deferred",
   IR["execution_economics_status"] == "OPRA_EXECUTION_DATA_UNAVAILABLE")
ck("30c. an executable price on a manual record is refused",
   refuses(lambda: C.assert_no_executable_claim(
       dict(IR, executable_straddle_cost=0.05))))
ck("30d. a simulated P&L field is refused",
   refuses(lambda: C.assert_no_executable_claim(dict(IR, straddle_pnl=1.0))))
ck("30e. a spread-adjusted return field is refused",
   refuses(lambda: C.assert_no_executable_claim(dict(IR, spread_aware_net_return=1.0))))
ck("30f. a trade instruction field is refused",
   refuses(lambda: C.assert_no_prohibited_fields(dict(IR, order_side="BUY"))))
ck("30g. the importer emits no trade instruction text",
   not re.search(r"\b(buy|sell|entry|exit|position size)\b", out, re.I))

# ------------------------------------- 31. earlier Alpaca evidence intact
ALP = [r for r in LEDGER_RECS if r.get("provider") == "alpaca"]
ck("31a. the Alpaca 401 connectivity evidence is still present",
   any(r.get("response_status") == 401
       and r.get("outcome") == "AUTH_OR_ENTITLEMENT_FAILED" for r in ALP))
ck("31b. the Alpaca auth cross-check is still present",
   any(r.get("record_type") == "auth_failure_cross_check"
       and r.get("conclusion") == "CREDENTIALS_REJECTED_BY_PROVIDER"
       for r in LEDGER_RECS))
ck("31c. Amendment 1 is still byte-identical to its frozen hash",
   hashlib.sha256(AMEND_PATH.read_bytes()).hexdigest()
   == "0417380b3115255ed65956a54b2120f789334a8f5a9afcde61e8ae184547df0f")
ck("31d. no fixture test left a real observation behind",
   not C.MANIFEST.exists())


# ----------------------------- 32. ROST pre-capture scheduling (non-observation)
SCHEDULE_SRC = SRC.split("def mode_schedule")[1].split(chr(10) + "def ")[0]
SCHED = [r for r in LEDGER_RECS if r.get("record_type") == C.SCHEDULE_RECORD_TYPE]
ck("32a. exactly one confirmed prospective event is scheduled", len(SCHED) == 1)
S1 = SCHED[0] if SCHED else {}
ck("32b. release time and conference-call time are distinguished, not conflated",
   S1.get("earnings_release_time") == "approximately 16:00 ET"
   and S1.get("conference_call_time") == "16:15 ET"
   and S1["earnings_release_time"] != S1["conference_call_time"])
ck("32c. the identity, date, session and official IR source are recorded",
   S1.get("ticker") == "ROST" and S1.get("event_date") == "2026-08-20"
   and S1.get("announcement_session") == "AMC"
   and S1.get("source_classification") == "OFFICIAL_ISSUER_INVESTOR_RELATIONS"
   and "investors.rossstores.com" in S1.get("official_source_url", ""))
ck("32d. both manual capture clocks denote the same instant",
   datetime.fromisoformat(S1["manual_capture_at_et"])
   == datetime.fromisoformat(S1["manual_capture_at_ct"]))
ck("32e. the event identity is deterministic",
   C.schedule_event_id("ROST", "2026-08-20", "AMC") == S1.get("schedule_event_id"))
ck("32f. scheduling happened BEFORE the event",
   datetime.fromisoformat(S1["confirmed_utc"].replace("Z", "+00:00"))
   < datetime.fromisoformat(S1["manual_capture_at_et"]))
ck("32g. a schedule is NOT an observation",
   S1.get("status") == "SCHEDULED_NOT_COLLECTED" and S1.get("is_observation") is False
   and S1.get("data_class") != C.RESEARCH_CLASS)
ck("32h. nothing has been collected for it",
   all(S1.get(k) is False for k in ("trends_input_collected", "option_chain_collected",
                                    "outcome_collected", "observation_collected",
                                    "cboe_accessed_by_code")))
ck("32i. scheduling did not create the research manifest", not C.MANIFEST.exists())
ck("32j. duplicate scheduling is refused",
   refuses(lambda: C.append_provenance(dict(S1), C.PROVENANCE_LEDGER)))
ck("32k. a schedule that omits the not-collected status is refused",
   refuses(lambda: C.append_provenance(
       dict(S1, status="COLLECTED", schedule_event_id="z" * 32),
       C.PROVENANCE_LEDGER)))
ck("32l. ROST is in the committed official universe",
   any(c["ticker"] == "ROST" for r in LEDGER_RECS
       if r.get("record_type") == "universe_snapshot" for c in r["constituents"]))
ck("32m. the frozen snapshot day and T-2 cutoff are applied, not improvised",
   S1.get("snapshot_date") == C.snapshot_date_for("2026-08-20", "AMC")
   and S1.get("search_window_end") == C.search_window_end("2026-08-20")
   and S1.get("snapshot_target_et") == C.SNAPSHOT_TARGET_ET)
ck("32n. the ticker Trends query follows the frozen rule with no new judgment",
   S1.get("resolved_ticker_query") == "ROST stock")
ck("32o. the unresolved issuer-name query is disclosed, not invented",
   "UNRESOLVED" in S1.get("issuer_name_query_status", ""))
ck("32p. no outcome was accessed for this event",
   not any(k for k in S1 if re.search(r"realized|post_?event|return|surprise", k, re.I))
   and S1.get("outcome_collected") is False)
ck("32q. scheduling reached no network: no Cboe or Trends request exists in the path",
   not re.search(r"(urlopen|urlretrieve|http_json|alpaca_get|requests\.|socket|pytrends"
                 r"|TrendReq|webdriver)",
                 SCHEDULE_SRC, re.I)
   and not any("cboe" in u.lower() or "google" in u.lower()
               for u in url_literals(SRC)))



# --------------- 33. ROST Trends leg: identity frozen, method underspecified
QID = [r for r in LEDGER_RECS if r.get("record_type") == "QUERY_IDENTITY_RULE_FROZEN"]
UND = [r for r in LEDGER_RECS if r.get("record_type") == "TRENDS_METHOD_UNDERSPECIFIED"]
Q1 = QID[0] if QID else {}
U1 = UND[0] if UND else {}
QID_SHA = [x for x in git("log", "--diff-filter=M", "--format=%H", "-S",
                          "QUERY_IDENTITY_RULE_FROZEN", "--",
                          "Live Signal Engine/Attention_Options_Dislocation/"
                          "collection_provenance.jsonl").splitlines() if x.strip()]
ck("33a. the query-identity rule is committed", bool(QID) and bool(QID_SHA))
ck("33b. its commit changed only the ledger",
   QID_SHA and [x for x in git("show", "--name-only", "--format=", QID_SHA[-1]).splitlines()
                if x.strip()] ==
   ["Live Signal Engine/Attention_Options_Dislocation/collection_provenance.jsonl"])
ck("33c. the rule was fixed before any Trends request and before any outcome",
   Q1.get("fixed_before_any_trends_request") is True
   and Q1.get("fixed_before_any_outcome") is True
   and Q1.get("trends_request_made") is False
   and Q1.get("uses_identity_information_only") is True)
R0 = (Q1.get("resolutions") or [{}])[0]
ck("33d. the exact ROST queries and cutoff are frozen",
   R0.get("ticker_query") == "ROST stock"
   and R0.get("issuer_query") == "Ross Stores, Inc. stock"
   and R0.get("data_cutoff") == "2026-08-18"
   and R0.get("data_cutoff") == C.search_window_end("2026-08-20"))
ck("33e. the issuer name came from the official IR announcement, not from stripping "
   "a Nasdaq security description",
   R0.get("resolved_by_rule_clause") == 1
   and R0.get("source_classification") == "OFFICIAL_ISSUER_INVESTOR_RELATIONS"
   and "investors.rossstores.com" in R0.get("official_source_url", "")
   and R0.get("issuer_display_name") == "Ross Stores, Inc.")
ck("33f. the rule forbids deriving issuer names by stripping words",
   any("stripping words" in str(x) for x in Q1.get("rule", [])))
ck("33g. the method gate recorded that the frozen method is underspecified", bool(U1))
ck("33h. it names the fields that materially determine gst_zscore",
   {m["field"] for m in U1.get("missing_fields", [])} >=
   {"gst_zscore_arithmetic", "baseline_window", "query_batching_comparison_method",
    "geography_geo", "category_cat", "google_property_gprop", "timeframe",
    "partial_weekly_period_treatment"})
ck("33i. no gst_zscore definition exists anywhere in this study to implement",
   "gst_zscore" not in DESIGN and "gst_zscore" not in SRC)
ck("33j. the run STOPPED before the first request; nothing was retrieved or computed",
   U1.get("trends_request_made") is False
   and U1.get("trends_attempts_executed") == 0
   and U1.get("gst_zscore_computed") is False
   and U1.get("rule_invented_or_optimised_after_seeing_values") is False)
ck("33k. no HYP-01 GST construct was borrowed to fill the gap",
   U1.get("hyp01_gst_construct_not_borrowed") is True)
ck("33l. no options, Cboe, price, return or outcome was accessed for the Trends leg",
   U1.get("options_or_cboe_accessed") is False
   and U1.get("outcome_accessed") is False
   and U1.get("observation_created") is False)
ck("33m. no Trends network client was added to the collector",
   not re.search(r"pytrends|TrendReq|trends\.google", SRC, re.I))
ck("33n. no completed observation and no snapshot manifest exist",
   not C.MANIFEST.exists()
   and all(r.get("data_class") != C.RESEARCH_CLASS for r in LEDGER_RECS))
ck("33o. this branch depends on no teammate branch, code or data",
   not re.search(r"import\s+(pytrends|gst_market_response)", SRC))

print()
print(f"{CHECKS - len(FAIL)} passed, {len(FAIL)} failed, {CHECKS} assertions total")
if FAIL:
    print(f"{len(FAIL)} FAILURE(S): {FAIL}")
    sys.exit(1)
print("ALL ATTENTION-OPTIONS DISLOCATION CHECKS PASSED")
sys.exit(0)

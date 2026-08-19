#!/usr/bin/env python3
"""Attention-Options Dislocation -- prospective input collector.

Implements the collection stage of
`Live Signal Engine/Attention_Options_Dislocation/FROZEN_DESIGN_v1.0.md`.

Modes:
    doctor    provider readiness, credential PRESENCE only -- never a value or a length
    calendar  next-90-day candidate earnings dates (scheduling input, unverified)
    snapshot  timestamped pre-event input snapshot
    validate  re-check stored snapshots: schema, timestamps, hashes, uniqueness, eligibility

This module NEVER computes a return, opens a post-event price, or calls a trading,
account or order endpoint. There is no order code path to disable.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import os
import re
import sys
import urllib.error
import urllib.parse
import urllib.request
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parents[1]
STUDY = ROOT / "Live Signal Engine" / "Attention_Options_Dislocation"
MANIFEST = STUDY / "snapshot_manifest.jsonl"
CACHE = Path(os.environ.get("AOD_CACHE_DIR") or (ROOT.parent / "gst-aod-cache"))

ET = ZoneInfo("America/New_York")
SNAPSHOT_TARGET_ET = "15:45"
SEARCH_CUTOFF_DAYS = 2
CALENDAR_HORIZON_DAYS = 90
DELAYED_LABEL = "DELAYED_15_MINUTES"
REALTIME_LABEL = "REALTIME"
SCHEDULING_LABEL = "SCHEDULING_INPUT_UNVERIFIED"

CRED_VARS = ("ALPHAVANTAGE_API_KEY", "TRADIER_TOKEN", "TRADIER_SANDBOX_TOKEN",
             "GOOGLE_TRENDS_ALPHA_KEY", "APCA_API_KEY_ID", "APCA_API_SECRET_KEY")

# ---------------------------------------------------------------------------
# Provider Amendment 1 (2026-08-17) -- PROVIDER_AMENDMENT_2026-08-17_ALPACA.md
#
# Tradier requires brokerage onboarding with a real legal identity and a real SSN.
# No fabricated identity is used, so Tradier stays unavailable. Alpaca Paper Only's
# free `indicative` options feed is the study's initial options-data provider.
#
# The amendment is ADDITIVE. It changes no statistical rule, attention feature,
# event rule, timestamp cutoff, contract-selection rule or primary forecast metric.
# ---------------------------------------------------------------------------
ALPACA_CRED_VARS = ("APCA_API_KEY_ID", "APCA_API_SECRET_KEY")
ALPACA_DATA_HOST = "data.alpaca.markets"
ALPACA_DATA_BASE = "https://" + ALPACA_DATA_HOST
ALPACA_OPTIONS_FEED = "indicative"
ALPACA_STOCK_FEED = "iex"
ALPACA_LABEL = "ALPACA_INDICATIVE_NON_EXECUTABLE"
ALPACA_OPTIONS_SNAPSHOT_PATH = "/v1beta1/options/snapshots/"

# ---------------------------------------------------------------------------
# Provider Amendment 2 (2026-08-18) -- PROVIDER_AMENDMENT_2026-08-18_CBOE_MANUAL.md
#
# Alpaca authentication failed (HTTP 401) and provider-acquisition work stopped.
# The replacement source is the official Cboe Delayed Quotes dashboard, which
# permits MANUAL ticker entry and CSV download but explicitly PROHIBITS automated
# extraction.
#
# Therefore NO CODE HERE REQUESTS, SCRAPES, CLICKS, DOWNLOADS OR OTHERWISE ACCESSES
# CBOE. A human downloads the file by hand; this module only reads a local file.
# There is no Cboe URL, HTTP client, browser driver or scheduled fetch in this
# repository, and none may be added.
# ---------------------------------------------------------------------------
CBOE_LABEL = "CBOE_MANUAL_DELAYED_NON_EXECUTABLE"
CBOE_PROVIDER = "cboe_manual"
CBOE_FEED = "delayed_quotes_manual_csv"
CBOE_CAPTURE_METHOD = "HUMAN_MANUAL_DOWNLOAD"
# The displayed market-data timestamp is the information cutoff. A delayed quote
# must PRECEDE its download, and not by more than this.
CBOE_MAX_DISPLAY_LAG_SECONDS = 3600

# A feed whose prices are not executable. No executable cost, P&L or trade
# instruction may ever be derived from a record carrying one of these.
NON_EXECUTABLE_LABELS = frozenset()   # populated below, after ALPACA_LABEL exists

SYSTEM_VALIDATION_LABEL = "NON_EVENT_SYSTEM_VALIDATION_ONLY"
DEFERRED_EXECUTION_STATUS = "OPRA_EXECUTION_DATA_UNAVAILABLE"
SCHEMA_INCOMPATIBLE_STATUS = "PROVIDER_SCHEMA_INCOMPATIBLE"
STRIKE_SELECTION_METHOD = "NEAREST_STRIKE_TO_CONTEMPORANEOUS_UNDERLYING"

NON_EXECUTABLE_LABELS = frozenset({ALPACA_LABEL, CBOE_LABEL})

# --------------------------------------------------------------------------
# TRENDS_METHOD_FROZEN (2026-08-19). Every value below was fixed in the ledger
# BEFORE this code existed and before any Trends request. Nothing here may be
# retuned after seeing a value.
# --------------------------------------------------------------------------
TRENDS_GEO = "US"
TRENDS_CAT = 0
TRENDS_GPROP = ""
TRENDS_CUTOFF = "2026-08-18"
TRENDS_WINDOW_DAYS = 730
TRENDS_BASELINE_WEEKS = 52
TRENDS_ZSCORE_DDOF = 1
TRENDS_REQUESTS_PER_QUERY_PER_DATE = 1
TRENDS_RETRY_POLICY = "NONE"
TRENDS_DIR = Path(r"C:\Users\hakur\Downloads\gst-source-quarantine"
                  r"\TRENDS_2026-08-20_ROST")
TRENDS_QUERIES = {"ticker_query": "ROST stock",
                  "issuer_query": "Ross Stores, Inc. stock"}
TRENDS_SCHEDULE = {"T-1": "2026-08-19", "T0": "2026-08-20"}
TRENDS_ATTEMPT_TYPE = "TRENDS_ATTEMPT"
TRENDS_DAILY_TYPE = "TRENDS_DAILY_COMPOSITE"
TRENDS_FINAL_TYPE = "TRENDS_EVENT_SCORE"
TRENDS_STATUS_CAPTURED = "PRE_EVENT_TRENDS_INPUT_CAPTURED"

SCHEDULE_RECORD_TYPE = "PROSPECTIVE_EVENT_SCHEDULE_CONFIRMED"
SCHEDULE_STATUS = "SCHEDULED_NOT_COLLECTED"
OFFICIAL_IR_SOURCE = "OFFICIAL_ISSUER_INVESTOR_RELATIONS"

RESEARCH_CLASS = "RESEARCH"
VALIDATION_CLASS = "SYSTEM_VALIDATION"
PROVENANCE_CLASS = "PROVENANCE"

# Repository-committed, append-only, and explicitly NOT the research panel.
PROVENANCE_LEDGER = STUDY / "collection_provenance.jsonl"

# A quote older than this is stale. The indicative feed is not a latency guarantee.
MAX_QUOTE_STALENESS_SECONDS = 900
# Call and put must be contemporaneous for a straddle midpoint to mean anything.
MAX_LEG_DIVERGENCE_SECONDS = 300
# Tolerance around the frozen 15:45 ET snapshot target.
SNAPSHOT_WINDOW_TOLERANCE_MINUTES = 10

# Fail-closed endpoint guard. Only these market-data path prefixes may be requested.
ALPACA_ALLOWED_PATH_PREFIXES = ("/v2/stocks/", "/v1beta1/options/")
# Anything that could reach an account, a position, an order or the trading API.
ALPACA_FORBIDDEN_ENDPOINT = re.compile(
    r"((paper-)?api|broker-api)\.alpaca\.markets"
    r"|/v2/(account|positions?|orders?|assets|watchlists|clock|calendar)"
    r"|/v2/options/contracts"
    r"|/orders?\b|/positions?\b|/trading\b", re.I)

# Official constituent sources only. Scraped/aggregator/generated lists are prohibited.
UNIVERSE_SOURCES = [
    # Host corrected www.nasdaq.com -> api.nasdaq.com BEFORE any universe request
    # was issued. Same official Nasdaq constituent source; only the API host differs.
    {"rank": 1, "name": "Nasdaq-100 official constituent source",
     "url": "https://api.nasdaq.com/api/quote/list-type/nasdaq100",
     "kind": "OFFICIAL_INDEX_CONSTITUENTS"},
    {"rank": 2, "name": "Invesco QQQ official holdings file (disclosed index proxy)",
     "url": ("https://www.invesco.com/us/financial-products/etfs/holdings/main/"
             "holdings/0?audienceType=Investor&action=download&ticker=QQQ"),
     "kind": "OFFICIAL_ETF_HOLDINGS_PROXY"},
]

PERMITTED_MANIFEST_FIELDS = (
    "schema_version", "record_id", "ticker", "issuer_name", "event_date",
    "announcement_session", "snapshot_date", "snapshot_timestamp_utc",
    "quote_timestamp_utc", "provider", "quote_latency_label", "underlying_price",
    "expiration", "strike", "call_bid", "call_ask", "call_mid", "call_last",
    "call_volume", "call_open_interest", "call_iv", "put_bid", "put_ask", "put_mid",
    "put_last", "put_volume", "put_open_interest", "put_iv",
    "midpoint_implied_move", "executable_straddle_cost",
    "search_window_end", "search_features", "raw_response_sha256",
    "event_timing_status", "universe_source_kind", "collected_utc",
    # Provider Amendment 1: provenance that is mandatory, not decorative.
    "feed", "feed_designation", "data_class", "strike_selection_method",
    "request_timestamp_utc", "response_status", "contract_symbol_call",
    "contract_symbol_put", "underlying_price_source", "execution_economics_status",
    "all_necessary_fields_present", "design_fields_absent",
    # Provider Amendment 2: manual capture provenance.
    "retrieved_at_utc", "underlying_timestamp_utc", "capture_method",
    "source_file_name", "source_file_bytes", "source_file_sha256",
)

# Recorded by frozen design section 4 for each leg. Absence is disclosed, not hidden.
DESIGN_RECORDED_FIELDS = (
    "call_bid", "call_ask", "call_mid", "call_last", "call_volume",
    "call_open_interest", "call_iv", "put_bid", "put_ask", "put_mid", "put_last",
    "put_volume", "put_open_interest", "put_iv",
    "quote_timestamp_utc", "expiration", "strike", "provider",
)
# Without every one of these the record is REFUSED, never repaired.
MANDATORY_RECORD_FIELDS = (
    "call_bid", "call_ask", "put_bid", "put_ask", "quote_timestamp_utc",
    "expiration", "strike", "underlying_price", "provider", "feed",
    "feed_designation", "data_class",
)

# While the indicative feed is in force the execution-economics stage is deferred.
EXECUTABLE_CLAIM_FIELD = re.compile(
    r"(executable|spread_aware|spread_cost|net_return|straddle_pnl|straddle_return"
    r"|tradeable|tradable|nbbo|alpha)", re.I)

PROHIBITED_FIELD = re.compile(
    r"(realized|return|post_?event|outcome|pnl|profit|order|position|fill|trade_id)", re.I)


class Refused(ValueError):
    """A record that violates a frozen rule. Refused, never repaired."""


# ------------------------------------------------------------------ credentials

def credential_presence(env=None):
    """PRESENCE ONLY. Never returns, prints, hashes or measures a credential value."""
    e = os.environ if env is None else env
    return {v: bool((e.get(v) or "").strip()) for v in CRED_VARS}


def options_provider(env=None):
    """Deterministic, single-shot provider selection. There is no silent fallback.

    Provider Amendment 1 makes Alpaca Paper Only the initial options-data provider.
    A provider that is selected and then FAILS is never retried against another
    provider -- the caller stops. Selection happens once, before any request, and is
    always reported.
    """
    e = os.environ if env is None else env
    kid = (e.get("APCA_API_KEY_ID") or "").strip()
    sec = (e.get("APCA_API_SECRET_KEY") or "").strip()
    if kid and sec:
        return ("alpaca", ALPACA_DATA_BASE, ALPACA_LABEL, "APCA_API_KEY_ID")
    if kid or sec:
        # Half a credential pair is a configuration error, not an invitation to
        # quietly use a different provider.
        raise Refused("exactly one Alpaca variable is set; both are required and no "
                      "other provider is substituted")
    if (e.get("TRADIER_TOKEN") or "").strip():
        return ("tradier", "https://api.tradier.com", REALTIME_LABEL, "TRADIER_TOKEN")
    if (e.get("TRADIER_SANDBOX_TOKEN") or "").strip():
        return ("tradier_sandbox", "https://sandbox.tradier.com", DELAYED_LABEL,
                "TRADIER_SANDBOX_TOKEN")
    return (None, None, None, None)


def redact(text, env=None):
    """Strip any credential value that may have reached a message."""
    e = os.environ if env is None else env
    s = str(text)
    for v in CRED_VARS:
        val = (e.get(v) or "").strip()
        if val:
            s = s.replace(val, "<REDACTED>")
    return re.sub(r"(Bearer\s+)[A-Za-z0-9._\-]+", r"\1<REDACTED>", s)


def sha256_bytes(b):
    return hashlib.sha256(b).hexdigest()


# ---------------------------------------------------------------- option chain

def _num(v):
    if v in (None, "", "None"):
        return None
    try:
        f = float(v)
    except (TypeError, ValueError):
        return None
    return f if f == f else None


def first_expiration_after(expirations, event_date):
    """Nearest expiration STRICTLY after the event date."""
    ev = event_date if isinstance(event_date, date) else date.fromisoformat(str(event_date))
    later = sorted(d for d in (date.fromisoformat(str(x)) for x in expirations) if d > ev)
    if not later:
        raise Refused("no expiration strictly after the event date")
    return later[0].isoformat()


def nearest_strike(chain, underlying_price):
    """Strike nearest the contemporaneous underlying price."""
    strikes = sorted({_num(o.get("strike")) for o in chain
                      if _num(o.get("strike")) is not None})
    if not strikes:
        raise Refused("no strikes in chain")
    return min(strikes, key=lambda s: (abs(s - underlying_price), s))


def leg(chain, strike, kind):
    for o in chain:
        if _num(o.get("strike")) == strike and str(o.get("option_type")).lower() == kind:
            return o
    raise Refused(f"no {kind} leg at strike {strike}")


def quote_fields(o, kind):
    """Bid/ask are mandatory. Last is recorded but NEVER substituted for a missing side."""
    bid, ask = _num(o.get("bid")), _num(o.get("ask"))
    if bid is None or ask is None:
        raise Refused(f"{kind} leg missing bid or ask; last-price substitution is prohibited")
    if bid > ask:
        raise Refused(f"{kind} leg crossed market: bid {bid} > ask {ask}")
    return {
        f"{kind}_bid": bid, f"{kind}_ask": ask, f"{kind}_mid": (bid + ask) / 2.0,
        f"{kind}_last": _num(o.get("last")),
        f"{kind}_volume": _num(o.get("volume")),
        f"{kind}_open_interest": _num(o.get("open_interest")),
        f"{kind}_iv": _num((o.get("greeks") or {}).get("mid_iv")
                           if isinstance(o.get("greeks"), dict) else o.get("iv")),
    }


def implied_move(call_mid, put_mid, underlying_price):
    if not underlying_price or underlying_price <= 0:
        raise Refused("non-positive underlying price")
    return (call_mid + put_mid) / underlying_price


def straddle_cost(call_ask, put_ask, underlying_price):
    if not underlying_price or underlying_price <= 0:
        raise Refused("non-positive underlying price")
    return (call_ask + put_ask) / underlying_price


# ---------------------------------------------------------------- Alpaca layer
#
# Provider Amendment 1. Market data ONLY. There is no account, position, order or
# trading code path here, and the guard below fails CLOSED: a URL must be on the
# allowlist to be requested at all, rather than merely not on a blocklist.

def assert_market_data_endpoint(url):
    """Fail closed. Only https market-data paths on the Alpaca data host may be used."""
    p = urllib.parse.urlsplit(str(url))
    if p.scheme != "https":
        raise Refused("non-https endpoint refused: %r" % (p.scheme,))
    if (p.hostname or "").lower() != ALPACA_DATA_HOST:
        raise Refused("host is not on the market-data allowlist: %r" % (p.hostname,))
    if ALPACA_FORBIDDEN_ENDPOINT.search(str(url)):
        raise Refused("order/trading/account endpoint refused: %s" % (p.path,))
    if not any(p.path.startswith(pre) for pre in ALPACA_ALLOWED_PATH_PREFIXES):
        raise Refused("path is not on the market-data allowlist: %s" % (p.path,))
    return True


def alpaca_credential_presence(env=None):
    """PRESENCE ONLY, for the two approved variables. Never a value or a length."""
    e = os.environ if env is None else env
    return {v: bool((e.get(v) or "").strip()) for v in ALPACA_CRED_VARS}


def alpaca_auth_headers(env=None):
    """Read credentials ONLY from the two approved environment variables.

    The returned mapping is passed straight to urllib and is never printed, logged,
    serialized, hashed or stored.
    """
    e = os.environ if env is None else env
    kid = (e.get("APCA_API_KEY_ID") or "").strip()
    sec = (e.get("APCA_API_SECRET_KEY") or "").strip()
    if not kid or not sec:
        raise Refused("Alpaca credentials absent; no request issued and no other "
                      "provider substituted")
    return {"APCA-API-KEY-ID": kid, "APCA-API-SECRET-KEY": sec,
            "Accept": "application/json"}


def alpaca_get(path, params=None, env=None, timeout=45, opener=None):
    """One authenticated market-data GET. Returns (status, raw_bytes).

    Never prints a response body, a header or a price. A failure is returned to the
    caller, which STOPS; it is never retried against a different provider.
    """
    url = ALPACA_DATA_BASE + path
    if params:
        url += "?" + urllib.parse.urlencode(params)
    assert_market_data_endpoint(url)
    req = urllib.request.Request(url, headers=alpaca_auth_headers(env), method="GET")
    send = opener or urllib.request.urlopen
    try:
        with send(req, timeout=timeout) as r:
            return (getattr(r, "status", 200), r.read())
    except urllib.error.HTTPError as e:
        return (e.code, e.read() or b"")


# ------------------------------------------------------------ OCC symbol identity

def parse_occ_symbol(sym):
    """Contract identity from the OCC symbol: root, expiration, type, strike."""
    s = str(sym or "").strip().upper()
    if (len(s) < 16 or not s[-8:].isdigit() or s[-9] not in "CP"
            or not s[-15:-9].isdigit() or not s[:-15].isalnum()):
        raise Refused("unparseable OCC option symbol: %r" % (sym,))
    root, ymd, cp, strike = s[:-15], s[-15:-9], s[-9], s[-8:]
    exp = "20%s-%s-%s" % (ymd[0:2], ymd[2:4], ymd[4:6])
    try:
        date.fromisoformat(exp)
    except ValueError:
        raise Refused("OCC symbol carries an impossible expiration: %r" % (sym,))
    return {"root": root, "expiration_date": exp,
            "option_type": "call" if cp == "C" else "put",
            "strike": int(strike) / 1000.0}


def parse_rfc3339(ts):
    """Alpaca stamps nanoseconds; datetime accepts at most microseconds."""
    s = str(ts or "").strip()
    if not s:
        raise Refused("missing timestamp; provenance is mandatory")
    s = s.replace("Z", "+00:00")
    m = re.match(r"^(.*?\.\d{1,6})\d*((?:[+-]\d{2}:\d{2})?)$", s)
    if m:
        s = m.group(1) + (m.group(2) or "+00:00")
    try:
        d = datetime.fromisoformat(s)
    except ValueError:
        raise Refused("unparseable timestamp: %r" % (ts,))
    return d if d.tzinfo else d.replace(tzinfo=timezone.utc)


def utc_second_stamp(dt):
    return dt.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


# --------------------------------------------------------------- chain adapter

def alpaca_snapshot_rows(payload):
    """Map an Alpaca options-snapshot payload onto the frozen internal chain schema.

    Field NAMES are translated; nothing is invented. A value Alpaca does not supply
    stays None so that its absence is visible rather than silently imputed. The
    frozen selection and arithmetic functions then run unchanged on these rows.
    """
    if not isinstance(payload, dict) or not isinstance(payload.get("snapshots"), dict):
        raise Refused("%s: response has no 'snapshots' object" % SCHEMA_INCOMPATIBLE_STATUS)
    rows = []
    for sym, s in payload["snapshots"].items():
        meta = parse_occ_symbol(sym)
        s = s or {}
        q = s.get("latestQuote") or {}
        t = s.get("latestTrade") or {}
        bar = s.get("dailyBar") or {}
        rows.append({
            "occ_symbol": str(sym).upper(),
            "expiration_date": meta["expiration_date"],
            "option_type": meta["option_type"],
            "strike": meta["strike"],
            "bid": _num(q.get("bp")),
            "ask": _num(q.get("ap")),
            "quote_timestamp": q.get("t"),
            "last": _num(t.get("p")),
            "volume": _num(bar.get("v")),
            # Alpaca's options snapshot does not carry open interest; it stays None.
            "open_interest": _num(s.get("openInterest")),
            "iv": _num(s.get("impliedVolatility")),
        })
    return rows


def alpaca_schema_report(rows):
    """Field presence counts only. Never a price, never a body."""
    fields = ("expiration_date", "option_type", "strike", "bid", "ask",
              "quote_timestamp", "last", "volume", "open_interest", "iv")
    n = len(rows)
    present = {f: sum(1 for r in rows if r.get(f) not in (None, "")) for f in fields}
    # The frozen calculation needs identity + bid/ask + a quote timestamp. Nothing else.
    required = ("expiration_date", "option_type", "strike", "bid", "ask",
                "quote_timestamp")
    implementable = bool(n) and all(present[f] > 0 for f in required)
    return {"contracts": n, "field_presence": present,
            "fields_required_by_frozen_arithmetic": list(required),
            "frozen_arithmetic_implementable": implementable,
            "fields_absent_from_provider": sorted(f for f in fields if present[f] == 0)}


# -------------------------------------------------------------- refusal rules

def assert_leg_usable(row, kind, now_utc=None,
                      max_staleness=MAX_QUOTE_STALENESS_SECONDS):
    """Missing, degenerate, crossed, stale or future-dated legs are REFUSED.

    A zero or negative ask is treated as a MISSING market, not as a price. The
    indicative feed publishes empty two-sided quotes and they are not repaired.
    """
    bid, ask = _num(row.get("bid")), _num(row.get("ask"))
    if bid is None or ask is None:
        raise Refused("%s leg missing bid or ask; last-price substitution is "
                      "prohibited" % kind)
    if ask <= 0:
        raise Refused("%s leg has a non-positive ask -- treated as a MISSING market, "
                      "never repaired" % kind)
    if bid < 0:
        raise Refused("%s leg has a negative bid" % kind)
    if bid > ask:
        raise Refused("%s leg crossed market: bid %s > ask %s" % (kind, bid, ask))
    q = parse_rfc3339(row.get("quote_timestamp"))
    now = now_utc or datetime.now(timezone.utc)
    age = (now - q).total_seconds()
    if age > max_staleness:
        raise Refused("%s leg quote is stale by %.0fs (limit %ds)"
                      % (kind, age, max_staleness))
    if age < -60:
        raise Refused("%s leg quote timestamp is in the future -- internally "
                      "inconsistent" % kind)
    return q


def assert_legs_contemporaneous(call_ts, put_ts,
                                max_divergence=MAX_LEG_DIVERGENCE_SECONDS):
    """A straddle midpoint from two non-contemporaneous quotes is meaningless."""
    gap = abs((call_ts - put_ts).total_seconds())
    if gap > max_divergence:
        raise Refused("call and put quotes diverge by %.0fs (limit %ds) -- internally "
                      "inconsistent straddle" % (gap, max_divergence))
    return True


def assert_internally_consistent(rec):
    """Cross-field checks that no single-field rule would catch."""
    if rec.get("call_mid") is not None and rec.get("call_bid") is not None:
        if not (rec["call_bid"] <= rec["call_mid"] <= rec["call_ask"]):
            raise Refused("call midpoint lies outside its own bid/ask")
    if rec.get("put_mid") is not None and rec.get("put_bid") is not None:
        if not (rec["put_bid"] <= rec["put_mid"] <= rec["put_ask"]):
            raise Refused("put midpoint lies outside its own bid/ask")
    m = rec.get("midpoint_implied_move")
    if m is None or not (m == m) or m <= 0:
        raise Refused("implied move is missing, non-finite or non-positive")
    if m >= 1.0:
        raise Refused("implied move of %.3f exceeds 100%% of the underlying -- "
                      "internally inconsistent" % m)
    exp = date.fromisoformat(str(rec["expiration"]))
    ev = date.fromisoformat(str(rec["event_date"]))
    if exp <= ev:
        raise Refused("expiration is not strictly after the event date")
    if rec.get("contract_symbol_call") and rec.get("contract_symbol_put"):
        for sym, kind in ((rec["contract_symbol_call"], "call"),
                          (rec["contract_symbol_put"], "put")):
            meta = parse_occ_symbol(sym)
            if meta["option_type"] != kind:
                raise Refused("contract symbol %r is not a %s" % (sym, kind))
            if abs(meta["strike"] - float(rec["strike"])) > 1e-9:
                raise Refused("contract symbol strike disagrees with the record")
            if meta["expiration_date"] != str(rec["expiration"]):
                raise Refused("contract symbol expiration disagrees with the record")
    return True


def assert_in_snapshot_window(now_et, event_date, session,
                              tolerance_minutes=SNAPSHOT_WINDOW_TOLERANCE_MINUTES):
    """Refuse any capture outside the frozen 15:45 ET window on the correct day."""
    want = snapshot_date_for(event_date, session)
    if now_et.date().isoformat() != want:
        raise Refused("wrong snapshot day: %s is not the required %s"
                      % (now_et.date().isoformat(), want))
    hh, mm = SNAPSHOT_TARGET_ET.split(":")
    target = now_et.replace(hour=int(hh), minute=int(mm), second=0, microsecond=0)
    off = abs((now_et - target).total_seconds()) / 60.0
    if off > tolerance_minutes:
        raise Refused("outside the frozen %s ET window by %.1f min (tolerance %d)"
                      % (SNAPSHOT_TARGET_ET, off, tolerance_minutes))
    return True


def resolve_feed(provider, latency_label, feed=None, feed_designation=None):
    """Provider AND feed provenance are mandatory. Alpaca's label is not optional."""
    p = str(provider or "")
    if not p:
        raise Refused("provider is mandatory provenance")
    if p.startswith("alpaca"):
        f = feed or ALPACA_OPTIONS_FEED
        d = feed_designation or ALPACA_LABEL
        if f != ALPACA_OPTIONS_FEED or d != ALPACA_LABEL:
            raise Refused("every Alpaca record must be feed %r labelled %s"
                          % (ALPACA_OPTIONS_FEED, ALPACA_LABEL))
        return f, d
    if p == CBOE_PROVIDER:
        f = feed or CBOE_FEED
        d = feed_designation or CBOE_LABEL
        if f != CBOE_FEED or d != CBOE_LABEL:
            raise Refused("every manual Cboe record must be feed %r labelled %s"
                          % (CBOE_FEED, CBOE_LABEL))
        return f, d
    d = feed_designation or latency_label
    if not d:
        raise Refused("feed designation is mandatory provenance")
    return (feed or p), d


def assert_provider_provenance(rec):
    """No record without provider AND feed provenance may be stored."""
    for f in ("provider", "feed", "feed_designation"):
        if not str(rec.get(f) or "").strip():
            raise Refused("missing mandatory provenance field %r" % (f,))
    if str(rec["provider"]).startswith("alpaca"):
        if rec.get("feed") != ALPACA_OPTIONS_FEED:
            raise Refused("Alpaca record declares feed %r" % (rec.get("feed"),))
        if rec.get("feed_designation") != ALPACA_LABEL:
            raise Refused("every Alpaca record must carry %s" % ALPACA_LABEL)
    if str(rec["provider"]) == CBOE_PROVIDER:
        if rec.get("feed_designation") != CBOE_LABEL:
            raise Refused("every manual Cboe record must carry %s" % CBOE_LABEL)
        if rec.get("capture_method") != CBOE_CAPTURE_METHOD:
            raise Refused("a Cboe record must declare capture_method %s"
                          % CBOE_CAPTURE_METHOD)
        for f in ("source_file_sha256", "source_file_name", "retrieved_at_utc"):
            if not str(rec.get(f) or "").strip():
                raise Refused("manual capture is missing %r" % (f,))
    return True


def assert_research_grade(rec):
    """System-validation data can never enter the prospective research panel."""
    if rec.get("data_class") != RESEARCH_CLASS:
        raise Refused("data_class %r may not enter the research panel"
                      % (rec.get("data_class"),))
    for v in rec.values():
        if isinstance(v, str) and SYSTEM_VALIDATION_LABEL in v:
            raise Refused("%s data is barred from the research panel"
                          % SYSTEM_VALIDATION_LABEL)
    return True


def assert_no_executable_claim(rec):
    """Amendment 1: the execution-economics stage is deferred on the indicative feed.

    No executable price, spread-aware alpha or realized-straddle-P&L field may be
    emitted while the provider is Alpaca's indicative feed.
    """
    if rec.get("feed_designation") in NON_EXECUTABLE_LABELS:
        bad = sorted(k for k in rec if EXECUTABLE_CLAIM_FIELD.search(k))
        if bad:
            raise Refused("%s: executable / spread-aware / straddle-P&L fields are "
                          "prohibited on indicative records: %s"
                          % (DEFERRED_EXECUTION_STATUS, bad))
        if rec.get("execution_economics_status") != DEFERRED_EXECUTION_STATUS:
            raise Refused("an indicative record must declare %s"
                          % DEFERRED_EXECUTION_STATUS)
    return True


# ------------------------------------------------------------ provenance ledger

def schedule_event_id(ticker, event_date, session):
    """Deterministic event identity, using the same convention as record_id():
    sha256 over pipe-joined identity fields, truncated to 32 hex characters."""
    return sha256_bytes("|".join([str(ticker).upper(), str(event_date),
                                  str(session).upper(),
                                  SCHEDULE_RECORD_TYPE]).encode())[:32]


def existing_schedule_ids(path=None):
    path = Path(path) if path else PROVENANCE_LEDGER
    ids = set()
    if Path(path).exists():
        for line in Path(path).read_text(encoding="utf-8").splitlines():
            if line.strip():
                r = json.loads(line)
                if r.get("record_type") == SCHEDULE_RECORD_TYPE:
                    ids.add(r.get("schedule_event_id"))
    return ids


def append_provenance(rec, path=None):
    """Append-only ledger for non-research provenance. Never the research panel."""
    path = path or PROVENANCE_LEDGER
    if rec.get("data_class") == RESEARCH_CLASS:
        raise Refused("a research record belongs in the manifest, not the "
                      "provenance ledger")
    if Path(path).name == Path(MANIFEST).name:
        raise Refused("the provenance ledger may not be the research manifest")
    if rec.get("record_type") == SCHEDULE_RECORD_TYPE:
        # A schedule is NOT an observation and must never look like one.
        if rec.get("status") != SCHEDULE_STATUS:
            raise Refused("a scheduling record must declare status %s"
                          % SCHEDULE_STATUS)
        sid = rec.get("schedule_event_id")
        if not sid:
            raise Refused("a scheduling record needs a deterministic event identity")
        if sid in existing_schedule_ids(path):
            raise Refused("duplicate scheduling refused for event identity %s" % sid)
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    with Path(path).open("a", encoding="utf-8", newline="\n") as fh:
        fh.write(json.dumps(rec, sort_keys=True) + "\n")
    return True


# ------------------------------------------------------------------ eligibility

def snapshot_date_for(event_date, session):
    """AMC -> announcement trading day. BMO -> preceding trading day."""
    ev = event_date if isinstance(event_date, date) else date.fromisoformat(str(event_date))
    s = str(session).upper()
    if s == "AMC":
        return ev.isoformat()
    if s == "BMO":
        d = ev - timedelta(days=1)
        while d.weekday() >= 5:                      # weekend roll-back only
            d -= timedelta(days=1)
        return d.isoformat()
    raise Refused(f"unknown announcement session {session!r}; expected AMC or BMO")


def search_window_end(event_date):
    ev = event_date if isinstance(event_date, date) else date.fromisoformat(str(event_date))
    return (ev - timedelta(days=SEARCH_CUTOFF_DAYS)).isoformat()


def assert_pre_announcement(quote_ts_utc, event_date, session):
    """A quote timestamped after the known announcement time is refused."""
    q = datetime.fromisoformat(str(quote_ts_utc).replace("Z", "+00:00"))
    if q.tzinfo is None:
        q = q.replace(tzinfo=timezone.utc)
    ev = date.fromisoformat(str(event_date))
    s = str(session).upper()
    if s == "AMC":                                   # release after the 16:00 ET close
        cutoff = datetime.combine(ev, datetime.strptime("16:00", "%H:%M").time(), ET)
    else:                                            # BMO: release before the 09:30 open
        cutoff = datetime.combine(ev, datetime.strptime("09:30", "%H:%M").time(), ET)
    if q.astimezone(ET) >= cutoff:
        raise Refused(f"quote timestamp {q.isoformat()} is at/after the {s} announcement "
                      f"cutoff {cutoff.isoformat()}")
    return True


def assert_no_prohibited_fields(rec):
    bad = sorted(k for k in rec if k not in PERMITTED_MANIFEST_FIELDS
                 or PROHIBITED_FIELD.search(k))
    if bad:
        raise Refused(f"prohibited or unpermitted manifest field(s): {bad}")
    return True


def record_id(rec):
    return sha256_bytes("|".join([
        str(rec["ticker"]), str(rec["event_date"]), str(rec["provider"]),
        str(rec["quote_timestamp_utc"])]).encode())[:32]


def existing_identities(path=None):
    path = Path(path) if path else MANIFEST
    ids = set()
    if path.exists():
        for line in path.read_text(encoding="utf-8").splitlines():
            if line.strip():
                r = json.loads(line)
                ids.add((r["ticker"], r["event_date"], r["provider"],
                         r["quote_timestamp_utc"]))
    return ids


def build_record(*, ticker, issuer_name, event_date, session, underlying_price, chain,
                 expirations, quote_timestamp_utc, provider, latency_label,
                 raw_sha256, search_features, universe_source_kind,
                 snapshot_timestamp_utc=None, feed=None, feed_designation=None,
                 request_timestamp_utc=None, response_status=None,
                 underlying_price_source=None, retrieved_at_utc=None,
                 underlying_timestamp_utc=None, capture_method=None,
                 source_file_name=None, source_file_bytes=None,
                 source_file_sha256=None):
    """Assemble one sanitized manifest record, refusing anything that breaks a rule.

    The frozen contract-selection and implied-move arithmetic below is UNCHANGED by
    Provider Amendment 1: nearest expiration strictly after the event, strike nearest
    the contemporaneous underlying, midpoints from bid/ask only. Only provenance
    fields were added, and on the indicative feed the executable straddle cost is
    withheld because that stage is deferred.
    """
    assert_pre_announcement(quote_timestamp_utc, event_date, session)
    exp = first_expiration_after(expirations, event_date)
    at_exp = [o for o in chain if str(o.get("expiration_date")) == exp]
    if not at_exp:
        raise Refused(f"no chain rows for expiration {exp}")
    k = nearest_strike(at_exp, underlying_price)
    call_row, put_row = leg(at_exp, k, "call"), leg(at_exp, k, "put")
    c = quote_fields(call_row, "call")
    p = quote_fields(put_row, "put")
    feed, feed_designation = resolve_feed(provider, latency_label, feed,
                                          feed_designation)
    rec = {
        "schema_version": "1.0",
        "ticker": ticker, "issuer_name": issuer_name,
        "event_date": str(event_date), "announcement_session": str(session).upper(),
        "snapshot_date": snapshot_date_for(event_date, session),
        "snapshot_timestamp_utc": (snapshot_timestamp_utc
                                   or datetime.now(timezone.utc).strftime(
                                       "%Y-%m-%dT%H:%M:%SZ")),
        "quote_timestamp_utc": str(quote_timestamp_utc),
        "provider": provider, "quote_latency_label": latency_label,
        "feed": feed, "feed_designation": feed_designation,
        "data_class": RESEARCH_CLASS,
        "strike_selection_method": STRIKE_SELECTION_METHOD,
        "underlying_price": float(underlying_price),
        "expiration": exp, "strike": float(k), **c, **p,
        "search_window_end": search_window_end(event_date),
        "search_features": search_features,
        "raw_response_sha256": raw_sha256,
        "event_timing_status": SCHEDULING_LABEL,
        "universe_source_kind": universe_source_kind,
        "collected_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
    }
    if request_timestamp_utc:
        rec["request_timestamp_utc"] = str(request_timestamp_utc)
    if response_status is not None:
        rec["response_status"] = int(response_status)
    if underlying_price_source:
        rec["underlying_price_source"] = str(underlying_price_source)
    if retrieved_at_utc:
        rec["retrieved_at_utc"] = str(retrieved_at_utc)
    if underlying_timestamp_utc:
        rec["underlying_timestamp_utc"] = str(underlying_timestamp_utc)
    if capture_method:
        rec["capture_method"] = str(capture_method)
    if source_file_name:
        rec["source_file_name"] = str(source_file_name)
    if source_file_bytes is not None:
        rec["source_file_bytes"] = int(source_file_bytes)
    if source_file_sha256:
        rec["source_file_sha256"] = str(source_file_sha256)
    if call_row.get("occ_symbol"):
        rec["contract_symbol_call"] = str(call_row["occ_symbol"])
    if put_row.get("occ_symbol"):
        rec["contract_symbol_put"] = str(put_row["occ_symbol"])

    # ---- frozen arithmetic, unchanged --------------------------------------
    rec["midpoint_implied_move"] = implied_move(rec["call_mid"], rec["put_mid"],
                                                underlying_price)
    if feed_designation in NON_EXECUTABLE_LABELS:
        # Amendment 1 section 7: deferred, not deleted. No executable price, no
        # spread cost and no straddle P&L is derived from an indicative quote.
        rec["execution_economics_status"] = DEFERRED_EXECUTION_STATUS
    else:
        rec["executable_straddle_cost"] = straddle_cost(rec["call_ask"],
                                                        rec["put_ask"],
                                                        underlying_price)

    # ---- field completeness is disclosed, never imputed ---------------------
    rec["design_fields_absent"] = sorted(f for f in DESIGN_RECORDED_FIELDS
                                         if rec.get(f) is None)
    missing = [f for f in MANDATORY_RECORD_FIELDS if rec.get(f) in (None, "")]
    rec["all_necessary_fields_present"] = not missing
    if missing:
        raise Refused(f"necessary field(s) missing: {sorted(missing)}; the record is "
                      "refused, not repaired")

    rec["record_id"] = record_id(rec)
    assert_no_prohibited_fields(rec)
    assert_provider_provenance(rec)
    assert_no_executable_claim(rec)
    assert_internally_consistent(rec)
    return rec


def append_record(rec, path=None):
    """Append-only research panel. A duplicate identity is refused, never overwritten.

    Every gate is re-applied here, so a record cannot reach the panel by being built
    somewhere other than build_record.
    """
    assert_no_prohibited_fields(rec)
    assert_provider_provenance(rec)
    assert_research_grade(rec)
    assert_no_executable_claim(rec)
    path = Path(path) if path else MANIFEST
    ident = (rec["ticker"], rec["event_date"], rec["provider"], rec["quote_timestamp_utc"])
    if ident in existing_identities(path):
        raise Refused(f"duplicate identity refused: {ident}")
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8", newline="\n") as fh:
        fh.write(json.dumps(rec, sort_keys=True) + "\n")
    return rec["record_id"]


# ---------------------------------------------------------------------- modes

def http_json(url, headers=None, timeout=45):
    req = urllib.request.Request(url, headers=headers or {})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        raw = r.read()
    return r.status if hasattr(r, "status") else 200, raw


def mode_doctor(argv=None):
    pres = credential_presence()
    prov, base, label, var = options_provider()
    print("PROVIDER READINESS (presence only; no value, no length, no prefix)")
    for k, v in pres.items():
        print(f"  {k:<28} {'PRESENT' if v else 'ABSENT'}")
    print(f"  options provider selected     "
          f"{prov or 'NONE -- fixture validation only'}")
    print(f"  quote latency label           {label or 'n/a'}")
    print(f"  calendar provider             "
          f"{'alphavantage' if pres['ALPHAVANTAGE_API_KEY'] else 'NONE'}")
    print(f"  trends alpha                  "
          f"{'PRESENT' if pres['GOOGLE_TRENDS_ALPHA_KEY'] else 'ABSENT (public sampling only)'}")
    print(f"  raw cache (repository-external) {CACHE}")
    print(f"  manifest                      {MANIFEST.relative_to(ROOT)}"
          f" ({'present' if MANIFEST.exists() else 'not yet created'})")
    if prov == "alpaca":
        print("\nPROVIDER AMENDMENT 1 (2026-08-17) IN FORCE:")
        print("  options feed                 " + ALPACA_OPTIONS_FEED)
        print("  mandatory record label       " + ALPACA_LABEL)
        print("  consolidated OPRA data       NO -- trades may be delayed, quotes are")
        print("                               modified/indicative, not the NBBO")
        print("  execution-economics stage    " + DEFERRED_EXECUTION_STATUS)
        print("  permitted use                magnitude forecasting vs an options-implied")
        print("                               benchmark")
        print("  prohibited use               executable bids/asks, spread costs,")
        print("                               straddle P&L, tradeable options alpha")
        print("  endpoints                    market data only; order/trading/account")
        print("                               endpoints fail closed")
    if not prov:
        print("\nSETUP REQUIRED for options snapshots -- no website is substituted:")
        print("  1. Set APCA_API_KEY_ID and APCA_API_SECRET_KEY (Alpaca Paper Only).")
        print("  2. Tradier stays unavailable until a legitimately-owned brokerage")
        print("     account exists; no fabricated identity or third-party SSN is used.")
        print("  3. Re-run: python tools/collect_attention_options_snapshot.py doctor")
    return 0


def mode_calendar(argv=None):
    """Alpha Vantage EARNINGS_CALENDAR -- dates only. EPS fields are never an outcome."""
    key = (os.environ.get("ALPHAVANTAGE_API_KEY") or "").strip()
    if not key:
        print("CALENDAR: ALPHAVANTAGE_API_KEY absent -- no request issued.")
        return 2
    url = ("https://www.alphavantage.co/query?" + urllib.parse.urlencode(
        {"function": "EARNINGS_CALENDAR", "horizon": "3month", "apikey": key}))
    try:
        status, raw = http_json(url)
    except Exception as e:                                   # noqa: BLE001
        print("CALENDAR ERROR:", redact(f"{type(e).__name__}: {e}"))
        return 1
    CACHE.mkdir(parents=True, exist_ok=True)
    (CACHE / "earnings_calendar.csv").write_bytes(raw)
    text = raw.decode("utf-8", "replace")
    rows = [r for r in text.splitlines() if r.strip()]
    today = date.today()
    horizon = today + timedelta(days=CALENDAR_HORIZON_DAYS)
    header = rows[0].split(",") if rows else []
    idx = {h.strip(): i for i, h in enumerate(header)}
    kept = 0
    if "reportDate" in idx:
        for r in rows[1:]:
            c = r.split(",")
            try:
                d = date.fromisoformat(c[idx["reportDate"]].strip())
            except (ValueError, IndexError):
                continue
            if today <= d <= horizon:
                kept += 1
    print(f"CALENDAR: http {status}, {len(raw):,} bytes, sha256 {sha256_bytes(raw)[:16]}...")
    print(f"  raw cached repository-external: {CACHE / 'earnings_calendar.csv'}")
    print(f"  rows returned: {max(0, len(rows) - 1)}")
    print(f"  candidate events within {CALENDAR_HORIZON_DAYS} days: {kept}")
    print(f"  status label: {SCHEDULING_LABEL} "
          "(vendor dates are scheduling inputs, not timing proof)")
    print("  NOTE: EPS fields in this feed are NOT an outcome and NOT point-in-time "
          "analyst data; only dates are used.")
    return 0


def mode_snapshot(argv):
    """Capture one prospective pre-event input snapshot, or refuse.

    Every gate is checked BEFORE any request: provider selection, the frozen 15:45 ET
    window on the correct snapshot day, and confirmed event timing. Nothing here
    computes a return, opens a post-event price, or touches an order endpoint.
    """
    ap = argparse.ArgumentParser(prog="snapshot")
    ap.add_argument("--ticker", required=True)
    ap.add_argument("--issuer", required=True)
    ap.add_argument("--event-date", required=True)
    ap.add_argument("--session", required=True, choices=["AMC", "BMO", "amc", "bmo"])
    ap.add_argument("--timing-confirmed", default=None,
                    help="issuer release or SEC filing URL confirming date AND session")
    a = ap.parse_args(argv)
    session = a.session.upper()
    try:
        prov, base, label, var = options_provider()
    except Refused as e:
        print("SNAPSHOT REFUSED:", redact(e))
        return 2
    if not prov:
        print("SNAPSHOT REFUSED: no options-provider credential present.")
        print("No website is scraped as a substitute. Run `doctor` for setup steps.")
        return 2

    now_et = datetime.now(ET)
    print(f"SNAPSHOT: provider={prov} feed="
          f"{ALPACA_OPTIONS_FEED if prov == 'alpaca' else prov} "
          f"now_et={now_et:%Y-%m-%d %H:%M} target={SNAPSHOT_TARGET_ET} ET")

    try:
        assert_in_snapshot_window(now_et, a.event_date, session)
    except Refused as e:
        print("  REFUSED (window):", redact(e))
        print("  No out-of-window capture is performed and no historical observation "
              "is manufactured.")
        return 3

    if not a.timing_confirmed:
        print("  REFUSED (timing): vendor calendar dates are "
              f"{SCHEDULING_LABEL}. Pass --timing-confirmed with an issuer release or "
              "SEC filing that fixes BOTH the date and the AMC/BMO session.")
        return 3

    if prov != "alpaca":
        print("  REFUSED: Provider Amendment 1 makes Alpaca the options provider; "
              "no other provider is silently substituted.")
        return 2

    sym = a.ticker.upper()
    req_ts = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    try:
        u_status, u_raw = alpaca_get(f"/v2/stocks/{sym}/trades/latest",
                                     {"feed": ALPACA_STOCK_FEED})
        if u_status != 200:
            print(f"  REFUSED: underlying price request returned {u_status}. "
                  "Stopping; no other provider is tried.")
            return 1
        px = _num(((json.loads(u_raw.decode("utf-8", "replace")).get("trade")) or {})
                  .get("p"))
        if px is None or px <= 0:
            raise Refused("no usable underlying price")
        ev = date.fromisoformat(str(a.event_date))
        o_status, o_raw = alpaca_get(ALPACA_OPTIONS_SNAPSHOT_PATH + sym,
                                     {"feed": ALPACA_OPTIONS_FEED, "limit": 1000,
                                      "expiration_date_gte":
                                          (ev + timedelta(days=1)).isoformat(),
                                      "expiration_date_lte":
                                          (ev + timedelta(days=45)).isoformat()})
        if o_status != 200:
            print(f"  REFUSED: option chain request returned {o_status}. "
                  "Stopping; no other provider is tried and no website is scraped.")
            return 1
        rows = alpaca_snapshot_rows(json.loads(o_raw.decode("utf-8", "replace")))
        exp = first_expiration_after({r["expiration_date"] for r in rows}, a.event_date)
        at_exp = [r for r in rows if r["expiration_date"] == exp]
        k = nearest_strike(at_exp, px)
        c_row, p_row = leg(at_exp, k, "call"), leg(at_exp, k, "put")
        now_utc = datetime.now(timezone.utc)
        c_ts = assert_leg_usable(c_row, "call", now_utc)
        p_ts = assert_leg_usable(p_row, "put", now_utc)
        assert_legs_contemporaneous(c_ts, p_ts)
        rec = build_record(
            ticker=sym, issuer_name=a.issuer, event_date=a.event_date,
            session=session, underlying_price=px, chain=at_exp,
            expirations={r["expiration_date"] for r in rows},
            quote_timestamp_utc=utc_second_stamp(max(c_ts, p_ts)),
            provider="alpaca", latency_label=ALPACA_LABEL,
            feed=ALPACA_OPTIONS_FEED, feed_designation=ALPACA_LABEL,
            raw_sha256=sha256_bytes(o_raw), search_features=[],
            universe_source_kind=(_committed_universe() or {}).get(
                "source_kind", "UNKNOWN"),
            request_timestamp_utc=req_ts, response_status=o_status,
            underlying_price_source=f"alpaca:{ALPACA_STOCK_FEED}")
        CACHE.mkdir(parents=True, exist_ok=True)
        (CACHE / f"alpaca_chain_{sym}_{a.event_date}.json").write_bytes(o_raw)
        rid = append_record(rec)
    except Refused as e:
        print("  REFUSED:", redact(e))
        return 3
    except Exception as e:                                    # noqa: BLE001
        print("  ERROR:", redact(f"{type(e).__name__}: {e}"))
        return 1
    print(f"  RECORDED record_id={rid} expiration={rec['expiration']} "
          f"strike={rec['strike']} label={rec['feed_designation']}")
    print("  raw body kept repository-external; only sanitized fields were committed.")
    return 0


def mode_validate(argv=None):
    """Re-verify every stored record against the frozen rules."""
    if not MANIFEST.exists():
        print("VALIDATE: no manifest yet -- nothing to validate (0 records).")
        return 0
    seen, bad, n = set(), [], 0
    for i, line in enumerate(MANIFEST.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        n += 1
        r = json.loads(line)
        try:
            assert_no_prohibited_fields(r)
            assert_provider_provenance(r)
            assert_research_grade(r)
            assert_no_executable_claim(r)
            assert_pre_announcement(r["quote_timestamp_utc"], r["event_date"],
                                    r["announcement_session"])
            if r["record_id"] != record_id(r):
                raise Refused("record_id does not recompute")
            if not re.fullmatch(r"[0-9a-f]{64}", str(r["raw_response_sha256"])):
                raise Refused("raw_response_sha256 malformed")
            if r["snapshot_date"] != snapshot_date_for(r["event_date"],
                                                       r["announcement_session"]):
                raise Refused("snapshot_date violates the AMC/BMO rule")
            if r["search_window_end"] != search_window_end(r["event_date"]):
                raise Refused("search_window_end violates the T-2 cutoff")
            ident = (r["ticker"], r["event_date"], r["provider"], r["quote_timestamp_utc"])
            if ident in seen:
                raise Refused("duplicate identity in manifest")
            seen.add(ident)
        except (Refused, KeyError) as e:
            bad.append(f"line {i}: {e}")
    print(f"VALIDATE: {n} record(s), {len(bad)} violation(s)")
    for b in bad:
        print("  " + b)
    return 1 if bad else 0


# ------------------------------------------------- manual Cboe local-file import
#
# NO NETWORK. This section reads a file a HUMAN downloaded by hand from the
# official Cboe Delayed Quotes dashboard. Cboe prohibits automated extraction, so
# there is deliberately no Cboe URL, no HTTP call, no browser driver and no
# download step anywhere in this repository.

CBOE_TS_PATTERNS = (
    "%Y-%m-%dT%H:%M:%SZ", "%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M",
    "%a %b %d %H:%M:%S %Z %Y", "%m/%d/%Y %H:%M:%S", "%m/%d/%Y %H:%M",
)


def parse_display_timestamp(text):
    """Parse the page-displayed market-data timestamp. Never guessed."""
    t = str(text or "").strip().strip('"')
    if not t:
        raise Refused("displayed market-data timestamp is missing")
    try:
        return parse_rfc3339(t)
    except Refused:
        pass
    for fmt in CBOE_TS_PATTERNS:
        try:
            d = datetime.strptime(t, fmt)
            return d if d.tzinfo else d.replace(tzinfo=timezone.utc)
        except ValueError:
            continue
    raise Refused("unparseable displayed market-data timestamp: %r" % (text,))


def _cboe_header_index(rows):
    """Locate the quote table header. Refuse rather than guess at the layout."""
    for i, r in enumerate(rows):
        low = [c.strip().lower() for c in r]
        if "strike" in low and "calls" in low and "puts" in low:
            return i, low
    raise Refused("the file has no recognisable Cboe options table header "
                  "(expected columns including Calls, Strike and Puts); refusing "
                  "rather than guessing at the layout")


def parse_cboe_csv(raw, expected_ticker):
    """Parse a manually downloaded Cboe delayed-quotes CSV.

    Returns (rows, meta). Layout follows Cboe's published table: every column left
    of `Strike` describes the CALL, every column right of it the PUT. Anything the
    file does not state is left absent -- nothing is inferred or imputed.
    """
    text = raw.decode("utf-8-sig", "replace")
    rows = list(csv.reader(io.StringIO(text)))
    if not rows:
        raise Refused("the file is empty")
    hi, header = _cboe_header_index(rows)

    meta = {}
    blob = "\n".join(",".join(r) for r in rows[:hi])
    m = re.search(r"(?:last\s*updated|as\s*of|date/time|timestamp)\s*[:,]\s*"
                  r"([^,\n]+)", blob, re.I)
    if m:
        meta["display_timestamp"] = m.group(1).strip()
    m = re.search(r"(?:underlying|last)\s*(?:price|sale)?\s*[:,]\s*\$?"
                  r"([0-9]+\.?[0-9]*)", blob, re.I)
    if m:
        meta["underlying_price"] = _num(m.group(1))

    # The file must name the ticker it is for; a file for another name is refused.
    up = blob.upper()
    tick = str(expected_ticker).upper()
    if not re.search(r"\b%s\b" % re.escape(tick), up):
        raise Refused("this file does not identify ticker %r in its header; wrong "
                      "file for this event" % (tick,))

    si = header.index("strike")
    ci, pi = header.index("calls"), header.index("puts")
    if not (ci < si < pi):
        raise Refused("unexpected Cboe column order (Calls must precede Strike, "
                      "Strike must precede Puts); refusing rather than guessing")

    def pick(seg_lo, seg_hi, *names):
        for n in names:
            for j in range(seg_lo, seg_hi):
                if header[j] == n:
                    return j
        return None

    exp_i = pick(0, len(header), "expiration date", "expiration", "exp date")
    if exp_i is None:
        raise Refused("no expiration column in the Cboe file")
    idx = {
        "call_bid": pick(ci, si, "bid"), "call_ask": pick(ci, si, "ask"),
        "call_last": pick(ci, si, "last sale", "last"),
        "call_volume": pick(ci, si, "volume"),
        "call_open_interest": pick(ci, si, "open interest"),
        "call_iv": pick(ci, si, "iv", "implied volatility"),
        "put_bid": pick(si, len(header), "bid"),
        "put_ask": pick(si, len(header), "ask"),
        "put_last": pick(si, len(header), "last sale", "last"),
        "put_volume": pick(si, len(header), "volume"),
        "put_open_interest": pick(si, len(header), "open interest"),
        "put_iv": pick(si, len(header), "iv", "implied volatility"),
    }
    for k in ("call_bid", "call_ask", "put_bid", "put_ask"):
        if idx[k] is None:
            raise Refused("the Cboe file has no %s column; a missing side is never "
                          "replaced by a last price" % k.replace("_", " "))

    out, seen = [], set()
    for r in rows[hi + 1:]:
        if len(r) <= max(si, pi, exp_i):
            continue
        strike = _num(r[si])
        exp = str(r[exp_i]).strip()
        if strike is None or not exp:
            continue
        try:
            exp = _cboe_date(exp)
        except Refused:
            continue
        key = (exp, strike)
        if key in seen:
            raise Refused("duplicate contract row for expiration %s strike %s"
                          % (exp, strike))
        seen.add(key)
        row = {"expiration_date": exp, "strike": strike}
        for k, j in idx.items():
            row[k] = _num(r[j]) if j is not None and len(r) > j else None
        out.append(row)
    if not out:
        raise Refused("the Cboe file contains no parseable contract rows")
    return out, meta


def _cboe_date(t):
    t = str(t).strip()
    for fmt in ("%Y-%m-%d", "%m/%d/%Y", "%b %d %Y", "%d-%b-%Y", "%Y/%m/%d"):
        try:
            return datetime.strptime(t, fmt).date().isoformat()
        except ValueError:
            continue
    raise Refused("unparseable expiration date: %r" % (t,))


def cboe_legs(rows, exp, strike):
    """Split one Cboe wide row into the frozen internal call/put leg schema."""
    hit = [r for r in rows if r["expiration_date"] == exp and r["strike"] == strike]
    if len(hit) != 1:
        raise Refused("expected exactly one row at %s / %s, found %d"
                      % (exp, strike, len(hit)))
    r = hit[0]
    legs = []
    for kind in ("call", "put"):
        legs.append({
            "expiration_date": exp, "strike": strike, "option_type": kind,
            "bid": r["%s_bid" % kind], "ask": r["%s_ask" % kind],
            "last": r["%s_last" % kind], "volume": r["%s_volume" % kind],
            "open_interest": r["%s_open_interest" % kind],
            "iv": r["%s_iv" % kind],
        })
    return legs


def assert_unambiguous_atm(strikes, underlying_price):
    """Refuse an ambiguous ATM: two strikes exactly equidistant from the underlying."""
    if not strikes:
        raise Refused("no strikes available for ATM selection")
    d = sorted((abs(s - underlying_price), s) for s in set(strikes))
    if len(d) > 1 and abs(d[0][0] - d[1][0]) < 1e-9:
        raise Refused("ambiguous ATM selection: strikes %s and %s are equidistant "
                      "from the underlying %s" % (d[0][1], d[1][1], underlying_price))
    return d[0][1]


def assert_delayed_display_timing(display_utc, retrieved_utc,
                                  max_lag=CBOE_MAX_DISPLAY_LAG_SECONDS):
    """Amendment 2: the DISPLAYED timestamp is the cutoff, and it must precede the
    download. Equal or later is refused; too far behind is stale."""
    lag = (retrieved_utc - display_utc).total_seconds()
    if lag <= 0:
        raise Refused("displayed market-data timestamp is not earlier than the "
                      "retrieval timestamp (lag %.0fs); a delayed quote must "
                      "precede its download" % lag)
    if lag > max_lag:
        raise Refused("displayed market-data timestamp is stale by %.0fs "
                      "(limit %ds)" % (lag, max_lag))
    return True


# ------------------------------------------------------- frozen Trends method
#
# Implements TRENDS_METHOD_FROZEN exactly. Every parsed response is archived
# repository-external and hashed BEFORE any z-score is computed, and the z-score
# is recomputed from the archived file rather than from memory.

def trends_window(cutoff=TRENDS_CUTOFF, days=TRENDS_WINDOW_DAYS):
    """Retrieval window: exactly `days` calendar days before the cutoff, to the cutoff."""
    end = date.fromisoformat(str(cutoff))
    return ((end - timedelta(days=days)).isoformat(), end.isoformat())


def trends_timeframe(cutoff=TRENDS_CUTOFF):
    a, b = trends_window(cutoff)
    return "%s %s" % (a, b)


def assert_in_trends_window(now_et, retrieval_date,
                            tolerance_minutes=SNAPSHOT_WINDOW_TOLERANCE_MINUTES):
    """The existing 15:45 ET convention, unchanged and not loosened."""
    if now_et.date().isoformat() != str(retrieval_date):
        raise Refused("wrong retrieval day: %s is not the scheduled %s"
                      % (now_et.date().isoformat(), retrieval_date))
    hh, mm = SNAPSHOT_TARGET_ET.split(":")
    target = now_et.replace(hour=int(hh), minute=int(mm), second=0, microsecond=0)
    off = abs((now_et - target).total_seconds()) / 60.0
    if off > tolerance_minutes:
        raise Refused("outside the frozen %s ET window by %.1f min (tolerance %d)"
                      % (SNAPSHOT_TARGET_ET, off, tolerance_minutes))
    return True


def select_complete_weeks(rows, cutoff=TRENDS_CUTOFF):
    """Apply the frozen complete-week rule. Refuses rather than repairs.

    `rows` is [(date_iso, value, is_partial)]. Zero is a valid value, not missing.
    """
    cut = date.fromisoformat(str(cutoff))
    if len(rows) < 2:
        raise Refused("too few rows to establish weekly resolution")
    kept = []
    for d, v, partial in rows:
        if partial:
            continue                      # rows marked partial are rejected outright
        if v is None:
            raise Refused("missing value at %s; no interpolation is permitted" % d)
        wk = date.fromisoformat(str(d))
        if wk + timedelta(days=6) <= cut:
            kept.append((wk, float(v)))
    kept.sort()
    if len(kept) < 2:
        raise Refused("fewer than two complete weeks survive the cutoff")
    for a, b in zip(kept, kept[1:]):
        gap = (b[0] - a[0]).days
        if gap != 7:
            raise Refused("non-weekly resolution or a missing week: %s -> %s is %d days"
                          % (a[0], b[0], gap))
    need = TRENDS_BASELINE_WEEKS + 1
    if len(kept) < need:
        raise Refused("need the target plus %d baseline weeks; only %d complete weeks "
                      "survive" % (TRENDS_BASELINE_WEEKS, len(kept)))
    return kept


def query_zscore(kept):
    """z = (target - mean(prev 52)) / sample sd(prev 52), ddof=1, target excluded."""
    window = kept[-(TRENDS_BASELINE_WEEKS + 1):]
    target = window[-1][1]
    baseline = [v for _, v in window[:-1]]
    if len(baseline) != TRENDS_BASELINE_WEEKS:
        raise Refused("baseline is %d weeks, not %d"
                      % (len(baseline), TRENDS_BASELINE_WEEKS))
    n = len(baseline)
    mean = sum(baseline) / n
    var = sum((x - mean) ** 2 for x in baseline) / (n - TRENDS_ZSCORE_DDOF)
    sd = var ** 0.5
    if sd == 0:
        raise Refused("baseline standard deviation is zero; the query is invalid")
    return {"z": (target - mean) / sd, "target_week": window[-1][0].isoformat(),
            "baseline_weeks": n, "ddof": TRENDS_ZSCORE_DDOF}


def daily_composite(z_ticker, z_issuer):
    """Both query z-scores are required. There is no one-query fallback."""
    if z_ticker is None or z_issuer is None:
        raise Refused("both query z-scores are required; no one-query fallback exists")
    return (z_ticker + z_issuer) / 2.0


def event_gst_zscore(c_tm1, c_t0):
    if c_tm1 is None or c_t0 is None:
        raise Refused("both daily composites are required; the Trends leg is invalid")
    return (c_tm1 + c_t0) / 2.0


def stability_gap(c_tm1, c_t0):
    """Descriptive only. No threshold; cannot change the predictor or eligibility."""
    return abs(c_tm1 - c_t0)


def atomic_write_bytes(path, payload):
    """Temporary file then rename, so a partial file can never be observed."""
    path = Path(path)
    if path.exists():
        raise Refused("filename collision refused: %s" % path.name)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".part")
    with tmp.open("wb") as fh:
        fh.write(payload)
        fh.flush()
        os.fsync(fh.fileno())
    os.replace(tmp, path)
    return path


def serialize_trends_csv(rows, query):
    """Canonical UTF-8 / LF. Column order is fixed so the hash is deterministic."""
    out = io.StringIO(newline="")
    w = csv.writer(out, lineterminator="\n")
    w.writerow(["date", "value", "isPartial", "query"])
    for d, v, p in rows:
        w.writerow([d, v, "True" if p else "False", query])
    return out.getvalue().encode("utf-8")


TRENDS_CSV_SCHEMA = ["date", "value", "isPartial", "query"]


def read_trends_csv(raw, expect_query=None):
    """Re-read an archived attempt. Schema drift and label drift are refused."""
    rows = list(csv.reader(io.StringIO(raw.decode("utf-8"))))
    if not rows:
        raise Refused("archived attempt is empty")
    if rows[0] != TRENDS_CSV_SCHEMA:
        raise Refused("unexpected columns %r; schema drift refused" % (rows[0],))
    out = []
    for r in rows[1:]:
        if len(r) != 4:
            raise Refused("partial row in the archived attempt")
        if expect_query is not None and r[3] != expect_query:
            raise Refused("unexpected query label %r; expected %r"
                          % (r[3], expect_query))
        out.append((r[0], _num(r[1]), r[2].strip().lower() == "true"))
    return out


def dependency_versions():
    v = {"python": sys.version.split()[0]}
    for m in ("pytrends", "pandas", "requests", "urllib3"):
        try:
            mod = __import__(m)
            v[m] = getattr(mod, "__version__", "unknown")
        except Exception:                                     # noqa: BLE001
            v[m] = "absent"
    return v


def trends_request_id(retrieval_date, query, attempt):
    return sha256_bytes("|".join(["ROST", str(retrieval_date), str(query),
                                  str(attempt)]).encode())[:32]


def _existing_trends_ids(path=None):
    path = Path(path) if path else PROVENANCE_LEDGER
    ids = set()
    if path.exists():
        for line in path.read_text(encoding="utf-8").splitlines():
            if line.strip():
                r = json.loads(line)
                if r.get("record_type") == TRENDS_ATTEMPT_TYPE:
                    ids.add(r.get("request_id"))
    return ids


def mode_trends_capture(argv):
    """One scheduled Trends retrieval date: one request per frozen query, no retry.

    Each parsed response is archived repository-external and hashed BEFORE any
    z-score is computed, and the z-score is recomputed from the archived bytes.
    Parsed values are never printed and never committed.
    """
    ap = argparse.ArgumentParser(prog="trends-capture")
    ap.add_argument("--retrieval-date", required=True,
                    choices=sorted(TRENDS_SCHEDULE.values()))
    ap.add_argument("--label", required=True, choices=sorted(TRENDS_SCHEDULE))
    a = ap.parse_args(argv)
    if TRENDS_SCHEDULE[a.label] != a.retrieval_date:
        print("REFUSED: label %s is scheduled for %s, not %s"
              % (a.label, TRENDS_SCHEDULE[a.label], a.retrieval_date))
        return 3
    try:
        assert_in_trends_window(datetime.now(ET), a.retrieval_date)
    except Refused as e:
        print("TRENDS CAPTURE REFUSED:", redact(e))
        print("  the frozen %s ET window is not loosened; nothing was requested."
              % SNAPSHOT_TARGET_ET)
        return 3

    from pytrends.request import TrendReq                     # noqa: PLC0415
    versions = dependency_versions()
    tf = trends_timeframe()
    zs, ok = {}, True
    for slot, query in sorted(TRENDS_QUERIES.items()):
        rid = trends_request_id(a.retrieval_date, query, 1)
        if rid in _existing_trends_ids():
            print("REFUSED: duplicate request identity for %s; no retry is permitted"
                  % slot)
            return 3
        started = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        base = {"data_class": PROVENANCE_CLASS, "record_type": TRENDS_ATTEMPT_TYPE,
                "request_id": rid, "attempt": 1, "retrieval_date": a.retrieval_date,
                "retrieval_label": a.label, "query_slot": slot, "query": query,
                "geo": TRENDS_GEO, "cat": TRENDS_CAT, "gprop": TRENDS_GPROP,
                "timeframe": tf, "data_cutoff": TRENDS_CUTOFF,
                "batched_with_other_query": False, "retry_policy": TRENDS_RETRY_POLICY,
                "request_started_utc": started, "dependency_versions": versions}
        try:
            py = TrendReq(hl="en-US", tz=0)
            py.build_payload([query], cat=TRENDS_CAT, timeframe=tf,
                             geo=TRENDS_GEO, gprop=TRENDS_GPROP)
            df = py.interest_over_time()
            ended = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
            if df is None or df.empty:
                raise Refused("empty Trends frame")
            cols = list(df.columns)
            if query not in cols:
                raise Refused("missing query column %r in %r" % (query, cols))
            rows = [(i.date().isoformat(), r[query],
                     bool(r.get("isPartial", False))) for i, r in df.iterrows()]
            payload = serialize_trends_csv(rows, query)
            fn = TRENDS_DIR / ("trends_%s_%s_attempt1.csv"
                               % (a.retrieval_date, slot))
            atomic_write_bytes(fn, payload)
            digest = sha256_bytes(payload)
            # Recompute strictly from the ARCHIVED bytes, after hashing.
            kept = select_complete_weeks(read_trends_csv(fn.read_bytes(), query))
            z = query_zscore(kept)
            zs[slot] = z["z"]
            base.update({"request_ended_utc": ended, "status": "SUCCESS",
                         "archived_file_name": fn.name,
                         "archived_file_bytes": len(payload),
                         "archived_file_sha256": digest,
                         "archived_repository_external": str(fn),
                         "schema": TRENDS_CSV_SCHEMA, "row_count": len(rows),
                         "complete_weeks_retained": len(kept),
                         "target_week": z["target_week"],
                         "baseline_weeks": z["baseline_weeks"], "ddof": z["ddof"],
                         "z_query": z["z"], "values_printed": False,
                         "values_committed": False})
            append_provenance(base)
            print("  %-12s SUCCESS  file=%s bytes=%d sha256=%s"
                  % (slot, fn.name, len(payload), digest))
        except Exception as e:                                # noqa: BLE001
            ok = False
            base.update({"request_ended_utc": datetime.now(timezone.utc).strftime(
                "%Y-%m-%dT%H:%M:%SZ"), "status": "FAILURE",
                "failure_reason": redact("%s: %s" % (type(e).__name__, e)),
                "retried": False})
            append_provenance(base)
            print("  %-12s FAILURE (recorded, not retried)" % slot)
    if not ok or len(zs) != 2:
        print("TRENDS DAY INVALID: both queries are required; no one-query fallback.")
        return 3
    comp = daily_composite(zs["ticker_query"], zs["issuer_query"])
    append_provenance({"data_class": PROVENANCE_CLASS,
                       "record_type": TRENDS_DAILY_TYPE,
                       "retrieval_date": a.retrieval_date, "retrieval_label": a.label,
                       "daily_composite": comp, "both_queries_present": True,
                       "status": TRENDS_STATUS_CAPTURED,
                       "options_or_cboe_accessed": False, "outcome_accessed": False,
                       "is_observation": False})
    print("  daily_composite recorded for %s (%s)." % (a.label, a.retrieval_date))
    print("  no options, price, return or outcome was accessed.")
    return 0


def mode_trends_finalize(argv=None):
    """Combine the two scheduled daily composites. Both are required."""
    recs = [json.loads(x) for x in
            PROVENANCE_LEDGER.read_text(encoding="utf-8").splitlines()
            if x.strip()] if PROVENANCE_LEDGER.exists() else []
    by = {r["retrieval_label"]: r["daily_composite"] for r in recs
          if r.get("record_type") == TRENDS_DAILY_TYPE}
    try:
        g = event_gst_zscore(by.get("T-1"), by.get("T0"))
    except Refused as e:
        print("TRENDS LEG INVALID:", redact(e))
        print("  have:", sorted(by))
        return 3
    gap = stability_gap(by["T-1"], by["T0"])
    append_provenance({"data_class": PROVENANCE_CLASS,
                       "record_type": TRENDS_FINAL_TYPE,
                       "schedule_event_id": schedule_event_id("ROST", "2026-08-20",
                                                              "AMC"),
                       "gst_zscore": g, "stability_gap": gap,
                       "stability_gap_is_descriptive_only": True,
                       "stability_gap_threshold": None,
                       "both_days_present": True,
                       "status": TRENDS_STATUS_CAPTURED,
                       "candidate_attention_proxy_not_validated_construct": True,
                       "directional": False, "is_an_outcome": False,
                       "is_observation": False,
                       "options_or_cboe_accessed": False, "outcome_accessed": False})
    print("TRENDS LEG FINALISED (pre-event input, NOT a completed observation)")
    print("  gst_zscore     %.6f" % g)
    print("  stability_gap  %.6f  (descriptive only; no threshold)" % gap)
    print("  snapshot_manifest.jsonl created: %s" % MANIFEST.exists())
    return 0


def mode_schedule(argv):
    """Prerecord ONE confirmed prospective event. Collects nothing.

    This writes a non-observation scheduling record to the provenance ledger. It
    never creates the research manifest, never contacts a provider, and never opens
    an outcome.
    """
    ap = argparse.ArgumentParser(prog="schedule")
    ap.add_argument("--ticker", required=True)
    ap.add_argument("--event-date", required=True)
    ap.add_argument("--event-session", required=True,
                    choices=["AMC", "BMO", "amc", "bmo"])
    ap.add_argument("--release-time", required=True)
    ap.add_argument("--call-time", required=True)
    ap.add_argument("--capture-at", required=True, help="manual capture, ET offset")
    ap.add_argument("--capture-at-ct", required=True, help="same instant, CT offset")
    ap.add_argument("--ir-url", required=True)
    a = ap.parse_args(argv)
    tick, session = a.ticker.upper(), a.event_session.upper()
    try:
        uni = _committed_universe()
        if not uni:
            raise Refused("no committed universe snapshot")
        members = {c["ticker"]: c["issuer_name"] for c in uni["constituents"]}
        if tick not in members:
            raise Refused("%s is not in the committed official universe" % tick)
        if MANIFEST.exists():
            raise Refused("a research manifest already exists; refusing to schedule "
                          "against an existing panel without review")
        sid = schedule_event_id(tick, a.event_date, session)
        rec = {
            "data_class": PROVENANCE_CLASS, "record_type": SCHEDULE_RECORD_TYPE,
            "schedule_event_id": sid,
            "ticker": tick, "issuer_name": members[tick],
            "event_date": str(a.event_date), "announcement_session": session,
            "earnings_release_time": a.release_time,
            "conference_call_time": a.call_time,
            "manual_capture_at_et": a.capture_at,
            "manual_capture_at_ct": a.capture_at_ct,
            "official_source_url": a.ir_url,
            "source_classification": OFFICIAL_IR_SOURCE,
            "event_timing_status": "CONFIRMED_BY_OFFICIAL_ISSUER_SOURCE",
            "confirmed_utc": datetime.now(timezone.utc).strftime(
                "%Y-%m-%dT%H:%M:%SZ"),
            "status": SCHEDULE_STATUS,
            "snapshot_date": snapshot_date_for(a.event_date, session),
            "snapshot_target_et": SNAPSHOT_TARGET_ET,
            "search_window_end": search_window_end(a.event_date),
            "universe_source_kind": uni["source_kind"],
            # Explicitly: nothing has been collected.
            "is_observation": False,
            "trends_input_collected": False,
            "option_chain_collected": False,
            "outcome_collected": False,
            "observation_collected": False,
            "cboe_accessed_by_code": False,
            "planned_options_provider": CBOE_PROVIDER,
            "planned_feed_designation": CBOE_LABEL,
            "frozen_query_rule": "<TICKER> stock ; <Issuer name> stock",
            "resolved_ticker_query": "%s stock" % tick,
            "issuer_name_query_status": (
                "UNRESOLVED_NO_FROZEN_NORMALISER: the committed universe stores the "
                "security description, not a bare issuer name, and no frozen "
                "query-normalisation code exists to derive one without judgment"),
        }
        append_provenance(rec)
    except Refused as e:
        print("SCHEDULE REFUSED:", redact(e))
        return 3
    print("SCHEDULED (not collected): %s %s %s" % (tick, a.event_date, session))
    print("  schedule_event_id      %s" % sid)
    print("  release / call         %s / %s" % (a.release_time, a.call_time))
    print("  manual capture         %s  (%s)" % (a.capture_at, a.capture_at_ct))
    print("  status                 %s" % SCHEDULE_STATUS)
    print("  manifest created       %s" % MANIFEST.exists())
    return 0


def mode_cboe_import(argv):
    """Import ONE manually downloaded Cboe delayed-quotes CSV. No network access.

    A human opened the official Cboe Delayed Quotes dashboard, typed the ticker and
    clicked Download CSV. This reads only that local file.
    """
    ap = argparse.ArgumentParser(prog="cboe-import")
    ap.add_argument("--ticker", required=True)
    ap.add_argument("--issuer", default="")
    ap.add_argument("--event-date", required=True)
    ap.add_argument("--event-session", required=True,
                    choices=["AMC", "BMO", "amc", "bmo"])
    ap.add_argument("--retrieved-at", required=True,
                    help="UTC timestamp of the MANUAL download")
    ap.add_argument("--csv", required=True, help="path to the manually saved file")
    ap.add_argument("--quote-timestamp", default=None,
                    help="page-displayed market-data timestamp, if not in the file")
    ap.add_argument("--underlying-timestamp", default=None)
    ap.add_argument("--underlying-price", default=None, type=float)
    ap.add_argument("--timing-confirmed", default=None,
                    help="issuer release or SEC filing confirming date AND session")
    a = ap.parse_args(argv)
    session = a.event_session.upper()
    print("CBOE MANUAL IMPORT  [%s]" % CBOE_LABEL)
    print("  no network access is performed; this reads a local file only")
    try:
        if not a.timing_confirmed:
            raise Refused("event timing is %s until confirmed against an issuer "
                          "release or SEC filing; pass --timing-confirmed"
                          % SCHEDULING_LABEL)
        src = Path(a.csv)
        if not src.is_file():
            raise Refused("no such file: %s" % src)
        raw = src.read_bytes()
        digest, nbytes = sha256_bytes(raw), len(raw)
        print("  source file            %s" % src.name)
        print("  bytes                  %d" % nbytes)
        print("  sha256                 %s" % digest)

        retrieved = parse_rfc3339(a.retrieved_at)
        rows, meta = parse_cboe_csv(raw, a.ticker)
        display = parse_display_timestamp(a.quote_timestamp
                                          or meta.get("display_timestamp"))
        under_ts = (parse_rfc3339(a.underlying_timestamp)
                    if a.underlying_timestamp else display)
        px = a.underlying_price if a.underlying_price is not None \
            else meta.get("underlying_price")
        if px is None or px <= 0:
            raise Refused("no usable underlying price; supply --underlying-price")

        assert_delayed_display_timing(display, retrieved)
        assert_in_snapshot_window(retrieved.astimezone(ET), a.event_date, session)

        exp = first_expiration_after({r["expiration_date"] for r in rows},
                                     a.event_date)
        at_exp = [r for r in rows if r["expiration_date"] == exp]
        k = assert_unambiguous_atm([r["strike"] for r in at_exp], px)
        if abs(k - nearest_strike(
                [{"strike": r["strike"]} for r in at_exp], px)) > 1e-9:
            raise Refused("ATM selection disagrees with the frozen nearest-strike rule")
        legs = cboe_legs(at_exp, exp, k)
        for lg in legs:
            if lg["bid"] is None or lg["ask"] is None:
                raise Refused("%s leg missing bid or ask; last-price substitution "
                              "is prohibited" % lg["option_type"])
            if lg["bid"] < 0 or lg["ask"] <= 0:
                raise Refused("%s leg has a negative or non-positive quote"
                              % lg["option_type"])
            if lg["bid"] > lg["ask"]:
                raise Refused("%s leg crossed market" % lg["option_type"])

        rec = build_record(
            ticker=a.ticker.upper(), issuer_name=a.issuer or a.ticker.upper(),
            event_date=a.event_date, session=session, underlying_price=float(px),
            chain=legs, expirations={r["expiration_date"] for r in rows},
            quote_timestamp_utc=utc_second_stamp(display),
            provider=CBOE_PROVIDER, latency_label=CBOE_LABEL,
            feed=CBOE_FEED, feed_designation=CBOE_LABEL,
            raw_sha256=digest, search_features=[],
            universe_source_kind=(_committed_universe() or {}).get(
                "source_kind", "UNKNOWN"),
            retrieved_at_utc=utc_second_stamp(retrieved),
            underlying_timestamp_utc=utc_second_stamp(under_ts),
            capture_method=CBOE_CAPTURE_METHOD,
            source_file_name=src.name, source_file_bytes=nbytes,
            source_file_sha256=digest,
            underlying_price_source="cboe_delayed_manual")

        CACHE.mkdir(parents=True, exist_ok=True)
        kept = CACHE / ("cboe_%s_%s_%s.csv" % (a.ticker.upper(), a.event_date,
                                               digest[:12]))
        kept.write_bytes(raw)
        append_provenance({
            "data_class": PROVENANCE_CLASS, "record_type": "cboe_manual_file",
            "label": CBOE_LABEL, "provider": CBOE_PROVIDER, "feed": CBOE_FEED,
            "capture_method": CBOE_CAPTURE_METHOD, "ticker": a.ticker.upper(),
            "event_date": str(a.event_date), "source_file_name": src.name,
            "source_file_bytes": nbytes, "source_file_sha256": digest,
            "retrieved_at_utc": utc_second_stamp(retrieved),
            "displayed_quote_timestamp_utc": utc_second_stamp(display),
            "underlying_timestamp_utc": utc_second_stamp(under_ts),
            "preserved_repository_external": str(kept),
            "automated_access_to_cboe": False,
        })
        rid = append_record(rec)
    except Refused as e:
        print("  REFUSED:", redact(e))
        return 3
    except Exception as e:                                    # noqa: BLE001
        print("  ERROR:", redact("%s: %s" % (type(e).__name__, e)))
        return 1
    print("  original preserved repository-external: %s" % kept)
    print("  RECORDED record_id=%s expiration=%s strike=%s" % (rid, rec["expiration"],
                                                               rec["strike"]))
    print("  displayed quote ts %s | retrieved %s (recorded separately)"
          % (rec["quote_timestamp_utc"], rec["retrieved_at_utc"]))
    print("  no executable cost, simulated P&L or trade instruction was emitted.")
    return 0


def mode_alpaca_check(argv=None):
    """ONE minimal Alpaca connectivity + schema-validation request.

    Marked NON_EVENT_SYSTEM_VALIDATION_ONLY. It is written to the provenance ledger,
    never to the research manifest, and it can never become a study observation. No
    response body and no option price is printed.
    """
    ap = argparse.ArgumentParser(prog="alpaca-check")
    ap.add_argument("--symbol", default="AAPL",
                    help="system-validation underlying; NOT a study observation")
    a = ap.parse_args(list(argv or []))
    print("ALPACA CONNECTIVITY / SCHEMA VALIDATION  [" + SYSTEM_VALIDATION_LABEL + "]")
    pres = alpaca_credential_presence()
    for k, v in pres.items():
        print(f"  {k:<24} {'PRESENT' if v else 'ABSENT'}")
    if not all(pres.values()):
        print("  REFUSED: both approved variables are required. No request issued and "
              "no other provider substituted.")
        return 2

    req_ts = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    path = ALPACA_OPTIONS_SNAPSHOT_PATH + a.symbol.upper()
    try:
        status, raw = alpaca_get(path, {"feed": ALPACA_OPTIONS_FEED, "limit": 25})
    except Refused as e:
        print("  REFUSED:", redact(e))
        return 2
    except Exception as e:                                    # noqa: BLE001
        print("  TRANSPORT ERROR:", redact(f"{type(e).__name__}: {e}"))
        return 1

    CACHE.mkdir(parents=True, exist_ok=True)
    raw_path = CACHE / "alpaca_system_validation.json"
    raw_path.write_bytes(raw)
    digest = sha256_bytes(raw)
    print(f"  request_timestamp_utc    {req_ts}")
    print(f"  endpoint                 {ALPACA_OPTIONS_SNAPSHOT_PATH}<underlying>"
          "   (market data only)")
    print(f"  feed                     {ALPACA_OPTIONS_FEED}")
    print(f"  feed_designation         {ALPACA_LABEL}")
    print(f"  response_status          {status}")
    print(f"  response_bytes           {len(raw):,}")
    print(f"  response_sha256          {digest}")
    print(f"  raw body kept repository-external, never committed: {raw_path}")

    rec = {
        "data_class": VALIDATION_CLASS, "record_type": "provider_connectivity_check",
        "label": SYSTEM_VALIDATION_LABEL, "provider": "alpaca",
        "feed": ALPACA_OPTIONS_FEED, "feed_designation": ALPACA_LABEL,
        "request_timestamp_utc": req_ts,
        "endpoint": ALPACA_OPTIONS_SNAPSHOT_PATH + "<underlying>",
        "response_status": int(status), "response_bytes": len(raw),
        "response_sha256": digest, "entered_research_panel": False,
        "may_be_used_as_a_study_observation": False,
    }

    if status != 200:
        # Distinguish "credentials rejected" from "no options entitlement" with one
        # further MARKET-DATA request. Statuses only; no credential detail is derived,
        # printed or stored, and no other provider is tried either way.
        eq_status = None
        try:
            eq_status, _eq_raw = alpaca_get("/v2/stocks/AAPL/trades/latest",
                                            {"feed": ALPACA_STOCK_FEED})
        except Exception:                                     # noqa: BLE001
            eq_status = None
        if status in (401, 403) and eq_status in (401, 403):
            diag = "CREDENTIALS_REJECTED_BY_PROVIDER"
            print("  AUTHENTICATION FAILED. Equity market data returns "
                  f"{eq_status} as well, so the credential pair itself is rejected -- "
                  "this is not an options-entitlement problem.")
        elif status in (401, 403):
            diag = "OPTIONS_FEED_NOT_ENTITLED"
            print(f"  Equity market data returns {eq_status} but options returns "
                  f"{status}: the credentials work and the options feed is not "
                  "entitled.")
        else:
            diag = "PROVIDER_ERROR"
            print(f"  Provider returned {status}.")
        print("  STOPPING. No fallback provider is tried, no website is scraped, and "
              "no observation is manufactured.")
        rec["outcome"] = "AUTH_OR_ENTITLEMENT_FAILED"
        rec["diagnosis"] = diag
        rec["equity_market_data_status"] = eq_status
        append_provenance(rec)
        return 1

    try:
        rows = alpaca_snapshot_rows(json.loads(raw.decode("utf-8", "replace")))
    except Refused as e:
        print("  SCHEMA REFUSED:", redact(e))
        rec["outcome"] = SCHEMA_INCOMPATIBLE_STATUS
        append_provenance(rec)
        return 1

    rep_ = alpaca_schema_report(rows)
    print(f"  contracts returned       {rep_['contracts']}")
    print("  field presence (counts only -- no values, no prices):")
    for f, n in sorted(rep_["field_presence"].items()):
        print(f"    {f:<20} {n}/{rep_['contracts']}")
    print(f"  fields absent from feed  {rep_['fields_absent_from_provider'] or 'none'}")
    ok = rep_["frozen_arithmetic_implementable"]
    print("  frozen contract-selection + implied-move arithmetic implementable: "
          + ("YES" if ok else "NO -> " + SCHEMA_INCOMPATIBLE_STATUS))
    rec.update({"contracts_returned": rep_["contracts"],
                "field_presence": rep_["field_presence"],
                "fields_absent_from_provider": rep_["fields_absent_from_provider"],
                "fields_required_by_frozen_arithmetic":
                    rep_["fields_required_by_frozen_arithmetic"],
                "frozen_arithmetic_implementable": ok,
                "outcome": "OK" if ok else SCHEMA_INCOMPATIBLE_STATUS})
    append_provenance(rec)
    if not ok:
        print("  STOPPING with " + SCHEMA_INCOMPATIBLE_STATUS
              + ": the frozen formulas are not altered to accommodate a provider.")
        return 1
    return 0


# ------------------------------------------------------------------- universe

ISSUER_NOISE = re.compile(
    r"\b(class\s+[a-c]|common\s+stock|ordinary\s+shares?|shares?|capital\s+stock"
    r"|inc|incorporated|corp|corporation|co|company|plc|ltd|limited|holdings?|group"
    r"|the|nv|sa|ag)\b", re.I)


def issuer_key(name, ticker):
    """Collapse multi-class listings of one issuer onto a single key."""
    n = ISSUER_NOISE.sub(" ", str(name or ""))
    n = re.sub(r"[^a-z0-9]+", "", n.lower())
    return n or str(ticker or "").upper()


def _universe_from_json(raw):
    """Official Nasdaq constituent JSON. Identity fields only."""
    d = json.loads(raw.decode("utf-8", "replace"))
    node = d.get("data") or {}
    rows = (node.get("data") or {}).get("rows") if isinstance(node.get("data"), dict) \
        else node.get("rows")
    if not rows:
        raise Refused("official constituent JSON carried no rows")
    out = []
    for r in rows:
        t = str(r.get("symbol") or r.get("ticker") or "").strip().upper()
        n = str(r.get("companyName") or r.get("name") or "").strip()
        if t:
            out.append({"ticker": t, "issuer_name": n})
    return out


def _universe_from_csv(raw):
    """Official Invesco QQQ holdings CSV. Weights and market values are DROPPED."""
    text = raw.decode("utf-8-sig", "replace")
    rows = list(csv.reader(io.StringIO(text)))
    tick_names = ("holding ticker", "ticker", "symbol", "holdingticker")
    name_names = ("name", "security name", "holding name", "description")
    for i, r in enumerate(rows[:10]):
        low = [c.strip().lower() for c in r]
        ti = next((low.index(x) for x in tick_names if x in low), None)
        if ti is None:
            continue
        ni = next((low.index(x) for x in name_names if x in low), None)
        out = []
        for c in rows[i + 1:]:
            if len(c) <= ti:
                continue
            t = c[ti].strip().upper()
            n = c[ni].strip() if ni is not None and len(c) > ni else ""
            if t and t.replace(".", "").replace("-", "").isalnum():
                out.append({"ticker": t, "issuer_name": n})
        if out:
            return out
    raise Refused("official holdings file had no recognisable ticker column")


def mode_universe(argv=None):
    """Retrieve the universe from the frozen official source hierarchy only.

    Nasdaq-100 official constituents first; the official Invesco QQQ holdings file as
    the DISCLOSED index proxy if the first is inaccessible. Only the two official
    sources in UNIVERSE_SOURCES are ever requested; scraped, aggregator, generated and
    remembered lists have no code path here. Only identity fields are kept -- weights
    and market values are never retained.
    """
    ua = {"User-Agent": "attention-options-dislocation-study/1.0 (research; contact via repo)",
          "Accept": "*/*"}
    chosen = None
    attempts = []
    for s in UNIVERSE_SOURCES:
        got_ts = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        try:
            status, raw = http_json(s["url"], headers=ua)
        except urllib.error.HTTPError as e:
            status, raw = e.code, b""
        except Exception as e:                                # noqa: BLE001
            attempts.append((s, None, 0, f"{type(e).__name__}", got_ts))
            print(f"  rank {s['rank']}: {s['name']}")
            print(f"    UNREACHABLE ({type(e).__name__}) -- falling through to the next "
                  "OFFICIAL source only")
            continue
        parser = _universe_from_json if s["url"].rstrip("/").endswith("nasdaq100") \
            else _universe_from_csv
        try:
            members = parser(raw)
        except Exception as e:                                # noqa: BLE001
            members = []
            print(f"  rank {s['rank']}: {s['name']}")
            print(f"    http {status}, {len(raw):,} bytes -- UNPARSEABLE ({redact(e)})")
            attempts.append((s, status, len(raw), "unparseable", got_ts))
            continue
        attempts.append((s, status, len(raw), "ok", got_ts))
        chosen = (s, status, raw, members, got_ts)
        break

    print("UNIVERSE RETRIEVAL -- official sources only")
    if not chosen:
        print("  NO OFFICIAL SOURCE COULD BE AUTHENTICATED.")
        print("  Stopping. Scraped, aggregator, generated and remembered lists "
              "are prohibited by the frozen design and no substitute is used.")
        return 1

    s, status, raw, members, got_ts = chosen
    # Deduplicate by issuer; multi-class issuers contribute exactly one issuer.
    uni, seen_issuer, seen_ticker = [], set(), set()
    for m in members:
        key = issuer_key(m["issuer_name"], m["ticker"])
        if m["ticker"] in seen_ticker or key in seen_issuer:
            continue
        seen_ticker.add(m["ticker"])
        seen_issuer.add(key)
        uni.append(m)

    digest = sha256_bytes(raw)
    CACHE.mkdir(parents=True, exist_ok=True)
    (CACHE / "universe_source_raw").write_bytes(raw)
    print(f"  source rank              {s['rank']}")
    print(f"  source name              {s['name']}")
    print(f"  source kind              {s['kind']}")
    print(f"  source url               {s['url']}")
    print(f"  retrieved_utc            {got_ts}")
    print(f"  response_status          {status}")
    print(f"  response_bytes           {len(raw):,}")
    print(f"  response_sha256          {digest}")
    print(f"  constituents (raw)       {len(members)}")
    print(f"  constituents (deduped)   {len(uni)}")
    print("  retained fields          ticker, issuer_name  (weights and market values "
          "are NOT retained)")
    if s["kind"] == "OFFICIAL_ETF_HOLDINGS_PROXY":
        print("  NOTE: this is the DISCLOSED INDEX PROXY, labelled as such everywhere.")
    append_provenance({
        "data_class": PROVENANCE_CLASS, "record_type": "universe_snapshot",
        "source_rank": s["rank"], "source_name": s["name"], "source_url": s["url"],
        "source_kind": s["kind"], "retrieved_utc": got_ts,
        "response_status": int(status), "response_bytes": len(raw),
        "response_sha256": digest,
        "constituent_count_raw": len(members),
        "constituent_count_deduplicated_by_issuer": len(uni),
        "identity_fields_retained": ["ticker", "issuer_name"],
        "weights_retained": False, "market_values_retained": False,
        "constituents": sorted(uni, key=lambda m: m["ticker"]),
    })
    print(f"  provenance appended      {PROVENANCE_LEDGER.name}")
    return 0


# ------------------------------------------------------------------ readiness

def _committed_universe():
    """Read the universe back out of the committed provenance ledger."""
    if not PROVENANCE_LEDGER.exists():
        return None
    latest = None
    for line in PROVENANCE_LEDGER.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        r = json.loads(line)
        if r.get("record_type") == "universe_snapshot":
            latest = r
    return latest


def mode_readiness(argv=None):
    """Universe x calendar readiness. Collects nothing and retrieves no outcome."""
    uni = _committed_universe()
    if not uni:
        print("READINESS: no universe snapshot recorded yet -- run `universe` first.")
        return 2
    tickers = {m["ticker"] for m in uni["constituents"]}
    print("EVENT READINESS")
    print(f"  universe source          {uni['source_kind']} rank {uni['source_rank']}")
    print(f"  universe constituents    {len(tickers)}")

    cal = CACHE / "earnings_calendar.csv"
    if not cal.exists():
        print("  calendar                 ABSENT -- no candidate events can be listed.")
        return 2
    craw = cal.read_bytes()
    rows = [r for r in craw.decode("utf-8", "replace").splitlines() if r.strip()]
    idx = {h.strip(): i for i, h in enumerate(rows[0].split(","))} if rows else {}
    print(f"  calendar source          Alpha Vantage EARNINGS_CALENDAR (dates only)")
    print(f"  calendar sha256          {sha256_bytes(craw)}")
    print(f"  calendar timing status   {SCHEDULING_LABEL} -- NOT confirmed event timing")

    today = date.today()
    horizon = today + timedelta(days=CALENDAR_HORIZON_DAYS)
    cands = []
    if "symbol" in idx and "reportDate" in idx:
        for r in rows[1:]:
            c = r.split(",")
            try:
                sym = c[idx["symbol"]].strip().upper()
                d = date.fromisoformat(c[idx["reportDate"]].strip())
            except (ValueError, IndexError):
                continue
            if sym in tickers and today <= d <= horizon:
                cands.append((d, sym))
    cands.sort()
    print(f"  candidate events (universe x calendar, next {CALENDAR_HORIZON_DAYS}d): "
          f"{len(cands)}")

    now_et = datetime.now(ET)
    print(f"  now (ET)                 {now_et:%Y-%m-%d %H:%M} ET")
    print(f"  frozen snapshot window   {SNAPSHOT_TARGET_ET} ET "
          f"(+/- {SNAPSHOT_WINDOW_TOLERANCE_MINUTES} min)")

    if not cands:
        print("  NO CANDIDATE EVENT. Nothing collected; no historical observation is "
              "manufactured.")
        return 0

    print("  next candidate dates (each requires issuer-release or SEC confirmation "
          "of BOTH the date and the AMC/BMO session):")
    shown, seen_d = 0, set()
    for d, sym in cands:
        if d in seen_d:
            continue
        seen_d.add(d)
        same = sorted(s for dd, s in cands if dd == d)
        # The AMC/BMO session is NOT supplied by the vendor calendar, so the snapshot
        # day cannot be fixed yet. Report the earlier of the two possibilities.
        bmo_day = snapshot_date_for(d.isoformat(), "BMO")
        print(f"    {d.isoformat()}  n={len(same):<3} session UNCONFIRMED  "
              f"snapshot day {bmo_day} (if BMO) or {d.isoformat()} (if AMC)  "
              f"e.g. {', '.join(same[:6])}")
        shown += 1
        if shown >= 5:
            break

    first = cands[0][0]
    earliest_day = snapshot_date_for(first.isoformat(), "BMO")
    print(f"  earliest possible required collection time: {earliest_day} "
          f"{SNAPSHOT_TARGET_ET} ET (only if that event is confirmed BMO)")
    print(f"  otherwise:                                  {first.isoformat()} "
          f"{SNAPSHOT_TARGET_ET} ET (if confirmed AMC)")
    print("  ELIGIBLE NOW: NO -- every candidate still lacks issuer-release or SEC "
          "confirmation of its date and session, and the frozen window is "
          f"{SNAPSHOT_TARGET_ET} ET.")
    print("  Exiting cleanly. No observation collected, no outcome retrieved.")
    return 0


MODES = {"doctor": mode_doctor, "calendar": mode_calendar,
         "snapshot": mode_snapshot, "validate": mode_validate,
         "alpaca-check": mode_alpaca_check, "universe": mode_universe,
         "readiness": mode_readiness, "cboe-import": mode_cboe_import,
         "schedule": mode_schedule, "trends-capture": mode_trends_capture,
         "trends-finalize": mode_trends_finalize}


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    if not argv or argv[0] not in MODES:
        print("usage: collect_attention_options_snapshot.py "
              "{doctor|calendar|alpaca-check|universe|readiness|cboe-import|"
              "snapshot|validate} [options]")
        return 2
    return MODES[argv[0]](argv[1:])


if __name__ == "__main__":
    sys.exit(main())

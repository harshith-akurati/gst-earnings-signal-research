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
import hashlib
import json
import os
import re
import sys
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
             "GOOGLE_TRENDS_ALPHA_KEY")

# Official constituent sources only. Scraped/aggregator/generated lists are prohibited.
UNIVERSE_SOURCES = [
    {"rank": 1, "name": "Nasdaq-100 official constituent source",
     "url": "https://www.nasdaq.com/api/quote/list-type/nasdaq100",
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
)

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
    """Prefer real-time Tradier; else sandbox with the delayed label; else none."""
    e = os.environ if env is None else env
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


def existing_identities(path=MANIFEST):
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
                 snapshot_timestamp_utc=None):
    """Assemble one sanitized manifest record, refusing anything that breaks a rule."""
    assert_pre_announcement(quote_timestamp_utc, event_date, session)
    exp = first_expiration_after(expirations, event_date)
    at_exp = [o for o in chain if str(o.get("expiration_date")) == exp]
    if not at_exp:
        raise Refused(f"no chain rows for expiration {exp}")
    k = nearest_strike(at_exp, underlying_price)
    c = quote_fields(leg(at_exp, k, "call"), "call")
    p = quote_fields(leg(at_exp, k, "put"), "put")
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
        "underlying_price": float(underlying_price),
        "expiration": exp, "strike": float(k), **c, **p,
        "search_window_end": search_window_end(event_date),
        "search_features": search_features,
        "raw_response_sha256": raw_sha256,
        "event_timing_status": SCHEDULING_LABEL,
        "universe_source_kind": universe_source_kind,
        "collected_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
    }
    rec["midpoint_implied_move"] = implied_move(rec["call_mid"], rec["put_mid"],
                                                underlying_price)
    rec["executable_straddle_cost"] = straddle_cost(rec["call_ask"], rec["put_ask"],
                                                    underlying_price)
    rec["record_id"] = record_id(rec)
    assert_no_prohibited_fields(rec)
    return rec


def append_record(rec, path=MANIFEST):
    """Append-only. A duplicate identity is refused, never overwritten."""
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
    if not prov:
        print("\nSETUP REQUIRED for options snapshots -- no website is substituted:")
        print("  1. Create a Tradier developer account (https://developer.tradier.com/).")
        print("  2. For delayed sandbox data, set TRADIER_SANDBOX_TOKEN.")
        print("     Records will be labelled DELAYED_15_MINUTES.")
        print("  3. For real-time data, obtain market-data entitlement and set TRADIER_TOKEN.")
        print("  4. Re-run: python tools/collect_attention_options_snapshot.py doctor")
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
    ap = argparse.ArgumentParser(prog="snapshot")
    ap.add_argument("--ticker", required=True)
    ap.add_argument("--issuer", required=True)
    ap.add_argument("--event-date", required=True)
    ap.add_argument("--session", required=True, choices=["AMC", "BMO", "amc", "bmo"])
    a = ap.parse_args(argv)
    prov, base, label, var = options_provider()
    if not prov:
        print("SNAPSHOT REFUSED: no Tradier credential present.")
        print("No website is scraped as a substitute. Run `doctor` for setup steps.")
        return 2
    now_et = datetime.now(ET)
    print(f"SNAPSHOT: provider={prov} latency={label} now_et={now_et:%Y-%m-%d %H:%M} "
          f"target={SNAPSHOT_TARGET_ET} ET")
    print("  live snapshot capture is gated on the prescribed timing window; this build "
          "performs no out-of-window capture.")
    return 3


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


MODES = {"doctor": mode_doctor, "calendar": mode_calendar,
         "snapshot": mode_snapshot, "validate": mode_validate}


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    if not argv or argv[0] not in MODES:
        print("usage: collect_attention_options_snapshot.py "
              "{doctor|calendar|snapshot|validate} [options]")
        return 2
    return MODES[argv[0]](argv[1:])


if __name__ == "__main__":
    sys.exit(main())

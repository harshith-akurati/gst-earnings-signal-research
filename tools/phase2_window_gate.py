#!/usr/bin/env python3
"""Local-time execution gate for the unattended Phase 2 daily panel.

The panel is scheduled for 02:15 America/Chicago. This gate permits execution
only inside 02:05-02:25 inclusive, in that zone, and refuses everything else.

Its purpose is to make a late or displaced firing fail closed. A task that was
missed -- because the host was asleep, or because the scheduler deferred it --
must not silently backfill hours later and attach a stale run_date to freshly
retrieved data. Together with StartWhenAvailable=False on the task itself, a
missed cycle is simply skipped until the next scheduled day.

Pure arithmetic on a clock. Makes NO network calls, touches no repository, and
reads nothing outside its arguments, which is what lets the deterministic suite
exercise it with sockets blocked.

Exit codes:
    0   inside the permitted window -- execution may proceed
    10  outside the permitted window -- refuse, and do nothing else

    python phase2_window_gate.py [--now <iso8601>] [--json]

--now accepts an ISO-8601 instant and exists for the deterministic tests. A
naive value is interpreted as already being America/Chicago local; an aware
value is converted into that zone. Its use is reported in the output so a
caller can never mistake an injected clock for the real one.
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import sys
from zoneinfo import ZoneInfo

EXIT_OK, EXIT_OUTSIDE_WINDOW = 0, 10

ZONE = "America/Chicago"
SCHEDULED = dt.time(2, 15)
WINDOW_OPEN = dt.time(2, 5)
WINDOW_CLOSE = dt.time(2, 25)          # inclusive


def to_zone(now: dt.datetime | None) -> tuple[dt.datetime, bool]:
    """Return (now-in-America/Chicago, whether an override was supplied)."""
    z = ZoneInfo(ZONE)
    if now is None:
        return dt.datetime.now(dt.timezone.utc).astimezone(z), False
    if now.tzinfo is None:
        return now.replace(tzinfo=z), True
    return now.astimezone(z), True


def evaluate(now: dt.datetime | None = None) -> dict:
    local, overridden = to_zone(now)
    t = local.timetz().replace(tzinfo=None)
    inside = WINDOW_OPEN <= t <= WINDOW_CLOSE

    # Minutes away from the scheduled instant, signed: negative = early.
    sched = local.replace(hour=SCHEDULED.hour, minute=SCHEDULED.minute,
                          second=0, microsecond=0)
    delta_min = round((local - sched).total_seconds() / 60.0, 2)

    if inside:
        reason = "inside permitted window"
    elif t < WINDOW_OPEN:
        reason = f"too early: {t.strftime('%H:%M:%S')} precedes window open {WINDOW_OPEN:%H:%M}"
    else:
        reason = (f"too late: {t.strftime('%H:%M:%S')} follows window close "
                  f"{WINDOW_CLOSE:%H:%M} -- a missed cycle is skipped, never backfilled")

    return {
        "zone": ZONE,
        "now_local": local.isoformat(),
        "tzname": local.tzname(),
        "scheduled": SCHEDULED.strftime("%H:%M"),
        "window_open": WINDOW_OPEN.strftime("%H:%M"),
        "window_close": WINDOW_CLOSE.strftime("%H:%M"),
        "minutes_from_scheduled": delta_min,
        "clock_overridden": overridden,
        "inside_window": inside,
        "reason": reason,
        "exit_code": EXIT_OK if inside else EXIT_OUTSIDE_WINDOW,
    }


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="phase2_window_gate")
    ap.add_argument("--now", help="ISO-8601 instant; TEST USE ONLY")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args(argv)

    now = None
    if a.now:
        try:
            now = dt.datetime.fromisoformat(a.now)
        except ValueError:
            print(f"GATE REFUSED: --now is not ISO-8601: {a.now!r}")
            return EXIT_OUTSIDE_WINDOW      # fail closed on an unreadable clock

    r = evaluate(now)
    if a.json:
        print(json.dumps(r, indent=2))
    else:
        verdict = "GATE OPEN" if r["inside_window"] else "GATE REFUSED"
        print(f"{verdict}: {r['reason']}")
        print(f"  now={r['now_local']} ({r['tzname']}) zone={r['zone']}")
        print(f"  window={r['window_open']}-{r['window_close']} scheduled={r['scheduled']} "
              f"offset={r['minutes_from_scheduled']:+g} min")
        if r["clock_overridden"]:
            print("  NOTE: clock was supplied via --now (test path), not read from the host")
    return r["exit_code"]


if __name__ == "__main__":
    sys.exit(main())

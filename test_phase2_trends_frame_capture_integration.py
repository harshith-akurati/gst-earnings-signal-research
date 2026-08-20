#!/usr/bin/env python3
# Integration tests for GST_Phase2_DailyPanel.fetch_ticker_series_scoped_backoff()
# against the new per-attempt frame archive. Imports the real module (a fake
# TrendReq-shaped object stands in for pytrends -- no network call is made;
# build_payload()/interest_over_time() are the only two methods it needs).
# Verifies two things a code-review pass can't fully guarantee on its own:
# (1) the function's return value is byte-identical to what the pre-archive
# reshape logic always produced, and (2) every attempt -- not just the
# successful one -- lands in the archive.
#
# time.sleep is monkeypatched to a no-op for the duration of these tests so
# the real (intentional) inter-attempt backoff delays don't make the suite
# slow; nothing about the retry COUNT or CONTROL FLOW is altered.
#
# Run directly: python test_phase2_trends_frame_capture_integration.py

from __future__ import annotations

import json
import os
import shutil
import sys
import tempfile
from pathlib import Path

import pandas as pd
import pandas.testing as pdt

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import GST_Phase2_DailyPanel as panel
import gst_trends_frame_archive as archive

FAILURES: list[str] = []


def check(label: str, condition: bool) -> None:
    if condition:
        print(f"PASS: {label}")
    else:
        print(f"FAIL: {label}")
        FAILURES.append(label)


class _FakeTrendReq:
    """Stands in for pytrends.request.TrendReq. Each call to
    interest_over_time() consumes the next scripted response in order --
    a DataFrame to return, or an Exception instance to raise."""

    def __init__(self, responses: list):
        self._responses = list(responses)
        self.call_count = 0
        self.build_payload_calls: list[tuple] = []

    def build_payload(self, kw_list, timeframe, geo, gprop, cat):
        self.build_payload_calls.append((tuple(kw_list), timeframe, geo, gprop, cat))

    def interest_over_time(self):
        resp = self._responses[self.call_count]
        self.call_count += 1
        if isinstance(resp, Exception):
            raise resp
        return resp


def _well_formed_df(term: str, n: int = 4) -> pd.DataFrame:
    idx = pd.date_range("2026-01-04", periods=n, freq="7D")
    return pd.DataFrame({term: [11, 22, 33, 44][:n], "isPartial": [False, False, False, True][:n]}, index=idx)


def _malformed_df() -> pd.DataFrame:
    return pd.DataFrame({"isPartial": [False]}, index=pd.date_range("2026-01-04", periods=1))


def _expected_reshape(df: pd.DataFrame, term: str) -> pd.DataFrame:
    """Exactly the reshape fetch_ticker_series_scoped_backoff has always
    done -- reproduced independently here so the test doesn't just call the
    same code it's checking."""
    return pd.DataFrame({
        "Week": df.index,
        "gst": pd.to_numeric(df[term], errors="coerce"),
        "isPartial": df["isPartial"].astype(bool),
    }).sort_values("Week").reset_index(drop=True)


class _Harness:
    """Redirects the module's archive directory to a throwaway temp dir and
    silences retry-backoff sleeps for the duration of one test."""

    def __enter__(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="phase2_trends_integration_"))
        self._orig_archive_dir = panel.TRENDS_ARCHIVE_DIR
        self._orig_sleep = panel.time.sleep
        panel.TRENDS_ARCHIVE_DIR = self.tmp
        panel.time.sleep = lambda *_a, **_k: None
        return self.tmp

    def __exit__(self, *exc):
        panel.TRENDS_ARCHIVE_DIR = self._orig_archive_dir
        panel.time.sleep = self._orig_sleep
        shutil.rmtree(self.tmp, ignore_errors=True)
        return False


def _artifact_statuses(tmp: Path) -> list[str]:
    files = sorted(p for p in tmp.iterdir() if p.name != archive.MANIFEST_FILENAME)
    return [json.loads(p.read_text(encoding="utf-8"))["status"] for p in files]


# --- 1. Immediate success: return value is byte-identical to the original
#        reshape logic, exactly one artifact written ----------------------

def test_1_immediate_success_return_value_and_single_artifact():
    with _Harness() as tmp:
        term = "AAPL"
        df = _well_formed_df(term)
        pt = _FakeTrendReq([df])
        out, status_dict = panel.fetch_ticker_series_scoped_backoff(pt, term)

        expected = _expected_reshape(df, term)
        try:
            pdt.assert_frame_equal(out, expected)
            check("1a. return value is byte-identical to the original reshape logic", True)
        except AssertionError as e:
            check(f"1a. return value is byte-identical to the original reshape logic ({e})", False)

        check("1b. status dict reports attempts=1", status_dict["attempts"] == 1)
        check("1c. status dict reports rate_limit_events=0", status_dict["rate_limit_events"] == 0)
        check("1d. status dict reports budget_exhausted=False", status_dict["budget_exhausted"] is False)
        check("1e. status dict reports status=ok", status_dict["status"] == "ok")
        check("1f. build_payload called with the exact expected query", pt.build_payload_calls[0][0] == (term,))

        statuses = _artifact_statuses(tmp)
        check(f"1g. exactly one artifact written (got {statuses})", statuses == ["success"])


# --- 2. Empty attempt then success: two artifacts, correct statuses,
#        return value still matches the SUCCESSFUL attempt only -----------

def test_2_empty_then_success_writes_both_attempts():
    with _Harness() as tmp:
        term = "MSFT"
        empty = pd.DataFrame()
        good = _well_formed_df(term)
        pt = _FakeTrendReq([empty, good])
        out, status_dict = panel.fetch_ticker_series_scoped_backoff(pt, term)

        expected = _expected_reshape(good, term)
        try:
            pdt.assert_frame_equal(out, expected)
            check("2a. return value reflects the eventual SUCCESSFUL attempt only", True)
        except AssertionError as e:
            check(f"2a. return value reflects the eventual SUCCESSFUL attempt only ({e})", False)

        check("2b. status dict reports attempts=2", status_dict["attempts"] == 2)
        statuses = _artifact_statuses(tmp)
        check(f"2c. two artifacts written, empty then success (got {statuses})", statuses == ["empty", "success"])


# --- 3. Malformed attempt then success ------------------------------------

def test_3_malformed_then_success():
    with _Harness() as tmp:
        term = "GOOGL"
        good = _well_formed_df(term)
        pt = _FakeTrendReq([_malformed_df(), good])
        out, status_dict = panel.fetch_ticker_series_scoped_backoff(pt, term)
        expected = _expected_reshape(good, term)
        try:
            pdt.assert_frame_equal(out, expected)
            check("3a. return value correct after a malformed first attempt", True)
        except AssertionError as e:
            check(f"3a. return value correct after a malformed first attempt ({e})", False)
        statuses = _artifact_statuses(tmp)
        check(f"3b. artifacts recorded as malformed then success (got {statuses})", statuses == ["malformed", "success"])


# --- 4. A raised exception (network-shaped failure) is archived as
#        status=failed, and the exception still propagates/retries exactly
#        as it did before this archive existed -----------------------------

def test_4_network_failure_archived_as_failed_and_retried():
    with _Harness() as tmp:
        term = "TSLA"
        good = _well_formed_df(term)
        pt = _FakeTrendReq([ConnectionError("simulated network failure"), good])
        out, status_dict = panel.fetch_ticker_series_scoped_backoff(pt, term)
        expected = _expected_reshape(good, term)
        try:
            pdt.assert_frame_equal(out, expected)
            check("4a. return value correct after a failed first attempt", True)
        except AssertionError as e:
            check(f"4a. return value correct after a failed first attempt ({e})", False)
        check("4b. status dict reports attempts=2 (the failure still counted as an attempt)",
              status_dict["attempts"] == 2)
        statuses = _artifact_statuses(tmp)
        check(f"4c. artifacts recorded as failed then success (got {statuses})", statuses == ["failed", "success"])
        files = sorted(p for p in tmp.iterdir() if p.name != archive.MANIFEST_FILENAME)
        failed_envelope = json.loads(files[0].read_text(encoding="utf-8"))
        check("4d. failed artifact records the exception message",
              "simulated network failure" in (failed_envelope["error_message"] or ""))


# --- 5. All attempts exhausted (all empty): return value matches the
#        original empty-fallback shape exactly, one artifact per attempt --

def test_5_all_attempts_exhausted():
    with _Harness() as tmp:
        term = "NKE"
        pt = _FakeTrendReq([pd.DataFrame()] * panel.GST_MAX_ATTEMPTS)
        out, status_dict = panel.fetch_ticker_series_scoped_backoff(pt, term)
        check("5a. return value is the documented empty fallback frame",
              list(out.columns) == ["Week", "gst", "isPartial"] and len(out) == 0)
        check("5b. status dict reports attempts_exhausted",
              status_dict["status"] == "attempts_exhausted")
        check(f"5c. status dict reports attempts={panel.GST_MAX_ATTEMPTS}",
              status_dict["attempts"] == panel.GST_MAX_ATTEMPTS)
        statuses = _artifact_statuses(tmp)
        check(f"5d. one artifact per attempt, all empty (got {statuses})",
              statuses == ["empty"] * panel.GST_MAX_ATTEMPTS)


# --- 6. An archive-write failure never fails the capture -------------------

def test_6_archive_write_failure_never_fails_capture():
    with _Harness() as tmp:
        term = "DELL"
        good = _well_formed_df(term)
        pt = _FakeTrendReq([good])

        def _boom(*args, **kwargs):
            raise OSError("simulated disk failure")

        orig = archive.write_trends_attempt_artifact
        panel.gst_trends_frame_archive.write_trends_attempt_artifact = _boom
        try:
            out, status_dict = panel.fetch_ticker_series_scoped_backoff(pt, term)
            expected = _expected_reshape(good, term)
            try:
                pdt.assert_frame_equal(out, expected)
                check("6a. capture still returns the correct value when the archive write raises", True)
            except AssertionError as e:
                check(f"6a. capture still returns the correct value when the archive write raises ({e})", False)
            check("6b. status dict still reports success", status_dict["status"] == "ok")
        finally:
            panel.gst_trends_frame_archive.write_trends_attempt_artifact = orig


if __name__ == "__main__":
    test_1_immediate_success_return_value_and_single_artifact()
    test_2_empty_then_success_writes_both_attempts()
    test_3_malformed_then_success()
    test_4_network_failure_archived_as_failed_and_retried()
    test_5_all_attempts_exhausted()
    test_6_archive_write_failure_never_fails_capture()

    print()
    if FAILURES:
        print(f"{len(FAILURES)} FAILURE(S): {FAILURES}")
        sys.exit(1)
    print("ALL PHASE2 TRENDS FRAME CAPTURE INTEGRATION TESTS PASSED")
    sys.exit(0)

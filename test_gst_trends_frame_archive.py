#!/usr/bin/env python3
# Deterministic unit tests for gst_trends_frame_archive.py. Plain-assert
# style matching this repository's existing convention (no external test
# framework). Zero network calls; every DataFrame is constructed locally.
#
# Run directly: python test_gst_trends_frame_archive.py

from __future__ import annotations

import json
import os
import shutil
import sys
import tempfile
from pathlib import Path

import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import gst_trends_frame_archive as archive

FAILURES: list[str] = []


def check(label: str, condition: bool) -> None:
    if condition:
        print(f"PASS: {label}")
    else:
        print(f"FAIL: {label}")
        FAILURES.append(label)


def _tmp_dir() -> Path:
    d = Path(tempfile.mkdtemp(prefix="gst_trends_frame_archive_test_"))
    return d


def _success_df(ticker: str = "AAPL", n: int = 5) -> pd.DataFrame:
    idx = pd.date_range("2026-01-04", periods=n, freq="7D")
    return pd.DataFrame({ticker: [10, 20, 30, 40, 50][:n], "isPartial": [False] * n}, index=idx)


def _base_kwargs(tmp: Path, **overrides) -> dict:
    kwargs = dict(
        archive_dir=tmp, ticker="AAPL", query_term="AAPL", attempt=1, run_date="2026-08-17",
        timeframe="2025-10-22 2026-08-17", geo="US", gprop="", cat=0,
        df=_success_df(), status=archive.STATUS_SUCCESS, error_message=None,
    )
    kwargs.update(overrides)
    return kwargs


# --- 1. Basic write: success status ------------------------------------

def test_1_success_write_creates_artifact_and_manifest():
    tmp = _tmp_dir()
    try:
        path = archive.write_trends_attempt_artifact(**_base_kwargs(tmp))
        check("1a. artifact file created", path.exists())
        check("1b. artifact filename is deterministic", path.name == "2026-08-17_AAPL_attempt01.json")
        manifest_path = tmp / archive.MANIFEST_FILENAME
        check("1c. manifest file created", manifest_path.exists())
        lines = manifest_path.read_text(encoding="utf-8").splitlines()
        check("1d. manifest has exactly one line", len(lines) == 1)
        entry = json.loads(lines[0])
        check("1e. manifest entry maps request_id to this artifact path", entry["artifact_path"] == path.name)
        envelope = json.loads(path.read_text(encoding="utf-8"))
        check("1f. envelope status recorded", envelope["status"] == "success")
        check("1g. envelope ticker recorded", envelope["ticker"] == "AAPL")
        check("1h. envelope has a request_id", bool(envelope["request_id"]))
        check("1i. envelope has ms-precision UTC timestamp", envelope["retrieved_at_utc"].endswith("+00:00")
              and "." in envelope["retrieved_at_utc"])
        check("1j. no leftover .tmp file", not any(p.name.startswith("2026-08-17_AAPL_attempt01.json.tmp")
                                                     for p in tmp.iterdir()))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


# --- 2. Every attempt is its own artifact -------------------------------

def test_2_repeated_pulls_never_combined():
    tmp = _tmp_dir()
    try:
        p1 = archive.write_trends_attempt_artifact(**_base_kwargs(tmp, attempt=1))
        p2 = archive.write_trends_attempt_artifact(**_base_kwargs(tmp, attempt=2))
        check("2a. two attempts produce two distinct files", p1 != p2)
        check("2b. both files exist independently", p1.exists() and p2.exists())
        manifest_lines = (tmp / archive.MANIFEST_FILENAME).read_text(encoding="utf-8").splitlines()
        check("2c. manifest has one line per attempt, not merged", len(manifest_lines) == 2)
        e1 = json.loads(p1.read_text(encoding="utf-8"))
        e2 = json.loads(p2.read_text(encoding="utf-8"))
        check("2d. each artifact records its own attempt number", e1["attempt"] == 1 and e2["attempt"] == 2)
        check("2e. each artifact has its own distinct request_id", e1["request_id"] != e2["request_id"])
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


# --- 3. All four statuses -------------------------------------------------

def test_3_all_four_statuses_writable():
    tmp = _tmp_dir()
    try:
        p_ok = archive.write_trends_attempt_artifact(**_base_kwargs(tmp, attempt=1))
        p_empty = archive.write_trends_attempt_artifact(
            **_base_kwargs(tmp, attempt=2, df=pd.DataFrame(), status=archive.STATUS_EMPTY))
        p_none = archive.write_trends_attempt_artifact(
            **_base_kwargs(tmp, attempt=3, df=None, status=archive.STATUS_EMPTY))
        malformed_df = pd.DataFrame({"isPartial": [False]}, index=pd.date_range("2026-01-04", periods=1))
        p_malformed = archive.write_trends_attempt_artifact(
            **_base_kwargs(tmp, attempt=4, df=malformed_df, status=archive.STATUS_MALFORMED))
        p_failed = archive.write_trends_attempt_artifact(
            **_base_kwargs(tmp, attempt=5, df=None, status=archive.STATUS_FAILED,
                            error_message="ConnectionError: timed out"))
        statuses = {p.name: json.loads(p.read_text(encoding="utf-8"))["status"]
                    for p in (p_ok, p_empty, p_none, p_malformed, p_failed)}
        check("3a. success status written", statuses[p_ok.name] == "success")
        check("3b. empty (empty df) status written", statuses[p_empty.name] == "empty")
        check("3c. empty (None df) status written", statuses[p_none.name] == "empty")
        check("3d. malformed status written", statuses[p_malformed.name] == "malformed")
        check("3e. failed status written", statuses[p_failed.name] == "failed")
        failed_envelope = json.loads(p_failed.read_text(encoding="utf-8"))
        check("3f. failed status records the error message", failed_envelope["error_message"] == "ConnectionError: timed out")
        check("3g. failed status has no frame_csv", failed_envelope["frame_csv"] is None)
        check("3h. failed status has no frame_sha256", failed_envelope["frame_sha256"] is None)
        none_envelope = json.loads(p_none.read_text(encoding="utf-8"))
        check("3i. None-df empty status has no frame_csv", none_envelope["frame_csv"] is None)
        check("3j. non-failed statuses have no error_message", json.loads(p_ok.read_text(encoding="utf-8"))["error_message"] is None)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


# --- 4. Metadata completeness -------------------------------------------

def test_4_envelope_has_all_required_fields():
    tmp = _tmp_dir()
    try:
        path = archive.write_trends_attempt_artifact(**_base_kwargs(tmp))
        envelope = json.loads(path.read_text(encoding="utf-8"))
        required = [
            "request_id", "ticker", "query_term", "attempt", "run_date", "retrieved_at_utc",
            "timeframe", "geo", "gprop", "cat", "python_version", "pytrends_version",
            "pandas_version", "numpy_version", "status", "error_message",
            "expected_columns", "actual_columns", "expected_row_count_estimate",
            "actual_row_count", "frame_sha256", "frame_csv",
        ]
        missing = [f for f in required if f not in envelope]
        check(f"4a. all required fields present (missing: {missing})", not missing)
        check("4b. python_version is non-empty", bool(envelope["python_version"]))
        check("4c. pandas_version is non-empty", bool(envelope["pandas_version"]))
        check("4d. geo/gprop/cat recorded exactly as given",
              envelope["geo"] == "US" and envelope["gprop"] == "" and envelope["cat"] == 0)
        check("4e. actual_row_count matches the real frame length", envelope["actual_row_count"] == 5)
        check("4f. expected_row_count_estimate is a plausible weekly estimate for a ~300-day window",
              isinstance(envelope["expected_row_count_estimate"], int)
              and 35 <= envelope["expected_row_count_estimate"] <= 50)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


# --- 5. SHA-256 correctness and round-trip -------------------------------

def test_5_sha256_and_roundtrip():
    tmp = _tmp_dir()
    try:
        df = _success_df()
        path = archive.write_trends_attempt_artifact(**_base_kwargs(tmp, df=df))
        envelope = json.loads(path.read_text(encoding="utf-8"))
        import hashlib
        expected_hash = hashlib.sha256(df.to_csv().encode("utf-8")).hexdigest()
        check("5a. frame_sha256 matches an independently computed hash of df.to_csv()",
              envelope["frame_sha256"] == expected_hash)
        recomputed_hash = hashlib.sha256(envelope["frame_csv"].encode("utf-8")).hexdigest()
        check("5b. frame_sha256 matches a hash of the frame_csv actually stored in the artifact",
              envelope["frame_sha256"] == recomputed_hash)
        roundtripped = pd.read_csv(pd.io.common.StringIO(envelope["frame_csv"]), index_col=0)
        check("5c. frame_csv round-trips to the same shape", roundtripped.shape == df.shape)
        check("5d. frame_csv round-trips to the same values",
              list(roundtripped["AAPL"]) == list(df["AAPL"]))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


# --- 6. Atomicity: no partial artifact ever visible ----------------------

def test_6_atomic_write_leaves_no_tmp_residue():
    tmp = _tmp_dir()
    try:
        archive.write_trends_attempt_artifact(**_base_kwargs(tmp))
        tmp_files = [p for p in tmp.iterdir() if ".tmp-" in p.name]
        check("6a. no .tmp file left behind after a successful write", not tmp_files)
        manifest_tmp_files = [p for p in tmp.iterdir() if p.name.startswith("MANIFEST.jsonl.tmp")]
        check("6b. no manifest .tmp file left behind", not manifest_tmp_files)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


# --- 7. Manifest is append-only: old lines never rewritten ---------------

def test_7_manifest_append_only():
    tmp = _tmp_dir()
    try:
        archive.write_trends_attempt_artifact(**_base_kwargs(tmp, attempt=1))
        manifest_path = tmp / archive.MANIFEST_FILENAME
        first_line = manifest_path.read_text(encoding="utf-8").splitlines()[0]
        archive.write_trends_attempt_artifact(**_base_kwargs(tmp, attempt=2))
        lines_after = manifest_path.read_text(encoding="utf-8").splitlines()
        check("7a. manifest grew by exactly one line", len(lines_after) == 2)
        check("7b. the first line is byte-for-byte unchanged", lines_after[0] == first_line)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


# --- 8. FAIL CLOSED: duplicate artifact path ------------------------------

def test_8_fail_closed_duplicate_artifact_path():
    tmp = _tmp_dir()
    try:
        archive.write_trends_attempt_artifact(**_base_kwargs(tmp, attempt=1))
        raised = False
        try:
            archive.write_trends_attempt_artifact(**_base_kwargs(tmp, attempt=1))
        except archive.TrendsArchiveCollisionError:
            raised = True
        check("8a. writing the same (run_date, ticker, attempt) twice raises TrendsArchiveCollisionError", raised)
        manifest_lines = (tmp / archive.MANIFEST_FILENAME).read_text(encoding="utf-8").splitlines()
        check("8b. the failed second write did not add a manifest line", len(manifest_lines) == 1)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


# --- 9. FAIL CLOSED: missing/empty query label ----------------------------

def test_9_fail_closed_missing_or_empty_label():
    tmp = _tmp_dir()
    for bad_ticker in (None, "", "   "):
        raised = False
        try:
            archive.write_trends_attempt_artifact(**_base_kwargs(tmp, ticker=bad_ticker, query_term=bad_ticker))
        except archive.TrendsArchiveLabelError:
            raised = True
        check(f"9a. ticker={bad_ticker!r} raises TrendsArchiveLabelError", raised)
    for bad_term in (None, "", "  "):
        raised = False
        try:
            archive.write_trends_attempt_artifact(**_base_kwargs(tmp, query_term=bad_term))
        except archive.TrendsArchiveLabelError:
            raised = True
        check(f"9b. query_term={bad_term!r} raises TrendsArchiveLabelError", raised)
    shutil.rmtree(tmp, ignore_errors=True)


# --- 10. FAIL CLOSED: ticker requested != ticker labeled ------------------

def test_10_fail_closed_ticker_mismatch():
    tmp = _tmp_dir()
    try:
        raised = False
        try:
            archive.write_trends_attempt_artifact(**_base_kwargs(tmp, ticker="AAPL", query_term="MSFT"))
        except archive.TrendsArchiveLabelError as e:
            raised = True
            check("10b. error message names both mismatched tickers", "AAPL" in str(e) and "MSFT" in str(e))
        check("10a. ticker != query_term raises TrendsArchiveLabelError", raised)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


# --- 11. FAIL CLOSED: status="success" but schema doesn't back it up -----

def test_11_fail_closed_schema_mismatch_on_success():
    tmp = _tmp_dir()
    try:
        # df missing the required ticker column entirely, but caller
        # (incorrectly) claims status=success.
        bad_df = pd.DataFrame({"isPartial": [False, False]}, index=pd.date_range("2026-01-04", periods=2))
        raised = False
        try:
            archive.write_trends_attempt_artifact(
                **_base_kwargs(tmp, df=bad_df, status=archive.STATUS_SUCCESS))
        except archive.TrendsArchiveSchemaError:
            raised = True
        check("11a. status=success with a df missing the ticker column raises TrendsArchiveSchemaError", raised)

        raised_on_none = False
        try:
            archive.write_trends_attempt_artifact(
                **_base_kwargs(tmp, df=None, status=archive.STATUS_SUCCESS))
        except archive.TrendsArchiveSchemaError:
            raised_on_none = True
        check("11b. status=success with df=None also raises TrendsArchiveSchemaError", raised_on_none)

        # An extra, unexpected column alongside the required ones must NOT
        # raise -- only a MISSING required column is a labeling bug.
        extra_col_df = _success_df().assign(extra_metadata_col=1)
        no_raise = True
        try:
            archive.write_trends_attempt_artifact(
                **_base_kwargs(tmp, attempt=99, df=extra_col_df, status=archive.STATUS_SUCCESS))
        except archive.TrendsArchiveSchemaError:
            no_raise = False
        check("11c. status=success with EXTRA columns beyond the required ones does not raise", no_raise)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


# --- 12. Malformed/empty/failed responses never raise ---------------------

def test_12_bad_responses_are_evidence_not_failures():
    tmp = _tmp_dir()
    try:
        # An empty df, a df missing the ticker column, and a None df must
        # all write successfully (no exception) as long as status honestly
        # reflects them -- this is the core distinction the spec draws.
        archive.write_trends_attempt_artifact(
            **_base_kwargs(tmp, attempt=1, df=pd.DataFrame(), status=archive.STATUS_EMPTY))
        archive.write_trends_attempt_artifact(
            **_base_kwargs(tmp, attempt=2, df=None, status=archive.STATUS_FAILED, error_message="boom"))
        malformed_df = pd.DataFrame({"isPartial": [True]}, index=pd.date_range("2026-01-04", periods=1))
        archive.write_trends_attempt_artifact(
            **_base_kwargs(tmp, attempt=3, df=malformed_df, status=archive.STATUS_MALFORMED))
        check("12a. all three bad-response artifacts were written without raising", True)
        manifest_lines = (tmp / archive.MANIFEST_FILENAME).read_text(encoding="utf-8").splitlines()
        check("12b. all three appear in the manifest", len(manifest_lines) == 3)
    except Exception as e:
        check(f"12. bad Trends responses must never raise (got {e!r})", False)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


# --- 13. Invalid status value is rejected up front -----------------------

def test_13_invalid_status_value_rejected():
    tmp = _tmp_dir()
    try:
        raised = False
        try:
            archive.write_trends_attempt_artifact(**_base_kwargs(tmp, status="not_a_real_status"))
        except ValueError:
            raised = True
        check("13a. an unrecognized status string raises ValueError", raised)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    test_1_success_write_creates_artifact_and_manifest()
    test_2_repeated_pulls_never_combined()
    test_3_all_four_statuses_writable()
    test_4_envelope_has_all_required_fields()
    test_5_sha256_and_roundtrip()
    test_6_atomic_write_leaves_no_tmp_residue()
    test_7_manifest_append_only()
    test_8_fail_closed_duplicate_artifact_path()
    test_9_fail_closed_missing_or_empty_label()
    test_10_fail_closed_ticker_mismatch()
    test_11_fail_closed_schema_mismatch_on_success()
    test_12_bad_responses_are_evidence_not_failures()
    test_13_invalid_status_value_rejected()

    print()
    if FAILURES:
        print(f"{len(FAILURES)} FAILURE(S): {FAILURES}")
        sys.exit(1)
    print("ALL GST TRENDS FRAME ARCHIVE TESTS PASSED")
    sys.exit(0)

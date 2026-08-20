#!/usr/bin/env python3
# GST TRENDS FRAME ARCHIVE -- immutable, append-only archival of every raw
# pytrends retrieval ATTEMPT (not just successful ones) for the production
# Phase 2 attention-panel collector.
#
# Deliberately dependency-light: only pandas and the standard library. This
# module never imports pytrends, requests, or yfinance -- it accepts a
# DataFrame (or None) that its caller already obtained, plus metadata
# describing the attempt. That keeps it fully unit-testable on its own, and
# keeps its own CI footprint to exactly what's already installed for the
# rest of this repository's deterministic test suite.
#
# SCOPE. This is the ONLY raw-Trends-response archival mechanism this module
# knows about. A separate, unrelated requests-response-hook mechanism exists
# on a different branch (archive/gst-raw-response-capture, commit a1a0717)
# and does not run in production; per an explicit product decision, this
# module's directory and manifest are its own -- nothing here reads,
# writes, or coordinates with that other mechanism in any way.
#
# WHAT COUNTS AS A FAILURE HERE, AND WHAT DOESN'T. An empty, malformed, or
# outright failed response from Google Trends is not a defect in this
# module -- it is exactly the evidence this archive exists to preserve, and
# is recorded via `status`. This module raises ONLY when asked to write
# something that would make the ARCHIVE ITSELF untrustworthy: a duplicate
# artifact path, a missing/empty ticker or query label, a labeling
# mismatch between the ticker requested and the ticker recorded, or a
# `status="success"` claim whose actual columns don't back it up. None of
# those raises are ever allowed to propagate into a live capture -- callers
# are expected to catch them, log loudly, and continue. This module does
# not do that catching itself: keeping the raise here (rather than
# swallowing internally) is what makes every fail-closed condition directly
# testable in isolation.
from __future__ import annotations

import hashlib
import importlib.metadata
import json
import os
import platform
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

import pandas as pd

STATUS_SUCCESS = "success"
STATUS_EMPTY = "empty"
STATUS_MALFORMED = "malformed"
STATUS_FAILED = "failed"
VALID_STATUSES = frozenset({STATUS_SUCCESS, STATUS_EMPTY, STATUS_MALFORMED, STATUS_FAILED})

MANIFEST_FILENAME = "MANIFEST.jsonl"


class TrendsArchiveError(ValueError):
    """Base class for fail-closed artifact-integrity errors. Always raised
    BEFORE any file is written or modified. Never raised because Google
    Trends returned a bad response -- that is `status`, not a defect."""


class TrendsArchiveCollisionError(TrendsArchiveError):
    """A duplicate artifact path or a duplicate request_id in the manifest.
    Artifacts and manifest lines are immutable once written; a collision is
    refused rather than silently overwritten or merged."""


class TrendsArchiveLabelError(TrendsArchiveError):
    """A missing/empty query label, or the ticker requested does not match
    the ticker labeled on the artifact."""


class TrendsArchiveSchemaError(TrendsArchiveError):
    """status="success" was declared, but the actual DataFrame's columns
    don't contain what a genuine success requires -- a caller-side
    mislabeling bug, never a Trends data-quality fact."""


def _package_version(name: str) -> str:
    try:
        return importlib.metadata.version(name)
    except importlib.metadata.PackageNotFoundError:
        return "unknown"


def _atomic_write_text(path: Path, text: str) -> None:
    """Temp file in the same directory, then os.replace() -- atomic on both
    POSIX and Windows when source and destination are on the same volume,
    which they always are here (both under archive_dir)."""
    tmp_path = path.with_name(path.name + f".tmp-{uuid.uuid4().hex[:8]}")
    with open(tmp_path, "w", encoding="utf-8") as f:
        f.write(text)
    os.replace(tmp_path, path)


def _append_manifest_line(manifest_path: Path, entry: dict) -> None:
    """Append-only: reads every existing line byte-for-byte, adds exactly one
    new line, and atomically rewrites the file so it is never observed in a
    partially-written state. No existing line's content is ever altered --
    the read-then-rewrite is for atomicity of the ADD, not for editing.
    Raises TrendsArchiveCollisionError if this request_id is already
    present (uuid4 makes this astronomically unlikely, not impossible)."""
    existing_lines: list[str] = []
    if manifest_path.exists():
        with open(manifest_path, "r", encoding="utf-8") as f:
            existing_lines = [line for line in f.read().splitlines() if line.strip()]
    for line in existing_lines:
        try:
            existing_entry = json.loads(line)
        except json.JSONDecodeError:
            continue
        if existing_entry.get("request_id") == entry["request_id"]:
            raise TrendsArchiveCollisionError(
                f"request_id {entry['request_id']!r} already present in manifest -- "
                f"refusing to append a duplicate mapping"
            )
    existing_lines.append(json.dumps(entry, sort_keys=True))
    _atomic_write_text(manifest_path, "\n".join(existing_lines) + "\n")


def _estimate_expected_row_count(timeframe: str) -> Optional[int]:
    """Audit aid only, never a validation gate: this module's callers always
    request a >=269-day window, where Trends buckets weekly, so the expected
    row count is roughly (days / 7). A real response landing a row or two
    off this estimate near a week boundary is normal, not evidence of a
    problem -- it is recorded purely so a downstream reader can see the
    estimate and the actual figure side by side."""
    try:
        start_s, end_s = timeframe.split(" ")
        start_d = datetime.fromisoformat(start_s).date()
        end_d = datetime.fromisoformat(end_s).date()
        return round((end_d - start_d).days / 7)
    except Exception:
        return None


def write_trends_attempt_artifact(
    *,
    archive_dir: Path,
    ticker: str,
    query_term: str,
    attempt: int,
    run_date: str,
    timeframe: str,
    geo: str,
    gprop: str,
    cat: int,
    df: Optional[pd.DataFrame],
    status: str,
    error_message: Optional[str] = None,
    pytrends_version: Optional[str] = None,
) -> Path:
    """Writes one immutable artifact for a single retrieval ATTEMPT (every
    attempt gets its own file and its own manifest line -- repeated pulls
    are never combined, averaged, or deduplicated at capture time; any
    stability analysis is a downstream concern over the archive), plus an
    append-only manifest line mapping its request_id to its artifact path.

    Records: a fresh request_id, ticker, query_term, attempt number,
    run_date, a UTC ms-precision retrieval timestamp, the exact timeframe/
    geo/gprop/cat used, the Python/pytrends/pandas/numpy versions in effect,
    the declared `status`, an error_message (only for status="failed"),
    expected vs. actual column sets, an expected-row-count ESTIMATE
    alongside the actual row count, and -- whenever a frame object exists
    at all -- its CSV serialization (its native, round-trippable form) plus
    a SHA-256 of that exact CSV text.

    FAIL CLOSED (raises, refuses to write) on an artifact-integrity
    problem:
      - the target artifact path already exists
      - `ticker` or `query_term` is missing/empty
      - `ticker` != `query_term`
      - status="success" but the DataFrame's columns don't actually contain
        the ticker column and "isPartial" (the two columns a genuine
        success requires)

    Never raises because Trends' response was empty, malformed, or the
    attempt failed outright -- record that honestly via `status` instead.
    The caller is responsible for catching any exception this function
    raises, logging it loudly, and continuing the capture: an archive
    write failure must never fail a live observation.
    """
    if status not in VALID_STATUSES:
        raise ValueError(f"status must be one of {sorted(VALID_STATUSES)}, got {status!r}")

    if not ticker or not str(ticker).strip():
        raise TrendsArchiveLabelError("ticker (query label) is missing or empty")
    if not query_term or not str(query_term).strip():
        raise TrendsArchiveLabelError("query_term (query label) is missing or empty")
    if ticker != query_term:
        raise TrendsArchiveLabelError(
            f"ticker requested {query_term!r} does not match ticker labeled {ticker!r}"
        )

    expected_columns = sorted({ticker, "isPartial"})
    actual_columns = sorted(df.columns.tolist()) if df is not None else None
    if status == STATUS_SUCCESS:
        if df is None or not set(expected_columns).issubset(set(actual_columns or [])):
            raise TrendsArchiveSchemaError(
                f"status={status!r} declares a well-formed response, but actual columns "
                f"{actual_columns} do not contain the required {expected_columns}"
            )

    archive_dir = Path(archive_dir)
    archive_dir.mkdir(parents=True, exist_ok=True)
    manifest_path = archive_dir / MANIFEST_FILENAME
    artifact_path = archive_dir / f"{run_date}_{ticker}_attempt{attempt:02d}.json"
    if artifact_path.exists():
        raise TrendsArchiveCollisionError(f"artifact path {artifact_path} already exists")

    request_id = str(uuid.uuid4())
    retrieved_at_utc = datetime.now(timezone.utc).isoformat(timespec="milliseconds")

    if df is None:
        frame_csv, frame_sha256, actual_row_count = None, None, None
    else:
        frame_csv = df.to_csv()
        frame_sha256 = hashlib.sha256(frame_csv.encode("utf-8")).hexdigest()
        actual_row_count = len(df)

    envelope = {
        "request_id": request_id,
        "ticker": ticker,
        "query_term": query_term,
        "attempt": attempt,
        "run_date": run_date,
        "retrieved_at_utc": retrieved_at_utc,
        "timeframe": timeframe,
        "geo": geo,
        "gprop": gprop,
        "cat": cat,
        "python_version": platform.python_version(),
        "pytrends_version": pytrends_version or _package_version("pytrends"),
        "pandas_version": _package_version("pandas"),
        "numpy_version": _package_version("numpy"),
        "status": status,
        "error_message": error_message,
        "expected_columns": expected_columns,
        "actual_columns": actual_columns,
        "expected_row_count_estimate": _estimate_expected_row_count(timeframe),
        "actual_row_count": actual_row_count,
        "frame_sha256": frame_sha256,
        "frame_csv": frame_csv,
    }

    _atomic_write_text(artifact_path, json.dumps(envelope, sort_keys=True))

    _append_manifest_line(manifest_path, {
        "request_id": request_id,
        "artifact_path": artifact_path.name,
        "ticker": ticker,
        "attempt": attempt,
        "run_date": run_date,
        "status": status,
        "recorded_at_utc": retrieved_at_utc,
    })

    return artifact_path

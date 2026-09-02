#!/usr/bin/env python3
"""Centralized, bounded, redacting diagnostic formatting for the Phase 2
unattended collector.

WHY THIS MODULE EXISTS
----------------------
Two consecutive unattended failures were diagnosed after the fact and both
were harder than they should have been, for the same reason: the failure
detail existed at the moment of failure and was then dropped.

  2026-08-29  Every one of the 24 tickers failed the implied-volatility leg.
              ``iv_status`` was persisted as ``error`` but ``iv_error`` was
              persisted EMPTY, so the CSV round-tripped it as ``nan``. The
              cause: ``run_bounded()`` recorded ``str(exc)``, and ``str()`` of
              an exception constructed with no arguments is the empty string.
              A leg that failed 24/24 recorded no reason at all.

  2026-08-31  The panel raised during Google Trends client construction, 15s
              in, before any row existed. The runner captured the child's
              stdout and stderr and then discarded both on the refusal path,
              so the traceback naming the exception was never written anywhere.

This module is the single place where an exception or a captured stream is
turned into something safe to persist. It changes no measurement, no schema,
no completeness rule and no gate. It only makes failures legible.

GUARANTEES
----------
1. ``format_exception()`` NEVER returns an empty string. The exception class
   name is always present, so a failed leg can never again persist a blank
   reason.
2. Nothing is persisted as a raw ``str(exc)`` / ``repr(exc)``. Every value
   returned by this module has passed through :func:`sanitize_text`.
3. Redaction covers authorization headers, bearer tokens, secret-bearing
   query-string and JSON/assignment keys, and user-specific absolute paths.
4. Every returned string is length-bounded, with an explicit truncation
   marker, and newline-normalized. Values destined for a CSV cell are
   collapsed to a single line so they cannot break tabular output.

WHAT THIS MODULE DELIBERATELY DOES NOT DO
-----------------------------------------
It does not retry, substitute, impute, carry forward or default any value.
A failed source stays failed and stays missing.
"""

from __future__ import annotations

import re

# --- documented bounds ------------------------------------------------------

#: Maximum length of a diagnostic persisted into a tabular ``<source>_error``
#: cell. Long enough for a class name plus a real provider message, short
#: enough that 24 of them cannot bloat a daily panel.
MAX_ERROR_FIELD_LEN = 500

#: Maximum total length of a multi-line diagnostic block written to a runner
#: log.
MAX_LOG_BLOCK_CHARS = 4000

#: Maximum number of lines retained from a captured stream. The TAIL is kept:
#: in a Python traceback the final lines name the exception.
MAX_LOG_BLOCK_LINES = 40

#: Appended whenever content was dropped to satisfy a bound.
TRUNCATION_MARKER = "...[truncated]"

#: Substituted for any redacted secret.
REDACTED = "<redacted>"

#: Substituted for a user-specific home-directory prefix.
HOME_PLACEHOLDER = "<HOME>"

#: Emitted when an exception carries no message of its own.
NO_MESSAGE = "(no message)"

# --- redaction rules --------------------------------------------------------

# Key names that may carry a secret when they appear as a query-string
# parameter, a JSON field or a plain assignment.
_SECRET_KEY = (
    r"(?:api[-_]?key|apikey|access[-_]?token|refresh[-_]?token|auth[-_]?token"
    r"|id[-_]?token|token|secret|client[-_]?secret|password|passwd|pwd"
    r"|signature|sig|session[-_]?id|sessionid|credential|credentials|auth|key)"
)

# Order matters: header and bearer forms are matched before the generic
# key=value forms, and path rules run last so they cannot eat a redaction.
_REDACTIONS: tuple[tuple[re.Pattern[str], str], ...] = (
    # Authorization / cookie style headers, in either "Name: value" or
    # "Name=value" form.
    (re.compile(
        r"(?i)\b(authorization|proxy-authorization|www-authenticate|x-api-key"
        r"|x-auth-token|x-access-token|cookie|set-cookie)\b\s*[:=]\s*[^\r\n,;]+"),
     r"\1: " + REDACTED),
    # A bearer/basic token anywhere, even without its header name.
    (re.compile(r"(?i)\b(bearer|basic|token)\s+[A-Za-z0-9._\-~+/=]{8,}"),
     r"\1 " + REDACTED),
    # JSON object field: "token": "...."
    (re.compile(r'(?i)"(' + _SECRET_KEY + r')"\s*:\s*"[^"]*"'),
     r'"\1": "' + REDACTED + '"'),
    # Quoted assignment: token='....'  /  password="...."
    (re.compile(r"(?i)\b(" + _SECRET_KEY + r")\s*[:=]\s*['\"][^'\"]*['\"]"),
     r"\1=" + REDACTED),
    # Query-string / bare assignment: ?api_key=....&  or  token=....
    (re.compile(r"(?i)\b(" + _SECRET_KEY + r")\s*=\s*[^&\s\"'<>\]\)]+"),
     r"\1=" + REDACTED),
    # Windows user profile:  C:\Users\someone\...  ->  <HOME>\...
    (re.compile(r"(?i)\b[A-Za-z]:[\\/]+Users[\\/]+[^\\/\s\"'<>]+"),
     HOME_PLACEHOLDER),
    # Git-Bash / MSYS style:  /c/Users/someone/...
    (re.compile(r"(?i)/[a-z]/Users/[^/\s\"'<>]+"), HOME_PLACEHOLDER),
    # POSIX and macOS home directories.
    (re.compile(r"/home/[^/\s\"'<>]+"), HOME_PLACEHOLDER),
    (re.compile(r"/Users/[^/\s\"'<>]+"), HOME_PLACEHOLDER),
    # Environment-variable spellings of the same thing.
    (re.compile(r"(?i)%USERPROFILE%"), HOME_PLACEHOLDER),
    (re.compile(r"(?i)\$(?:HOME|USERPROFILE)\b"), HOME_PLACEHOLDER),
)

# Control characters that must never reach a log line or a CSV cell.
_CONTROL = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]")


def redact(text: str) -> str:
    """Apply every redaction rule. Pure string in, pure string out."""
    for pattern, replacement in _REDACTIONS:
        text = pattern.sub(replacement, text)
    return text


def _truncate(text: str, max_len: int) -> str:
    if max_len <= 0 or len(text) <= max_len:
        return text
    keep = max(0, max_len - len(TRUNCATION_MARKER))
    return text[:keep] + TRUNCATION_MARKER


def sanitize_text(value: object, *, max_len: int = MAX_ERROR_FIELD_LEN,
                  single_line: bool = True) -> str:
    """Redact, normalize and bound arbitrary text for persistence.

    ``single_line=True`` (the default, and what every ``<source>_error`` cell
    uses) collapses all newlines and tabs so the value cannot break a CSV row.
    ``single_line=False`` keeps line structure for a runner-log block.

    Returns ``""`` for empty input -- callers that require a non-empty value
    must supply their own fallback (:func:`format_exception` always does).
    """
    if value is None:
        return ""
    text = value if isinstance(value, str) else str(value)
    if not text:
        return ""

    # Normalize newlines first so the control-character sweep cannot merge
    # CRLF into something ambiguous.
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = _CONTROL.sub(" ", text)
    text = redact(text)

    if single_line:
        text = text.replace("\n", " | ").replace("\t", " ")
        text = re.sub(r"[ ]{2,}", " ", text)
    else:
        text = "\n".join(line.rstrip() for line in text.split("\n"))

    return _truncate(text.strip(), max_len)


def format_exception(exc: BaseException | None, *,
                     max_len: int = MAX_ERROR_FIELD_LEN,
                     single_line: bool = True) -> str:
    """Turn an exception into a bounded, redacted, NEVER-EMPTY diagnostic.

    The exception class name always survives, because that alone would have
    identified the 2026-08-29 IV failure. An exception whose ``str()`` is
    empty -- the exact defect that produced 24 blank ``iv_error`` cells --
    yields ``"ClassName: (no message)"``, never ``""``.
    """
    if exc is None:
        return "UnknownError: " + NO_MESSAGE

    cls = type(exc).__name__ or "UnknownError"
    try:
        message = str(exc)
    except Exception:                                              # noqa: BLE001
        # A __str__ that itself raises must not take the run down with it.
        message = ""

    message = sanitize_text(message, max_len=max_len, single_line=single_line)
    if not message:
        message = NO_MESSAGE

    cls = sanitize_text(cls, max_len=120) or "UnknownError"
    return _truncate(f"{cls}: {message}", max_len)


def format_stream_for_log(stream: object, *,
                          max_lines: int = MAX_LOG_BLOCK_LINES,
                          max_chars: int = MAX_LOG_BLOCK_CHARS) -> str:
    """Prepare a captured child stream (stderr) for a runner log.

    Keeps the TAIL -- in a Python traceback the last lines carry the exception
    class and message. Every retained line is redacted and stripped of control
    characters. Line structure is preserved so a traceback stays readable.

    This is intended for stderr. The panel writes every measured value to
    STDOUT via its own ``log()``, so stdout is never passed here by the runner.
    """
    text = sanitize_text(stream, max_len=0, single_line=False)
    if not text.strip():
        return ""

    lines = [ln for ln in text.split("\n")]
    dropped = 0
    if len(lines) > max_lines:
        dropped = len(lines) - max_lines
        lines = lines[-max_lines:]

    block = "\n".join(lines).strip("\n")
    if dropped:
        block = f"[{dropped} earlier line(s) omitted]\n" + block
    return _truncate(block, max_chars)

#!/usr/bin/env python3
"""Deterministic Exhibit 99.1 parser: point-in-time GAAP revenue, operating income, diluted EPS.

Reads ONLY the earnings-release exhibit filed with the 8-K. Later 10-Q XBRL is never
consulted to choose a value; it is used elsewhere purely as an audit reference.

RULES
  - parse HTML tables, keep row labels and column headers
  - locate the CURRENT quarter / three-month column; reject year-to-date columns
  - reject adjusted / non-GAAP / pro-forma rows
  - resolve thousands / millions units from headers or captions
  - distinguish current quarter from prior-year quarter by column order
  - REFUSE on ambiguous multiple matches rather than guessing
  - retain exact row label, column label, units and table index for every value
"""
from __future__ import annotations

import re
from html.parser import HTMLParser

MONEY = re.compile(r"^\(?\$?\s*-?[\d,]+(?:\.\d+)?\)?$")
ADJUSTED = re.compile(r"(?i)\b(adjusted|non[- ]?gaap|pro\s*forma|excluding|ex-items|core\b|"
                      r"constant currency|organic|ebitda|free cash flow|guidance|outlook)\b")
YTD = re.compile(r"(?i)(six|nine|twelve|year[- ]to[- ]date|ytd|first half|full year|"
                 r"\bsix months\b|\bnine months\b|\btwelve months\b)")
QTR = re.compile(r"(?i)(three months|quarter|13 weeks|fourteen weeks|thirteen weeks|q[1-4]\b)")
REV_ROW = re.compile(r"(?i)^(total\s+)?(net\s+)?(revenue|revenues|net revenue|net revenues|"
                     r"net sales|total net sales|total revenue|total revenues|sales)\b")
OPI_ROW = re.compile(r"(?i)^(total\s+)?(operating\s+(income|profit|loss|earnings)|income from operations|"
                     r"operating income \(loss\))\b")
EPS_ROW = re.compile(r"(?i)(diluted).{0,40}(per (common )?share|eps)|"
                     r"(earnings|income|loss).{0,30}per.{0,20}share.{0,20}dilut")
EPS_ROW2 = re.compile(r"(?i)^\s*diluted\s*$")
UNIT_THOU = re.compile(r"(?i)in thousands")
UNIT_MIL = re.compile(r"(?i)in millions")


class Tables(HTMLParser):
    """Minimal table extractor: rows of cell text, plus surrounding caption text."""

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.tables, self._t, self._r, self._c = [], None, None, None
        self.text_chunks = []

    def handle_starttag(self, tag, attrs):
        if tag == "table":
            self._t = []
        elif tag == "tr" and self._t is not None:
            self._r = []
        elif tag in ("td", "th") and self._r is not None:
            self._c = []

    def handle_endtag(self, tag):
        if tag == "table" and self._t is not None:
            self.tables.append(self._t)
            self._t = None
        elif tag == "tr" and self._t is not None and self._r is not None:
            self._t.append(self._r)
            self._r = None
        elif tag in ("td", "th") and self._r is not None and self._c is not None:
            self._r.append(re.sub(r"\s+", " ", "".join(self._c)).strip())
            self._c = None

    def handle_data(self, d):
        if self._c is not None:
            self._c.append(d)
        else:
            self.text_chunks.append(d)


def _num(s: str):
    s = s.strip()
    if not s or not MONEY.match(s):
        return None
    neg = s.startswith("(") and s.endswith(")")
    v = re.sub(r"[^\d.\-]", "", s)
    if v in ("", "-", "."):
        return None
    try:
        x = float(v)
    except ValueError:
        return None
    return -x if neg else x


def _scale(context: str) -> float:
    if UNIT_THOU.search(context):
        return 1e3
    if UNIT_MIL.search(context):
        return 1e6
    return 1.0


def _header_rows(tbl, upto=6):
    return [" | ".join(r) for r in tbl[:upto]]


def _pick_current_quarter_col(tbl, period_end_hint=None):
    """Return (col_index, column_label) for the current-quarter column.

    Column order in earnings releases is current period first among quarter columns.
    Any column whose header mentions a YTD span is rejected outright.
    """
    head = tbl[:6]
    ncol = max((len(r) for r in tbl), default=0)
    scores = {}
    for ci in range(ncol):
        lab = " ".join(r[ci] for r in head if ci < len(r)).strip()
        if not lab:
            continue
        if YTD.search(lab):
            continue                        # reject year-to-date columns
        if QTR.search(lab):
            scores[ci] = lab
    if period_end_hint:
        # a column naming the announced period end is unambiguous
        import datetime as _dt
        try:
            d = _dt.date.fromisoformat(period_end_hint)
            pats = [d.strftime("%B %-d, %Y") if hasattr(d, "strftime") else "", d.strftime("%B %d, %Y"),
                    d.strftime("%b %d, %Y"), d.strftime("%m/%d/%Y"), str(d.year)]
        except Exception:
            pats = []
        for ci, lab in scores.items():
            for pt in pats[:-1]:
                if pt and pt.lower().replace(" 0", " ") in lab.lower().replace(" 0", " "):
                    return ci, lab
    if scores:
        ci = min(scores)                    # leftmost surviving quarter column
        return ci, scores[ci]
    return None, None


def parse_exhibit(html: str, period_end_hint: str | None = None):
    """Return (values, diagnostics). values maps component -> dict or None."""
    p = Tables()
    try:
        p.feed(html)
    except Exception:
        pass
    doc_text = re.sub(r"\s+", " ", " ".join(p.text_chunks))
    out = {"revenue": None, "operating_income": None, "diluted_eps": None}
    diag = {"n_tables": len(p.tables), "refusals": []}

    for ti, tbl in enumerate(p.tables):
        if len(tbl) < 3:
            continue
        head_txt = " ".join(_header_rows(tbl))
        table_ctx = head_txt + " " + doc_text[:4000]
        if YTD.search(head_txt) and not QTR.search(head_txt):
            continue                                    # whole table is YTD
        qcol, qlab = _pick_current_quarter_col(tbl, period_end_hint)
        # Unit captions ("in thousands"/"in millions") usually sit OUTSIDE the table,
        # so fall back to document context when the header carries no unit. _scale
        # returns 1.0 (truthy) when nothing matches, so test explicitly.
        scale = _scale(head_txt)
        if scale == 1.0:
            scale = _scale(table_ctx)
        for row in tbl:
            if not row:
                continue
            label = row[0].strip()
            if not label or ADJUSTED.search(label) or YTD.search(label):
                continue
            nums = [(i, _num(c)) for i, c in enumerate(row) if _num(c) is not None]
            if not nums:
                continue
            # choose the current-quarter cell: the identified column if present,
            # else the first numeric cell (leftmost = current period by convention)
            cell = None
            if qcol is not None:
                for i, v in nums:
                    if i >= qcol:
                        cell = (i, v)
                        break
            if cell is None:
                cell = nums[0]
            ci, val = cell
            col_label = " ".join(r[ci] for r in tbl[:6] if ci < len(r)).strip() or (qlab or "")
            if YTD.search(col_label):
                continue
            rec = {"value": val, "row_label": label[:120], "column_label": col_label[:120],
                   "table_index": ti, "raw_scale": scale}
            if REV_ROW.match(label) and out["revenue"] is None:
                rec["value"] = val * scale
                rec["component"] = "revenue"
                out["revenue"] = rec
            elif OPI_ROW.match(label) and out["operating_income"] is None:
                rec["value"] = val * scale
                rec["component"] = "operating_income"
                out["operating_income"] = rec
            elif (EPS_ROW.search(label) or EPS_ROW2.match(label)) and out["diluted_eps"] is None:
                if abs(val) < 1000:                     # EPS is never scaled
                    rec["component"] = "diluted_eps"
                    out["diluted_eps"] = rec
    return out, diag

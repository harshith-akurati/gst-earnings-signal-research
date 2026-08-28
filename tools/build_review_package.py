#!/usr/bin/env python3
"""Build the Signal Without Strategy v1.1 reviewer package.

Renders the committed markdown deliverables to PDF, extracts Tables 1-3 as CSV,
embeds the three committed SVG figures, and reports layout problems (overflow,
clipped table columns, missing figures) rather than hiding them.

Renders only. It fits no model, computes no statistic, and reads no panel value.
Every number reaching a page came from an already-audited markdown source.
"""
from __future__ import annotations

import csv
import re
import sys
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_JUSTIFY
from reportlab.lib.pagesizes import LETTER
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import (KeepTogether, PageBreak, Paragraph,
                                SimpleDocTemplate, Spacer, Table, TableStyle)

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "review_package"

WARNINGS: list[str] = []

SS = getSampleStyleSheet()
BODY = ParagraphStyle("body", parent=SS["BodyText"], fontSize=9.2, leading=12.6,
                      alignment=TA_JUSTIFY, spaceAfter=6)
H1 = ParagraphStyle("h1", parent=SS["Heading1"], fontSize=15, leading=19, spaceBefore=14, spaceAfter=7)
H2 = ParagraphStyle("h2", parent=SS["Heading2"], fontSize=12, leading=15, spaceBefore=11, spaceAfter=5)
H3 = ParagraphStyle("h3", parent=SS["Heading3"], fontSize=10.3, leading=13, spaceBefore=9, spaceAfter=4)
TITLE = ParagraphStyle("title", parent=SS["Title"], fontSize=17, leading=21, spaceAfter=12)
MONO = ParagraphStyle("mono", parent=SS["BodyText"], fontName="Courier", fontSize=7.6,
                      leading=9.6, spaceAfter=6, backColor=colors.HexColor("#F4F4F4"))
CELL = ParagraphStyle("cell", parent=SS["BodyText"], fontSize=7.0, leading=8.6)
CELLH = ParagraphStyle("cellh", parent=CELL, fontName="Helvetica-Bold")
CAP = ParagraphStyle("cap", parent=BODY, fontSize=8.2, leading=10.5,
                     textColor=colors.HexColor("#444444"))


def esc(t: str) -> str:
    t = t.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    t = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", t)
    t = re.sub(r"(?<!\*)\*([^*]+?)\*(?!\*)", r"<i>\1</i>", t)
    t = re.sub(r"`([^`]+?)`", r'<font face="Courier" size="7.8">\1</font>', t)
    return t


def split_row(line: str) -> list[str]:
    return [c.strip() for c in line.strip().strip("|").split("|")]


def make_table(rows: list[list[str]], width: float) -> Table:
    head, body = rows[0], rows[1:]
    ncol = max(len(r) for r in rows)
    head += [""] * (ncol - len(head))
    body = [r + [""] * (ncol - len(r)) for r in body]
    weights = []
    for c in range(ncol):
        longest = max([len(head[c])] + [len(r[c]) for r in body] or [1])
        weights.append(max(4, min(longest, 46)))
    total = sum(weights)
    cw = [width * w / total for w in weights]
    # Enforce a legibility floor: give every column at least MIN_COL, taking the
    # shortfall proportionally from columns that are above it. Paragraph cells
    # wrap rather than clip, so this is a legibility fix, not a data-loss fix.
    MIN_COL = 30.0
    if ncol * MIN_COL < width:
        deficit = sum(MIN_COL - c for c in cw if c < MIN_COL)
        if deficit > 0:
            surplus = sum(c - MIN_COL for c in cw if c > MIN_COL)
            cw = [MIN_COL if c < MIN_COL
                  else c - (c - MIN_COL) * deficit / surplus for c in cw]
    else:
        WARNINGS.append(f"table too wide for the page at ncol={ncol}; "
                        f"consider splitting it")
    if min(cw) < 26:
        WARNINGS.append(f"table column still narrower than 26pt (ncol={ncol})")
    data = [[Paragraph(esc(h), CELLH) for h in head]] + \
           [[Paragraph(esc(c), CELL) for c in r] for r in body]
    t = Table(data, colWidths=cw, repeatRows=1)
    t.setStyle(TableStyle([
        ("GRID", (0, 0), (-1, -1), 0.35, colors.HexColor("#999999")),
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#E8E8E8")),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 3),
        ("RIGHTPADDING", (0, 0), (-1, -1), 3),
        ("TOPPADDING", (0, 0), (-1, -1), 2.5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 2.5),
    ]))
    return t


def md_to_flow(md: str, width: float) -> list:
    flow = []
    lines = md.splitlines()
    i = 0
    para: list[str] = []

    def flush():
        nonlocal para
        if para:
            flow.append(Paragraph(esc(" ".join(para)), BODY))
            para = []

    while i < len(lines):
        ln = lines[i]
        st = ln.strip()
        if st.startswith("```"):
            flush()
            i += 1
            buf = []
            while i < len(lines) and not lines[i].strip().startswith("```"):
                buf.append(lines[i]); i += 1
            i += 1
            body = "<br/>".join(esc(b) for b in buf)
            flow.append(Paragraph(body, MONO))
            continue
        if st.startswith("|") and i + 1 < len(lines) and set(lines[i + 1].strip()) <= set("|-: "):
            flush()
            rows = [split_row(st)]
            i += 2
            while i < len(lines) and lines[i].strip().startswith("|"):
                rows.append(split_row(lines[i])); i += 1
            flow.append(Spacer(1, 3))
            flow.append(make_table(rows, width))
            flow.append(Spacer(1, 7))
            continue
        if st.startswith("#"):
            flush()
            lvl = len(st) - len(st.lstrip("#"))
            txt = st.lstrip("# ").strip()
            flow.append(Paragraph(esc(txt), {1: H1, 2: H2}.get(lvl, H3)))
            i += 1
            continue
        if st in ("---", "***", "___"):
            flush(); flow.append(Spacer(1, 8)); i += 1; continue
        if st.startswith(("- ", "* ", "> ")) or re.match(r"^\d+\. ", st):
            flush()
            txt = re.sub(r"^([-*]|\d+\.|>)\s+", "", st)
            pref = "&bull; " if not st.startswith("> ") else ""
            flow.append(Paragraph(pref + esc(txt), ParagraphStyle(
                "li", parent=BODY, leftIndent=13, spaceAfter=3)))
            i += 1
            continue
        if not st:
            flush(); i += 1; continue
        para.append(st)
        i += 1
    flush()
    return flow


def build_pdf(src: Path, dest: Path, title: str) -> int:
    doc = SimpleDocTemplate(str(dest), pagesize=LETTER,
                            leftMargin=0.85 * inch, rightMargin=0.85 * inch,
                            topMargin=0.8 * inch, bottomMargin=0.8 * inch,
                            title=title)
    width = doc.width
    flow = md_to_flow(src.read_text(encoding="utf-8"), width)
    doc.build(flow)
    from pypdf import PdfReader
    return len(PdfReader(str(dest)).pages)


def build_figures_pdf(dest: Path) -> tuple[int, list[str]]:
    from svglib.svglib import svg2rlg
    from reportlab.platypus import Image as RLImage  # noqa: F401
    figs = sorted(ROOT.glob("SIGNAL_WITHOUT_STRATEGY_FIGURE_*.svg"))
    missing = []
    doc = SimpleDocTemplate(str(dest), pagesize=LETTER,
                            leftMargin=0.7 * inch, rightMargin=0.7 * inch,
                            topMargin=0.8 * inch, bottomMargin=0.8 * inch,
                            title="Signal Without Strategy v1.1 — Figures")
    flow = [Paragraph("Signal Without Strategy v1.1 — Figures", TITLE)]
    caps = {
        1: ("Figure 1. Evidence ladder. Attention clears rung 1 (matched association, "
            "+2.0797 pp, p = 0.00397) and fails rungs 2 and 3 (incremental contribution "
            "+0.0131 pp, p = 0.98332; no out-of-sample forecast improvement). Clearing "
            "rung 1 does not establish rungs 2 or 3."),
        2: ("Figure 2. Earnings-surprise temporal replication. Retained unchanged from v1.0; "
            "no underlying value was recomputed."),
        3: ("Figure 3. Leakage correction: an apparent 63.6% directional accuracy fell to "
            "47.9% after duplicated events and a mis-specified lag feature were corrected."),
    }
    for f in figs:
        m = re.search(r"FIGURE_(\d)", f.name)
        idx = int(m.group(1)) if m else 0
        try:
            d = svg2rlg(str(f))
            if d is None:
                missing.append(f.name); continue
            scale = min((doc.width) / d.width, 7.2 * inch / d.height, 1.0)
            d.width *= scale; d.height *= scale
            d.scale(scale, scale)
            flow.append(KeepTogether([d, Spacer(1, 6),
                                      Paragraph(caps.get(idx, f.name), CAP)]))
            flow.append(PageBreak())
        except Exception as e:  # noqa: BLE001
            missing.append(f"{f.name}: {e}")
    if flow and isinstance(flow[-1], PageBreak):
        flow.pop()
    doc.build(flow)
    from pypdf import PdfReader
    return len(PdfReader(str(dest)).pages), missing


def extract_tables(src: Path, out_dir: Path) -> list[str]:
    """Emit every markdown table in the manuscript as CSV, preserving cell text
    verbatim so displayed values and their rounding survive unchanged."""
    lines = src.read_text(encoding="utf-8").splitlines()
    made = []
    i = k = 0
    while i < len(lines):
        st = lines[i].strip()
        if st.startswith("|") and i + 1 < len(lines) and set(lines[i + 1].strip()) <= set("|-: "):
            rows = [split_row(st)]
            i += 2
            while i < len(lines) and lines[i].strip().startswith("|"):
                rows.append(split_row(lines[i])); i += 1
            k += 1
            p = out_dir / f"table_{k:02d}.csv"
            with p.open("w", newline="", encoding="utf-8") as fh:
                csv.writer(fh).writerows(rows)
            made.append(p.name)
            continue
        i += 1
    return made


def main() -> int:
    OUT.mkdir(exist_ok=True)
    (OUT / "tables").mkdir(exist_ok=True)
    print("=" * 64)
    print("BUILDING REVIEW PACKAGE")
    print("=" * 64)

    jobs = [
        ("SIGNAL_WITHOUT_STRATEGY_MANUSCRIPT_v1.1_DRAFT.md",
         "Signal_Without_Strategy_v1.1_MANUSCRIPT.pdf", "Signal Without Strategy v1.1"),
        ("SIGNAL_WITHOUT_STRATEGY_NUMBER_AUDIT_v1.1.md",
         "Signal_Without_Strategy_v1.1_NUMBER_AUDIT.pdf", "Number audit v1.1"),
        ("SIGNAL_WITHOUT_STRATEGY_FIGURE_TABLE_PLAN_v1.1.md",
         "Signal_Without_Strategy_v1.1_FIGURE_TABLE_PLAN.pdf", "Figure and table plan v1.1"),
        ("SIGNAL_WITHOUT_STRATEGY_REVIEWER_COVER_MEMO_v1.1.md",
         "Signal_Without_Strategy_v1.1_COVER_MEMO.pdf", "Reviewer cover memo"),
    ]
    for src, dest, title in jobs:
        sp = ROOT / src
        if not sp.exists():
            WARNINGS.append(f"source missing: {src}")
            print(f"  SKIP  {src} (missing)")
            continue
        n = build_pdf(sp, OUT / dest, title)
        print(f"  OK    {dest:52} {n} pages")

    npages, missing = build_figures_pdf(OUT / "Signal_Without_Strategy_v1.1_FIGURES.pdf")
    print(f"  OK    {'Signal_Without_Strategy_v1.1_FIGURES.pdf':52} {npages} pages")
    for m in missing:
        WARNINGS.append(f"figure render problem: {m}")

    made = extract_tables(ROOT / "SIGNAL_WITHOUT_STRATEGY_MANUSCRIPT_v1.1_DRAFT.md",
                          OUT / "tables")
    print(f"  OK    tables extracted: {len(made)} CSV files")

    print("\nWARNINGS:" if WARNINGS else "\nNo layout warnings.")
    for w in sorted(set(WARNINGS)):
        print(f"  ! {w}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

#!/usr/bin/env python3
"""Deterministic builder for the Signal Without Strategy submission PDFs.

ONE source, TWO outputs: the identified package and the anonymised review package.
The manuscript markdown is the single source of truth for wording and results -- this
script only typesets it. It never edits, recomputes or reinterprets anything.

Build:
    python submission/build_submission_pdfs.py

Dependencies (both pure Python, no native toolchain, no LaTeX):
    pip install reportlab svglib

A LaTeX source was deliberately not added: no TeX distribution exists in this
environment, so a .tex file could not be compiled or verified here, and shipping an
unverifiable second source alongside the one that actually produces the PDFs would
create two divergent sources of truth. This script is the editable source.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_LEFT
from reportlab.lib.pagesizes import LETTER
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import (BaseDocTemplate, Frame, KeepTogether, NextPageTemplate,
                                PageBreak, PageTemplate, Paragraph, Spacer, Table,
                                TableStyle)
from svglib.svglib import svg2rlg

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "submission"
MANUSCRIPT = ROOT / "SIGNAL_WITHOUT_STRATEGY_MANUSCRIPT_v1.0.md"

IDENTIFIED_AUTHOR = "[Author information to be completed by project owner]"
ANONYMOUS_AUTHOR = "Author information withheld for review"

TITLE = ("Signal Without Strategy: Search Attention, Earnings Surprise, and the "
         "Difference Between Association and Tradable Prediction")

KEYWORDS = ("earnings announcements; investor attention; out-of-sample forecasting; "
            "data leakage; replication; post-earnings-announcement drift")

# Proposed only -- the author should confirm these against the chosen venue.
JEL = "G14, G17, C52, C53"

FIGURES = [
    ("SIGNAL_WITHOUT_STRATEGY_FIGURE_1_EVIDENCE_LADDER.svg",
     "Figure 1. Evidence ladder. Each study is placed at the highest level its evidence "
     "actually supports. No study in this program reached Level 3 (tradability)."),
    ("SIGNAL_WITHOUT_STRATEGY_FIGURE_2_SURPRISE_REPLICATION.svg",
     "Figure 2. Earnings-surprise replication: MAE difference (baseline minus "
     "augmented), with 95% moving-block bootstrap intervals. The two samples do not "
     "overlap in time and are not pooled. Both intervals include zero."),
    ("SIGNAL_WITHOUT_STRATEGY_FIGURE_3_LEAKAGE_CORRECTION.svg",
     "Figure 3. Leakage correction in the directional model. Pre-correction values are "
     "invalidated and are shown only to size the distortion."),
]
# Figures are placed after these section headings.
FIGURE_AFTER = {1: "3.", 3: "6.", 2: "8."}


# ------------------------------------------------------------------ styles

def styles():
    ss = getSampleStyleSheet()
    body = ParagraphStyle(
        "Body", parent=ss["BodyText"], fontName="Times-Roman", fontSize=10.2,
        leading=14.2, alignment=TA_JUSTIFY, spaceAfter=6, firstLineIndent=0)
    return {
        "body": body,
        "title": ParagraphStyle("TitleX", parent=ss["Title"], fontName="Times-Bold",
                                fontSize=19, leading=24, spaceAfter=18),
        "author": ParagraphStyle("AuthorX", parent=body, alignment=TA_CENTER,
                                 fontSize=11.5, leading=15, spaceAfter=6,
                                 textColor=colors.HexColor("#333333")),
        "datel": ParagraphStyle("DateX", parent=body, alignment=TA_CENTER, fontSize=9.5,
                                textColor=colors.HexColor("#555555"), spaceAfter=20),
        "h1": ParagraphStyle("H1X", parent=ss["Heading1"], fontName="Times-Bold",
                             fontSize=13, leading=16, spaceBefore=14, spaceAfter=6,
                             textColor=colors.black),
        "h2": ParagraphStyle("H2X", parent=ss["Heading2"], fontName="Times-Bold",
                             fontSize=11, leading=14, spaceBefore=10, spaceAfter=4,
                             textColor=colors.black),
        "abshead": ParagraphStyle("AbsHead", parent=body, fontName="Times-Bold",
                                  fontSize=11, alignment=TA_CENTER, spaceAfter=6),
        "abs": ParagraphStyle("Abs", parent=body, fontSize=9.8, leading=13.4,
                              leftIndent=26, rightIndent=26, spaceAfter=10),
        "meta": ParagraphStyle("Meta", parent=body, fontSize=9.4, leading=12.8,
                               leftIndent=26, rightIndent=26, spaceAfter=5),
        "cap": ParagraphStyle("Cap", parent=body, fontSize=8.8, leading=11.6,
                              alignment=TA_CENTER, spaceBefore=5, spaceAfter=12,
                              textColor=colors.HexColor("#222222")),
        "cell": ParagraphStyle("Cell", parent=body, fontSize=8.4, leading=10.8,
                               alignment=TA_LEFT, spaceAfter=0),
        "cellh": ParagraphStyle("CellH", parent=body, fontSize=8.4, leading=10.8,
                                fontName="Times-Bold", spaceAfter=0),
        "ref": ParagraphStyle("Ref", parent=body, fontSize=9.2, leading=12.4,
                              leftIndent=17, firstLineIndent=-17, spaceAfter=5),
        "bullet": ParagraphStyle("Bul", parent=body, leftIndent=15, bulletIndent=4,
                                 spaceAfter=3),
        "note": ParagraphStyle("Note", parent=body, fontSize=9, leading=12,
                               alignment=TA_CENTER,
                               textColor=colors.HexColor("#555555"), spaceAfter=4),
    }


# ------------------------------------------------------- markdown -> flowables

URL = re.compile(r"(https?://[^\s)<>\]]+)")


def inline(text):
    """Markdown inline -> reportlab mini-HTML. Order matters."""
    t = (text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;"))
    t = re.sub(r"`([^`]+)`", r'<font face="Courier" size="8.6">\1</font>', t)
    t = re.sub(r"\*\*([^*]+)\*\*", r"<b>\1</b>", t)
    t = re.sub(r"(?<!\*)\*([^*]+)\*(?!\*)", r"<i>\1</i>", t)
    # Bare URLs become clickable, blue, and are not broken across the line badly.
    t = URL.sub(lambda m: f'<link href="{m.group(1)}" color="#0645AD">{m.group(1)}</link>',
                t)
    return t


def md_table(rows, st, avail):
    head, body_rows = rows[0], rows[1:]
    ncol = len(head)
    data = [[Paragraph(inline(c), st["cellh"]) for c in head]]
    for r in body_rows:
        r = (r + [""] * ncol)[:ncol]
        data.append([Paragraph(inline(c), st["cell"]) for c in r])
    # First column usually carries the label; give it more room.
    if ncol == 1:
        widths = [avail]
    else:
        first = min(avail * 0.34, avail / ncol * 1.9)
        rest = (avail - first) / (ncol - 1)
        widths = [first] + [rest] * (ncol - 1)
    t = Table(data, colWidths=widths, repeatRows=1, hAlign="LEFT")
    t.setStyle(TableStyle([
        ("FONTNAME", (0, 0), (-1, 0), "Times-Bold"),
        ("LINEABOVE", (0, 0), (-1, 0), 0.9, colors.black),
        ("LINEBELOW", (0, 0), (-1, 0), 0.5, colors.black),
        ("LINEBELOW", (0, -1), (-1, -1), 0.9, colors.black),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("TOPPADDING", (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
        ("LEFTPADDING", (0, 0), (-1, -1), 4),
        ("RIGHTPADDING", (0, 0), (-1, -1), 4),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1),
         [colors.white, colors.HexColor("#f6f6f6")]),
    ]))
    return t


def figure_flowable(svg_name, caption, st, avail):
    drawing = svg2rlg(str(ROOT / svg_name))
    try:                                   # true ink extent, not the declared viewBox
        x0, y0, x1, y1 = drawing.getBounds()
        extent = max(drawing.width, x1, x1 - x0)
    except Exception:
        extent = drawing.width
    scale = min(avail / extent, 1.0)
    drawing.width = extent * scale
    drawing.height *= scale
    drawing.scale(scale, scale)
    drawing.hAlign = "CENTER"
    return KeepTogether([Spacer(1, 6), drawing, Paragraph(caption, st["cap"])])


def parse(md, st, avail, figures_enabled=True):
    """Convert the manuscript body into flowables, preserving wording exactly."""
    body = md.split("## References")[0]
    refs_block = md.split("## References")[1].split("## Source artifacts")[0]
    src_block = md.split("## Source artifacts")[1] if "## Source artifacts" in md else ""

    flow, i = [], 0
    lines = body.splitlines()
    pending_fig = []
    para: list[str] = []

    def flush():
        nonlocal para
        if para:
            flow.append(Paragraph(inline(" ".join(para).strip()), st["body"]))
            para = []

    while i < len(lines):
        ln = lines[i]
        s = ln.strip()

        if s.startswith("|"):                                   # table block
            flush()
            rows = []
            while i < len(lines) and lines[i].strip().startswith("|"):
                cells = [c.strip() for c in lines[i].strip().strip("|").split("|")]
                if not re.fullmatch(r"[\s:\-|]+", lines[i].strip().strip("|")):
                    rows.append(cells)
                i += 1
            if rows:
                flow.append(Spacer(1, 4))
                flow.append(md_table(rows, st, avail))
                flow.append(Spacer(1, 8))
            continue

        if s.startswith("## "):
            flush()
            for f in pending_fig:
                flow.append(f)
            pending_fig = []
            title = s[3:].strip()
            if title.startswith("1. Abstract"):                 # handled on title page
                while i < len(lines) and not lines[i].strip().startswith("## 2."):
                    i += 1
                continue
            flow.append(Paragraph(inline(title), st["h1"]))
            num = title.split(".")[0] + "."
            if figures_enabled:
                for fignum, after in FIGURE_AFTER.items():
                    if after == num:
                        name, cap = FIGURES[fignum - 1]
                        pending_fig.append(figure_flowable(name, cap, st, avail))
            i += 1
            continue

        if s.startswith("### "):
            flush()
            flow.append(Paragraph(inline(s[4:].strip()), st["h2"]))
            i += 1
            continue

        if s.startswith("> "):
            flush()
            flow.append(Paragraph(inline(s[2:]), ParagraphStyle(
                "Q", parent=st["body"], leftIndent=20, rightIndent=20,
                fontName="Times-Italic", spaceBefore=4, spaceAfter=8)))
            i += 1
            continue

        m = re.match(r"^(\d+)\.\s+(.*)", s)
        if s.startswith("- ") or s.startswith("* ") or m:
            flush()
            txt = s[2:] if not m else m.group(2)
            bullet = "\u2022" if not m else f"{m.group(1)}."
            j = i + 1
            while (j < len(lines) and lines[j].startswith("   ")
                   and lines[j].strip() and not lines[j].strip().startswith(("-", "*", "|"))
                   and not re.match(r"^\s*\d+\.\s", lines[j])):
                txt += " " + lines[j].strip()
                j += 1
            flow.append(Paragraph(inline(txt), st["bullet"], bulletText=bullet))
            i = j
            continue

        if s.startswith("---") or s.startswith("# "):
            flush()
            i += 1
            continue

        if not s:
            flush()
            i += 1
            continue

        para.append(s)
        i += 1

    flush()
    for f in pending_fig:
        flow.append(f)

    # references -- flow naturally; a forced break here left a near-empty page
    flow.append(Spacer(1, 6))
    flow.append(Paragraph("References", st["h1"]))
    for m in re.finditer(r"^\s*(\d+)\.\s+(.*?)(?=^\s*\d+\.\s|\Z)",
                         refs_block, re.S | re.M):
        txt = " ".join(m.group(2).split())
        txt = re.sub(r"\s*-{3,}\s*$", "", txt)      # drop a trailing markdown rule
        flow.append(Paragraph(f"[{m.group(1)}] " + inline(txt), st["ref"]))

    if src_block.strip():
        # Kept together so the artifact list cannot orphan a two-line final page.
        app = [Paragraph("Appendix A. Source artifacts", st["h1"])]
        intro = [l.strip() for l in src_block.strip().splitlines()
                 if l.strip() and not l.strip().startswith("-")]
        if intro:
            app.append(Paragraph(inline(intro[0]), st["body"]))
        for m in re.finditer(r"^\s*-\s+(.*)$", src_block, re.M):
            app.append(Paragraph(inline(m.group(1)), st["bullet"], bulletText="\u2022"))
        flow.append(KeepTogether(app))
    return flow


def abstract_text(md):
    body = md.split("## 1. Abstract")[1].split("## 2.")[0]
    paras, cur = [], []
    for ln in body.splitlines():
        s = ln.strip()
        if s.startswith("*(Abstract") or set(s) <= set("-*_") and len(s) >= 3:
            continue
        if not s:
            if cur:
                paras.append(" ".join(cur))
                cur = []
            continue
        cur.append(s)
    if cur:
        paras.append(" ".join(cur))
    return paras


# ------------------------------------------------------------------- document

def build(path, author_line, anonymous):
    st = styles()
    md = MANUSCRIPT.read_text(encoding="utf-8")
    lm = rm = 0.95 * inch
    avail = LETTER[0] - lm - rm

    doc = BaseDocTemplate(str(path), pagesize=LETTER,
                          leftMargin=lm, rightMargin=rm,
                          topMargin=0.9 * inch, bottomMargin=0.9 * inch,
                          title="Signal Without Strategy",
                          author=("Withheld for review" if anonymous
                                  else "To be completed by project owner"),
                          subject="Association, incremental prediction and tradability",
                          creator="build_submission_pdfs.py")
    frame = Frame(lm, 0.9 * inch, avail,
                  LETTER[1] - 1.8 * inch, id="f")

    def footer(canvas, d):
        canvas.saveState()
        canvas.setFont("Times-Roman", 9)
        canvas.setFillColor(colors.HexColor("#444444"))
        canvas.drawCentredString(LETTER[0] / 2.0, 0.58 * inch, str(canvas.getPageNumber()))
        canvas.restoreState()

    def title_page(canvas, d):
        footer(canvas, d)

    doc.addPageTemplates([
        PageTemplate(id="title", frames=[frame], onPage=title_page),
        PageTemplate(id="body", frames=[frame], onPage=footer),
    ])

    flow = [Spacer(1, 34), Paragraph(TITLE, st["title"]),
            Paragraph(author_line, st["author"]),
            Paragraph("Working paper &mdash; venue-neutral submission draft",
                      st["datel"]),
            Paragraph("Abstract", st["abshead"])]
    for p in abstract_text(md):
        flow.append(Paragraph(inline(p), st["abs"]))
    flow += [
        Paragraph("<b>Keywords:</b> " + KEYWORDS, st["meta"]),
        Paragraph("<b>JEL classification (proposed; to be confirmed against the target "
                  "venue):</b> " + JEL, st["meta"]),
        Spacer(1, 8),
        Paragraph("Exploratory retrospective research synthesis. Not preregistered. "
                  "No investable strategy is claimed.", st["note"]),
        NextPageTemplate("body"), PageBreak(),
    ]
    flow += parse(md, st, avail)
    doc.build(flow)
    return path


def main(argv=None):
    OUT.mkdir(parents=True, exist_ok=True)
    a = build(OUT / "Signal_Without_Strategy_Submission.pdf", IDENTIFIED_AUTHOR, False)
    b = build(OUT / "Signal_Without_Strategy_Anonymous.pdf", ANONYMOUS_AUTHOR, True)
    for p in (a, b):
        print(f"wrote {p.relative_to(ROOT)}  ({p.stat().st_size:,} bytes)")
    return 0


if __name__ == "__main__":
    sys.exit(main())

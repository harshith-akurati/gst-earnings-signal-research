#!/usr/bin/env python3
"""Build the AARE Student Research upload set.

Reuses the committed review-package rendering pipeline
(`tools/build_review_package.py`) so the blind manuscript is typeset by the
same code that produced the committed v1.1 manuscript PDF. Adds a title page
and strips identifying PDF metadata from the blind file.

Deterministic. No network. Reads only committed manuscript artifacts.
"""
from __future__ import annotations

import hashlib
import io
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(ROOT / "tools"))

from reportlab.lib.pagesizes import LETTER                          # noqa: E402
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet  # noqa: E402
from reportlab.lib.units import inch                                # noqa: E402
from reportlab.platypus import (Paragraph, SimpleDocTemplate,       # noqa: E402
                                Spacer)
from pypdf import PdfReader, PdfWriter                              # noqa: E402

import build_review_package as brp                                  # noqa: E402

TITLE = ("Search Attention Without Strategy: Association, Prediction, "
         "and Tradability Around Earnings Announcements")

AUTHOR = "Harshith Akurati"
SCHOOL = "Marquette High School"
CITY = "Chesterfield, Missouri, USA"
TRACK = "Student Research Track"

# No committed manuscript artifact authorizes a correspondence address, and an
# address in a script User-Agent header is not an authorship field. The
# correspondence line is omitted entirely rather than guessed or left blank.

MANUSCRIPT = ROOT / "SIGNAL_WITHOUT_STRATEGY_MANUSCRIPT_v1.1_DRAFT.md"
ABSTRACT = HERE / "ABSTRACT.txt"


def sha256(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def scrub_metadata(path: Path, title: str) -> None:
    """Rewrite the PDF with neutral, non-identifying metadata."""
    reader = PdfReader(str(path))
    writer = PdfWriter()
    for page in reader.pages:
        writer.add_page(page)
    writer.add_metadata({
        "/Title": title,
        "/Author": "",
        "/Subject": "",
        "/Keywords": "",
        "/Creator": "",
        "/Producer": "",
    })
    buf = io.BytesIO()
    writer.write(buf)
    path.write_bytes(buf.getvalue())


def build_title_page(dest: Path) -> int:
    doc = SimpleDocTemplate(str(dest), pagesize=LETTER,
                            leftMargin=1.1 * inch, rightMargin=1.1 * inch,
                            topMargin=1.4 * inch, bottomMargin=1.1 * inch,
                            title=TITLE, author=AUTHOR)
    ss = getSampleStyleSheet()
    h = ParagraphStyle("t", parent=ss["Title"], fontSize=17, leading=22, spaceAfter=26)
    n = ParagraphStyle("n", parent=ss["Normal"], fontSize=12, leading=17,
                       alignment=1, spaceAfter=7)
    flow = [Paragraph(brp.esc(TITLE), h), Spacer(1, 12)]
    for line in (AUTHOR, SCHOOL, CITY):
        flow.append(Paragraph(brp.esc(line), n))
    flow += [Spacer(1, 20), Paragraph(f"<b>{brp.esc(TRACK)}</b>", n)]
    doc.build(flow)
    return len(PdfReader(str(dest)).pages)


def build_blind_manuscript(dest: Path) -> int:
    """Same renderer as the committed review package, with the submission
    title substituted for the internal v1.1 running title. The manuscript body
    carries no author name, school, email, acknowledgments or local paths, so
    no textual redaction is required; this was verified before rendering."""
    md = MANUSCRIPT.read_text(encoding="utf-8")
    lines = md.split("\n")
    assert lines[0].startswith("# "), "manuscript must open with an H1 title"
    lines[0] = "# " + TITLE
    body = "\n".join(lines)

    for banned in ("Akurati", "Marquette", "Chesterfield", "@gmail",
                   "C:\\Users", "/c/Users", "hakur"):
        if banned.lower() in body.lower():
            raise SystemExit(f"REFUSING TO BUILD: identifier {banned!r} in blind body")

    # Legibility fix, applied to this build only: the shared renderer sizes
    # columns proportionally to content length, which squeezes a short status
    # column so hard that "PRIMARY" and "sensitivity" wrap mid-word. Raise the
    # per-column floor and take the shortfall from the widest columns. The
    # committed review-package renderer is not modified.
    _orig_make_table = brp.make_table

    def _wide_min_make_table(rows, width):
        t = _orig_make_table(rows, width)
        cw = list(t._argW)
        floor = 46.0
        if len(cw) * floor < width:
            deficit = sum(floor - c for c in cw if c < floor)
            surplus = sum(c - floor for c in cw if c > floor)
            if deficit > 0 and surplus > 0:
                cw = [floor if c < floor
                      else c - (c - floor) * deficit / surplus for c in cw]
                t._argW = cw
        return t

    brp.make_table = _wide_min_make_table

    tmp = HERE / "_blind_source.md"
    tmp.write_text(body, encoding="utf-8")
    try:
        doc = SimpleDocTemplate(str(dest), pagesize=LETTER,
                                leftMargin=0.9 * inch, rightMargin=0.9 * inch,
                                topMargin=0.9 * inch, bottomMargin=0.9 * inch,
                                title=TITLE, author="")
        width = LETTER[0] - 1.8 * inch
        doc.build(brp.md_to_flow(body, width))
    finally:
        tmp.unlink(missing_ok=True)
        brp.make_table = _orig_make_table

    # The committed figures are deliberately NOT appended. Two reasons, both
    # checked rather than assumed: the manuscript body makes zero references to
    # Figure 1, 2 or 3, so nothing in the text depends on them; and page 1 of
    # review_package/Signal_Without_Strategy_v1.1_FIGURES.pdf has real
    # right-edge clipping (annotation blocks reach x1 = 612.3 to 614.6 pt on a
    # 612 pt page), which would fail the no-clipping gate. This mirrors the
    # committed manuscript PDF, which is likewise text and tables only.
    return len(PdfReader(str(dest)).pages)


def main() -> int:
    abstract = ABSTRACT.read_text(encoding="utf-8").strip()
    words = len(abstract.split())
    if words > 250:
        raise SystemExit(f"abstract is {words} words, over the 250 limit")

    tp = HERE / "AARE_TITLE_PAGE.pdf"
    bm = HERE / "AARE_BLIND_MANUSCRIPT.pdf"
    n_tp = build_title_page(tp)
    n_bm = build_blind_manuscript(bm)
    scrub_metadata(bm, TITLE)

    (HERE / "AARE_SUBMISSION_TEXT.txt").write_text(
        "SELECTED CATEGORY\n"
        "Student research (undergraduate and master students)\n\n"
        "TITLE\n"
        f"{TITLE}\n\n"
        "ABSTRACT\n"
        f"{abstract}\n\n"
        "ABSTRACT WORD COUNT\n"
        f"{words} words (limit 250, title excluded)\n",
        encoding="utf-8")

    print(f"title page       : {n_tp} page(s)  {tp.stat().st_size} bytes  {sha256(tp)}")
    print(f"blind manuscript : {n_bm} page(s)  {bm.stat().st_size} bytes  {sha256(bm)}")
    print(f"abstract words   : {words}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

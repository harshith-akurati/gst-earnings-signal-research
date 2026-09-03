# AARE submission readiness checklist

**Date:** 2026-09-03 · **Branch:** `manuscript-v1.1-revision-20260827`
**Package:** `AARE_Submission/` · **Not submitted.** No form was filled in and no file was uploaded.

## Files

| File | Bytes | Pages | SHA-256 |
|---|---|---|---|
| `AARE_TITLE_PAGE.pdf` | 2201 | 1 | `740340aea76ff3846e10cb26def4ee47e23d5a74ac7fa676688043bf2093b9ef` |
| `AARE_BLIND_MANUSCRIPT.pdf` | 56149 | 16 | `57b92a506a5b69357c0f245879299d69601e1cfc66337348de0b041570e1a7e3` |
| `AARE_SUBMISSION_TEXT.txt` | 1946 | — | `d3200f1381b0429b61eccf57a3fa647775986ca5bada1662e08a474f1a0723e9` |
| `ABSTRACT.txt` | 1676 | — | `be04279b647267e34fd13aa580229cfc85086b68e002f0eb4bcad6314920fb15` |

Hashes are of the build recorded here. Rebuilding regenerates the PDF creation timestamp, so the
PDF hashes change on a rebuild even when the content does not.

## Checklist

| # | Item | Result | Evidence |
|---|---|---|---|
| 1 | No placeholders anywhere in the abstract | **PASS** | `count_words.py` scans for `TBD`, `TODO`, `XXX`, `PLACEHOLDER`, and bracket characters; result `none` |
| 2 | Abstract at most 250 words | **PASS** | **249 words**, title excluded, counted by `count_words.py` |
| 3 | Exact high-attention definition included | **PASS** | Abstract states: weekly Google Trends spike at least 5 rolling standard deviations above the prior 12 week mean, event week excluded from its own baseline. Verified against `/frozen_definitions/high_gst` and `GST_FixedWindow_PerEvent_Canonical.py` lines 85 to 143 |
| 4 | Sample period included | **PASS** | "between March 2021 and December 2025", from `/sample/date_range` = `["2021-03-24","2025-12-19"]` |
| 5 | Sample-size language accurate | **PASS** | Matched analysis described as 73 matched pairs against 73 matched controls, not as "146 observations". Clustered and incremental models described at 285 events. No single headline N is asserted |
| 6 | Title-page PDF under 10 MB | **PASS** | 2201 bytes = 0.002 MB |
| 7 | Blind-manuscript PDF under 10 MB | **PASS** | 56149 bytes = 0.054 MB |
| 8 | No author identifiers in visible blind-manuscript text | **PASS** | Full text extracted from all 16 pages (59310 characters); zero hits for `akurati`, `marquette`, `chesterfield`, `@gmail`, `hakur`, Windows or POSIX user paths; zero email-shaped patterns; no acknowledgments section exists in the source manuscript |
| 9 | No author identifiers in blind PDF metadata | **PASS** | `/Author`, `/Subject`, `/Keywords`, `/Creator`, `/Producer` all empty; `/Title` is the paper title; creation and modification dates removed |
| 10 | All headline numbers resolve to committed artifacts | **PASS** | Every abstract number traced in `AARE_FACT_AUDIT.md` §4 to a JSON pointer or a named line in a committed artifact |
| 11 | Unsupported or superseded claims absent | **PASS** | 7.72%, 3.72%, Cohen's d = 1.294 and the permutation p all absent from the abstract; the superseded +1.4411 pp figure absent; sensitivity D absent. `tools/check_signal_without_strategy_numbers.py` exits 0 with "sensitivity D absent from title and abstract" |
| 12 | PDFs render without clipping, blank pages, or broken tables | **PASS** | Both PDFs rendered at 100 dpi; every text block lies inside the page box (0 overflowing blocks in 17 pages); no page has fewer than 3 characters of extractable text; every table-bearing page inspected visually |

**Result: 12 of 12 PASS.**

## Disclosures

These are recorded rather than hidden. None of them fails a checklist item.

1. **The committed figures are not included.** `review_package/Signal_Without_Strategy_v1.1_FIGURES.pdf`
   page 1 has genuine right-edge clipping: annotation blocks reach x1 = 612.3 to 614.6 pt on a
   612 pt page, so the trailing words of five Figure 1 rows are cut off. Including it would fail
   item 12. The manuscript body makes **zero** references to Figure 1, 2 or 3, so nothing in the
   text depends on them, and the committed manuscript PDF is likewise text and tables only. The
   figure clipping is a pre-existing defect in that artifact; it was **not** repaired here, because
   repairing it is figure work outside this package.

2. **Submission title differs from the internal manuscript title.** The blind manuscript is
   rendered with the submission title "Search Attention Without Strategy: Association, Prediction,
   and Tradability Around Earnings Announcements". The committed source retains its own title,
   "Signal Without Strategy: Search Attention, Earnings Surprise, and the Difference Between
   Association and Tradable Prediction". Only the rendered H1 is substituted; no other manuscript
   text is altered, and the committed manuscript file is unchanged.

3. **The manuscript's own abstract is 336 words** and is unchanged. The 249-word AARE abstract is a
   separate artifact for the submission form; it does not replace the manuscript abstract.

4. **Correspondence email is a blank field.** No committed manuscript artifact states one. An
   address appears in repository script `USER_AGENT` headers, which is not an authorship record, so
   it was not promoted. Enter it by hand before upload.

5. **Category label is unverified against the live form.** `AARE_SUBMISSION_TEXT.txt` records
   "Student research (undergraduate and master students)" exactly as supplied. Confirm the wording
   on the form before selecting, since the entrant is a high-school student and the label names
   undergraduate and master students.

6. **Long tokens wrap across lines in the widest tables.** In the eight-column synthesis table,
   strings such as `Retrospective` and `NO_INCREMENTAL_SEARCH_VALUE` break across lines without a
   hyphen. No content is truncated or clipped, and the column-width floor was raised for this build
   so that `PRIMARY` and `sensitivity` no longer split. Cosmetic only.

## Verification commands

```bash
python AARE_Submission/count_words.py                        # 249 words, exit 0
python AARE_Submission/build_aare_package.py                 # rebuilds both PDFs
python tools/check_signal_without_strategy_numbers.py        # NUMERICAL AUDIT PASSED, exit 0
```

## Not done, deliberately

No form was submitted. No PR was opened, marked ready, or merged. The prospective HYP-01 pipeline,
the event registry, the collector, the scheduled task, PR #39, PR #40, PR #42, the F5 materials, the
SESOI materials and the live data branch were not touched.

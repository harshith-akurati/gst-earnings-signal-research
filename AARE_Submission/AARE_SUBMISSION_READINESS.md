# AARE submission readiness checklist

**Date:** 2026-09-03 · **Branch:** `manuscript-v1.1-revision-20260827`
**Package:** `AARE_Submission/` · **Not submitted.** No form was filled in and no file was uploaded.

> ## BLOCKING: the two PDFs are stale as of 2026-09-04
>
> `ABSTRACT.txt`, `AARE_SUBMISSION_TEXT.txt`, the manuscript and the executive summary were
> corrected on 2026-09-04 to the recomputed pooled statistics. **`AARE_TITLE_PAGE.pdf` and
> `AARE_BLIND_MANUSCRIPT.pdf` were not rebuilt and still contain the superseded numbers**
> (+1.509 pp at p = 0.0662 described as spanning zero; +0.0131 pp at p = 0.98332), which the
> 2026-08-22 overlay marks `DO_NOT_CITE_PENDING_CORRECTION`.
>
> **Do not upload these PDFs.** Rebuild them with `build_aare_package.py` first, then refresh the
> byte counts and SHA-256 values in the table below, which are also stale.
>
> They were not rebuilt here for two reasons: `pypdf` and `reportlab` are not installed in the
> environment used for this correction, so the build cannot run; and commit `d5e94c5` deliberately
> preserved the existing PDF bytes, so regenerating them is a decision for the author rather than a
> side effect of a text correction.

## Upload files

| File | Bytes | Pages | SHA-256 |
|---|---|---|---|
| `AARE_TITLE_PAGE.pdf` | 1966 | 1 | `588877ec6706ec85253b37df83f6c967dca61ac2af7c018b5d2c8a682d1141f6` |
| `AARE_BLIND_MANUSCRIPT.pdf` | 54850 | 16 | `2797c9a3c75d2f27edd305ff857f39c1ae3e53ea114aaadc65ddf35a26de6cbd` |
| `AARE_SUBMISSION_TEXT.txt` | — | — | see repository |
| `ABSTRACT.txt` | 1674 | — | `09cae432a55326d62b9ec6af9952de069689a1fa6045c9fea3d1ed5bc4821b84` |

`*.pdf -text` is now set in `.gitattributes`, so these PDF bytes and hashes reproduce exactly after
a fresh clone. Rebuilding from source still changes the title-page hash, because reportlab stamps a
creation timestamp; the blind manuscript has its timestamps stripped.

## Checklist

| # | Item | Result | Evidence |
|---|---|---|---|
| 1 | No placeholders | **PASS** | `count_words.py` scans for `TBD`, `TODO`, `XXX`, `PLACEHOLDER` and bracket characters; result `none` |
| 2 | Abstract at most 240 words | **PASS** | **239 words**, title excluded. NOTE: `count_words.py` enforces the looser 250-word cap; 240 is the binding requirement stated here and the abstract is held to it |
| 3 | No em dashes | **PASS** | 0 em dashes, 0 en dashes |
| 4 | Attention definition stated and verified | **PASS** | `z >= 5` confirmed an explicit deterministic selection rule (`STRONG_Z = 5.0`; `qualifies = z >= STRONG_Z`; signal arm filtered on `qualifies_z5 == True`), so the abstract says "were selected for". See `AARE_FACT_AUDIT.md` §2a |
| 5 | Control disclosure retained | **PASS** | Abstract states matched controls were not required to fall below the threshold **and now states how many exceeded it**: six of the 73 surviving matched controls are themselves z >= 5.0 events (32 are z >= 2; largest control z = 14.60). Re-measured 2026-09-04, see `AARE_FACT_AUDIT.md` §2b |
| 6 | Sample period and universe included | **PASS** | "285 usable U.S. earnings announcements from 28 companies between March 2021 and December 2025", from `/sample/date_range`, `/sample/events_usable`, `/sample/tickers` |
| 7 | Sample-size language accurate | **PASS** | 73 signal events and 73 individually matched controls for the matched analysis; **217** deduplicated events for the clustered regression (corrected 2026-09-04 from 285, which double-counted reused and cross-labelled control rows). 285 remains correct for the *usable population*, which is how the abstract's first paragraph uses it. The two analyses are explicitly described as a matched difference versus a conditional association, not competing estimates |
| 8 | Correct hyphenation | **PASS** | `ticker-clustered`, `price-and-calendar`, `event-day`, `12-week`, `2.72-percentage-point`, `intercept-only`, `attention-filtered`, `post-earnings`, `Out-of-sample` |
| 9 | No causal language | **PASS** | `check_signal_without_strategy_numbers.py`: "no prohibited causal, alpha, confirmatory or tradability language" |
| 10 | No unsupported or superseded figures | **PASS** | 7.72%, 3.72%, d = 1.294, the permutation p, the superseded +1.4411 pp and sensitivity D are all absent from the abstract |
| 11 | Form abstract identical to manuscript abstract | **PASS** | `ABSTRACT.txt` compared byte-for-byte against the manuscript §1 block and against the block inside `AARE_SUBMISSION_TEXT.txt`; both identical |
| 12 | All headline numbers resolve to committed artifacts | **PASS** | 160 claims resolved, 219 tokens accounted. The six conference-precision renderings (`2.08`, `1.51`, `0.013`, `3.630`, `3.628`, `0.85`) were registered as claims against the same artifact pointers, not allowlisted |
| 13 | Title page carries no correspondence-email line | **PASS** | Extracted title-page text is title, author, school, city, track only |
| 14 | No mentors or advisers added as authors | **PASS** | No committed artifact names any other author |
| 15 | Title-page PDF under 10 MB | **PASS** | 1966 bytes = 0.0019 MB |
| 16 | Blind-manuscript PDF under 10 MB | **PASS** | 54850 bytes = 0.0523 MB |
| 17 | No author identifiers in visible blind text | **PASS** | All 16 pages extracted; zero hits for name, school, city, `@gmail`, user paths or "correspondence"; zero email-shaped patterns |
| 18 | No author identifiers in blind PDF metadata | **PASS** | `/Author`, `/Subject`, `/Keywords`, `/Creator`, `/Producer` empty; creation and modification dates removed |
| 19 | PDFs render without clipping, blank pages or broken tables | **PASS** | 0 text blocks outside the page box across all 17 pages; 0 blank pages; every table-bearing page (2, 6, 8, 10, 11, 15) inspected visually |
| 20 | PDF bytes survive a fresh checkout | **PASS** | `*.pdf -text` added; verified by temporary clone, see the report accompanying this commit |

**Result: 20 of 20 PASS.**

## Deviation from the supplied abstract text, and why

One token was changed from the text supplied in the task: **"attention contributed 0.01 percentage
points" became "0.013 percentage points"**.

**Superseded note (2026-09-04).** The paragraph previously here explained why the incremental
coefficient was rendered as `0.013` rather than `0.01`: `0.01` is reserved in the numerical checker
as the USD 0.01 EPS match tolerance used in manuscript §4.4, and the checker forbids one token from
being both an allowlisted definition and a research claim.

That rationale no longer applies. The incremental coefficient was recomputed on the corrected
217-event sample and is now **+0.7665 pp (p = 0.16525)**, rendered `0.77` in the abstract, which
collides with nothing. The conclusion is unchanged -- the contribution is still not distinguishable
from zero -- but it must now be argued from the interval rather than read off a coefficient that
was visibly near zero. See `Correction_Overlays/2026-09-04_Pooled_Recompute/`.

## Other disclosures

1. **Figures are not included in the blind manuscript.** The manuscript body references no figure,
   and page 1 of `review_package/Signal_Without_Strategy_v1.1_FIGURES.pdf` has real right-edge
   clipping (blocks reach x1 = 612.3 to 614.6 pt on a 612 pt page). Including it would fail item 19.
   That defect is pre-existing and was not repaired here.

2. **Submission title differs from the internal manuscript title.** The blind manuscript is rendered
   with the submission title; the committed source keeps its own title. Only the rendered H1 is
   substituted.

3. **Category label is unverified against the live form.** `AARE_SUBMISSION_TEXT.txt` records
   "Student research (undergraduate and master students)" exactly as supplied. Confirm the wording
   on the form, since the entrant is a high-school student.

4. **Long tokens wrap across lines in the widest tables.** No content is truncated or clipped.

## Verification commands

```bash
python AARE_Submission/count_words.py                        # 233 words, exit 0
python AARE_Submission/build_aare_package.py                 # rebuilds both PDFs
python tools/check_signal_without_strategy_numbers.py        # NUMERICAL AUDIT PASSED, exit 0
```

## Not done, deliberately

No form submitted. No PR opened, marked ready, or merged. No amend, reset, rebase, squash or
force-push. The prospective HYP-01 pipeline, event registry, collector, scheduled task, live-data
branch, PR #39, PR #40, PR #42, F5 and SESOI materials were not touched. The v1.0 manuscript was
not modified.

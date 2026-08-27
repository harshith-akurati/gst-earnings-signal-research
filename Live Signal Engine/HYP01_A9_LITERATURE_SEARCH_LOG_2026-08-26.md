# Bounded literature search — external effect-size anchor for A9

**Date searched:** 2026-08-26 · **Status:** DRAFT, uncommitted · **Scope:** one bounded pass, closed
at the end of this document. Not left open.

## Purpose

Identify whether any external published estimate can serve as a justified effect-size anchor for a
future A9 design-sensitivity analysis of HYP-01, whose locked primary model is
`abs_overnight_gap ~ gst_zscore` (OLS, cluster-robust CR2 on `ticker`, α = 0.05, two-sided).

## Prespecified inclusion criteria

All five must hold. These were fixed before searching and were not relaxed during it.

1. Estimates a **marginal** relationship, not only an interaction.
2. Uses **pre-announcement** attention.
3. Outcome is **absolute announcement-movement magnitude**, or explicitly convertible to it.
4. Predictor can be translated into `gst_zscore` units **with documented assumptions**.
5. The translation can be completed **before** any power calculation.

## Databases and sites searched

| Source | Access route |
|---|---|
| Publisher DOI resolver (doi.org) | direct |
| MDPI (`mdpi.com`) — *International Journal of Financial Studies* | direct — **HTTP 403, blocked** |
| DOAJ (`doaj.org`) | direct — **HTTP 403, blocked** |
| RePEc / IDEAS (`ideas.repec.org`) | direct — **succeeded** |
| Wiley Online Library (`onlinelibrary.wiley.com`) | via search index — abstract page only |
| BYU ScholarsArchive (`scholarsarchive.byu.edu`) | landing page succeeded; PDF 403 to the markdown-extraction fetcher, **retrieved successfully by direct HTTPS download** — 41 pages, 462,447 bytes |
| Semantic Scholar Graph API (`api.semanticscholar.org`) | direct — returned `openAccessPdf`, status **GREEN**, pointing at the BYU deposit |
| ResearchGate (`researchgate.net`) | **HTTP 403, blocked** |
| General web search | multiple queries, below |

## Queries run

| # | Query | Date |
|---|---|---|
| Q1 | `Drake Roulstone Thornock 2012 "investor information demand" Google search earnings announcements Journal of Accounting Research` | 2026-08-26 |
| Q2 | `Ahluwalia "Online Search Activity and Market Reaction to Earnings Announcements" International Journal of Financial Studies 2026` | 2026-08-26 |
| Q3 | `Da Engelberg Gao 2011 "In Search of Attention" Journal of Finance Google search volume index SVI` | 2026-08-26 |
| Q4 | `Drake Roulstone Thornock 2012 abnormal search ASVI interaction "unexpected earnings" "-5 to -1" preemption announcement return response coefficient` | 2026-08-26 |
| Q5 | `"Online Search Activity and Market Reaction to Earnings Announcements" Ahluwalia abstract outcome variable abnormal return regression Google Trends 2004 2008` | 2026-08-26 |
| F1 | Fetch `https://doi.org/10.3390/ijfs14020033` → 302 → `https://www.mdpi.com/2227-7072/14/2/33` | 2026-08-26 |
| F2 | Fetch `https://www.mdpi.com/2227-7072/14/2/33` — **403** | 2026-08-26 |
| F3 | Fetch `https://www.mdpi.com/2227-7072/14/2/33/pdf` — **403** | 2026-08-26 |
| F4 | Fetch `https://doaj.org/article/2ee5228471da4ebd9d6d7673b82b60ab` — **403** | 2026-08-26 |
| F5 | Fetch `https://ideas.repec.org/a/bla/joares/v50y2012i4p1001-1040.html` — **succeeded, verbatim abstract obtained** | 2026-08-26 |
| F6 | Fetch `https://scholarsarchive.byu.edu/facpub/8399` — succeeded (landing page only) | 2026-08-26 |
| F7 | Fetch `https://scholarsarchive.byu.edu/cgi/viewcontent.cgi?article=9315&context=facpub` — **403** to markdown fetcher | 2026-08-26 |
| F8 | Fetch `https://www.researchgate.net/publication/228259600_...` — **403** | 2026-08-26 |
| F9 | Semantic Scholar Graph API by DOI — returned `openAccessPdf` = BYU deposit, `GREEN` | 2026-08-26 |
| F10 | **Direct HTTPS download of the BYU open-access PDF — HTTP 200, 462,447 bytes, 41 pages, full text extracted (126,037 characters)** | 2026-08-26 |

## Candidates assessed

### C1 — Drake, Roulstone & Thornock (2012)

**Verified citation.** Michael S. Drake, Darren T. Roulstone, and Jacob R. Thornock, 2012. "Investor
Information Demand: Evidence from Google Searches Around Earnings Announcements." *Journal of
Accounting Research*, vol. 50(4), pages 1001–1040, September. DOI `10.1111/j.1475-679X.2012.00443.x`.
Verified against the RePEc/IDEAS bibliographic record (F5) and the Wiley abstract page.

**Verified abstract content (verbatim, from F5).** "When investors search for more information in the
days just prior to the announcement, preannouncement price and volume changes reflect more of the
upcoming earnings news and there is less of a price and volume response when the news is announced.
This result suggests that, when investors demand more information about a firm, the information
content of the earnings announcement is partially preempted."

**Assessment against criteria.**

| Criterion | Verdict | Basis |
|---|---|---|
| 1 — marginal, not only interaction | **FAIL** | Verified from Table 8: the estimand is `UE × AbSearch[window]`, an interaction conditional on unexpected earnings. Not a marginal attention→magnitude coefficient |
| 2 — pre-announcement attention | **PASS** | Abnormal Google search in the days prior to the announcement |
| 3 — absolute movement magnitude | **FAIL** | Verified from Table 8: the dependent variable is `AR[0, +1]`, a **signed** announcement abnormal return, not `abs_overnight_gap` |
| 4 — translatable to `gst_zscore` units | **FAIL** | Verified from full text: `AbSearch` is an abnormal-search construction on S&P 500 tickers, not the project's `gst_zscore`; no documented mapping exists |
| 5 — translation completable pre-power | **FAIL** | Follows from 4 |

**EXCLUDED.** Fails criteria 1, 3, 4 and 5.

**Full text obtained and verified.** The Semantic Scholar Graph API reported an `openAccessPdf`
with status `GREEN` pointing at the BYU ScholarsArchive deposit; a direct HTTPS download returned
HTTP 200 (462,447 bytes, 41 pages) and full text was extracted. The following are now **verified
against the paper itself**, superseding the earlier verification-gap notice:

- **Sample:** S&P 500 firms, **2005 to 2008**; **N = 4,133** quarterly observations.
- **Structure:** the preemption result is an **interaction of unexpected earnings with abnormal
  search**, `UE x AbSearch[window]`, predicted sign **negative**.
- **Location — Table 8**, "The Association Between Announcement Abnormal Returns, the Earnings
  Surprise, and Abnormal Search", model (6), dependent variable **`AR[0, +1]`**.
- **Coefficients (standard errors):** `UE x AbSearch[FQE, -1]` = **-3.289\*** (2.223) col (1),
  **-2.477\*\*\*** (1.043) col (2); `UE x AbSearch[-5, -1]` = **-3.818\*\*\*** (1.364) col (3),
  **-2.863\*\*\*** (0.809) col (4).
- **Standard errors** are clustered by time (calendar quarter) x industry (Fama-French 17).
- **One-tailed tests:** footnote verbatim — "*, **, *** indicates statistical significance at the
  p < 0.10, 0.05, 0.01 level, respectively. **We use one-tailed tests when a direction is
  predicted.**"
- **Both shorter-window (`[-5, -1]`) estimates carry \*\*\***; the longer `[FQE, -1]` window carries
  \* in column (1) and \*\*\* in column (2).

> **VERSION NOTE — numbering follows the FINAL PUBLISHED ARTICLE.** In the published version of record
> (*JAR* 50(4), 1001–1040, DOI `10.1111/j.1475-679X.2012.00443.x`) the preemption coefficients are in
> **Table 8** (model 6, DV `AR[0, +1]`, printed p. 1033). **Table 6** in that version (p. 1029) is a
> different result — model (4), DV `AR[-5, -1]` — with **positive** interactions 2.795, 1.952, 1.769,
> 1.614. Table 7 (p. 1031) is abnormal volume, `Abvol[-5, -1]`, model (5).
>
> **Earlier circulated versions are not asserted to be erroneous.** Pre-publication drafts circulated
> with different table numbering, and a "Table 6" citation may be correct against one of them. This log
> takes no position on any working-paper version; it fixes the published version of record as the
> citation authority and records which table that authority places the coefficients in.

**Provenance record.**

| Field | Value |
|---|---|
| Version | Final published article, *JAR* 50(4), 1001-1040 |
| DOI | `10.1111/j.1475-679X.2012.00443.x` |
| Copy | Author-deposited open access, BYU ScholarsArchive Faculty Publications 8399 |
| URL | `https://scholarsarchive.byu.edu/facpub/8399` |
| PDF URL | `https://scholarsarchive.byu.edu/cgi/viewcontent.cgi?article=9315&context=facpub` |
| OA status | `GREEN` (Semantic Scholar `openAccessPdf`) |
| Access date | 2026-08-26 |
| PDF SHA-256 | `faabe0549cd6853227ce4c28811d63fd8ad46ba1ccb0ea8d73bbb4052e27198a` |
| Size / pages | 462,447 bytes / 41 PDF pages |
| Table / model | Table 8, model (6), DV `AR[0, +1]`, printed p. 1033 |

**The PDF is not committed to this repository** — copyrighted article. Hash and location only.

**Verification does not change the exclusion.** Criterion 3 still fails — `AR[0, +1]` is a **signed**
announcement return, not absolute movement magnitude. Criterion 1 still fails — the estimand is an
interaction conditional on `UE`, a variable HYP-01's locked model does not contain. Criteria 4 and 5
still fail — `AbSearch` is not `gst_zscore` and no documented conversion exists. **No coefficient
from this paper may be used as an anchor.**

### C2 — Da, Engelberg & Gao (2011)

**Verified citation.** Zhi Da, Joseph Engelberg, and Pengjie Gao, 2011. "In Search of Attention."
*The Journal of Finance*, vol. 66(5), pages 1461–1499, October. DOI
`10.1111/j.1540-6261.2011.01679.x`. Verified via the RePEc record and the AFA issue listing.

**Verified content.** Introduces the Google Search Volume Index (SVI) as a direct attention measure on
Russell 3000 stocks, 2004–2008; SVI increases predict higher prices over the following two weeks with
an eventual reversal within the year; also treats IPO first-day returns.

**Assessment.**

| Criterion | Verdict | Basis |
|---|---|---|
| 1 — marginal | **PASS** | The headline SVI→return relationships are marginal |
| 2 — pre-announcement attention | **FAIL** | SVI is measured in calendar time relative to trading, not specifically in a pre-earnings-announcement window |
| 3 — absolute movement magnitude | **FAIL** | Outcome is *signed* subsequent return and reversal, not absolute announcement-period movement |
| 4 — translatable to `gst_zscore` | **FAIL** | SVI/ASVI construction differs from the project's z-score; no documented mapping |
| 5 — completable pre-power | **FAIL** | Follows from 4 |

**EXCLUDED.** Fails criteria 2, 3, 4 and 5.

### C3 — Ahluwalia (2026)

**Verified citation.** Saurabh Ahluwalia, "Online Search Activity and Market Reaction to Earnings
Announcements," *International Journal of Financial Studies*, 2026, vol. 14, no. 2, article 33.
DOI `10.3390/ijfs14020033`. Published 3 February 2026. Citation verified via the DOI resolver
redirect (F1, `10.3390/ijfs14020033` → `mdpi.com/2227-7072/14/2/33`, confirming journal/volume/issue/
article number) and via search-index records (Q2, Q5).

**Verified content (abstract level only).** Uses Google Trends search volume, 2004–2008, as a proxy
for investor information demand. Greater pre-announcement search activity is **positively** associated
with future market reaction to earnings announcements, pre-earnings-announcement drift, and buying
pressure; associations are stronger for more obscure firms.

**Assessment.**

| Criterion | Verdict | Basis |
|---|---|---|
| 1 — marginal | **PASS (provisional)** | Reported as a marginal association |
| 2 — pre-announcement attention | **PASS** | Search activity prior to the announcement |
| 3 — absolute movement magnitude | **FAIL** | Outcome is *signed/directional* — market reaction, drift, and buying pressure. Nothing in the accessible record indicates an absolute-magnitude outcome, and convertibility could not be established |
| 4 — translatable to `gst_zscore` | **`NOT_EVALUATED_AFTER_CRITERION_3_FAILURE`** | Not assessed. Criterion 3 already excludes the paper, and full text was inaccessible (MDPI and DOAJ both 403, F2–F4). Recorded as untested, **not** as a failure |
| 5 — completable pre-power | **`NOT_EVALUATED_AFTER_CRITERION_3_FAILURE`** | Not assessed, for the same reason. Recorded as untested, **not** as a failure |

**EXCLUDED on criterion 3.** Criteria 4 and 5 were **not evaluated**: assessment stopped once
criterion 3 failed, and full text was in any case inaccessible. They are recorded as
`NOT_EVALUATED_AFTER_CRITERION_3_FAILURE`. **An untested criterion is not a failed criterion**, and
nothing in this log should be read as evidence that Ahluwalia's predictor cannot be translated — that
question was never reached.

## Conclusion

All three named papers were located and their bibliographic records verified. **Drake was verified
against its full text**; Da–Engelberg–Gao and Ahluwalia were assessed at abstract/record level. None
satisfies the prespecified comparability criteria.

The binding obstacle is **criterion 3** in every case: HYP-01's locked outcome `abs_overnight_gap` is
an **absolute** movement magnitude, whereas the literature located here estimates **signed**
quantities — announcement abnormal return, drift, buying pressure, subsequent return and reversal.

For Drake and Da–Engelberg–Gao, criterion 4 also fails on verified or recorded grounds. For
Ahluwalia, criteria 4 and 5 are `NOT_EVALUATED_AFTER_CRITERION_3_FAILURE` and must not be cited as
failures.

> **No compatible external effect-size anchor identified as of 2026-08-26 under the prespecified
> comparability criteria.**

**This search is closed.** It is not left open pending full-text access. Should a co-author obtain the
Drake or Ahluwalia full text, that is a *new* bounded search with its own log, and it would still have
to clear criterion 3 before any coefficient could be used.

## Sources

- [Drake, Roulstone & Thornock (2012) — RePEc/IDEAS record](https://ideas.repec.org/a/bla/joares/v50y2012i4p1001-1040.html)
- [Drake, Roulstone & Thornock (2012) — Wiley](https://onlinelibrary.wiley.com/doi/abs/10.1111/j.1475-679X.2012.00443.x)
- [Da, Engelberg & Gao (2011) — RePEc/IDEAS record](https://ideas.repec.org/a/bla/jfinan/v66y2011i5p1461-1499.html)
- [Da, Engelberg & Gao (2011) — Wiley](https://onlinelibrary.wiley.com/doi/10.1111/j.1540-6261.2011.01679.x)
- [Ahluwalia (2026) — MDPI landing (403 to automated fetch)](https://www.mdpi.com/2227-7072/14/2/33)
- [Ahluwalia (2026) — DOAJ record (403 to automated fetch)](https://doaj.org/article/2ee5228471da4ebd9d6d7673b82b60ab)

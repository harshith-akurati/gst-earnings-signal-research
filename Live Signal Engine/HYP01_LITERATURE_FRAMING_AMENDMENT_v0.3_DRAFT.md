# HYP-01 Literature-Framing Amendment — v0.3 DRAFT

**Date drafted:** 2026-08-26 · **Status:** DRAFT, **uncommitted**, for co-author review.
**Type:** **FRAMING ONLY.** This document adds published-literature context to the justification
narrative around HYP-01. It makes **no new hypothesis and no new scientific-design decision.**

## 0. What this amendment does not do

Stated first so the boundary is unambiguous. This amendment:

- does **not** change HYP-01's prediction, predictor, outcome, model, α, sidedness, cluster variable,
  eligibility rules, ordering rule, freeze threshold, or run count;
- does **not** resolve C6, C7, E3, E8, F5 or A9;
- does **not** register, propose, or imply a SESOI;
- does **not** perform, license, or presuppose any power or design-sensitivity calculation;
- does **not** modify any locked or preregistration artifact. Every existing lock retains its original
  bytes and hashes, unchanged. The artifacts consulted and their SHA-256 values are recorded in
  `HYP01_A9_ARTIFACT_RECONCILIATION_TABLE_v1.0_DRAFT.md`;
- does **not** inspect any panel row, financial value, search value, or HYP-01 outcome.

## 1. The prediction is unchanged

HYP-01 predicts **positive amplification**: higher pre-announcement attention is associated with
**larger** absolute overnight movement at the announcement. The locked model is unchanged:

```
abs_overnight_gap ~ gst_zscore        OLS
coefficient of interest : gst_zscore
null hypothesis         : beta_gst = 0
alpha                   : 0.05
sidedness               : two_sided
cluster variable        : ticker
```

Source: `GST_HYP01_EFFECTIVE_LOCK_REPORT_v1.0.json`, `/unamended_base_lock_invariants`.

## 2. The two-sided test was already locked, and remains so

`primary_model.sidedness = "two_sided"` is an **unamended base-lock invariant**, corroborated by
`GST_PROSPECTIVE_HYPOTHESIS_REGISTRY_v1.0.json` `/statistical_governance/inference_sidedness`. It was
locked before this amendment and is not reopened by it.

**Drake, Roulstone & Thornock (2012) provides additional pre-outcome justification for retaining that
two-sided test. It is not the test's original rationale.** The test was two-sided already; what the
literature adds is an independent reason why a one-sided test would have been unwise — a credible
published mechanism points the opposite way from HYP-01's own prediction, so the opposite tail is not
a direction the design may treat as uninteresting.

Recording this now matters because it is being recorded **before any eligible HYP-01 outcome was
observed or analysed** (eligible count = 0; `analysis_run = false`; `scientific_result = null`). A
justification added after an outcome is seen is not a justification.

## 3. What Drake actually shows, and what it does not

**Verified from the primary bibliographic record.** Michael S. Drake, Darren T. Roulstone, and Jacob R.
Thornock, 2012, "Investor Information Demand: Evidence from Google Searches Around Earnings
Announcements," *Journal of Accounting Research* 50(4), 1001–1040, DOI
`10.1111/j.1475-679X.2012.00443.x`.

**Verified abstract, verbatim:** "When investors search for more information in the days just prior to
the announcement, preannouncement price and volume changes reflect more of the upcoming earnings news
and there is less of a price and volume response when the news is announced. This result suggests
that, when investors demand more information about a firm, the information content of the earnings
announcement is partially preempted."

**Verified sample.** Daily Google search volume for the tickers of **S&P 500** firms, **2005 to 2008**;
the estimation sample is **N = 4,133 quarterly observations** ("The sample consists of 4,133 quarterly
observations for S&P 500 firms over the period 2005 to 2008").

**Drake is an interaction conditional on unexpected earnings**, and this is now verified against the
paper's own tables rather than inferred from the abstract. The preemption result is **Table 8**, "The
Association Between Announcement Abnormal Returns, the Earnings Surprise, and Abnormal Search",
reporting model (6) with dependent variable **`AR[0, +1]`** — the *announcement-window abnormal
return*. The tested quantity is the interaction `UE × AbSearch[window]`, i.e. unexpected earnings
interacted with abnormal search, with predicted sign **−**:

| Term | Col (1) Analysts | Col (2) Time-Series | Col (3) Analysts | Col (4) Time-Series |
|---|---|---|---|---|
| `UE × AbSearch[FQE, −1]` | **−3.289\*** (2.223) | **−2.477\*\*\*** (1.043) | — | — |
| `UE × AbSearch[−5, −1]` | — | — | **−3.818\*\*\*** (1.364) | **−2.863\*\*\*** (0.809) |
| `UE` (ERC) | 8.528\*\*\* (1.478) | 3.027\*\*\* (0.636) | 7.168\*\*\* (1.615) | 2.287\*\*\* (0.551) |
| N | 4,133 | 4,133 | 4,133 | 4,133 |

Parentheses are **standard errors**, "clustered by time (calendar quarter) × industry (Fama-French 17
classifications)". Significance markers per the table footnote: "∗, ∗∗, ∗∗∗ indicates statistical
significance at the p < 0.10, 0.05, 0.01 level, respectively. **We use one-tailed tests when a
direction is predicted.**" The four interaction estimates above carry a predicted direction and are
therefore **one-tailed**.

> **VERSION NOTE — table numbering follows the FINAL PUBLISHED ARTICLE.** In the final published
> version of record (*Journal of Accounting Research* 50(4), 1001–1040, DOI
> `10.1111/j.1475-679X.2012.00443.x`) the announcement-abnormal-return preemption results are
> **Table 8**, model (6), dependent variable `AR[0, +1]`, printed page 1033. In that same published
> version, **Table 6** (printed page 1029) is a *different* result — "The Association Between
> Preannouncement Abnormal Returns, the Earnings Surprise, and Abnormal Search", model (4), dependent
> variable `AR[−5, −1]` — whose interactions are **positive**: `UE × AbSearch[FQE, −1]` = 2.795\*\*
> (1.220) and 1.952\*\*\* (0.598); `UE × AbSearch[−5, −1]` = 1.769\*\*\* (0.625) and 1.614\*\*\*
> (0.436). Table 7 (printed page 1031) is abnormal *volume*, `Abvol[−5, −1]`, model (5).
>
> **Earlier circulated versions of this paper are not asserted to be wrong.** Working papers and
> pre-publication drafts of Drake, Roulstone & Thornock circulated with different table numbering, and
> a citation of "Table 6" for the preemption result may well be correct against one of those versions.
> This amendment takes no position on any pre-publication draft. It simply fixes the **published
> version of record** as the citation authority for this project, and under that authority the
> preemption coefficients are located in **Table 8**. Any downstream document should cite Table 8 and
> state the version, so the reference stays checkable.

**Provenance of the Drake verification.** Recorded so the citation is auditable, per the co-author's
version-control requirement:

| Field | Value |
|---|---|
| Version used | **Final published article**, *Journal of Accounting Research* 50(4), 1001–1040 |
| DOI | `10.1111/j.1475-679X.2012.00443.x` |
| Copy consulted | Author-deposited open-access copy, BYU ScholarsArchive Faculty Publications 8399 |
| Repository URL | `https://scholarsarchive.byu.edu/facpub/8399` (PDF: `https://scholarsarchive.byu.edu/cgi/viewcontent.cgi?article=9315&context=facpub`) |
| Open-access status | `GREEN`, per the Semantic Scholar Graph API `openAccessPdf` record |
| Access date | **2026-08-26** |
| PDF SHA-256 | `faabe0549cd6853227ce4c28811d63fd8ad46ba1ccb0ea8d73bbb4052e27198a` |
| PDF size / pages | 462,447 bytes / 41 PDF pages (includes the ScholarsArchive cover sheet) |
| Table / model used | **Table 8**, model (6), dependent variable `AR[0, +1]` |
| Printed pages of tables | Table 6 p. 1029 · Table 7 p. 1031 · **Table 8 p. 1033** |

**The PDF itself is deliberately NOT committed to this repository** — it is a copyrighted article. Only
its hash, location, and the specific figures quoted above are recorded.

Two consequences follow, and both are framing statements rather than design decisions:

**3.1 HYP-01's marginal absolute-gap coefficient cannot identify preemption.** `beta_gst` in
`abs_overnight_gap ~ gst_zscore` is a marginal association between attention and *absolute* movement.
Drake's preemption estimand is an interaction on a **signed** announcement return, `AR[0, +1]`,
conditional on unexpected earnings. A marginal absolute-magnitude coefficient cannot separate
"attention preempted the news" from "attention accompanied a larger event", and it does not contain
the `UE` conditioning that Drake's estimand is defined on. HYP-01 is not a test of Drake's mechanism,
and a result in either direction must not be reported as confirming or refuting it.

**3.2 Where the estimates were more consistently significant — verified.** The negative estimates
were **more consistently statistically significant in the days −5 to −1 specifications**: both
`UE × AbSearch[−5, −1]` estimates are marked **\*\*\*** (p < 0.01, one-tailed), whereas the longer
`[FQE, −1]` window gives **\*** (p < 0.10) in column (1) and \*\*\* in column (2). This is a statement
about **consistency of significance across specifications**, not about magnitude — the two largest
point estimates in absolute value are −3.818 (`[−5,−1]`) and −3.289 (`[FQE,−1]`), which sit in
different windows, so the significance pattern and any magnitude ranking do not coincide. The claim
that the interaction was "strongest" in `[−5,−1]` is **not** supported and is not made.

**3.3 No mapping is available.** **No justified mapping is available from Drake's reported
coefficients alone from which to derive an anchor for HYP-01, without additional distributional and
structural assumptions** — minimally: the distribution of the project's `gst_zscore` versus Drake's
`AbSearch` construction; the relationship between an interaction coefficient on a signed announcement
return and a marginal coefficient on an absolute overnight gap; the role of the `UE` conditioning
variable, which HYP-01's locked model does not contain; and the transportability of all of these from
S&P 500 firms in 2005–2008 to a locked 24-ticker universe observed 2026–2027. None of these is
established, and the verified coefficients do not make any of them more available. See
`A9_EFFECT_SIZE_COMPARABILITY_MEMO_v0.3_DRAFT.md`.

## 4. Adjacent literature, recorded for completeness

**Da, Zhi, Joseph Engelberg, and Pengjie Gao, 2011.** "In Search of Attention." *The Journal of
Finance* 66(5), 1461–1499. DOI `10.1111/j.1540-6261.2011.01679.x`. Establishes Google SVI as a direct,
timely attention proxy weighted toward retail investors. Relevant as construct provenance for
search-based attention measures. Its outcomes are signed subsequent returns and reversal, not
absolute announcement movement.

**Ahluwalia, Saurabh, 2026.** "Online Search Activity and Market Reaction to Earnings Announcements."
*International Journal of Financial Studies* 14(2), 33. DOI `10.3390/ijfs14020033`. Published
3 February 2026. Uses Google Trends search volume 2004–2008; reports that greater pre-announcement
search activity is **positively** associated with market reaction to earnings announcements,
pre-earnings-announcement drift, and buying pressure, with stronger associations among more obscure
firms.

**Why both are recorded rather than used.** Ahluwalia's positive marginal direction is closer to
HYP-01's own prediction than Drake's preemption result is, and a reader is entitled to know that the
published record is not uniform. Neither paper is used as an anchor: full text for Ahluwalia was
inaccessible (MDPI and DOAJ both returned HTTP 403), and in both cases the outcome is a signed
quantity rather than absolute movement magnitude. Recording a *direction* from the literature is
framing; adopting a *number* would be a design decision, and none is adopted.

For Ahluwalia specifically, assessment stopped at criterion 3 (signed rather than absolute
outcome). Criteria 4 and 5 are recorded as **`NOT_EVALUATED_AFTER_CRITERION_3_FAILURE`** — untested,
**not** failed. Nothing here should be read as evidence that its predictor cannot be translated.

## 5. SESOI

**No SESOI is asserted here, and none is asserted to be unchanged.** The reconciliation searched every
committed HYP-01, registry, gap-audit and preregistration artifact and **located no registered
SESOI**. Asserting that a SESOI is "unchanged" would imply one exists. It does not.
`GST_PROSPECTIVE_RESULT_DISPLAY_GATES_v1.0.md` §6 states affirmatively that the 60 / 60 / 40
thresholds "are **not** … minimum detectable effect sizes".

Status: **`A9_BLOCKED_MISSING_REGISTERED_SESOI`.**

## 6. HYP-02

**No HYP-02 idea is introduced, advanced, or moved by this amendment.** No prior version of this
document exists in any committed branch (see §8), so there was no HYP-02 proposal in it to relocate.

For the avoidance of doubt: HYP-02 is an **already-registered** hypothesis
(`GST_PROSPECTIVE_HYPOTHESIS_REGISTRY_v1.0.json`, threshold 60, status
`PREREGISTERED_MEASUREMENT_NOT_IMPLEMENTED`, gate CLOSED). A registered hypothesis is not a loose idea
and must **not** be moved into a future-hypotheses queue by a framing amendment — that would be a
scientific-design change of exactly the kind this document is barred from making. If a *new*
HYP-02-adjacent question arises during review, it belongs in
`Live Signal Engine/FUTURE_HYPOTHESES_QUEUE.md` (which currently exists on branch
`phase5-external-scrutiny-audit`, not on this base), appended in that file's existing
`queued-pending-*` format, as a placeholder and not an approval.

## 7. Lock integrity

No locked or preregistration artifact is modified. All original bytes and hashes are preserved. The
ten artifacts consulted, with SHA-256 values as checked out on base
`63e8a13d8fadc4a52b8046df983fb6a8705e9985`, are listed in
`HYP01_A9_ARTIFACT_RECONCILIATION_TABLE_v1.0_DRAFT.md`. This amendment adds a new file and edits none.

## 8. Version note

This is labelled **v0.3** per the co-author's instruction. **No v0.1 or v0.2 of this document exists in
any committed branch of this repository, nor as an uncommitted file on disk** — verified by searching
every ref for filenames matching `LITERATURE.?FRAMING`, `EFFECT.?SIZE.?COMPARABILITY`, `A9_MEMO`, and
by a filesystem search across all worktrees. A redline against v0.2 therefore cannot be produced from
committed evidence. If a v0.2 exists outside this repository, it should be supplied so a genuine
redline can replace §9.

## 9. INSTRUCTION-DERIVED CHANGE SUMMARY

**This is not a redline.** A redline is a byte-level comparison against a predecessor document, and
no predecessor exists in this repository (§8). What follows is a summary of changes *derived from
the co-author's instructions*, not diffed from v0.2 bytes.

> **A genuine redline requires the external v0.2 bytes.** Supply the v0.2 file and a true diff will
> replace this section. Until then the "v0.2 as described by co-author" column is an **unverified**
> description of the predecessor, recorded so the intended deltas remain auditable — it is not
> evidence of what v0.2 actually said, and no provenance for it is invented.

| # | v0.2 as described by co-author (UNVERIFIED) | v0.3 asserts |
|---|---|---|
| 1 | Drake framed as the rationale for the two-sided test | Drake provides **additional pre-outcome justification for retaining** the already-locked two-sided test (§2) |
| 2 | Drake described loosely | Drake described as an **interaction conditional on unexpected earnings** (§3) |
| 3 | Implied HYP-01 could speak to preemption | States HYP-01's **marginal absolute-gap coefficient cannot identify preemption** (§3.1) |
| 4 | Interaction described as "strongest" in days −5 to −1 | States the negative estimates were **more consistently statistically significant** in the days −5 to −1 specifications — now **verified from Table 8** (both `[−5,−1]` estimates \*\*\*; `[FQE,−1]` gives \* and \*\*\*); explicitly not a magnitude claim (§3.2) |
| 5 | Suggested a mapping from Drake's coefficient | States **no justified mapping** exists from Drake's coefficient alone without additional distributional and structural assumptions (§3.3) |
| 6 | "before any prospective observation exists" | "**before any eligible HYP-01 outcome was observed or analysed**" (§2) |
| 7 | Ahluwalia citation incomplete | **Complete verified citation** incl. volume 14, issue 2, article 33, DOI `10.3390/ijfs14020033`, published 3 February 2026 (§4) |
| 8 | Contained a HYP-02 idea | No HYP-02 idea introduced; registered HYP-02 explicitly **not** moved, with rationale (§6) |
| 9 | Asserted the SESOI was "unchanged" | States **no SESOI is registered**; `A9_BLOCKED_MISSING_REGISTERED_SESOI` (§5) |
| 10 | — | Adds explicit lock-integrity statement and artifact hash manifest (§7) |
| 11 | — | Drake full text **retrieved and verified** against the published version of record (S&P 500, 2005–2008, N = 4,133, Table 8 model (6), all four coefficients and standard errors, one-tailed tests), with a full provenance record incl. PDF SHA-256. The verification-gap notice carried by the initial v0.3 draft is **removed** (§3) |
| 12 | — | Adds a **version note** fixing the final published article as citation authority: under it the preemption coefficients are **Table 8** (p. 1033), while Table 6 (p. 1029) is a different, *positive* result on `AR[−5,−1]`. Earlier working-paper numbering is **not** called erroneous (§3) |

## 10. Open items this amendment deliberately leaves open

- **C6 / C7** — **`SUBSTANTIVELY_RESOLVED`** by the 2026-08-16 amendment, **`ADMINISTRATIVELY_OPEN`**
  because no artifact closes the register entries by identifier. See
  `C6_C7_GAP_AUDIT_ERRATUM_DRAFT.md`. Not settled here.
- **A9** — **`A9_BLOCKED_MISSING_REGISTERED_SESOI`**. Unaffected by the Drake verification: verifying
  a coefficient does not make it transportable, and Drake's estimand still fails the comparability
  criteria.
- **Drake full text** — **RESOLVED.** Retrieved from the BYU ScholarsArchive open-access deposit and
  verified; the verification-gap notice is removed.
- **Ahluwalia full text** — still not retrieved (MDPI and DOAJ both 403). Criteria 4 and 5 are
  recorded as `NOT_EVALUATED_AFTER_CRITERION_3_FAILURE`, not as failures.
- **`n = 75`** — unsourced in the repository; recorded as unsourced, not refuted.

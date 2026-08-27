# Signal Without Strategy v1.1 — submission-readiness report

**Date:** 2026-08-27 · **Branch:** `manuscript-v1.1-revision-20260827`
**Base:** `phase6-control-matching-integrity` @ `63e8a13d8fadc4a52b8046df983fb6a8705e9985`

---

## 1. Verdict

**Ready for co-author review. Not yet submitted, and one editorial decision remains open.**

Every number in v1.1 resolves to a committed artifact. The extended checker passes. The central
conclusion is stated in a form the evidence supports, and every null is preserved as a null.

## 2. What changed from v1.0

| # | Change | Why |
|---|---|---|
| 1 | **New §5.1 — Level-1 matched association.** +2.0797 pp, p = 0.00397, with three sensitivities | v1.0 had no explicit Level-1 estimate in §5; the matched result now anchors the hierarchy |
| 2 | **New §5.2 — primary clustered magnitude model.** +1.509 pp, CI [−0.113, +3.131], p = 0.0662 | v1.0 never stated the primary inferential specification in the results section |
| 3 | **§5 reordered** to association → prediction → tradability, matching Figure 1 | The paper's argument is a hierarchy; the section now reads as one |
| 4 | **Q1 (+1.4411 pp) marked superseded**, moved to Appendix A.2 | The 2026-08-22 overlay supersedes it and the artifact says so |
| 5 | **Appendix A.3** records the unmatched mechanism-stability comparison (7.72% / 3.72%, d = 1.294) as explicitly non-headline and non-comparable | It exists in the repository and would otherwise be mistaken for the Level-1 result |
| 6 | **§5.3 standalone return** now states the drift existed without the attention filter and must not be cited as a GST result | v1.0 implied this; v1.1 states it |
| 7 | **Abstract rewritten** to lead with the hierarchy and end on the central conclusion | v1.0's abstract did not carry the Level-1 result |
| 8 | **Conclusion rewritten** to open with the one-sentence finding, then walk the levels | Same |
| 9 | **§4.7 HYP-01** reframed as a future confirmatory protocol with no results | v1.0 said "never ran"; v1.1 states its role and that it contributes nothing here |
| 10 | **Header** strengthened: not preregistered, known after analysis | Exploratory status must be unmissable |
| 11 | **Source artifacts** updated with the overlay and mechanism-stability files | Provenance |

## 3. Central conclusion, as stated

> **Search attention is associated with unusually active earnings events in retrospective matched
> comparisons, but it does not provide reliable incremental forecasting or trading value.**

Every qualifier is load-bearing: *retrospective* (nothing preregistered), *matched* (against
comparable earnings events, not ordinary weeks), *association* (all incremental tests null).

## 4. Evidence hierarchy as reported

| Level | Result | Estimate | Verdict |
|---|---|---|---|
| 1 — Association | Matched-event absolute move | **+2.0797 pp, p = 0.00397** | Supported, retrospective only |
| 1 — Primary inference | Clustered magnitude model | **+1.509 pp, CI [−0.113, +3.131], p = 0.0662** | **Suggestive, not supported at 5%** |
| 2 — Incremental | Strategy E marginal contribution | **+0.0131 pp, p = 0.98332** | **Null** |
| 2 — Incremental | OOS magnitude MAE | **3.6299 vs 3.6284, p = 0.9827** | **Null** |
| 2 — Incremental | Direction | Brier 0.2711 vs 0.2560; AUC 0.4654 | **Null — worse than baseline** |
| 3 — Tradability | Standalone strategy | 0.8543%/event | **Not a GST result** — drift present without the filter |

## 5. Audit results

| Check | Result |
|---|---|
| Independent number-to-source audit | **35/35 verified, 0 discrepancies** |
| Extended committed checker | **PASSED** |
| Claims resolved against artifacts | **120** |
| Distinct numeric tokens accounted | **170** (120 claims + 78 allowlisted) |
| Allowlist shadows a research claim | No |
| Prohibited interpretation matched | No |
| Required disclaimers present | Yes |
| Secondary metric promoted over primary | **No** — p = 0.03707 recorded, not promoted |
| Replication described as having failed its gate | Yes |
| Figures present and unmodified | 3/3 |

## 6. Checker extension

`tools/check_signal_without_strategy_numbers.py` was extended, not replaced:

- audits `SIGNAL_WITHOUT_STRATEGY_MANUSCRIPT_v1.1_DRAFT.md` when present, falling back to v1.0 so
  branches without the revision stay auditable;
- loads the correction overlay and the mechanism-stability CSV as first-class artifacts;
- adds claims for the overlay primary and all three sensitivities, the primary clustered model, the
  superseded Q1 block, and the Appendix A.3 values;
- allowlists only non-research tokens (version string, ISO date parts, abstract word count, the new
  subsection number). No research value was allowlisted — the checker's own anti-shadowing test
  confirms this.

## 7. Open editorial decision

**Figure plan items P1–P3** (`SIGNAL_WITHOUT_STRATEGY_FIGURE_TABLE_PLAN_v1.0.md`) are proposed and
not built. P1 (leave-one-ticker-out forest plot) and P2 (three-estimate panel) are presentation-only,
require no new analysis, and would materially help a reader. **Recommended but not required for
submission.** Existing figures F1–F3 are unchanged and remain correct.

## 8. Not done, deliberately

- No analysis rerun, no specification searched, no new result generated.
- No prospective panel value or HYP-01 outcome inspected.
- No SESOI registered; the abandoned 50-basis-point proposal is untouched.
- No null converted into a positive claim.
- Live collection branch, its scheduled task, and PR #39 untouched.
- v1.0 manuscript, executive summary, and all result artifacts left byte-identical.

## 9. Remaining before submission

1. Co-author review of v1.1, the number audit, and the figure plan.
2. Decide P1/P2/P3.
3. Decide whether the executive summary is revised to match v1.1 — **it currently still reflects
   v1.0** and does not carry the corrected Level-1 result.
4. Target-venue formatting and the anonymised build.
5. Remove `_DRAFT` from the filename only when 1–4 are settled.

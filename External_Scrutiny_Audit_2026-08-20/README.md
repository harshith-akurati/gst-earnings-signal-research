# External scrutiny audit — 2026-08-20

Five read-only reviews produced ahead of external submission. **Nothing in this directory modifies a
result, a frozen rule, a locked pre-registration, the collector, or the manuscript text.** These are
new dated files under the project's append-only convention.

| File | Task | Outcome |
|---|---|---|
| `GST_INCREMENTAL_VALUE_RECONCILIATION_2026-08-20.md` | Reconcile the magnitude-forecast null against the H16 exploratory regression | **Not a contradiction.** They measure different things; H16's GST regressor is contemporaneous with its own outcome window (100% containment, all 125 events). The magnitude forecast is the methodologically stronger design. |
| `SIGNAL_WITHOUT_STRATEGY_CLAIM_AUDIT_2026-08-20.md` | Claim-by-claim provenance audit of the paper | **37 of 37 numeric claims traceable; 11 of 11 declared artifacts present.** Four findings, all provenance-tier or repository hygiene. Highest-value action: merge PR #30 before PR #36. |
| `QUANTUM_KERNEL_SECTION_REVIEW_2026-08-20.md` | Review the Qiskit quantum-kernel work | **No such work exists.** Confirmed by exhaustive search. The only `quantum` matches are assertions that quantum models were *not* used, including a passing test that forbids them. |
| `ROST_T1_COLLECTOR_POSTMORTEM_2026-08-20.md` | Root-cause the T−1 capture failure without new Google requests | **Root cause: query wording.** Throttling, transport failure and pytrends defect all ruled out by an identical-parameter query succeeding 2 seconds later. The defect originates in the frozen query-identity rule. |
| `PROSPECTIVE_COHORT_YIELD_MATH_2026-08-20.md` | Honest accumulation rate for the no-retry two-query design | **22.1 / 10.6 / 4.4 valid events per month** at 10/25/40% i.i.d. per-query failure. But the i.i.d. model is wrong: the real failure mode is deterministic per issuer and produces **selection bias correlated with the study's own predictor**. |

## Two items needing a decision from the author

1. **Merge ordering (paper).** Section 5.4's source artifact lives on the unmerged branch
   `phase2-attention-activity-mismatch`. If a reviewer clones `main`, that section is unverifiable
   until PR #30 merges.
2. **Uncommitted evidence (collector).** As of this writing the two `TRENDS_ATTEMPT` ledger records
   for the ROST T−1 run exist only as an unstaged working-tree change in `gst-aod-worktree`. The T0
   capture is scheduled for 2026-08-20 15:45 ET and appends to the same file.

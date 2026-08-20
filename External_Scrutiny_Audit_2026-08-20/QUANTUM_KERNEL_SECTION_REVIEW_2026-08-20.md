# Quantum-kernel section review

**Date:** 2026-08-20
**Status:** REPORT ONLY. Nothing deleted, moved or modified.

---

## 1. Finding

**There is no Qiskit or quantum-kernel work in this project. It does not exist to review.**

This is a negative finding reached by exhaustive search, not by failing to look. Every search below
was run on 2026-08-20 and returned nothing.

| Search | Scope | Result |
|---|---|---|
| Filename match `*qiskit*`, `*quantum*`, `*qkernel*` | `C:/Users/hakur/Downloads`, `Documents`, `Desktop`, `OneDrive`, `G:/My Drive` | **0 files** |
| Content grep `qiskit` (case-insensitive) | main checkout + submission + synthesis worktrees | **0 hits** |
| `git grep -i qiskit` | across reachable commits on all branches | **0 hits** |
| `pip list \| grep -i qiskit` | active interpreter (Python 3.14.6) | **not installed** |
| Content grep `quantum kernel`, `quantum` | main checkout, all worktrees | see below |
| Manuscript + executive summary | full text | **0 hits** |

There is no quantum section in the paper, no quantum result artifact, no quantum script, and no
quantum dependency.

---

## 2. What the word "quantum" actually matches

Three occurrences exist in the whole repository. **Every one is a negative assertion** — a statement
that quantum methods were *not* used.

**1. Commit `359cf5f`** (search-demand nowcast, `INSUFFICIENT_DATA`), commit message line 49:

> "...networks or quantum models; universe and queries frozen before retrieval and unchanged."

**2. Commit `2b8ff45`** (network-spillover MVP, `DATA_UNAVAILABLE`), commit message line 4:

> "No quantum artifact, universe constant or prospective observation read or modified."

**3. `test_market_response_search_demand_nowcast.py`, line 81** — an executable test that **forbids**
these model families in the nowcast tool:

```python
not any(k in TOOL for k in ("RandomForest", "GradientBoosting", "MLP", "quantum", "Kernel"))
```

A companion guard exists at `test_market_response_semiconductor_surprise_temporal_replication.py:111`.

So the repository does not merely lack quantum work — it has an **automated test asserting that no
quantum or kernel model is used**, and that test currently passes (verified by running the file on
2026-08-20: `ALL SEARCH DEMAND NOWCAST CHECKS PASSED`).

---

## 3. Is it load-bearing for any claim in the paper?

**No.** It cannot be, since it does not exist.

Concretely:

- The manuscript's **Source artifacts** section lists 11 files. None is quantum-related.
- The manuscript's model inventory is Ridge, L2 logistic, a shallow gradient-boosted tree, and OLS
  (see the claim audit, Finding D). No kernel method of any kind.
- The repository's numerical auditor resolves 82 claimed values against committed artifacts and
  accounts for all 139 numeric tokens in the paper. None routes to a quantum artifact.

Removing quantum work from the paper would change nothing, because there is nothing to remove.

---

## 4. Recommendation

**There is nothing to delete and no section to cut.** The recommendation is about description, not
code:

1. **Do not describe this project as involving quantum kernels, Qiskit, or quantum machine learning
   in any external material** — applications, an SSRN abstract, or a CV line. The claim would be
   unsupported by the repository, and a technical reviewer who checked would find not merely an
   absence but a *test forbidding it*. That is a materially worse position than never having
   mentioned it.

2. **If quantum-kernel work exists somewhere outside this machine**, it is not in
   `gst-earnings-signal-research` and would need to be introduced as a separate project with its own
   artifacts before it could be cited.

3. **The absence is a strength, not a gap, for the paper's actual argument.** The manuscript's thesis
   is that method discipline — strong baselines, chronological validation, leakage audits — changes
   conclusions, and that an intercept-only forecast beat a fitted logistic model. Adding an exotic
   kernel method to a paper whose central finding is "the simple baseline won" would weaken it. The
   deliberate model minimalism is on-thesis and should be presented as such.

---

## 5. Note on how this item entered the review queue

This task was posed as "locate the Qiskit quantum-kernel work" — presupposing it exists. It does not.
Recording that plainly here so the question does not get re-asked and so the negative result is itself
part of the append-only record.

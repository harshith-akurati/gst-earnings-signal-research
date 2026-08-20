# Compliance ruling: 1-hop network attention pilot

**Date:** 2026-08-20
**Proposal:** Using an SEC-sourced economic relationship network and a 7,060-row event panel, test
whether high-GST earnings announcements produce different next-day abnormal **volume** at
directly-linked firms than low-GST announcements.
**Ruling:** **MOOT as described** — the artifacts do not exist as characterised — **and BLOCKED on
saturated, underpowered data** even after the description is corrected.

Checked in the required order: provenance before scope, scope before merits. The ruling is reached at
provenance and confirmed at overlap; merits were never the deciding factor.

---

## 1. Provenance — the described artifacts do not exist

| Described | Actually found |
|---|---|
| "SEC-sourced economic relationship network" | `Live Signal Engine/Network_Spillover_Daily/network_relationships_v1.0.csv` — **42 rows**, every row `evidence_status = EXPLORATORY_STATIC`. Hand-specified edges: 3 anchors (NVDA, AMD, INTC), 15 distinct neighbours. Edge types: CUSTOMER_DEMAND 12, EQUIPMENT 9, COMPETITOR 7, NETWORKING 6, SERVER_INTEGRATOR 6, SUPPLIER_FOUNDRY 2. |
| "7,060-row event panel" | **No such artifact exists anywhere.** The event panel is `anchor_earnings_events_v1.0.csv` — **63 rows** (NVDA 21, AMD 21, INTC 21), filing dates 2021-01-14 → 2025-11-19. A search of both network worktrees for `7060` / `7,060` returns nothing. |

**The "SEC-sourced" attribution is misplaced.** SEC sourcing applies to the *anchor events* — 8-K
Item 2.02 filings with CIK and acceptance timestamps — **not** to the relationship edges, which are
static and self-labelled exploratory. There is no SEC-derived economic relationship network in this
repository.

Full directory inventory (`Live Signal Engine/Network_Spillover_Daily/`, branch
`phase2-network-spillover-daily-delay`):

| File | Rows |
|---|---|
| `network_relationships_v1.0.csv` | 42 |
| `anchor_earnings_events_v1.0.csv` | 63 |
| `anchor_event_spillovers_v1.0.csv` | 63 |
| `neighbor_rows_descriptive_v1.0.csv` | 1,512 |
| `daily_prices_v1.0.csv` | 21,335 |

The MVP branch `phase2-network-spillover-mvp` contains only the same 42-row relationship file.

---

## 2. The test has already been run

`NETWORK_SPILLOVER_DAILY_REPORT_v1.0.md` contains a section titled **"Does GST strengthen the
spillover?"** — the proposed comparison, already executed and committed:

| Group | n | Mean | 95% CI |
|---|---|---|---|
| High GST (z ≥ 1.0) | **2** | −0.6878% | [−1.653, +0.278] |
| Low GST | 40 | −0.0522% | [−0.191, +0.086] |

`NETWORK_SPILLOVER_DAILY_RESULTS_v1.0.json` records `gst_high_threshold_z: 1.0`,
`events_with_gst: 42`, `high_gst_events: 2`, `low_gst_events: 40`, with the GST feature defined as a
"strictly pre-event z from weeks closing before the event day". The committed branch result is
**`NO_DAILY_NETWORK_SPILLOVER`**.

**Coverage limit, recorded in the report:** weekly GST exists for **NVDA and INTC only. AMD has
none**, so its 21 events enter the spillover analysis but no GST comparison.

**The high-GST cell contains two events.** No effect size is detectable at that n. Re-running the
same split against a different outcome does not change this.

---

## 3. Overlap with the saturated population

- **2 of 3 anchors** (INTC, NVDA) are tickers inside the canonical 152-event population
  (`Live Signal Engine/FixedWindow_PerEvent_Canonical.csv`, 175 candidate rows, 28 tickers).
- **14 of 63** anchor events fall within ±7 days of a canonical `spike_week` for the same ticker —
  7 NVDA and 7 INTC events, at lags of 2–4 days.

The overlapping portion is squarely subject to the no-new-hypotheses-on-saturated-data rule. The
non-overlapping portion is largely AMD, which has **no GST coverage at all** and therefore cannot
contribute to a GST-split test.

---

## 4. Scope

Two scope findings, neither of which is the binding reason for the ruling:

- **The linked-firm set is not a generated list under `FROZEN_DESIGN_v1.0.md` §2.** It derives
  reproducibly from a committed relationship artifact. §2 governs the *prospective* study's universe
  in any case; this pilot is a separate retrospective study.
- **It would require its own pre-registration.** It is not covered by the prospective study's
  pre-registration, shares neither its universe nor its construct, and could not borrow its gates.

**No timing violation arises.** Running a separate retrospective study does not breach the
prospective study's 75-event analysis gate, which governs only that study's own data. Had provenance
and overlap been clean, the correct route would have been a fresh pre-registration.

---

## 5. Ruling

**BLOCKED.** Grounds, in the order they were reached:

1. **MOOT as described.** The relationship network is 42 static exploratory edges, not an SEC-sourced
   economic network. The 7,060-row panel does not exist; the panel is 63 rows.
2. **Already tested.** The exact high-GST versus low-GST spillover comparison is committed, with a
   published null (`NO_DAILY_NETWORK_SPILLOVER`).
3. **Underpowered past rescue.** The high-GST cell is n = 2. One of three anchors has no GST data.
4. **Overlaps saturated data.** 2 of 3 anchors and 14 of 63 events sit inside the exhausted
   population.

Changing the outcome variable from abnormal return to abnormal **volume** is the one genuinely new
element. It does not cure any of the four grounds. Swapping outcomes on an already-tested 63-event
panel with a 2-event treatment cell, overlapping saturated data, is specification search — and the
prohibition on that is the reason this project's governance exists.

**This ruling is not softened to make the pilot possible.** The honest answer is blocked.

---

## 6. What would make it viable

Recorded so the question is preserved rather than discarded. Both conditions are required:

1. **A real relationship network** — supplier/customer relationships derived reproducibly from a
   documented source (for example 10-K Exhibit 21 subsidiary data, segment disclosures, or a
   licensed relationship dataset), with per-edge provenance, replacing 42 hand-specified
   `EXPLORATORY_STATIC` edges.
2. **Forward data.** Anchor events accumulated after the pre-registration's own commit timestamp,
   with GST coverage verified for every anchor before enrolment — the coverage failure that left AMD
   with no GST must be resolved at enrolment, not discovered afterwards.

Queued in `Live Signal Engine/FUTURE_HYPOTHESES_QUEUE.md` as
**queued-pending-infrastructure**.

---

## 7. Audit note — consistency with prior rulings this session

Fourth ruling on 2026-08-20, same convention:

- **n = 40 rejected as a verdict gate** — §7 pre-commits 75; 40 kept as descriptive-only.
- **Open universe rejected** — §2 prohibits generated ticker lists; official hash-recorded snapshots
  adopted instead.
- **Descriptive census permitted narrowly** — composition only, with outcome comparisons prohibited
  absolutely (`SATURATED_DATA_DESCRIPTIVE_CENSUS_RULING_2026-08-20.md`).
- **This ruling** — blocked at provenance and overlap, preserved as a forward-data question.

The common principle: **claims are checked against files before they are acted on, and an in-force
commitment is never relaxed after seeing what it costs.** Three externally supplied numbers have been
corrected against the files this session — the "~3-4pp" cost floor (Amendment A), the "7,060-row
panel" and "SEC-sourced network" (here).

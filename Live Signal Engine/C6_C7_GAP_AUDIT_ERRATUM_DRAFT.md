# Erratum to `PREREGISTRATION_GAP_AUDIT_v1.0.md` — items C6 and C7

**Date drafted:** 2026-08-26 · **Status:** DRAFT, **uncommitted**, for co-author review.
**Type:** **ADMINISTRATIVE ERRATUM ONLY.**

This erratum records that the register entries for C6 and C7 have not been updated to reflect a
later dated instrument. **It makes no new inference decision.** It does not select an estimator, a
finite-sample correction, a reference distribution, a bootstrap, a cluster-count floor, or a
degrees-of-freedom rule. Every such choice was made — or deliberately left open — by the artifacts
cited below, and this document only points at them.

## 1. What the gap audit currently says

`PREREGISTRATION_GAP_AUDIT_v1.0.md`
(SHA-256 `82885acda38ff51369b2ad47e38442106ce9f0af46ec2e00c2e366e31a1d3dd8`, last modified in commit
`6aefdd2`, 2026-08-09):

- **Line 75 — C6, "Ticker-cluster covariance estimator":** status **UNRESOLVED**, class
  `SCIENTIFIC_DECISION`, established portion "cluster-robust on `ticker`", open portion "the exact
  estimator variant (CR0 / CR1 / CR2 / CR3 or equivalent) is unspecified", severity **Critical**,
  could change significance **yes**, deadline `BEFORE_PREREG_AND_FIRST_OBSERVATION`.
- **Line 76 — C7, "Finite-sample correction and inference procedure":** status **UNRESOLVED**, class
  `SCIENTIFIC_DECISION`, established portion "the flag is enabled", open portion "*which* correction,
  and whether reference-distribution or wild-cluster-bootstrap inference is used, is unspecified; the
  small-cluster problem is real at ~24 clusters", severity **Critical**, could change significance
  **yes**, deadline `BEFORE_PREREG_AND_FIRST_OBSERVATION`.
- **Line 165:** "Three of these — C6, C7 and E3 — could each change whether HYP-01 is reported as
  significant."

## 2. The later dated instrument

`Live Signal Engine/GST_HYP01_ANALYSIS_LOCK_AMENDMENT_2026-08-16.json`
(SHA-256 as checked out on this base:
`e8aa72cabef191ce4136377b33713a34eead9b1e3d891d8a079bfe0cb2ce3895`; LF-normalised SHA-256 as declared
inside the effective-lock report: `11b4df9a6e3321584a617fb2134afae431ac2c84ced193f85279b5bee70b54bd`),
dated **2026-08-16**, authorised **2026-08-16T03:57:18Z** by the project authorizer / repository owner,
statement verbatim: *"I authorize the recommended D1–D16 methodological package as specified on
August 16, 2026."* Resolved form:
`Live Signal Engine/GST_HYP01_EFFECTIVE_LOCK_REPORT_v1.0.json`
(SHA-256 `af5a8c963f14d93787477078ca82a90401e79ed678ad82788a01386722b7d892`).

The amendment's decisions that fall within C6's and C7's subject matter, quoted by JSON pointer:

| Pointer | Value | Bears on |
|---|---|---|
| `/effective_decisions/D1` | `CR2_BIAS_REDUCED_LINEARIZATION` | **C6** — estimator variant |
| `/authoritative_calculation/covariance_call` | `vcovCR(fit, cluster = <ticker factor>, type = "CR2")` | **C6** |
| `/effective_decisions/D2` | `BRL_ADJUSTMENT_BUILT_INTO_CLUBSANDWICH_CR2` | **C7** — finite-sample correction |
| `/effective_decisions/D3` | `COEFFICIENT_SPECIFIC_SATTERTHWAITE` | **C7** — reference distribution |
| `/authoritative_calculation/inference_call` | `coef_test(fit, vcov = <CR2>, test = "Satterthwaite")` | **C7** |
| `/effective_decisions/D4` | `NOT_USED_IN_HYP01` (amendment note: "The wild cluster bootstrap-t plays no role in HYP-01.") | **C7** — bootstrap-versus-reference-distribution question |
| `/effective_decisions/D5`, `/D6`, `/D7` | `NOT_APPLICABLE` | **C7** — remaining bootstrap parameters |

## 3. The administrative defect

**Observed fact.** The amendment JSON, its markdown companion
`GST_HYP01_ANALYSIS_LOCK_AMENDMENT_2026-08-16.md`, and
`GST_HYP01_METHOD_AUTHORIZATION_2026-08-16.md` **never reference the identifiers `C6` or `C7`**.
Verified by identifier-bounded search across all three files. The gap audit has not been re-issued
since 2026-08-09.

**Consequence.** The register still reads UNRESOLVED for two items whose subject matter a later dated,
authorised instrument addresses in full. Nothing is wrong with either artifact taken alone; what is
missing is the cross-reference between them.

## 4. Status recorded by this erratum

| Item | Status |
|---|---|
| **C6** — ticker-cluster covariance estimator | **`SUBSTANTIVELY_RESOLVED`** · **`ADMINISTRATIVELY_OPEN`** |
| **C7** — finite-sample correction and inference procedure | **`SUBSTANTIVELY_RESOLVED`** · **`ADMINISTRATIVELY_OPEN`** |

**`SUBSTANTIVELY_RESOLVED`** means: the scientific content the register entry describes as unspecified
has been specified by the dated instrument in §2, before any eligible HYP-01 outcome existed
(eligible count 0; `analysis_run = false`).

**`ADMINISTRATIVELY_OPEN`** means: the register entry itself has not been closed by an artifact that
names the item, and no artifact yet links the two. Until a co-author issues that link, any downstream
document should cite **both** the gap-audit row and the amendment, and should not describe C6 or C7 as
simply "resolved".

## 5. Scope limits

This erratum:

- makes **no** new inference decision, and selects nothing;
- does **not** modify `PREREGISTRATION_GAP_AUDIT_v1.0.md`, the base lock, the amendment, the effective
  lock report, the registry, or any other artifact — all retain their original bytes and hashes;
- does **not** address **E3** (multiplicity), **E8** (development boundary), **F5** (construct
  validity) or **A9** (design sensitivity), which remain `UNRESOLVED` on their own terms. A9 in
  particular remains **`A9_BLOCKED_MISSING_REGISTERED_SESOI`**;
- does **not** close the cluster-count / effective-df threshold, which remains
  `PLACEHOLDER_PENDING_METHODOLOGIST` per decision D10, whose own rule states that "Any future
  cluster-count or effective-df threshold requires a NEW dated amendment authored without outcome
  inspection";
- does **not** resolve the gap audit's own line-132 recommendation to split the B4 bundle so that the
  statistical rule (C6, C7) is dated earlier than the software option string. That split is still not
  recorded as made in any artifact.

## 6. Action required from a co-author

Issue a dated gap-audit v1.1, or a signed erratum adopting this draft, that:

1. names **C6** and **C7** explicitly;
2. cites `GST_HYP01_ANALYSIS_LOCK_AMENDMENT_2026-08-16.json` and the decisions in §2 above;
3. records the closure date and authorizer;
4. states whether the line-132 B4 bundle split is adopted or declined.

Until then C6 and C7 remain **`ADMINISTRATIVELY_OPEN`** and must be reported as such.

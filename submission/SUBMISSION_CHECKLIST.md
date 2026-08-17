# Submission Checklist — Signal Without Strategy

*Venue-neutral. Fill the venue-specific fields first, then work down. Nothing below is
pre-answered on the owner's behalf.*

Package contents:

| File | Purpose |
|---|---|
| `Signal_Without_Strategy_Submission.pdf` | Identified version, 14 pages |
| `Signal_Without_Strategy_Anonymous.pdf` | Blinded version, 14 pages |
| `build_submission_pdfs.py` | Editable source; rebuilds both PDFs |
| `AUTHOR_INFORMATION_AND_CONTRIBUTIONS_TEMPLATE.md` | Author/contribution fields |
| `SUBMISSION_CHECKLIST.md` | This file |

Rebuild command: `python submission/build_submission_pdfs.py`
(requires `pip install reportlab svglib`)

---

## 1. Venue

| Item | Value |
|---|---|
| Venue name | |
| Track / category | |
| Submission deadline (date, time, timezone) | |
| Submission portal URL | |
| Notification date | |

## 2. Venue requirements — record the rule, then confirm compliance

| Requirement | Venue's rule | Our package | Compliant? |
|---|---|---|---|
| Word limit | | 4,455 words (body, excl. references and tables) | |
| Page limit | | 14 pages incl. references and appendix | |
| Abstract limit | | 231 words | |
| Anonymised review required? | | Anonymous PDF provided | |
| Citation style | | Author–date, alphabetical, numbered list; DOIs/stable URLs as links | |
| Figure rules (count, colour, placement, resolution) | | 3 vector figures, embedded, captioned in place | |
| Table rules | | 8 tables, no vertical rules, header rules only | |
| File format / naming convention | | PDF | |
| Supplementary material allowed? | | | |
| JEL codes required? | | G14, G17, C52, C53 — **proposed, unconfirmed** | |
| Keywords required / count | | 6 provided | |

> **Note.** Word and page counts are *our* measurements under the convention stated in the
> manuscript. Confirm the venue counts the same way (some count references, tables, or captions).

## 3. Anonymisation (if the venue requires blind review)

- [ ] Author line reads `Author information withheld for review`
- [ ] No author name, affiliation, email, or ORCID anywhere in the text
- [ ] No acknowledgments or funding statement that identifies the authors
- [ ] No repository URL, owner handle, or branch name that identifies the authors
- [ ] PDF document metadata carries no author identity
- [ ] Self-citations phrased in the third person
- [ ] Methodological provenance retained (frozen-design protocol, gates, audit) — blinding must
      not remove what a reviewer needs to judge the method

*Verified for this build: the two PDFs differ in exactly the author line; no owner name or email
appears in either.*

## 4. Author and contribution sign-off

- [ ] Every author's name spelled as they want it in print
- [ ] Every affiliation current and correct
- [ ] Corresponding author designated, exactly one
- [ ] ORCIDs added where available
- [ ] Authorship order agreed **by every author**
- [ ] Contribution table completed
- [ ] Every author has read and approved the final version
- [ ] Anyone providing narrower assistance moved to acknowledgments, with their consent
- [ ] Use of automated tools disclosed per venue policy

## 5. Disclosures

- [ ] Funding statement completed (or "no external funding")
- [ ] Conflict-of-interest statement completed (or "none")
- [ ] Holdings in, or relationships with, the named issuers or the data vendor disclosed
- [ ] Data and code availability statement completed
- [ ] Vendor licensing checked before redistributing any earnings data

## 6. Scientific integrity

| Check | Status |
|---|---|
| Numerical audit (`tools/check_signal_without_strategy_numbers.py`) | **PASSED** — 82 claimed values resolved against committed artifacts; all numeric tokens accounted for |
| Empirical artifacts unchanged by packaging | **Confirmed blob-identical** to starting `main` |
| Figures reproducible | Byte-identical across rebuilds |
| Offline test suite | **54/54 passed** |

- [ ] Plagiarism / similarity check run before submission
- [ ] Self-plagiarism reviewed — this synthesis reuses text from the project's own committed
      reports and changelog; confirm the venue's policy on prior public posting
- [ ] Prior-dissemination status declared (the underlying repository is public / private — state
      which)
- [ ] Claims re-read for overstatement: no investable strategy, replication described as failed,
      the significant association not overstated *or* denied
- [ ] Vendor EPS never described as GAAP or SEC-validated
- [ ] Point-in-time estimate provenance still described as not guaranteed

## 7. Final mechanics

- [ ] Correct file(s) uploaded, correct version
- [ ] PDF opens cleanly on a machine other than the author's
- [ ] Hyperlinks clickable in the submitted PDF
- [ ] Cover letter written (if required)
- [ ] Suggested / excluded reviewers entered (if applicable)

## 8. After submission

| Item | Value |
|---|---|
| Date and time submitted | |
| Submission / tracking number | |
| Confirmation email received? (yes / no) | |
| Confirmation archived where | |
| Expected decision date | |

---

## Known items requiring owner input before submission

1. **All author information** — nothing is filled in anywhere.
2. **Venue, deadline, and every venue-specific limit** in §2.
3. **JEL codes are proposed**, not confirmed against a venue's list.
4. **Funding, conflicts, acknowledgments, data availability** — all blank.
5. **Similarity check** has not been run.
6. **PR #30 dependency**: the weekly-volatility source artifact reached `main` through that PR.
   Confirm it is present in whatever snapshot is cited as the paper's data source.

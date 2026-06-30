# Revenue Cycle Claims Analysis — PROJECT PLAN

> A SQL + Excel project that mirrors how a **centralized healthcare revenue cycle analytics team** works: building repeatable, reusable analytical workflows that consultants can rerun across many client engagements, not one-off scripts. Scope is **mid revenue cycle** — charge capture, coding, claim submission, denials, and managed care — surfaced through five core metrics.
>
> This document is the contract for the whole build. Nothing gets coded until it is approved. After approval we execute **one numbered step at a time**, and I stop and wait for "next" after each.

---

## 0. How to read this plan

- Sections 1-8 describe the *what* and *why* (goal, data, workflow, metrics, reusability, techniques, deliverable, structure).
- Section 9 is the **ordered execution checklist** — the steps we actually run, one at a time.
- Section 10 is the pace contract.

---

## 1. Goal — framed as a centralized analytics function

A centralized revenue cycle analytics team is a shared service. Consultants on client engagements come to it and say "I need a denial breakdown for this hospital," or "show me where AR is aging by payer." The team's job is **not** to write a bespoke script for each ask. It is to build a **library of analyses that are parameterized, documented, and rerunnable** so that the *same* denial-rate logic produces a defensible number for client A on Monday and client B on Friday — with only the inputs changing.

So the goal of this project is to demonstrate that I can:

1. Take messy, realistic claims data and turn it into a **trusted analytic layer** (profiled, quality-checked, cleaned, standardized) before computing anything.
2. Define revenue cycle metrics **precisely and consistently**, the way a team would standardize them so every consultant reports the same number the same way.
3. Build the analysis so it is **repeatable and reusable** — parameterized by payer and service line, structured so a teammate could rerun it on a new client's extract without rewriting logic.
4. Deliver in the two tools the role actually uses: **SQL** (the analytic engine) and **Excel** (the consultant-facing deliverable — pivots).

The deliverable is judged less on "did you get a number" and more on **"could someone else trust and reproduce this number, and could you defend every definition cold."**

### How this maps to my background
My data work already follows this arc: exploration → missingness checks → cleaning → variable selection → segmentation → reusable outputs. Revenue cycle is a new *domain* on top of a workflow I already use. The plan deliberately names that parallel at each stage so I can speak to it in the interview: "I do exactly this in my research pipelines — here it is applied to claims."

---

## 2. Dataset design

We use a **synthetic but realistic** claims dataset. Synthetic because real PHI claims can't be shared in an interview portfolio; realistic because we deliberately inject the dirt a real extract has (missing values, inconsistent payer spellings, impossible dates, duplicate claims) so the data-quality stage is genuine, not theater.

Modeled as a small **star schema**: one fact table at the claim grain plus dimension tables. This mirrors how a warehouse-backed analytics team actually receives data and is itself an interview talking point (grain, facts vs. dimensions).

### 2.1 `fact_claims` — one row per claim (the central fact)

| Column | Type | Why it matters for revenue cycle |
|---|---|---|
| `claim_id` | TEXT (PK) | Unique claim identifier. The grain anchor. Duplicates here are a data-quality red flag (double billing / extract error). |
| `patient_id` | TEXT | Links claims to patients. Needed for patient-responsibility and self-pay analysis; also lets us detect rebills of the same encounter. |
| `payer_id` | TEXT (FK) | Which insurer. **The single most important segmentation key** — denial behavior, allowed amounts, and AR aging differ wildly by payer. Managed care analysis lives here. |
| `service_line` | TEXT (FK) | Cardiology, Ortho, ED, etc. Charge capture and coding issues cluster by service line. The second key segmentation axis. |
| `provider_id` | TEXT | Rendering provider. Coding/denial patterns can trace to specific providers (education opportunity). |
| `cpt_code` / `drg_code` | TEXT | Procedure / DRG coding. Ties denials and charge capture to **coding** accuracy. Missing or invalid codes are a charge-capture/coding signal. |
| `date_of_service` | DATE | When care happened. Start of the revenue cycle clock. |
| `date_submitted` | DATE | When the claim was first submitted. `submitted - service` = lag in getting claims out the door (charge capture / coding throughput). |
| `date_paid` | DATE | When payment posted (NULL if unpaid/open). Endpoint for **days in AR**. |
| `charge_amount` | NUMERIC | Gross charge (list price). Denominator-side of markup; the "asking price." |
| `allowed_amount` | NUMERIC | Contractually allowed amount per the payer contract. **Managed care** lives here — charge vs. allowed = contractual adjustment. |
| `paid_amount` | NUMERIC | What the payer actually paid. Numerator for net collection rate. |
| `adjustment_amount` | NUMERIC | Contractual write-offs (charge - allowed) plus other adjustments. |
| `patient_responsibility` | NUMERIC | Copay/coinsurance/deductible owed by patient. |
| `claim_status` | TEXT | Paid / Denied / Open / Partially Paid. Drives denial and AR logic. |
| `denial_flag` | INT (0/1) | Was the claim denied at least once. Numerator for denial rate. |
| `denial_reason_code` | TEXT (FK) | CARC-style reason code when denied (NULL otherwise). Drives denial **reason mix**. |
| `denial_date` | DATE | When denied. |
| `first_pass_flag` | INT (0/1) | Did the claim adjudicate **clean on first submission** (no edits/rejections/rework). Numerator for **clean claim rate**. |
| `rebill_flag` | INT (0/1) | Was this a resubmission of a prior claim. Distinguishes fresh vs. reworked volume. |

### 2.2 Dimension tables

- **`dim_payer`** — `payer_id`, `payer_name`, `payer_type` (Commercial / Medicare / Medicaid / Self-Pay / Other). Lets us roll denial and collection metrics up to payer *type*, the level execs care about, and is where messy payer-name spellings get standardized.
- **`dim_service_line`** — `service_line_id`, `service_line_name`, optional `department_group`. The clinical segmentation axis.
- **`dim_denial_reason`** — `denial_reason_code`, `reason_description`, `reason_category` (Eligibility / Authorization / Coding / Medical Necessity / Timely Filing / Technical-Other). The category rollup is what turns 40 raw codes into a story a consultant can present: "62% of your denied dollars are *preventable* front-end errors."
- **`dim_date`** (optional, light) — calendar helper for month/quarter rollups and aging math. May be replaced by date functions if it adds no value; we'll decide at the grain step.

### 2.3 Intentional dirt (so DQ is real)
We will seed, on purpose: missing `denial_reason_code` on some denied claims, missing `date_paid` on paid claims, payer names spelled inconsistently ("BCBS" / "Blue Cross" / "blue cross blue shield"), a few `date_paid < date_of_service` impossibilities, negative or zero charges, and a handful of duplicate `claim_id`s. Each one maps to a real check in Stage 2.

---

## 3. Analytical workflow (the spine of the project)

Executed in this order. Each stage names (a) what we do, (b) why, (c) how it parallels what a consultant's analyst does on a real engagement, (d) how it maps to my own experience.

### Stage A — Data exploration & profiling
**Do:** Row counts, distinct counts, min/max/ranges on every column, value distributions on categoricals (payer, status, service line), basic shape of charges/payments.
**Why:** You cannot define a metric on data you haven't looked at. Profiling reveals the cardinality, the unexpected categories, the date ranges, the scale of dollars.
**Consulting parallel:** When an engagement lands a new client extract, the first thing the analyst does is "get to know the file" — what's in it, how big, what the columns really contain vs. what the data dictionary claims. You never trust the dictionary blind.
**My-experience parallel:** This is `df.shape`, `df.describe()`, `value_counts()` — the first thing I do on any NHANES/MEPS extract before touching analysis.

### Stage B — Missingness & data-quality checks
**Do:** Per-column null rates; logical-consistency checks (paid claims with no pay date, denied claims with no reason, dates out of order, negative charges, duplicate claim_ids); flag vs. drop decisions.
**Why:** Every downstream metric is only as trustworthy as the fields it's built on. A 30% null rate on `date_paid` would quietly break days-in-AR if unexamined.
**Consulting parallel:** This is the analyst protecting the engagement from an embarrassing wrong number in front of a client. You document data caveats so the consultant can caveat the deck.
**My-experience parallel:** My missingness audits before modeling — null heatmaps, deciding impute vs. complete-case, documenting why.

### Stage C — Cleaning & standardization
**Do:** Standardize payer names to canonical values, normalize code formats, resolve/remove duplicates, decide null-handling per field, build a **clean staging layer (views or a cleaned table)** that all metrics read from.
**Why:** Metrics must be computed on one consistent, blessed version of the data — not re-cleaned ad hoc in every query. This is what makes the whole thing repeatable.
**Consulting parallel:** The team builds a "trusted layer" once so every consultant's pull agrees. Standardizing "BCBS" → "Blue Cross Blue Shield" is exactly the kind of mapping a shared analytics function owns centrally.
**My-experience parallel:** My cleaning/recoding scripts that produce an `analytic_cohort.csv` everything downstream reads — same idea, claims edition.

### Stage D — Define the grain
**Do:** State explicitly: the fact is **one row per claim**; metrics are computed at claim grain then aggregated to payer / service-line / month. Decide how rebills and duplicates affect counts.
**Why:** Ambiguous grain is the #1 source of wrong healthcare metrics. "Denial rate" means nothing until you say denials *per what* — per claim, per line, per dollar.
**Consulting parallel:** Senior analysts pin the grain before computing anything, because a client will ask "is that per claim or per encounter?" and the wrong answer kills credibility.
**My-experience parallel:** Defining the unit of analysis (person vs. person-visit vs. person-year) before any survival or regression work.

### Stage E — Variable & metric selection
**Do:** From the cleaned fields, select exactly which feed each of the five metrics, and write down each metric's precise numerator/denominator and inclusion rules.
**Why:** Forces definitional discipline before computation. Prevents "I'll just SUM something" drift.
**Consulting parallel:** Agreeing the metric definitions *with the engagement* up front so the deliverable isn't relitigated later.
**My-experience parallel:** Choosing exposure/outcome/covariates and pre-specifying them before analysis.

### Stage F — The analysis
**Do:** Compute the five metrics, each as its own parameterized, documented query, then segment by payer and service line.
**Why:** This is the payload — but it's deliberately last, resting on A-E.
**Consulting parallel:** The numbers that go in the client deck — defensible precisely because of everything before them.
**My-experience parallel:** The regression/estimation step at the end of a clean pipeline.

---

## 4. Metrics — definitions and what an interviewer probes

For each: plain meaning, exact formula, and the **probe** an interviewer is likely to push on.

### 4.1 Denial rate
- **Meaning:** Share of claims (or dollars) the payer denied.
- **Formula (claim count):** `denied claims / total claims`. We will also compute **dollar-weighted**: `denied charges / total charges`.
- **Probe:** "Per claim or per dollar?" (they differ — a few big denied claims skew dollars). "Initial vs. final denial rate?" (some denials get overturned on appeal). "Are partial denials counted?" We'll define **initial denial rate, claim-count and dollar-weighted**, and note the final-vs-initial distinction.

### 4.2 Denial reason mix
- **Meaning:** Distribution of *why* claims were denied, rolled to category.
- **Formula:** For denied claims, `count (and denied $) per reason_category / total denied`.
- **Probe:** "Which are *preventable* / front-end (eligibility, auth, coding) vs. payer-driven?" "Are you weighting by count or by dollars?" (a high-frequency low-dollar reason may matter less than a rare high-dollar one). The category rollup is the point — raw CARC codes don't tell a story.

### 4.3 Days in AR (with aging buckets)
- **Meaning:** How long money sits unpaid. Two views: (a) average days to pay for paid claims (`date_paid - date_of_service`); (b) **aging buckets** for still-open claims (0-30 / 31-60 / 61-90 / 90+ days from service to *as-of date*).
- **Formula:** Paid: mean/median of `date_paid - date_of_service`. Open AR: bucket `as_of_date - date_of_service`, report count and $ per bucket.
- **Probe:** "From date of service or date of submission?" (we'll state our choice and why — DOS is the cleaner, more comparable clock). "Mean or median?" (AR is right-skewed; median is often more honest). "How do you handle open vs. paid?" "What's your as-of date?" The 90+ bucket is the danger zone — that's where money goes uncollectible.

### 4.4 Net collection rate
- **Meaning:** Of the money you were *contractually entitled to*, how much did you actually collect. The truest "are we getting paid" metric.
- **Formula:** `paid_amount / allowed_amount` (i.e., payments / (charges − contractual adjustments)). **Not** paid/charges — that's *gross* collection rate and is misleadingly low because charges are inflated list prices.
- **Probe:** "Net vs. gross — which and why?" This is the classic trap. Net uses *allowed*, controlling for the fact that charges are fictional list prices. Getting this right signals you understand managed care contracts. "Over what period — date of service or posting?"

### 4.5 Clean claim rate
- **Meaning:** Share of claims that adjudicate correctly on **first submission** with no edits, rejections, or rework.
- **Formula:** `first_pass_clean claims / total submitted claims`.
- **Probe:** "What counts as 'clean' — never touched, or just not denied?" (clean = no rework at all, stricter than not-denied). "Why does it matter?" (every non-clean claim costs staff time to rework; it's the leading indicator that *predicts* downstream denials and AR aging). It's a **front-end** efficiency metric, distinct from denial rate.

> **Cross-metric story** the interviewer wants to hear: clean claim rate (front-end) → denial rate & reason mix (what's failing) → days in AR (the cash consequence) → net collection rate (the bottom line). Five metrics, one narrative.

---

## 5. Repeatability & reusability

This is the whole reason the role exists, so it's a first-class design goal, not a footnote.

- **Parameterized queries.** Every metric query is written to filter by `:payer_type`, `:service_line`, and `:date_range` as parameters, not hardcoded values. Swap the parameter, get the same metric for a different slice/client.
- **A clean staging layer everything reads from.** Metrics never touch raw tables; they read the blessed cleaned views (Stage C). One place to fix data; all metrics inherit the fix.
- **Consistent metric modules.** Each metric is one self-contained, commented `.sql` file with its definition in a header block, so a teammate can open it, read the definition, and run it.
- **Segmentation that generalizes.** Payer and service line are the two axes that exist at *every* hospital client. Building the analysis around them means the exact same code reruns on a new client's extract — that's the "reusable across engagements" claim made concrete.
- **A driver / README that explains run order.** Someone new can reproduce every number without me in the room.

**Interview line:** "I didn't write five throwaway queries. I built a small analytic layer — clean once, define once, parameterize by the two axes every hospital shares — so the next consultant reruns it on a new client by changing inputs, not logic."

---

## 6. SQL techniques and why

| Technique | Where used | Why |
|---|---|---|
| **DDL / star schema** | Schema build | Models fact-vs-dimension; demonstrates data-modeling literacy. |
| **Views / staging layer** | Cleaning (Stage C) | The reusable "trusted layer"; metrics read views, not raw tables. |
| **CTEs** | Every metric | Readable, stepwise logic instead of nested subqueries — reviewable by a teammate. |
| **Conditional aggregation** (`SUM(CASE WHEN ...)`) | Denial rate, clean claim rate | Numerator/denominator in one pass — the core revenue-cycle SQL pattern. |
| **Date arithmetic** | Days in AR | `date_paid - date_of_service`, bucketing with CASE. |
| **`NULLIF` / null-safe division** | All rates | Avoid divide-by-zero and silent wrong rates. |
| **`GROUP BY` rollups + `GROUPING`/UNION for subtotals** | Segmentation | Payer × service-line breakdowns with totals. |
| **Window functions** (`SUM() OVER`, `RANK`) | Reason mix, AR | Share-of-total and ranking denial reasons without a self-join. |
| **Parameterization** | All metrics | The reusability mechanism (Section 5). |

**Stack:** **SQLite** as the engine (zero-install, single file, ships with Python, runs on any interviewer's machine). SQL is written in portable ANSI style so it lifts cleanly to SQL Server / Snowflake / Postgres — and we'll note the few dialect swaps (e.g., date functions) in comments. This is itself defensible: "I chose SQLite for reproducibility; the logic is warehouse-agnostic."

---

## 7. Excel deliverable

The consultant-facing output. Same five metrics as the SQL, delivered as **pivot tables** off a clean export.

- **Export:** the cleaned claim-grain table (and small pre-aggregated tables) to CSV/XLSX from SQL.
- **Pivots, one per metric:**
  1. Denial rate by payer type (rows) × service line (columns), count- and dollar-weighted.
  2. Denial reason mix — reason category by denied count and denied $, with % of total.
  3. Days in AR — aging buckets by payer, count and $.
  4. Net collection rate by payer type and service line.
  5. Clean claim rate by service line and payer.
- **A summary tab** with the headline numbers and the cross-metric narrative.
- **Why Excel too:** consultants live in Excel; the analytics team hands off pivots a consultant can re-slice live in a client meeting. Showing the *same* numbers reconcile between SQL and Excel is the credibility proof.

---

## 8. Project structure

```
Projects/revenue-cycle-sql/
├── PLAN.md                      # this file
├── PROGRESS.md                  # running log: each step, decision, role-map, what I learned
├── README.md                    # how to reproduce, run order, metric definitions
├── data/
│   ├── raw/                     # generated dirty synthetic data (CSV)
│   └── clean/                   # exports of the cleaned/blessed layer
├── sql/
│   ├── 00_schema.sql            # DDL: fact + dimensions
│   ├── 01_load.sql              # load raw CSVs
│   ├── 02_profile.sql          # Stage A exploration/profiling queries
│   ├── 03_quality_checks.sql    # Stage B missingness & DQ checks
│   ├── 04_clean_views.sql       # Stage C cleaned/standardized staging layer
│   ├── metrics/
│   │   ├── denial_rate.sql
│   │   ├── denial_reason_mix.sql
│   │   ├── days_in_ar.sql
│   │   ├── net_collection_rate.sql
│   │   └── clean_claim_rate.sql
│   └── 99_segmentation.sql      # parameterized payer × service-line rollups
├── scripts/
│   └── generate_data.py         # synthetic data generator (with seeded dirt)
└── excel/
    └── revenue_cycle_pivots.xlsx  # the consultant deliverable
```

---

## 9. Execution checklist (one step at a time)

We run these **in order, one per turn**. For each, I'll explain what/why/decisions/interviewer-probe *before* doing it, do only that step, show the result, update PROGRESS.md, and stop for "next."

1. **Scaffold the project** — create the folder tree and stub files (PROGRESS.md, README.md). Confirm stack choice (SQLite).
2. **Design & write the schema** (`00_schema.sql`) — fact + dimension DDL, documented. Decide grain on paper here, lock it in Step 7.
3. **Build the synthetic data generator** (`generate_data.py`) — realistic claims + dimensions, with intentional dirt seeded. Generate `data/raw/`.
4. **Load the data** (`01_load.sql`) — create the DB, load raw CSVs, confirm row counts.
5. **Stage A — Exploration & profiling** (`02_profile.sql`) — shapes, ranges, distributions.
6. **Stage B — Missingness & data-quality checks** (`03_quality_checks.sql`) — null rates, logical-consistency checks, document caveats.
7. **Stage C — Cleaning & standardization** (`04_clean_views.sql`) — canonical payer names, dedupe, null-handling, build the blessed staging views. **Lock the grain.**
8. **Stage D/E — Grain statement & variable/metric selection** — written into PROGRESS.md/README: grain, and each metric's exact numerator/denominator/inclusions.
9. **Metric 1 — Denial rate** — count- and dollar-weighted, parameterized.
10. **Metric 2 — Denial reason mix** — category rollup, count- and dollar-weighted, share-of-total.
11. **Metric 3 — Days in AR + aging buckets** — paid-claim days + open-AR buckets, as-of date defined.
12. **Metric 4 — Net collection rate** — paid/allowed, with the gross-vs-net discussion.
13. **Metric 5 — Clean claim rate** — first-pass-clean definition.
14. **Segmentation layer** (`99_segmentation.sql`) — payer × service-line, parameterized, the reusability proof.
15. **Export clean + aggregated tables** to `data/clean/` and `excel/` source.
16. **Build the Excel pivots** — five pivots + summary tab; reconcile to SQL.
17. **Write the README** — run order, metric definitions, how a teammate reruns it.
18. **Interview-prep wrap-up** — consolidate the probes/answers and the cross-metric narrative in PROGRESS.md.

---

## 10. Pace contract

- One step at a time, in the order above.
- Before each step: explain what we're doing, why, every decision and its nuance, how it mirrors the role, and what an interviewer would probe.
- Then do **only that step**, show the result, update PROGRESS.md, and **wait for "next."**
- No running ahead, no batching.
- Goal is understanding deep enough to defend the project cold — not speed.

---

**STOP — awaiting your approval of this plan before any code is written.**

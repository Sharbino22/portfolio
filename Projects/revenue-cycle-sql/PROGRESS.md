# PROGRESS LOG — Revenue Cycle Claims Analysis

> Running record of each step: what we did, the decision behind it, how it maps to the role and to my own data experience, and what I learned. Built one step at a time. See [PLAN.md](PLAN.md) for the full design.

**Stack:** SQLite (engine) + portable ANSI SQL + Python (synthetic data) + Excel (pivots).

---

## Step 1 — Scaffold the project ✅

**What we did:** Created the directory tree (`data/raw`, `data/clean`, `sql`, `sql/metrics`, `scripts`, `excel`) and stub files (this PROGRESS.md, README.md). Locked the stack to SQLite.

**Decision & nuance:**
- Folder layout follows the analytical workflow so file order = run order (profile → quality → clean → metrics → segmentation). The structure itself is part of the deliverable — it signals the work was built to be rerun by someone other than me.
- SQLite chosen for zero-install reproducibility (ships with Python); SQL kept portable so it lifts to SQL Server / Snowflake / Postgres with only date-function swaps.

**How it maps to the role:** A centralized analytics team's output is only reusable if its structure is predictable. A teammate should know where the schema, cleaning layer, and each metric live without asking. Predictable structure > clever one-off script.

**How it maps to my experience:** Same discipline as my research repos — a fixed layout (raw → clean → analysis) so any reader can reproduce the pipeline.

**Interviewer probe rehearsed:** "How does someone else rerun this?" → the structure answers it. "Why SQLite?" → reproducibility; logic is warehouse-agnostic.

**What I learned:** The deliverable starts before the data — a legible structure is itself a credibility signal in a shared-analytics role.

---

## Step 2 — Design & write the schema ✅

**What we did:** Wrote `sql/00_schema.sql` — a star schema with fact `claims_raw` (21 cols) + `dim_payer`, `dim_service_line`, `dim_denial_reason`. Validated it builds in SQLite. Pure DDL; no data.

**Decisions & nuance:**
- **Grain locked = one row per claim (header), not line or encounter.** Stated in the file header. This is the decision every metric depends on; "denial rate per *what*" is answered by the schema, not improvised later.
- **Permissive landing table.** `claims_raw` has NO primary key on `claim_id`, few NOT NULLs, NUMERIC amounts (negatives allowed), dates as TEXT. Reason: we intentionally seed dirt (dup ids, missing pay dates, impossible dates). Constraints here would reject those rows and gut the data-quality stage. Constraints/standardization live in the clean layer (Step 7). Pattern: *land permissively, enforce on the trusted layer.*
- **Dimensions are constrained** (real PKs) — clean reference data, like a shared team's canonical lookups.
- **Three deliberate join patterns:** `payer_name_raw` (messy free text → crosswalk), `service_line` (clean name → direct lookup), `denial_reason_code` (coded → category rollup). Each teaches a different cleaning/join skill.
- **SQLite specifics encoded & defensible:** dates as ISO-8601 TEXT (no native date type; sorts correctly); money NUMERIC with a DECIMAL/floating-point caveat; FKs declared but only enforced under `PRAGMA foreign_keys = ON` (off by default).
- **DDL kept separate from DML** (load happens in `01_load.sql`) — warehouse convention.

**How it maps to the role:** Modeling the extract as fact + dimensions is exactly how a warehouse-backed analytics team receives and structures client data so metrics join and roll up consistently across engagements.

**How it maps to my experience:** Same as defining the unit of analysis (person vs. person-visit vs. person-year) before any modeling — pin the grain first.

**Interviewer probes rehearsed:** "Per claim or per line?" (schema-locked grain). "Why no PK on claim_id?" (permissive landing so dirt is detectable). "Net vs gross handled where?" (allowed_amount field present for net collection). "How are dates typed in SQLite?" (ISO TEXT).

**What I learned:** The landing-zone-vs-trusted-layer split is the real-world reason you *don't* over-constrain raw tables — looseness is what makes data-quality work possible and visible.

---

## Step 3 — Build the synthetic data generator ✅

**What we did:** Wrote `scripts/generate_data.py` (seeded, reproducible) and generated four CSVs in `data/raw/`: the three dimensions + `claims_raw` (5,025 rows = 5,000 unique claims + 25 duplicate rows). Created a project-local `.venv` (no scientific Python on the machine), `requirements.txt`, and `.gitignore`.

**Decisions & nuance:**
- **Reproducibility via `numpy` seed = 42** + a project venv + `requirements.txt`. Directly backs the "a teammate reruns it and gets the same numbers" claim.
- **Realistic economics drive the metrics, not random noise:** `allowed = charge × payer-type contract factor` (Commercial 0.55 / Medicare 0.35 / Medicaid 0.28). Result: **gross collection 45.3% vs net 91.0%** — the gross-vs-net trap appears naturally. Denial propensity, pay lag, contract factor all vary by payer type so segmentation reveals real patterns.
- **Denial reasons weighted toward preventable front-end causes** (Auth/Eligibility/Coding) so the category rollup tells a story.
- **Dirt seeded controllably and the ground-truth counts are printed** so Stage B detection is validated against truth: 116 missing pay dates on paid, 30 denied-without-reason, 15 impossible dates, 10 non-positive charges, 25 dup rows. Payer-spelling messiness is pervasive by construction — **28 raw spellings collapse to 7 canonical payers.**
- **Status mix realistic:** 69% Paid, 12.2% Denied, 10% Open, 8% Partially Paid.

**How it maps to the role:** Analytics teams build synthetic/de-identified test data to develop and unit-test analyses before a real client extract lands. Controlling the data-generating process also enables a real validation technique: reconcile computed metrics back to construction parameters.

**How it maps to my experience:** Same as simulating data with known parameters to test an estimator before running it on real survey data.

**Interviewer probes rehearsed:** "How do you know the denial rate is right?" → reconcile against the known generating process. "Why net vs gross?" → the 45% vs 91% gap is the contractual adjustment; charges are inflated list prices.

**What I learned:** Building data with the *right relationships* (not just random fills) is what makes a metrics demo defensible — and the printed ground-truth dirt counts turn Stage B into a real, checkable test rather than a narrated formality.

**Snag handled:** numpy 2.5 / pandas 3.0 rejected a `datetime64` array init; switched those two columns to object lists (filled in-loop, ISO-formatted at the end).

---

## Step 4 — Load the data ✅

**What we did:** Wrote `sql/01_load.sql`, built `revenue_cycle.db` (`00_schema.sql` then `01_load.sql`), loaded all four CSVs, normalized empty-string→NULL, and verified. All counts reconcile to ground truth: 7/8/9 dim rows; 5,025 claim rows with 5,000 distinct ids (25 dups landed); denied-missing-reason 30, paid-missing-paydate 116, non-positive charge 10 — exact matches.

**Decisions & nuance:**
- **Loading is engine-specific.** Used SQLite `.import` (by column position; `--skip 1` for the header) and commented the warehouse equivalents (Snowflake `COPY INTO`, SQL Server `BULK INSERT`/BCP, Postgres `COPY`). Only this file is SQLite-flavored; downstream SQL stays portable.
- **One load-time normalization, deliberately bounded: `''`→NULL** on nullable columns only. Framed as *technical* (CSV can't encode NULL) vs *semantic* cleaning (payer standardization, dedup), which waits for Stage C. Keeps the trusted layer the single source of truth.
- **Verification is part of the load**, not an afterthought — row counts + dirt spot-checks reconciled to the generator's printed truth.

**How it maps to the role:** Post-load reconciliation (row counts, null spot-checks) is standard practice; silent truncation is a real failure mode an analytics team guards against on every client extract.

**How it maps to my experience:** Same as verifying `nrow`/`shape` and key distributions immediately after importing a raw survey extract, before trusting anything.

**Interviewer probes rehearsed:** "Isn't null-handling cleaning?" → encoding-level (`''`→NULL) vs meaning-level standardization are different stages. "How would this load on a real warehouse?" → COPY INTO / BULK INSERT; the analysis SQL is unchanged.

**What I learned:** Separating technical encoding fixes from semantic cleaning keeps stage boundaries honest — and verifying the load against known ground truth is what turns "it ran" into "it's correct."

---

## Step 5 — Stage A: Exploration & profiling ✅

**What we did:** Wrote `sql/02_profile.sql` (7 read-only queries: status mix, raw payer spellings, service-line mix, denial-reason distribution, numeric profiling of money columns, date spans, key cardinality) and ran it. Also: first deep SQL-reading walkthrough.

**SQL-reading skill started — the core mental model:** read queries in EXECUTION order, not written order: `FROM → WHERE → GROUP BY → SELECT → ORDER BY`. After GROUP BY you know what one output row represents; SELECT is just "what to show per group." Rule: every SELECT column is either in the GROUP BY or wrapped in an aggregate.
- **Scalar subquery** `(SELECT COUNT(*) FROM claims_raw)` for a denominator; `*100.0` forces float division (integer `/` truncates — classic trap).
- **LEFT JOIN vs INNER:** LEFT keeps unmatched left rows (right cols → NULL). Profiling A4's NULL-category row (30 denied-without-reason) only appears because of LEFT JOIN; INNER would silently hide the DQ problem. Default to LEFT when profiling.
- **Conditional aggregation** `SUM(CASE WHEN cond THEN 1 ELSE 0 END)` = a filtered count in one pass — the workhorse for every metric (denial rate = SUM(flag)/COUNT(*)).
- **UNION ALL** stacks per-column profiling rows into one tidy table (keeps dups, faster than UNION).

**What the data revealed (analyst's read):**
- 28 payer spellings for 7 payers, spread evenly → any payer metric is wrong without Stage C standardization. This IS the cleaning case.
- charge_amount min −250 → impossible values confirmed; allowed/paid non-positives (613/1,137) are STRUCTURAL zeros (denied allowed=0; denied+open paid=0), not errors. "Impossible vs structurally-zero" is the judgment Stage B formalizes.
- date_paid null 1,253 (open + missing); denial_date null 4,412 (≈ non-denied) — both expected.
- 5,000 distinct claim_ids in 5,025 rows confirms claim grain + 25 dups; 2,499 patients → ~2 claims each (expected fan-out).

**How it maps to the role:** First thing on a new client extract — interrogate the file, never trust the dictionary blind. Profiling sets up every later decision.

**How it maps to my experience:** `df.describe()`, `value_counts()`, null scans before any modeling.

**Interviewer probes rehearsed:** "Why LEFT not INNER here?" (don't hide missingness). "Why `*100.0`?" (avoid integer-division truncation). "Are those zero allowed amounts errors?" (no — structural, denied claims).

**What I learned:** Reading SQL = reading it in execution order. And profiling's job is to separate *expected* structure (zeros, nulls by status) from *real* problems (negative charges, split spellings) before cleaning.

---

## Step 6 — Stage B: Missingness & data-quality checks ✅

**What we did:** Wrote `sql/03_quality_checks.sql` — missingness profile (B1), a reconciliation SCORECARD of seeded defects (B2), duplicate detail (B3), and a battery of un-seeded integrity checks (B4). Ran it; all seeded checks reconcile to ground truth: duplicate_claim_ids 25, paid_missing_paydate 116, denied_missing_reason 30, paid_before_service 15, nonpositive_charge 10.

**Core judgment of the stage — structural vs problematic missingness:** a null is neutral until read against status/grain. denial_date 87.8% null = structural (non-denied). drg_code 60.3% = structural (DRG ~40% of claims). date_paid 24.9% = MIXED (Open=structural + 116 Paid-with-no-paydate=defect). denial_reason_code 88.4% = mostly structural + 30 denied-without-reason defect.

**Un-seeded finding traced to root cause (real analyst work):** B4 flagged allowed_exceeds_charge = 12. Investigation: NOT a new defect — 6 are the already-known negative-charge rows (positive allowed trivially exceeds a negative charge → same rows as nonpositive_charge), 6 are self-pay edge cases from the generator's contract assumption. Lesson: one root defect trips multiple checks; decompose before logging N "new" problems.

**New SQL taught:**
- **HAVING vs WHERE:** WHERE filters rows before grouping (no aggregates allowed); HAVING filters groups after aggregation. Duplicate detection (`GROUP BY claim_id HAVING COUNT(*)>1`) is the canonical HAVING case.
- **Scorecard pattern:** UNION ALL rows of `(check_name, n_flagged, expected)` — placing expected next to computed turns "I ran checks" into "each check is proven correct." Interview-grade.

**Documented defect list -> Stage C:** standardize 28 payer spellings → 7 canonical; drop/flag 25 dup rows; quarantine 10 non-positive charges + 15 impossible pay dates; flag 30 denied-no-reason and 116 paid-no-paydate as untrustworthy for dependent metrics.

**How it maps to the role:** This stage protects the engagement — produces a documented defect inventory and caveats, not a fix. The consultant caveats the deck from it.

**How it maps to my experience:** Null heatmaps + logical-consistency checks before modeling; deciding impute/flag/drop per field with a documented rationale.

**Interviewer probes rehearsed:** "Is 88% null on denial_date a problem?" (no — structural). "A check fired 12 — what do you do?" (trace root cause; decompose to known causes). "WHERE or HAVING for dups?" (HAVING — it's a group property).

**What I learned:** The output of data quality is a documented, reconciled defect list — and the real skill is interpreting each null against context and decomposing fired checks to root cause rather than inflating the problem count.

---

## Step 7 — Stage C: Cleaning & standardization (keystone) ✅

**What we did:** Wrote `sql/04_clean_views.sql` — the trusted layer as views: `v_params` (centralized as_of_date), `v_claims_clean` (standardized + de-duplicated + derived + flagged), `v_claims_analytic` (metric-ready subset). Verified: 5,000 rows / 5,000 distinct (dedup worked); 28 spellings → 7 canonical payers, zero UNKNOWN (BCBS largest at 1,125); 25 hard-corrupt rows quarantined → 4,975 metric-ready; soft missingness retained (115 paid-missing-date, 30 denied-missing-reason kept in analytic layer).

**Design decisions (all interview points):**
- **Views, not a copied table** — saved query, computed on read, cannot drift from definition = ideal "single source of truth." Warehouse alt: materialize (dbt model/table) for speed.
- **Two layers:** `v_claims_clean` (everything, flagged, nothing hidden) + `v_claims_analytic` (WHERE include_in_metrics=1). Metrics read analytic; audit reads clean.
- **Quarantine ≠ delete.** Hard corruption (charge<=0; date_paid<date_of_service) → gated out but retained+flagged. Soft missingness (missing pay date/reason) → KEPT; only specific metrics affected, handled per-metric. Dropping a whole claim for one unused-by-most field would bias other metrics.
- **Payer standardization via normalized pattern rules** (UPPER+TRIM + CASE/LIKE → canonical payer_id, UNKNOWN fallback). Generalizes to a new client's unseen spellings = the reusability story. Tradeoff vs explicit crosswalk table (more auditable, brittle to new spellings) noted.
- **Centralized `as_of_date` in v_params** — change once, all aging follows.
- **COALESCE(reason_category, 'Unknown')** for denied-missing-code so reason mix still sums to 100%.
- **Derived columns precomputed once** (days_to_pay, days_outstanding, service_month, DQ flags) → every metric is a short query, all reconciling via the shared source.

**SQL taught — window functions:** `ROW_NUMBER() OVER (PARTITION BY claim_id ORDER BY rowid)` then `WHERE rn=1` to dedup. Read as: number rows, restart per claim_id, deterministic order. KEY distinction: **GROUP BY summarizes (collapses + forces aggregates); window functions annotate-then-filter (keep all rows/columns).** Use window+filter to PICK rows (dedup, latest-per-patient, top-N-per-group). Also COALESCE = first non-NULL.

**How it maps to the role:** This IS why a centralized function exists — clean once so every consultant's number reconciles. Standardization + a documented quarantine policy is the shared team's core deliverable.

**How it maps to my experience:** Building the single `analytic_cohort.csv` everything downstream reads; deciding flag-vs-drop per field with documented rationale instead of silent deletion.

**Interviewer probes rehearsed:** "GROUP BY or window to dedup?" (window — keep rows). "Why not drop the missing-paydate claims?" (soft defect; still valid for other metrics). "What if a new payer spelling appears?" (pattern rules generalize; UNKNOWN surfaces it). "Views or tables?" (views can't drift; materialize for speed).

**What I learned:** The trusted layer is the contract — clean once, derive once, quarantine (don't delete), and every metric becomes a short, mutually-reconciling query on top.

---

## Step 8 — Stage D/E: Grain statement & metric selection ✅

**What we did:** No new SQL. Wrote the authoritative metric dictionary `METRIC_DEFINITIONS.md` (grain + exact numerator/denominator/inclusion for all five metrics + each interviewer probe and our answer + named extensions). Linked it from README.

**Locked decisions:**
- **Grain:** one row per claim; base = `v_claims_analytic` = 4,975 (5,000 distinct − 25 quarantined). Rebills not collapsed → denial rate is initial/record-level (named limitation).
- **Denial rate:** count- AND dollar-weighted (dollar uses charge, since denied→allowed=0); initial not final; partials ≠ denials.
- **Reason mix:** denied base; per-category count & $; preventable = Auth+Eligibility+Coding; `Unknown` bucket keeps mix at 100%.
- **Days in AR:** clock from date_of_service (comparable, not gameable); median+mean (skew); paid throughput vs open aging separated; buckets 0-30/31-60/61-90/90+; as_of from v_params.
- **Net collection:** paid/allowed (NOT paid/charge); gross shown only as the contrast that exposes the inflated-charge trap (~45% vs ~91%).
- **Clean claim rate:** first_pass_flag/submitted; clean = no rework (stricter than not-denied); upstream leading indicator.

**How it maps to the role:** A centralized team maintains a metric dictionary so every consultant's "denial rate" is the same number computed the same way. Agreeing definitions up front prevents relitigating the deliverable in front of the client.

**How it maps to my experience:** Pre-specifying exposure/outcome/covariates and their exact operational definitions before running any model.

**Interviewer probes rehearsed:** captured inline per metric in METRIC_DEFINITIONS.md (per-claim vs per-dollar; initial vs final; net vs gross; mean vs median; service vs submission date; clean vs not-denied).

**What I learned:** Writing the definitions BEFORE the SQL is what makes the numbers defensible — the dictionary, not the query, is the source of truth a metric must conform to.

---

## Step 9 — Metric 1: Denial rate ✅

**What we did:** Wrote `sql/metrics/denial_rate.sql` — parameterized base + overall, by-payer-type, by-service-line cuts (count & dollar weighted). Ran it; proved the parameterization separately.

**Results (reconcile to the generating process):**
- Overall 12.2% count / 12.3% dollar (609 denied / 4,975; 4 denied quarantined vs raw 613).
- By payer type: Medicaid 18.6% > Commercial 12.9% > Self-Pay 7.9% ≈ Medicare 7.5% — matches encoded DENIAL_PROB ordering exactly. Metric recovers ground truth = validation.
- By service line: flat 10–14%, NO strong concentration — honest null finding (denial driven by payer, not service line). Report the null, don't invent a story.
- Self-Pay dollar (6.1%) < count (7.9%): denied self-pay claims skew smaller-dollar — why both weightings are reported.
- Parameterization proof: `p_payer_type='Medicaid'` → 555/103/18.6%, identical to the segment cut.

**SQL taught:**
- **Rate pattern:** `100.0 * SUM(denial_flag) / NULLIF(COUNT(*),0)` — SUM of a 0/1 flag = count of 1s; the workhorse for every rate. NULLIF guards an empty slice.
- **Null-guard parameterization:** `flt` CTE + `(:param IS NULL OR col = :param)` = "unset → don't filter, else filter." One query, any slice; rerun on a new client by editing only the flt CTE.

**How it maps to the role:** Write the analysis once with parameters; consultants point it at any payer/service-line/period without touching logic. Reporting count AND dollar (and the null service-line finding) is the kind of defensible, honest output the team standardizes.

**How it maps to my experience:** Recovering known simulation parameters as an estimator check; reporting a null result rather than over-fitting a narrative.

**Interviewer probes rehearsed:** "Count or dollar?" (both; they diverge for Self-Pay). "Where do denials concentrate?" (payer, not service line — show the flat cut). "How do you reuse this for another client?" (edit flt CTE; null-guard pattern).

**What I learned:** A metric that recovers the ground-truth generating process is validated; and the null-guard CTE turns a single query into a reusable, slice-able analysis.

---

## Step 10 — Metric 2: Denial reason mix ✅

**What we did:** Wrote `sql/metrics/denial_reason_mix.sql` — category mix (count & dollar share), granular code detail, and the preventable-vs-payer-driven rollup. Ran it.

**Results (the "so what" of denials):**
- Top categories: Coding 22.7%, Authorization 20.0%, Eligibility 17.6%.
- HEADLINE: 60.3% of denials / 60.5% of denied dollars are PREVENTABLE front-end errors (Auth+Eligibility+Coding). Payer-driven/Other 34.8%; Unknown 4.9% (the 30 missing-code claims, visible not hidden; mix sums to 100%).
- Count vs dollar mostly agree, but Authorization (20.0% count / 21.0% $) and Timely Filing (6.4% / 8.0%) skew larger-dollar → a recovery-dollar prioritization differs from a count one. This is why both weightings are required.

**SQL taught — share-of-total via window:** `SUM(COUNT(*)) OVER ()` = total of per-group counts (window runs AFTER group-by, sees all groups) → percentage denominator with no extra table scan. `SUM(SUM(charge)) OVER ()` is the dollar analogue. Read: inner aggregate = per group; windowed outer SUM(...) OVER () = across all groups. Cleaner than the scalar-subquery denominator used in profiling.

**How it maps to the role:** The category rollup converts raw CARC codes into an actionable client story ("60% preventable"). That translation — codes → category → actionability → one sentence — is the consulting deliverable.

**How it maps to my experience:** Collapsing many raw codes/categories into an interpretable grouping with shares, and reporting both count and magnitude weightings.

**Interviewer probes rehearsed:** "How much is preventable?" (60%, by count and dollars). "Count or dollar weighted?" (both; Auth/Timely skew larger-dollar). "What about missing reason codes?" (explicit Unknown bucket, 4.9%).

**What I learned:** The window share-of-total is the clean idiom for distribution metrics, and the actionability rollup (preventable vs payer-driven) is what makes a denial analysis decision-grade rather than descriptive.

---

## Step 11 — Metric 3: Days in AR + aging buckets ✅

**What we did:** Wrote `sql/metrics/days_in_ar.sql` — Part A paid throughput (overall + by-payer mean & median) and Part B open-AR aging (buckets overall + payer pivot). Ran it.

**Results (reconcile to generating process):**
- Throughput overall mean 39.0 / median 35.0 → mean>median confirms right skew (why median is reported); max 158 (slow tail).
- By payer: Self-Pay 56 > Medicaid 52 > Commercial 38 > Medicare 31 — matches encoded PAY_LAG_MEAN ordering; mean>median in every segment.
- Aging headline: 90+ bucket = 397/521 open claims and 78.5% of open dollars ($1.78M) = the danger-zone red flag. (Caveat: synthetic AR skews old by construction; method/presentation is the point.)
- Pivot: Commercial largest open balance $1.48M ($1.15M in 90+).

**SQL taught:**
- **Median by hand** (SQLite has no MEDIAN/PERCENTILE_CONT): `ROW_NUMBER() OVER(ORDER BY x)` + `COUNT(*) OVER()` then `WHERE rn IN ((cnt+1)/2,(cnt+2)/2)` — odd→1 middle row, even→2 averaged. By-group adds PARTITION BY. Snowflake/Postgres = one-word MEDIAN()/PERCENTILE_CONT.
- **CASE bucketing** with a parallel bucket_sort key for correct (non-alphabetical) ordering.
- **First pivot:** `SUM(CASE WHEN bucket='90+' THEN charge END)` turns row VALUES into COLUMNS — the bridge to the Excel deliverable.

**How it maps to the role:** Splitting throughput (speed, closed claims) from aging (risk, open claims) is what "days in AR" really means; collapsing both into one average hides the 90+ risk. The aging pivot is the CFO-facing artifact.

**How it maps to my experience:** Choosing median over mean for skewed distributions; building age/time bins; presenting distributions as readable tables.

**Interviewer probes rehearsed:** "Mean or median?" (both, lead median — skew). "From service or submission?" (service — comparable). "How'd you get median in SQLite?" (rank + middle ordinal). "What's the risk?" (78.5% in 90+).

**What I learned:** Days in AR is two metrics, not one; median needs hand-building in SQLite via ranking; and conditional-aggregation pivots are how SQL output takes the shape Excel wants.

---

## Step 12 — Metric 4: Net collection rate ✅

**What we did:** Wrote `sql/metrics/net_collection_rate.sql` — net (paid/allowed) vs gross (paid/charge), overall + by payer type (with contract_ratio) + by service line. Ran it.

**Results (the marquee teaching table):**
- Overall: net 91.0% vs gross 45.1%.
- By payer NET is FLAT ~91% (Commercial 91.1, Self-Pay 90.8, Medicare 90.8, Medicaid 90.7) = uniform collection PERFORMANCE.
- By payer GROSS swings 25–82% (Medicaid 25.4 → Self-Pay 81.7) = contaminated by CONTRACT rate. contract_ratio (55.1/89.9/35.0/28.1) reproduces encoded CONTRACT_FACTOR exactly.
- Punchline: reporting gross-by-payer would say "you only collect 25% from Medicaid" — wrong; they collect 91% of Medicaid ALLOWED; 25% is the contractual discount. Net separates performance from contract terms; gross conflates them.
- Service line net flat 90–93% (null cut).

**Base decision (interview-grade):** adjudicated only (Paid/Partially Paid, allowed>0). Denied excluded (allowed=0). OPEN EXCLUDED — they have allowed>0 but paid=0 only because not-yet-paid, not underpaid; including them would falsely depress net.

**SQL:** no new syntax — rate pattern + NULLIF guards. The difficulty here is DEFINITIONAL (right denominator, right base), not syntactic. By design: patterns now repeat, analytical judgment is the demonstration.

**How it maps to the role:** Net vs gross is the managed-care literacy test. Choosing allowed (not charge) as denominator, and excluding open/denied correctly, is what makes the number trustworthy for a client.

**How it maps to my experience:** Picking the correct denominator/population for a rate (e.g., person-time vs persons) so the estimate answers the actual question.

**Interviewer probes rehearsed:** "Net or gross, and why?" (net — charges are inflated list prices). "Why exclude open claims?" (unpaid ≠ underpaid). "Why is gross-by-payer misleading?" (it's contract rate, not performance). "Are patient payments in paid_amount?" (yes — total payments).

**What I learned:** The hardest part of a metric is often the definition, not the SQL — net collection's value comes entirely from denominator choice and base selection, and the net-flat / gross-variable contrast is the clearest proof that gross conflates contract terms with collection performance.

---

## Step 13 — Metric 5: Clean claim rate (+ narrative close) ✅  — ALL 5 METRICS DONE

**What we did:** Wrote `sql/metrics/clean_claim_rate.sql` — overall + by payer + by service line + Q4 (denial rate among clean vs non-clean). Ran it.

**Results:**
- Overall clean claim rate 83.8% (4,170/4,975).
- By payer: inverse to denial rate (Self-Pay 87.9, Medicare 87.1 high; Medicaid 80.0 low). Service line flat 81–85%.
- Q4 PUNCHLINE: clean claims deny at 3.9%, non-clean at 55.7% → a reworked claim is ~14× more likely to be denied. Proves clean claim rate is a leading indicator of denials (matches Bayes from generator params).

**Cross-metric narrative (numbers, not assertion):** clean rate 83.8% → 16% reworked deny at 55.7% → denial rate 12.2% (~60% preventable front-end) → 78.5% of open AR $ in 90+ → net collection 91%. One upstream lever (front-end cleanliness) cascades down to denials, AR aging, and realized cash. That's a recommendation, not a dashboard.

**Definitional nuance:** clean = never reworked (stricter than not-denied); upstream event vs denial as downstream consequence.

**SQL pattern:** group by one flag (first_pass_flag) and compute a DIFFERENT metric (denial rate) within each group = test whether one metric predicts another. Cheap, high payoff.

**How it maps to the role:** Clean claim rate is the front-end lever; linking it quantitatively to denials is what elevates analysis from descriptive to causal/recommendation-grade.

**How it maps to my experience:** Stratifying an outcome by an upstream factor to show predictive/explanatory structure (like an exposure-stratified event rate).

**Interviewer probes rehearsed:** "Clean vs not-denied?" (clean is stricter, upstream). "Why does it matter?" (rework cost + 14× denial risk shown in Q4). "Tie the five metrics together?" (the chain above).

**What I learned:** The strongest analytic move is connecting metrics — grouping by a leading indicator and measuring a downstream metric inside each group turns five separate numbers into one defensible causal story.

---

## Step 14 — Segmentation layer (reusability centerpiece) ✅

**What we did:** Wrote `sql/99_segmentation.sql` — `v_segment_metrics` computing all 5 metrics at payer_type × service_line in one pass, storing ADDITIVE COMPONENTS + convenience rates. Showed the 32-cell matrix (A), payer rollup (B), grand total (C).

**Reconciliation proof:** rollup B matches the standalone metric files to the decimal (Medicaid denial 18.6, net 90.7, clean 80.0, days 52.0; etc.). Grand total C reproduces every headline (denial 12.2, clean 83.8, net 91.0, gross 45.1, 90+ AR $1.777M). One fine-grain view → correct at every coarser grain.

**Core principle:** store additive components (n_denied, adj_paid, adj_allowed, sum_days_to_pay), roll up by SUM-then-divide — NEVER average rates across segments (segments have different sizes). Rollup B = SUM(n_denied)/SUM(n_claims), not AVG(denial_rate_pct).

**Drill-down findings from the matrix:** hot cells — Medicaid×Cardiology denial 26.9% (worst), Medicaid×Primary Care clean 71.1%, Commercial×Oncology denial 17.7%, Commercial×Orthopedics $425K of 90+ AR. Fine grain turns "12% denial" into "here's the 27% pocket."

**SQL:** all metrics coexist in one GROUP BY via conditional aggregation (each metric's CASE filters its own base). Components stored so ratios recompute at any grain.

**How it maps to the role:** THE reusable artifact — same SQL on a new client's extract yields the full scorecard + any rollup. Reconciling rollups to standalone metrics is how you prove a consolidated layer is trustworthy.

**How it maps to my experience:** Building a single tidy results table with additive sufficient statistics so any aggregation/subgroup recomputes correctly.

**Interviewer probes rehearsed:** "How do you reuse this across clients?" (one parameterized view, rerun on new data). "Can you average the segment rates for the total?" (no — sum components, then divide). "Where's the real problem?" (drill to hot cells, not the headline).

**What I learned:** A reusable metrics layer stores additive components and computes ratios last, so one fine-grain view is correct at every grain — and reconciling its rollups to the standalone metrics is the proof of correctness.

---

## Step 15 — Publish to portfolio ✅ (Excel deferred)

**What we did:** Finalized README (leads with the 3.9% vs 55.7% / 14× showpiece + cross-metric chain + synthetic-data/PHI note). Built `revenue-cycle-sql.html`, a full case-study page on the existing `cs-` template (blue theme, revenue-cycle.html spacing), with the complete write-up on the page + GitHub repo link. Added a homepage card and moved both revenue projects to the front of the projects grid (SQL first, then realization). Ran a coherence audit across all 8 case-study pages: all share cs.css/section architecture/nav/footer; per-project accent colors are intentional; Madera flagged as the visual outlier (custom `.mc-*` + inline SVG) and deliberately left untouched. Excel pivots (Steps 16) deferred. Committed only this work (index.html, revenue-cycle-sql.html, Projects/revenue-cycle-sql/); 11 unrelated pre-existing working-tree changes left out. Pushed to main (one deploy).

**How it maps to the role:** The portfolio page frames the project the way a centralized analytics function would present it — workflow, definitions, findings, and the one-lever recommendation — readable in one place.

**What I learned:** Scoping a commit to exactly the intended files (not sweeping the dirty working tree) is part of publishing cleanly; and refactoring working pages for "coherence" is a separate, deliberate task, not something to bundle into a deploy.

---

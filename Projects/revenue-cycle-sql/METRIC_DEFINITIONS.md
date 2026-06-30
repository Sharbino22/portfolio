# Metric Dictionary — Revenue Cycle Claims Analysis

> The authoritative definition of every metric. All SQL in `sql/metrics/` must
> match these definitions exactly. This is the document a teammate reads before
> running or trusting any number. Locked at Step 8, before any metric was computed.

---

## Grain & analytic base (locked)

- **Fact grain:** one row per **claim** (header level). Not per claim line, not per encounter.
- **Source for all metrics:** `v_claims_analytic` (the trusted layer, metric-ready subset).
- **Duplicates:** exact-duplicate `claim_id` rows removed in `v_claims_clean` via
  `ROW_NUMBER() … PARTITION BY claim_id` keeping `rn = 1`. (25 rows removed.)
- **Quarantine:** 25 hard-corrupt rows (`charge_amount <= 0`, or `date_paid < date_of_service`)
  excluded via `include_in_metrics = 0`. **Analytic base = 4,975 claims.**
- **Rebills:** `rebill_flag` marks resubmissions. We do **not** collapse rebills into a
  parent claim (this synthetic extract has no parent-claim link). Every claim record is
  counted once. Consequence: denial rate here is **record-level / initial**, not
  net-of-appeals. *Known limitation; see "Extensions."*
- **Segmentation axes available on every claim:** `payer_type`, `payer_id`/`payer_name`,
  `service_line`, `department_group`, `service_month`.

---

## 1. Denial rate

**Business meaning:** share of claims (or billed dollars) the payer denied on first adjudication.

| | Count-weighted | Dollar-weighted |
|---|---|---|
| **Numerator** | claims with `denial_flag = 1` | `SUM(charge_amount)` where `denial_flag = 1` |
| **Denominator** | all claims in base | `SUM(charge_amount)` over all claims in base |

- **Inclusion:** all metric-ready claims, any status.
- **Why `charge_amount` for the dollar version:** denied claims have `allowed_amount = 0`,
  so billed charge is the only meaningful dollar exposure for a denied claim.
- **This is INITIAL denial rate** (denied at adjudication). We do not model appeal overturns,
  so we do not report a *final* denial rate.
- **Partial payments are not denials:** `Partially Paid` claims have `denial_flag = 0`.

**Interviewer probe → our answer:** "Per claim or per dollar?" → we report **both**; they
differ when a few large claims are denied. "Initial or final?" → **initial**; final would
require appeal/overturn data. "Do partials count?" → **no**.

---

## 2. Denial reason mix

**Business meaning:** distribution of *why* claims were denied, rolled up to category, to
separate **preventable front-end** causes (Authorization, Eligibility, Coding) from
payer-driven ones.

- **Base:** denied claims only (`denial_flag = 1`).
- **Per category:** numerator = `COUNT(*)` (and `SUM(charge_amount)`) in that
  `reason_category`; denominator = total denied count (and total denied charges).
- **`Unknown` category** holds the 30 denied-but-missing-reason claims, so the mix still
  sums to 100% and the data gap is visible rather than hidden.
- **"Preventable" rollup:** Authorization + Eligibility + Coding.

**Interviewer probe → our answer:** "Count or dollar weighted?" → **both**; a rare
high-dollar reason can outweigh a frequent low-dollar one. "How much is preventable?" →
sum the front-end categories. "What about missing reasons?" → an explicit `Unknown` bucket.

---

## 3. Days in AR (with aging buckets)

Two complementary views; revenue cycle reports both.

**3a. Days to pay (throughput, paid claims):**
- `days_to_pay = date_paid − date_of_service`, for `Paid` / `Partially Paid` claims with a
  non-null `date_paid`.
- Report **median and mean** (AR is right-skewed; median is the honest central value).
- **Excludes** the soft paid-but-missing-date claims (no `date_paid`) — documented gap.

**3b. Open AR aging (unpaid claims):**
- For `Open` claims, `days_outstanding = as_of_date − date_of_service`.
- Bucket: **0–30 / 31–60 / 61–90 / 90+** days.
- Report **count and outstanding dollars** per bucket; outstanding balance = `charge_amount`
  (claim billed, nothing collected yet).
- **90+ is the danger zone** (where receivables turn uncollectible).

- **Clock starts at `date_of_service`** (not submission): more comparable across claims and
  not gameable by submission timing. `as_of_date = 2025-01-15` (from `v_params`).

**Interviewer probe → our answer:** "From service or submission?" → **service**; comparable
and conservative. "Mean or median?" → **both**, lead with median (skew). "Open vs paid?" →
separated: throughput vs aging. "As-of date?" → fixed in `v_params`.

---

## 4. Net collection rate

**Business meaning:** of the money we were **contractually entitled to**, how much did we
actually collect. The truest "are we getting paid" metric.

- **Numerator:** `SUM(paid_amount)`.
- **Denominator:** `SUM(allowed_amount)`  (= charges − contractual adjustments).
- **Base:** adjudicated claims with `allowed_amount > 0` (excludes denied, where allowed = 0,
  and open/not-yet-adjudicated). Guard denominator with `NULLIF(..., 0)`.
- **Contrast metric — GROSS collection rate** = `SUM(paid_amount) / SUM(charge_amount)`.
  We report it *only* to show why it is misleading: charges are inflated list prices, so
  gross looks alarmingly low (~45%) while net is healthy (~91%). The gap is the contractual
  adjustment, not a collection failure.

**Interviewer probe → our answer:** "Net or gross — which and why?" → **net**, on `allowed`,
because charges are fictional list prices; gross understates performance. "Are patient
payments included?" → `paid_amount` represents **total** payments (payer + patient).

---

## 5. Clean claim rate

**Business meaning:** share of claims that adjudicate correctly on **first submission** with
no edits, rejections, or rework. A front-end efficiency / leading indicator.

- **Numerator:** claims with `first_pass_flag = 1`.
- **Denominator:** all submitted claims in base (all metric-ready claims are submitted).
- **"Clean" = no rework at all** — stricter than "not denied." A claim can be eventually paid
  but still not clean if it needed a correction/resubmission first.

**Interviewer probe → our answer:** "Clean = never-touched or just not-denied?" →
**never reworked**, stricter. "Why does it matter?" → every non-clean claim costs staff
rework time and **predicts** downstream denials and AR aging; it's the upstream lever.

---

## The cross-metric narrative (the story these five tell together)

Clean claim rate (front-end discipline) → denial rate & reason mix (what's failing and why)
→ days in AR (the cash-flow consequence) → net collection rate (the bottom line). Five
metrics, one chain from front-end cause to bottom-line effect.

## Extensions (named limitations, for honesty in interview)

- Rebill/parent-claim linkage → enables **final** (net-of-rework) denial rate.
- Line-level grain → denial rate per line, partial-denial dollars.
- Appeal/overturn outcomes → initial vs final denial.
- Posting-date vs service-date period definitions for collection.

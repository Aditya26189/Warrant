# SPEC.md — technical specification

Companion to `CLAUDE.md`. Reference snippets are illustrative; preserve the semantics exactly.

Customer extension (DECISIONS 184): `controlplane.release` registers identity,
scope, label meaning, fixed criteria, expiry and disjoint development/holdout
ID manifests locally. Content hashes permit checks against retained copies;
they are not signatures or independently trusted timestamps. Existing research
and customer certification commands retain their original contracts.

---

## 1. Core data model

Frozen dataclasses. Build these first; everything else consumes them.

### 1.1 Enums

```python
class Severity(IntEnum):        INFO=0; LOW=1; MEDIUM=2; HIGH=3; CRITICAL=4
class AccessTier(IntEnum):      T3_TEXT=3; T2_LOGPROBS=2; T1_ACTIVATIONS=1
class WarrantStatus(Enum):      VALID; STALE; REVOKED; REFUSED; UNVALIDATED
class MetricKind(Enum):         EXACT; ESTIMATED      # see CLAUDE.md, yield vs rate
class Reversibility(IntEnum):   READ_ONLY=0; REVERSIBLE_WRITE=1; IRREVERSIBLE_WRITE=2; EXTERNAL_COMM=3
```

`MetricKind` is not decorative. Every metric object carries it, and the renderer refuses to print an `ESTIMATED` value without an interval.

### 1.2 Finding

```python
@dataclass(frozen=True)
class Finding:
    finding_id: str
    detector_id: str            # "probe-qwen2.5-7b-L23", "presidio-stock", "qwen3guard-0.6b"
    detector_version: str       # semver + weights hash
    category: str               # PII | HALLUCINATION | INJECTION | UNSAFE | COST | BIAS_SIGNAL
    severity: Severity
    confidence: float           # raw detector score [0,1]
    evidence_spans: list[Span]  # character offsets — required, drives explainability
    access_tier: AccessTier
    latency_ms: float
    warrant_id: str | None      # None == UNWARRANTED, an honest state, not an error
```

Categories overlap by design. A fabricated detail about a person emits both `HALLUCINATION` and `PII`. Detectors never resolve conflicts; policy does.

### 1.3 Warrant

```python
@dataclass(frozen=True)
class Warrant:
    warrant_id: str
    detector_id: str
    detector_version: str
    operating_point_id: str
    eval_set_id: str            # content hash — this IS the envelope key
    validation_run_id: str
    issued_at: datetime
    expires_at: datetime
    metrics: WarrantMetrics     # each field: value, ci_low, ci_high, n, MetricKind
    n_test: int
    base_rate: float
    envelope: DistributionEnvelope
    controls: list[ControlResult]
    kappa: float | None         # inter-rater agreement, where labels are human
    status: WarrantStatus
    status_reason: str | None
```

**The key is `(detector_id, operating_point_id, eval_set_id)`.** Not detector alone. This is invariant 1 and the entire matrix depends on it.

As shipped, the record holds the whole `operating_point: OperatingPoint` rather than its id, and `Warrant.key` reads `operating_point.operating_point_id` — the key is unchanged. Sequence fields in §1.2–§1.4 are tuples, not lists, because a frozen record holding a list is still mutable. Additions not shown above (`Finding.confidence_band`, `Warrant.access_tier`, `superseded_by`, `calibration`, `Certificate.unchecked`) each have a `DECISIONS.md` entry. `DECISIONS.md` 168.

`status` on a *record* is one of `VALID`, `STALE`, `REVOKED`, `REFUSED`. **`UNVALIDATED` is a property of a matrix cell, not of a warrant**, and a `Warrant` cannot be constructed carrying it: an unvalidated cell has no metrics, no envelope and no controls, so building a record for one would mean inventing all three. The matrix reports `UNVALIDATED` for a cell holding no warrant. See `DECISIONS.md` 024.

### 1.4 Certificate

```python
@dataclass(frozen=True)
class Certificate:
    certificate_id: str
    request_id: str
    session_id: str
    timestamp: datetime
    findings: list[Finding]
    resolution: Resolution              # action, policy_version, triggering_finding_ids
    warrants_relied_upon: list[str]
    weakest_warrant_status: WarrantStatus
    claimed_bounds: dict                # the bounded, falsifiable assertion
    envelope_match: EnvelopeMatchResult  # which envelope this input landed in
    access_tier_available: AccessTier
    prev_certificate_hash: str
    self_hash: str
```

`claimed_bounds` is what makes liability bounded: the system asserts *"checked at measured recall 0.14 [0.10, 0.19] on envelope E"*, not *"this is safe."*

### 1.5 Store

SQLite, append-only, hash-chained: `self_hash = SHA256(prev_hash || canonical_json(record))`.

Retention: at least one year. DPDP Rules 2025, Rule 6(1)(e) requires security logs be kept *"for a period of one year"*, and Rule 8(3) sets *"a minimum period of one year"* for processing logs; both commence 13 May 2027. `config.yaml` declares 400 days and the store refuses anything under 365.

Query paths — **this project's design, not the rule's text**: by session, time range, policy version, detector version, warrant status, and personal-data category accessed. Rule 6(1)(c) requires *"visibility on the accessing of such personal data, through appropriate logs, monitoring and review, for enabling detection of unauthorised access, its investigation and remediation"*; it names no predicate. These six are what an investigation of that kind asks, and they are indexed so it can be answered. Every record self-describing enough to interpret a year later without the current codebase.

This paragraph originally credited all of the above to Rule 6. `DECISIONS.md` 168.

Demonstrate tamper-evidence by mutating a row and showing the chain break. This is a two-line test and it is worth a slide.

---

## 2. Validation harness

### 2.1 The control suite

All five run on every validation. **A failed control fails the run and refuses the warrant.**

| Control | Method | Pass condition |
|---|---|---|
| **Padding fault injection** | Score one batch with correct left padding and with deliberately broken right padding | Correct: rel-L2 ≤ 0.1, cosine ≥ 0.999. Broken: **must be rejected** |
| **Label shuffle** | Retrain on permuted labels, score held-out. Repeated until the null is resolved | **Mean** AUROC ∈ [0.45, 0.55] **and** SE(mean) ≤ ¼ of the band width |
| **Null feature** | Replace activations with Gaussian noise matched in mean/variance. Same repeat rule | **Mean** AUROC ∈ [0.45, 0.55], same power condition |
| **Canary recall** | Score `canary-20` | Recall == 1.0 |
| **Determinism** | Re-run scoring twice at fixed seed | Bit-identical |

Label-shuffle and null-feature are **negative controls**: they assert the pipeline can produce a null result when there is no signal. A pipeline that cannot fail cannot be trusted when it succeeds. That sentence is the thesis applied to our own code and it belongs in the README.

Both are repeated rather than run once, and **each sizes its own repeat count from its own measured null spread**. A single draw is unusable: at a holdout of 600 the null spread is 0.068 for a 32-feature probe and 0.271 for a single-feature one, because a fitted probe's scores are not exchangeable and a one-dimensional probe's shuffle merely picks a sign. No closed form predicts that — the Hanley–McNeil SE understates it by 2.1× and 8.3× respectively — so the spread is measured and `k ≥ (2·spread / band_half)²` repeats are run, capped by `validation.null_control_max_repeats`. Measured counts: 8 repeats at 32 features, 22 at 4, 125 at 1.

A control that reaches the cap without resolving its null **fails as underpowered** rather than passing. Its job is to show the pipeline *can* produce a null result; without the power to show it, it has shown nothing. Derivation, the measured null distributions and the rejected alternatives are in `DECISIONS.md` 029 and 031.

**The figures in the paragraph above are the fixture's, not a language model's.** The 0.068 and 0.271 spreads, the 2.1× and 8.3× ratios and the 8 / 22 / 125 repeat counts were measured on synthetic data at base rate 0.152 (`DECISIONS.md` 031). On the real T1 runs — 3,584 features, holdout 600, base rate 0.46 — the measured null spread is 0.7–1.0× the Hanley–McNeil closed form and every negative control resolves at the 8-repeat minimum (`results/validation-T1-*.json`, `controls[1..2].detail`). The rule stands: measuring the spread costs nothing, and the low-dimensional case it guards has no real instance here yet. `DECISIONS.md` 169.

### 2.2 `/validate`

```
POST /validate { detector_id, operating_point_id, eval_set_id }
→ ValidationRun {
    run_id, started_at, completed_at,
    metrics with 95% bootstrap CIs (1000 resamples),
    control_results: [5, each pass/fail with measured margin],
    envelope: reference distribution from this eval set,
    warrant: issued | refused,
    provenance: git commit, config hash, versions, device, seed
  }
```

Under one minute from cached activations. Streams progress. **Displays the deliberately-broken padding case being rejected** — that is the moment in the demo.

### 2.3 Refusal criteria

Refuse if any control fails; or AUROC lower CI bound ≤ 0.55; or recall below the policy's declared minimum at the operating point; or FPR on the hard-negative set above the declared maximum; or `n_test` < 200.

Recall and hard-negative FPR are compared at the **interval bound**, not the point estimate — a profile declaring "at least 10% recall" is asking for a guarantee, and a point estimate of 0.11 whose lower bound is 0.06 does not supply one. `n_test` counts the **test split**, so an eval set is sized by that split rather than by its total; see `DECISIONS.md` 030.

**No override path exists.** Not a flag, not an env var.

**A sixth criterion shipped: lift lower bound ≤ 1.0** — the detector is not demonstrably better than random sampling at the same budget. Found by measurement, not designed in: a warrant was issued `VALID` on recall `[0.000, 0.077]` because AUROC is a ranking bar and the product's claim is about usefulness at a budget. 1.0 is a definitional null rather than a tunable, which is why it is `issuance.py::MIN_LIFT_LOWER_BOUND` and not a `config.yaml` value. `DECISIONS.md` 043, 169.

---

## 3. The warrant matrix

### 3.1 Why a matrix and not a curve

An envelope violation is a property of the input distribution, not of a detector. Long-context traffic invalidates the score-to-error-rate mapping for T1, T2 and T3 *simultaneously*. "Downgrade to the next tier" without re-checking the envelope replaces one unwarranted claim with another.

So build:

|  | `triviaqa-600` | `triviaqa-longctx-600` | `hinglish-pii-200` | `hard-negatives-200` |
|---|---|---|---|---|
| T1 probe, mean-pool | VALID | **REFUSED** | UNVALIDATED | VALID |
| T1 probe, max-rolling-means | VALID | VALID (wider) | UNVALIDATED | VALID |
| T2 logprob | VALID | ? | ? | ? |
| T3 judge | VALID | ? | ? | ? |
| presidio-stock | n/a | n/a | **REFUSED** | VALID |

Cheap to build: Phase 2's ablation extracts all tiers in one pass; run it once per eval set.

**The table above was a prediction, and one cell was wrong.** Measured on `triviaqa-longctx-600`, max-of-rolling-means is `REFUSED`, not `VALID (wider)`; last-token is the probe that holds. `hinglish-pii-200` is measured for the PII reference detector, and T2/T3 rows exist only on synthetic envelopes, which `RESULTS.md` masks. The shipped matrix is `results/warrant_matrix.md`. `DECISIONS.md` 170.

### 3.2 Routing

Drift fires → *"which detector holds a `VALID` warrant on the envelope I am actually in?"* → route there, adopt **that warrant's bounds**, and if the row is empty, refuse everything and fall back to the profile's most conservative action.

```python
def route(envelope_id: str, profile: Profile) -> RoutingDecision:
    candidates = matrix.valid_warrants(envelope_id)
    eligible  = [w for w in candidates if profile.accepts(w.metrics)]
    if eligible:
        return RoutingDecision(warrant=best(eligible), claimed_bounds=...)
    unvalidated = matrix.unvalidated_cells(envelope_id)
    enqueue_for_validation(unvalidated)          # matrix self-populates from live traffic
    return RoutingDecision(warrant=None, action=profile.conservative_default,
                           reason=f"no valid warrant on envelope {envelope_id}")
```

**As shipped, the matrix does not self-populate.** `route()` hands unvalidated cells to an `enqueue` callback that defaults to a log line, and nothing consumes it. Two additions the sketch lacks: a *suspended* profile — something holds a warrant here, none this profile accepts — is a different event from an empty row; and an envelope the matrix does not know raises rather than reading as a measured absence (`DECISIONS.md` 050). `DECISIONS.md` 170.

### 3.3 The three states, precisely

| State | Meaning | Behaviour |
|---|---|---|
| `VALID` | Validated here, cleared the bar | Normal operation, full claimed bounds |
| `REFUSED` | Validated here, failed the bar | Detector removed from service on this envelope until re-validated by a human |
| `UNVALIDATED` | Never tested here | **Modal state in production.** No claim available → conservative action, enqueue for validation, log |

Collapsing `UNVALIDATED` into `REFUSED` makes the system unusable on day one. Collapsing it into `VALID` is the failure the whole product argues against.

These are **cell** states. `VALID`, `STALE`, `REVOKED` and `REFUSED` are carried on the warrant record occupying the cell; `UNVALIDATED` is the state of a cell with no record in it. Representing it as a record would require fabricating the metrics that make a record a claim, which is the failure mode the state exists to prevent.

---

## 4. Evaluation sets

Content-hashed, immutable.

| Set | Contents | Validates |
|---|---|---|
| `triviaqa-600` | Existing held-out set | Round 1 anchor |
| `triviaqa-longctx-600` | Same questions padded with distractors to 4–16k tokens | The drift trigger; mean-pool collapse |
| `hinglish-pii-200` | Hand-built code-switched Hindi-English with Aadhaar/PAN/UPI/phone in verbatim, spaced, and obfuscated forms | India differentiator; Presidio refusal |
| `hard-negatives-200` | Boundary cases that **must be allowed**: security analyst summarising malware, clinician discussing overdose thresholds, HR describing a discrimination complaint, customer quoting abuse in a grievance | FPR — the number a skeptic accepts |
| `canary-20` | Known positives the detector must always catch | Regression tripwire |
| `agent-actions-N` | Tool-call traces labelled by reversibility class and safety | Phase 9 |

Hand-build the middle three. Do not generate them with an LLM and call them ground truth.

`hard-negatives-200` is the most under-appreciated item here. FPR measured on easy benign traffic makes a damaging filter look excellent.

**`triviaqa-longctx-600` as built is 2,838–11,103 tokens, median 6,954, and 82 of 600 prompts are under 4,000** — not 4–16k. Measured at extraction (`results/cache-triviaqa-longctx-600.npz`, `__token_lengths`). The builder sized padding at 4.0 characters per token and this filler tokenises at 5.77. The padding repeats eight distractor paragraphs, and responses and labels are the short-context pass's, so a label records whether the model was right *without* the padding. The set is frozen and is not rebuilt; the range is corrected wherever it was claimed. `agent-actions-N` does not exist: the gate is measured on one declared injection scenario and eight declared workflows (`DECISIONS.md` 156). `DECISIONS.md` 171.

---

## 5. Drift and revocation

### 5.1 Envelope features

Computed at validation time, stored **inside the warrant**.

1. **Input token length** — the highest-priority feature; long-context is the documented probe killer
2. **Script/language mix** — Latin / Devanagari / mixed; code-switching density
3. **Embedding centroid distance** — mean cosine from the eval set centroid
4. **Reference perplexity** — small-model perplexity as a distributional proxy
5. **Category mix** — proportion of requests triggering each finding category

### 5.2 Detection

- **Per-feature:** Population Stability Index over a sliding window. `<0.10` stable, `0.10–0.25` moderate, `>0.25` significant. PSI is native vocabulary in Indian banking risk teams.
- **Multivariate:** MMD on embeddings with a permutation test.
- **Window:** sliding, minimum 200 requests before any verdict. Do not revoke on noise.

### 5.3 Revocation ladder

| Envelope state | Status | Behaviour |
|---|---|---|
| Inside | `VALID` | Normal, full bounds |
| PSI 0.10–0.25 | `STALE` | Widen reported CIs, trigger background revalidation, log |
| PSI > 0.25 | `REVOKED` | **Refuse to certify.** Consult the matrix for a valid warrant on the new envelope. Route or refuse |
| Control failure | `REFUSED` | Out of service until human re-validation |

### 5.4 Model-version invalidation

A probe is pinned to a model version. On model change, every activation-tier warrant is invalidated until revalidation. State this as an operational cost; the mitigation is that T2 and T3 are model-agnostic and keep working through the gap.

**As shipped, §5 is one feature deep.** Only input token length (§5.1, item 1) is computed and fed to the monitor; the other four features are declared in `config.yaml` and computed nowhere, and MMD (§5.2) is not implemented. The monitor names every unscored feature in its verdict and the certificate lists MMD as unchecked, so nothing is hidden at runtime. PSI bands are simulated from the null rather than taken from the 0.10 / 0.25 rule of thumb (`DECISIONS.md` 070); the claim that PSI is native vocabulary in Indian banking risk teams has no source here. `STALE` widens bounds by a declared 1.5×, stated on the transition as policy rather than derived — and the same message says revalidation is scheduled, which nothing does. `DECISIONS.md` 172.

---

## 6. On-traffic warrant — stratified estimation

**This is what makes the product more than a staleness detector.** Escalated items are already reviewed. Those reviews are labels we currently discard.

### 6.1 The two strata

- **Stratum A — flagged.** 100% reviewed already. Free.
- **Stratum B — random sample of unflagged traffic.** The expensive half.

Importance-weight the two for an unbiased on-traffic estimate.

### 6.2 Sizing — get this right, it is the error the spec exists to prevent

Let `N` = monthly volume, `f` = flag rate, `N_u = N(1−f)` unflagged, `TP` = confirmed true positives in stratum A, `q` = prevalence of errors in the unflagged pool.

```
R = TP / (TP + q·N_u)
∂R/∂q = −TP·N_u / (TP + q·N_u)²
```

To hit a recall margin `m_R`, size the *prevalence* estimate to `m_q = m_R / |∂R/∂q|`, then:

```
n = 1.96² · q(1−q) / m_q²
```

**Worked, at the declared workload** (N=200,000, base error rate 0.03, f=0.0148, TP=850, N_u=197,036, q=0.0261):

```
∂R/∂q = −850 × 197,036 / 6,000²  =  −4.65
m_R = 0.05  →  m_q = 0.01075  →  n ≈  847
m_R = 0.02  →  m_q = 0.00430  →  n ≈ 5,292
```

**The trap this encodes.** `1.96²·(0.05)(0.95)/0.02² = 456` sizes a *prevalence* estimate to ±2pp. Calling that "recall to ±2pp" understates the labels needed by roughly 22×, because sample size scales as `1/margin²` and the derivative is 4.65. The amplification is structural: the unflagged pool is ~232× the **confirmed true positives**, so any error in `q` is multiplied by that ratio on its way into `R`. `TP` is the other term in the denominator of `R = TP/(TP + q·N_u)`, which is what makes it the right comparator. The unflagged pool is only ~66× the *flagged* pool, and the flagged pool does not appear in the derivative at all — it holds the false positives, which are exactly the items that do not enter `R`. `DECISIONS.md` 148 records the correction.

**Assert this in code.** The derivative is exposed by `controlplane/sampling/planning.py::recall_sensitivity` (it was specified for `sizing.py`; the sampling package is where the estimator that consumes it lives), and `tests/test_sampling.py::test_sizing_derivative` confirms that sizing for recall differs from sizing for prevalence by `(∂R/∂q)²`.

**The closed form above does not deliver its own margin, and the shipped planner does not use it by default.** It is a first-order expansion, and `R` is far from linear across the interval it is asked to hold over: at `n = 846` the prevalence interval runs from 0.016 to 0.039, over which `R` moves by a factor of two. Fed back through the estimator that publishes the interval, the closed form's sample sizes realise half-widths of 0.0546 and 0.0206 against the ±0.05 and ±0.02 targets worked above, and 0.0101 against ±0.01. The shortfall is the **linearisation**, not the switch to an exact interval — at ±0.05 the exact interval is narrower than the Wald one. `labels_for_recall` therefore defaults to `basis="exact"`: the smallest `n` from which the Clopper-Pearson-induced recall half-width meets the margin and **keeps** meeting it. The closed-form figure is still reported on every plan as `labels_normal`, because it is what a reader recomputes from this section. Month one is additionally priced at full simple-random-sampling cost, not at an expected design effect (§6.3). `DECISIONS.md` 149, 150.

### 6.3 Allocation

Neyman allocation across probe-score bands concentrates labels where variance is:

```
n_h ∝ W_h · √(q_h(1−q_h))
```

**Expect ~1.5× reduction, not more.** Neyman variance goes as `[Σ W_h √(q_h(1−q_h))]²`, and √ is concave, so a large band with small-but-nonzero prevalence dominates the sum precisely *because* it is large. On plausible band structure for a detector at AUROC 0.855 the design effect lands near 0.67. Treat 2× as a good outcome. **Size it empirically from the observed score distribution; do not assume a factor.**

Measured on the declared band structure: **0.7929**, against the 0.67 expected above and in `config.yaml` (`results/on_traffic/ON_TRAFFIC.md`). `DECISIONS.md` 173.

**Month one runs proportional allocation** because Neyman needs `q_h` you do not have yet. The first warrant costs full SRS price. Say this in the README rather than letting someone discover it.

### 6.4 The price list — computed, never typed

`controlplane/economics/sizing.py` derives all of this from the single declared workload in `config.yaml`. The README pulls the rendered table. **No figure here is written by hand**, which is also how invariant 6 is enforced structurally rather than by discipline.

| Claim | Extra labels | Cost | Why |
|---|---|---|---|
| Precision | 0 | **free** | Stratum A already reviewed |
| FPR | 0 | **free** | FP known exactly, denominator known |
| **Yield** — *"we surfaced N real errors"* | 0 | **free** | Exact count, `MetricKind.EXACT` |
| Recall ±5pp | ~847 SRS / ~570 Neyman | computed | Requires estimating `q` over the unflagged pool |
| Recall ±2pp | ~5,292 SRS / ~3,500 Neyman | computed | Same, at 6× precision |

Three of the four are free. The pitch line falls out:

> **The recall rows above are superseded, and typed — which this section forbids.** ~847 and ~5,292 are the closed-form sizes §6.2 shows under-deliver; the Neyman figures assume a design effect month one cannot have. The computed price list is rendered into `results/RESULTS.md` and the README from `results/on_traffic/on_traffic.json`. **FPR is nearly free, not free**: its denominator includes the misses `q·N_u`, which is the estimated quantity, so it is `ESTIMATED` — about ±1% on the denominator at the declared workload — and the on-traffic estimator does not return it. `DECISIONS.md` 173.

> *"Three of the four numbers you need are free — you're already reviewing the flags, you're just throwing the labels away. Only recall costs money, because recall means estimating what you missed across two hundred thousand responses nobody looked at. Here's what each precision level costs. Pick one."*

### 6.5 Label quality

**Blinding.** Stratum A reviewers see items the system flagged; stratum B reviewers see items it didn't. If flag status, score, stratum or ordering is visible, the two strata get systematically different label distributions and the importance-weighted estimate is biased *in the direction that flatters us*. Interleave both strata into **one blinded queue with identical UI**. Nearly free, and it is the difference between a warrant and a self-report.

**Noise.** Published work measures human agreement near 48% on contextual redaction (RedactionBench, arXiv:2606.18782: 47.7% consensus *with target labels* on contextual redactions, against 89.4% on mandatory ones — agreement with a gold label, not an inter-rater κ), and label noise materially degrades measured detector performance. A ±5pp interval is meaningless at κ = 0.5. **Double-label ~10% of both strata; publish Cohen's κ alongside every warrant.** At the ±5pp tier that is ~85 extra reviews.

A warrant carrying its own label-agreement statistic is doing to itself what it does to detectors — refusing to claim more precision than its evidence supports.

**"~85 extra reviews" counted one stratum** at the superseded ±5pp size. Ten percent of *both* strata includes the flagged stratum, which is several times larger; the price list carries the computed figure. `DECISIONS.md` 173.

---

## 7. Policy engine

### 7.1 Policy is data

OPA/Rego or Cedar. **Do not write a DSL.** Versioned, content-hashed, hot-reloadable bundles. Every certificate stamps the policy version.

### 7.2 Load-time warrant resolution

On bundle load, resolve every referenced operating point against the matrix. **Missing, expired, refused, unvalidated, or below declared minimums → the bundle fails to load**, with an error naming the missing warrant. Not a warning.

```yaml
profile: customer_support
version: 3.1
requires_warrant:
  - detector: probe-qwen2.5-7b-L23
    operating_point: P-conservative
    envelope: triviaqa-600
    min_recall: 0.10
    max_fpr_hard_negatives: 0.02
    max_age: 24h
rules:
  - when: warrant.weakest_status != VALID and action.reversibility >= IRREVERSIBLE_WRITE
    then: BLOCK
    reason: "no valid warrant backs an irreversible action"
  - when: finding.category == PII and finding.severity >= HIGH
    then: REDACT
  - when: severity >= HIGH and confidence_band == UNCERTAIN
    then: ESCALATE
```

The first rule is the entire product in four lines.

### 7.3 Profiles

Three, each at a **different validated operating point on the same measured curve** — not three invented thresholds.

| Profile | Inline budget | Operating point | Rationale |
|---|---|---|---|
| Customer support | ≤200ms | High precision, low flag rate | Over-blocking destroys the channel; volume high |
| Internal knowledge | ≤500ms | Balanced, retrieval verification on | Corpus exists; internal users tolerate friction |
| Decision support | ≤2s | High recall, escalation-heavy | Low volume, high consequence, review affordable |

### 7.4 Weighted-error objective

```
τ* = argmin_τ  Σ wᵢ·ERRORᵢ(τ) / Σ wᵢ
  w_fpr_benign = 50 ; w_fnr = 5 ; w_fpr_hard_negative = 2
```

Weights live in the bundle, are versioned, and appear on screen. Complexity 4 answered by declaring the tradeoff, not solving it.

**As shipped, these weights select no operating point.** `policy/objective.py::choose_threshold` implements the argmin and is exercised by tests only. The three profiles' points are selected on validation at `config.yaml`'s `target_flag_rate` — `objective: flag_rate_budget=…` in `results/policy-triviaqa-2400-t960.json` — and the bundle weights are identical across the three, so if they selected, the profiles would share one threshold. The tradeoff that moves the threshold is still declared and versioned; it is the flag-rate budget, not these weights. `DECISIONS.md` 174.

---

## 8. Detector adapters

| Detector | Licence | Role |
|---|---|---|
| Probe (T1) | ours | Correctness trigger; tier-ladder anchor |
| Qwen3Guard-0.6B / Stream | Apache-2.0 | Content safety; its safe/controversial/unsafe output already models deferral |
| LettuceDetect / TinyLettuce | MIT | RAG grounding for the knowledge profile |
| Presidio | MIT | PII, and the warrant-refusal demo |
| LLM judge | — | T3 tier, cascade fallback |

### 8.1 The Presidio sequence

Presidio ships `IN_AADHAAR`, `IN_PAN`, `IN_PASSPORT`, `IN_VEHICLE_REGISTRATION`, `IN_VOTER`, `IN_GSTIN` — **all English-only and disabled by default.**

Measure three configurations on `hinglish-pii-200`, all three reported:

1. **Stock** — recognisers off. Expect near-zero recall on Indian identifiers → **warrant REFUSED** automatically.
2. **Enabled** — recognisers on. Better; still imperfect on obfuscated and code-switched forms.
3. **Enabled + custom** — checksum-validated Aadhaar (Verhoeff), PAN structural, UPI VPA, IFSC.

**Verify what the shipped `InAadhaarRecognizer` actually validates before claiming novelty on the checksum.** If it already does Verhoeff, the contribution is the measurement and the Hinglish evaluation, not the algorithm. Claim the right thing.

When citing the published Presidio HIGH-sensitivity recall of 0.07, state that the benchmark is synthetic and deliberately includes obfuscated and non-verbatim disclosure forms. Describing its construction is what stops it being turned against you.

The source is REDACT (arXiv:2606.19881, June 2026): 0.23 recall on LOW-tier entities falling to 0.07 on HIGH, under **partial-overlap** matching, on LLM-generated documents whose PII is fictional. Checked against the installed `presidio-analyzer` 2.2.364: the six recognisers above are English-only and `enabled: false`, and `InAadhaarRecognizer` already validates Verhoeff. Of the §8 table, Qwen3Guard, LettuceDetect and the LLM judge are not built. `DECISIONS.md` 175.

---

## 9. Action gate

### 9.1 Reversibility

Registered per tool at definition time — a **static property of the tool**, not an inference about the request. That is what makes it robust to an attacker who has defeated every detector.

### 9.2 Session Rule-of-Two

Three sticky booleans per session: `has_ingested_untrusted_input`, `has_sensitive_access`, `can_change_state_or_communicate`. **Two of three is the limit.** Sticky for the session — once untrusted content has entered, it has entered. This is complexity 5 answered.

**The rule describes what a session can do, and it is evaluated against the session as it would be after the call.** It is Meta's *Agents Rule of Two* (31 October 2025): an agent should satisfy no more than two of the three properties within a session, and one needing all three without starting a new session should not act autonomously. Read as three flags recording what a session *has done*, it loses exactly one case — the one where the action being decided is itself the third capability. That case is the canonical indirect injection: read something sensitive, read attacker-controlled text, then move money. The only remedy for a session that holds all three is a new session with a fresh context; the flags have no unsetter. `DECISIONS.md` 156.

### 9.3 The gate

```
BLOCK    if reversibility >= IRREVERSIBLE_WRITE and warrant.weakest_status != VALID
BLOCK    if rule_of_two_violated(session.after(tool)) and reversibility >= IRREVERSIBLE_WRITE
CONFIRM  if reversibility >= IRREVERSIBLE_WRITE and severity >= MEDIUM
ESCALATE if severity >= HIGH and confidence_band == UNCERTAIN
ALLOW    otherwise
```

The first two rules consult no detector score. Deliberate: Nasr et al., *The Attacker Moves Second* (arXiv:2510.09023, October 2025) bypassed 12 published injection and jailbreak defences at an attack success rate above 90% for most, where the majority had originally reported near-zero — so any control depending on detection has a measured ceiling. A control keyed to static tool class plus session state holds against an attacker who has completely defeated the probe.

**Rule 2 reads `session.after(tool)`, not `session`.** This section originally specified the latter, and implemented exactly as written it **allows** the attack §9.4 exists to demonstrate: `get_balance` → `search_transactions` → `transfer_funds` reaches the transfer holding two of three flags, because the transfer is the call that sets the third. The first demonstration appeared to block it only because a legitimate `draft_dispute` sat between the memo and the transfer. Evaluated prospectively, the rule blocks exactly the irreversible actions that would complete the triad: `get_balance` → `transfer_funds` is allowed, a reversible `draft_dispute` after reading a memo is allowed, and the attack is refused. Measured cost on eight declared legitimate workflows: two blocked, both recovered by a new session — an exact count over a declared set, not a production rate. `DECISIONS.md` 156.

### 9.4 The agent

One domain, four tools, clean reversibility gradient. Banking: `get_balance` (READ_ONLY), `search_transactions` (READ_ONLY), `draft_dispute` (REVERSIBLE_WRITE), `transfer_funds` (IRREVERSIBLE_WRITE). Gate at **tool-call time**, not text-generation time.

---

## 10. Tests

| Test | Asserts |
|---|---|
| `test_hash_chain` | Mutating a row breaks the chain |
| `test_warrant_key` | Warrants keyed by (detector, op, eval_set); same detector on two envelopes yields two warrants |
| `test_three_states` | `UNVALIDATED` routes conservatively and enqueues; `REFUSED` removes from service; they are not interchangeable |
| `test_no_override` | No code path issues a warrant with a failed control. Grep-level assertion plus behavioural test |
| `test_controls` | All five controls; each fails when it should |
| `test_padding_equivalence` | Batched == unbatched to 1e-2; right-padded batch is rejected |
| `test_sizing_derivative` | `∂R/∂q` matches analytic form; **sizing for recall differs from sizing for prevalence by `(∂R/∂q)²`** |
| `test_sizing_units` | Sizing function refuses to return a number without a declared target quantity |
| `test_no_scenario_mixing` | All economics figures derive from one workload block; test fails if two are mixed |
| `test_yield_vs_rate` | `MetricKind.EXACT` values carry no interval; `ESTIMATED` values always do |
| `test_blinding` | Label queue payload contains no flag status, score, stratum, or ordering signal |
| `test_stratified_unbiased` | On synthetic data with known ground truth, the estimator recovers true recall within CI at nominal coverage over 1000 trials |
| `test_policy_refusal` | Bundle referencing an unwarranted operating point fails to load |
| `test_gate_no_detector` | Gate's first two rules produce correct decisions with all detector scores nulled |
| `test_polarity` | Positive class is "incorrect" |
| `test_no_test_leakage` | Scaler and classifier fit on train indices only |
| `test_determinism` | Two runs at one seed, identical coefficients |
| `test_smoke` | Full pipeline at n=100 completes, all artifacts written |

`test_stratified_unbiased` is the most important new test. An estimator that is subtly biased produces confident wrong intervals, and nothing raises.

**Names, reconciled.** Thirteen of the eighteen names above exist in `tests/` exactly. Five do not, and every one of those behaviours is tested under a descriptive name: `test_controls` is `test_all_five_controls_run_and_report_margins` plus a failure test per control; `test_padding_equivalence` is `test_padding_control_rejects_the_deliberate_fault` and its siblings; `test_policy_refusal` is `test_a_bundle_naming_an_unwarranted_point_fails_to_load`; `test_determinism` is `test_determinism_control_detects_a_wobble`; `test_smoke` is the `test_smoke_*` family. The map is `controlplane/report/invariants.py::SPEC_TEST_ALIASES`, and `test_every_test_named_in_spec_section_10_exists` fails if a name in this table resolves to nothing. `DECISIONS.md` 167.

---

## 11. What `results/RESULTS.md` must contain

1. Run metadata — models, quantisation, device, seed, config hash, git commit, timestamp
2. Eval set registry — IDs, hashes, sizes, base rates
3. **The warrant matrix** — every (detector × envelope) cell with status and metrics
4. Tier ladder on each envelope, with CIs
5. Control results for every run, including the rejected fault case
6. Drift trace — envelope violation detected, revocation, routing decision
7. **The computed price list**, with the declared workload stated above it
8. Stratified estimator validation — coverage over synthetic trials
9. Cohen's κ
10. Presidio three-configuration comparison
11. Action-gate results, including the detector-nulled case
12. Limitations — written honestly and specifically, not boilerplate

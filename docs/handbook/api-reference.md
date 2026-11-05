# Library interface reference

The CLI and versioned records are the preferred external interfaces. These selected Python entry points are documented for maintainers; this catalog is not a promise that every internal symbol is stable.

## controlplane/model/metrics.py

Metrics that cannot be constructed in violation of their own kind.

### MetricError

[Source](../../controlplane/model/metrics.py#L32)

Raised when a metric would misrepresent what is known about it.

### Metric

[Source](../../controlplane/model/metrics.py#L55)

One measured quantity, carrying what is and is not known about it.

Args:
    name: What was measured, e.g. ``"recall"`` or ``"confirmed_errors"``.
    value: The measurement.
    kind: ``EXACT`` for a count of reviewed, confirmed items; ``ESTIMATED``
        for anything requiring inference about unreviewed items.
    n: The sample or population size the value came from. Required for both
        kinds — invariant 4 says every interval names its ``n``, and an
        exact count is uninterpretable without its denominator either.
    ci_low: Lower bound. Required for ``ESTIMATED``, forbidden for ``EXACT``.
    ci_high: Upper bound. Same rule.
    ci_level: Coverage of the interval, e.g. ``0.95``.
    unit: ``"rate"``, ``"count"``, ``"ratio"`` or similar. Rendered beside
        the value so a count is never read as a proportion.
    estimator: How the interval was produced, e.g.
        ``"bootstrap-percentile-1000"``. An interval whose construction is
        unstated is not reproducible.
    convention: ``"two_sided_95"`` or ``"one_sided_95"``. **Required for
        ``ESTIMATED``**, because the two are 23% apart at n=200 and both
        look like "95%". The shipped hard-negative bound is
        ``cp_upper(0, 200, alpha=0.025)`` -- two-sided -- while
        ``warrant_stats.cp_upper`` is one-sided by design, and eyeballing a
        certification target off the wrong one moves the demo's refusal
        figure by 17% (``DECISIONS.md`` 110). A warrant bound is one-sided
        because *"FPR <= x at 95%"* is a one-sided claim; a descriptive
        interval is two-sided. Having both is correct. Having both
        unlabelled is the defect.

Raises:
    MetricError: If the metric would misrepresent its own kind.

### WarrantMetrics

[Source](../../controlplane/model/metrics.py#L257)

The measured bounds a warrant asserts.

Precision and recall are both required fields, which is invariant 5 made
structural: there is no way to construct a warrant that claims one without
the other, so there is no way for a report to quote recall alone.

``flag_rate`` is here because lift is ``recall / flag_rate`` and quoting
lift without the flag rate it was computed at is how a lift number becomes
unfalsifiable. ``confirmed_errors`` is the exact yield — the free claim —
and sits beside the estimated rates so the difference is visible at a
glance rather than explained in a footnote.

Args:
    auroc: Threshold-free ranking quality. Estimated.
    recall: Estimated. Sensitive to the unreviewed pool, so this is the one
        that costs money (``SPEC.md`` §6.2).
    precision: Estimated. Free in labels, because the flagged stratum is
        already reviewed — free is a statement about label cost, not about
        certainty (``DECISIONS.md`` 022).
    flag_rate: The measured rate at which this operating point fires.
    confirmed_errors: Count of reviewed, confirmed true positives. Exact.
    fpr_hard_negatives: FPR on the hard-negative set, where it means
        something. Optional because not every envelope has one.
    base_rate: Positive-class prevalence on the set these were measured on.
        Carried here, beside the metrics rather than only on the warrant,
        because **lift is not interpretable without it**: the maximum
        achievable lift is ``1 / max(base_rate, flag_rate)``, so a detector
        on an enriched set sits near a low ceiling however good it is
        (``DECISIONS.md`` 047).
    ranking_absent_reason: Why ``auroc``/``recall``/``precision`` are
        absent, when they are. Carried because **the metrics alone cannot
        distinguish the two causes**: a single-class envelope and a
        threshold that flagged nothing both leave the ranking triple empty
        with a present ``flag_rate`` and ``fpr``. Issuance used to infer
        "single class" from an absent AUROC and wrote "measured no
        positives in this eval set" into a refusal for a 600-item set that
        had plenty (``DECISIONS.md`` 108).
    extra: Any additional metrics, each carrying its own kind.

## controlplane/intake/contract.py

The input contract: a customer's scored items, read strictly.

### InputError

[Source](../../controlplane/intake/contract.py#L75)

A file that does not meet the contract.

Distinct from a refusal. This means *we cannot read what you sent*; a
refusal means *we read it and the evidence does not support a warrant*.
Conflating them would turn a fixable typo into an apparent verdict on the
detector.

### ScoredItems

[Source](../../controlplane/intake/contract.py#L86)

One detector's scores and the ground truth they are judged against.

### load_scored_items

[Source](../../controlplane/intake/contract.py#L286)

```python
load_scored_items(path: str | Path, *, require_both_classes: bool=True)
```

Read a customer's scored items, refusing anything that breaks the contract.

Args:
    path: A ``.csv`` or ``.jsonl`` file.
    require_both_classes: Preserve legacy certification rejection by default.
        Release evaluation opts out to retain a study with a missing
        denominator. New release registrations report REFUSED; the legacy
        protocol retains UNVALIDATED for replay (DECISIONS 185; Codex-parallel
        decision 200, docs/decisions/CODEX-PARALLEL.md).

Returns:
    The parsed :class:`ScoredItems`.

Raises:
    InputError: Naming the column, the row and what was expected. Never
        coerces, fills or drops.

## controlplane/intake/certify.py

Certify a customer's detector against a false-positive budget, or refuse.

### CertificationResult

[Source](../../controlplane/intake/certify.py#L37)

A warrant or a refusal, with everything needed to act on either.

### certify_budget

[Source](../../controlplane/intake/certify.py#L189)

```python
certify_budget(items: ScoredItems, budget: float, alpha: float)
```

The certification step itself, and the only copy of it.

``certify --budget`` and ``certify --frontier`` both call this, so the two
cannot disagree about a status, a threshold or the unit of inference. They
did until ``DECISIONS.md`` 190: the frontier dropped the ``group`` column and
certified grouped files at item level, reporting budgets as certified that
this function refuses.

Quantity: the lowest threshold whose one-sided Clopper-Pearson upper bound
on the false-positive rate clears ``budget``. Propagation: exact binomial
bound over independent negative units -- items, or equal-sized clusters
when the file is grouped, a cluster counting as a false positive when any
member fires (:func:`controlplane.validation.warrant_stats.certify_fpr`).

Raises:
    ValueError: If the file is grouped with unequal group sizes.

### certify_items

[Source](../../controlplane/intake/certify.py#L227)

```python
certify_items(config: Config, items: ScoredItems, *, budget: float, alpha: Optional[float]=None, selection: Optional[dict[str, Any]]=None, grouped_boundary_abstention: bool=True, grouped_rate_boundary_abstention: Optional[bool]=None)
```

Certify ``items``' detector at ``budget``, or refuse with the shortfall.

Quantity: the detector's false-positive rate on the supplied negatives,
bounded above, and the lowest threshold whose bound clears ``budget``.
Propagation: one-sided Clopper-Pearson upper bound at ``alpha``, the
same bound :func:`controlplane.validation.warrant_stats.certify_fpr`
uses, so a customer's certificate and a published warrant mean the
same thing. Recall at the chosen threshold uses a percentile bootstrap
over independent groups when declared, or over items otherwise.

Args:
    config: Supplies the bootstrap count, coverage and seed; the grouped
        boundary protocol is recorded separately from historical research.
    items: The parsed input.
    budget: Target false-positive rate, in (0, 1).
    alpha: Certification level. Defaults to ``1 - config.validation.ci``.
    selection: When the budget was picked off a frontier, that frontier's
        digest, grid, ``row_alpha`` and ``family_alpha`` (``DECISIONS.md``
        195). ``alpha`` must then be its ``row_alpha``; the record keeps
        ``family_alpha`` for every later test on fresh labels.
    grouped_boundary_abstention: New records use vacuous grouped recall and
        precision bounds on bootstrap collapse. False is only for exact
        replay of an older record without a metrics protocol (219).
    grouped_rate_boundary_abstention: New records also withhold collapsed
        grouped flag-rate intervals; False with recall/precision abstention
        replays v1. None follows grouped_boundary_abstention (221).

Returns:
    A :class:`CertificationResult`, VALID or REFUSED.

Raises:
    ValueError: If the budget is out of range, or the file is grouped with
        unequal group sizes — see below.

### input_sha256

[Source](../../controlplane/intake/certify.py#L390)

```python
input_sha256(items: ScoredItems)
```

One digest for one scored file, whatever order its rows are in (195).

The release path's convention (``release/evaluate.py``, ``data_sha256``):
the canonical digest of the sorted ``(sha256 of item id, label, score)``
rows, so two commands name one file by one digest. A grouped file -- which
the release path refuses -- appends each row's group digest.

### evidence_sha256

[Source](../../controlplane/intake/certify.py#L414)

```python
evidence_sha256(items: ScoredItems)
```

Bind every scored-file field that can affect certification (211).

The existing frontier digest intentionally excludes ``label_2`` because
second review changes no frontier row. A certify record also reports second
review, so its own binding must include that column. The seeded bootstrap
samples array positions, so row order affects finite interval endpoints and
is bound too (212). Source path and ignored passthrough columns are excluded.

## controlplane/intake/verify.py

Replay a certify result against retained scored rows (DECISIONS 211-212).

### CertificationVerification

[Source](../../controlplane/intake/verify.py#L36)

A replay result, deliberately distinct from the warrant's verdict.

### load_evidence_record

[Source](../../controlplane/intake/verify.py#L47)

```python
load_evidence_record(path: str | Path)
```

Read one unambiguous JSON object; duplicate keys cannot silently win.

### verify_certification

[Source](../../controlplane/intake/verify.py#L81)

```python
verify_certification(record: dict[str, Any], items: ScoredItems, config: Config, *, frontier_record: Optional[dict[str, Any]]=None)
```

Recompute material certificate fields; never infer authorship or time.

A matching file and record can still be rewritten together by their holder.
This is arithmetic and input-binding verification, not authentication.

## controlplane/release/contract.py

Freeze identity, selection and holdout membership before evaluation.

### canonical_json

[Source](../../controlplane/release/contract.py#L19)

```python
canonical_json(value: Any)
```

Use one finite, deterministic encoding for every evidence digest.

### digest

[Source](../../controlplane/release/contract.py#L25)

```python
digest(value: Any)
```

Bind structured values without relying on indentation or key order.

### utc_time

[Source](../../controlplane/release/contract.py#L30)

```python
utc_time(value: str)
```

Reject naive times so expiry cannot depend on the reader's timezone.

### timestamp

[Source](../../controlplane/release/contract.py#L43)

```python
timestamp(now: datetime | None=None)
```

Keep test clocks injectable without accepting timezone ambiguity.

### ReleaseSpec

[Source](../../controlplane/release/contract.py#L54)

Declared criteria; positive recall prevents a never-fire detector passing.

### id_hashes

[Source](../../controlplane/release/contract.py#L100)

```python
id_hashes(ids: Iterable[str])
```

Check membership without exporting raw IDs; hashes remain sensitive.

Unsalted hashes allow guessing low-entropy IDs. Stable independent question
IDs and detection of semantic duplicates remain the caller's responsibility.

### ReleaseContract

[Source](../../controlplane/release/contract.py#L115)

A content-addressed local registration, never a trusted timestamp.

### register

[Source](../../controlplane/release/contract.py#L166)

```python
register(spec: ReleaseSpec, development_ids: Iterable[str], holdout_ids: Iterable[str], *, now: datetime | None=None)
```

Freeze disjoint membership, enforcing the question-split invariant.

### read_document

[Source](../../controlplane/release/contract.py#L186)

```python
read_document(path: Path)
```

Reject duplicate keys and nonstandard non-finite JSON numbers.

### write_document

[Source](../../controlplane/release/contract.py#L195)

```python
write_document(path: Path, value: dict)
```

Refuse replacement, including concurrent attempts at the same path.

An interrupted write can leave an incomplete file; verification rejects it.
There is no overwrite flag to silently erase a previous decision.

### read_ids

[Source](../../controlplane/release/contract.py#L206)

```python
read_ids(path: Path)
```

Require one stable ID per line, without blanks or duplicates.

## controlplane/release/evaluate.py

Fixed-holdout inference with simultaneous uncertainty (DECISIONS 184).

### binomial_rate

[Source](../../controlplane/release/evaluate.py#L40)

```python
binomial_rate(k: int, n: int, alpha: float)
```

Invert binomial tails for an equal-tailed Clopper-Pearson interval.

This estimates a population proportion, not a count. With no denominator,
the point is undefined and the interval is vacuous; never substitute zero.

### identity_for

[Source](../../controlplane/release/evaluate.py#L57)

```python
identity_for(contract: ReleaseContract)
```

Require the scorer to restate identity instead of implicitly adopting it.

### software_provenance

[Source](../../controlplane/release/evaluate.py#L62)

```python
software_provenance(*, include_certify: bool=False)
```

Record executed source and runtime, including an honest repository state.

Wheels need no Git installation. Source hashes bind the implementation even
there; repository metadata is present only when running inside this checkout.
No customer paths, input rows or environment variables enter the record.
The separate label audit uses certify's effective-row digest, so its
manifest includes that module without changing earlier evaluation records.

### evaluate

[Source](../../controlplane/release/evaluate.py#L113)

```python
evaluate(contract: ReleaseContract, items: ScoredItems, identity: dict, *, now: datetime | None=None)
```

Measure a fixed operating point on exactly the registered holdout.

Five intervals each get alpha/5; the union bound gives joint coverage at
least 1-alpha. Lift propagates the recall/flag-rate rectangle conservatively.
No threshold, model or criterion is selected by this function.

### seal_evaluation

[Source](../../controlplane/release/evaluate.py#L189)

```python
seal_evaluation(measurement: dict)
```

Attach implementation provenance before calculating the evidence digest.

### verify_evaluation

[Source](../../controlplane/release/evaluate.py#L195)

```python
verify_evaluation(record: dict, contract: ReleaseContract, items: ScoredItems, identity: dict, *, now: datetime | None=None)
```

Recompute decisions from bound input; return current status with expiry.

Rehashing a fabricated metric is insufficient: every measurement field must
reproduce. This does not authenticate the record's author or software claim.

## controlplane/sampling/estimator.py

The on-traffic warrant: recall estimated on your traffic, not on a benchmark.

### EstimationError

[Source](../../controlplane/sampling/estimator.py#L62)

An on-traffic estimate was requested that the evidence cannot support.

### Band

[Source](../../controlplane/sampling/estimator.py#L67)

One score band of the unflagged stratum, and what was labelled in it.

Bands exist so that labels can be concentrated where the variance is
(``SPEC.md`` §6.3). With a single band the design is simple random sampling
of the unflagged pool, which is what month one runs.

Attributes:
    name: Band identifier, for reporting only.
    population: ``N_h``, unflagged items in this band this month.
    sampled: ``n_h``, items drawn and labelled.
    errors: ``k_h``, of those, confirmed incorrect.

### OnTrafficEstimate

[Source](../../controlplane/sampling/estimator.py#L114)

What this month's traffic says, with the exact half separated from the
estimated half.

Attributes:
    recall: ESTIMATED. The claim the labels were bought for.
    precision: EXACT. A census of the flagged stratum, free.
    confirmed_errors: EXACT. ``TP`` -- the yield. *"We surfaced this many
        real errors"*, with no sampling and no interval.
    errors_missed: ESTIMATED. ``q * N_B``, the errors in the pool nobody
        reviewed.
    unflagged_prevalence: ESTIMATED. ``q`` itself, reported because it is
        what was actually measured and everything else is a transform of it.
    labels_spent: Items labelled in the unflagged stratum.
    realised_margin: Half-width actually achieved on recall, against which
        a plan's declared margin can be checked.
    planned_margin: What was planned, when a plan was supplied.
    margin_met: Whether the realised half-width reached the planned one.
    proportional: Whether every band was sampled at the same fraction, which
        decides whether the interval is exact-conservative or approximate.
    interval_basis: Which of the two was used, in words.
    bands: The unflagged strata as supplied.
    notes: Anything a reader must know before quoting these numbers.

### estimate_on_traffic

[Source](../../controlplane/sampling/estimator.py#L277)

```python
estimate_on_traffic(*, flagged_reviewed: int, flagged_confirmed: int, bands: Sequence[Band], flagged_population: Optional[int]=None, ci: float=0.95, planned_margin: Optional[float]=None, kappa: Optional[float]=None, kappa_floor: float=0.6)
```

Recall and precision on one month of real traffic.

Quantity: finite-population recall and precision on the realised month.
Propagation: Clopper-Pearson (or stratified-normal under Neyman) on ``q``,
carried into recall by the exact monotone transform
``R = TP/(TP + q*N_B)``, which preserves coverage because ``R`` is strictly
decreasing in ``q``.

Args:
    flagged_reviewed: ``N_A``. Items the detector flagged, all reviewed.
    flagged_confirmed: ``TP``. Of those, confirmed incorrect. Exact.
    bands: The unflagged stratum, one :class:`Band` per score band. A single
        band is simple random sampling, which is what month one runs.
    flagged_population: Items the detector flagged this month, when that
        differs from the number reviewed. Supplying a larger value is
        refused: the whole reason ``TP`` and precision are free of intervals
        is that stratum A is a census, and a sampled stratum A makes both of
        them estimates. Left ``None``, the reviewed count is taken as the
        census.
    ci: Coverage for every interval returned. Only 0.95 is supported.
    planned_margin: The recall half-width a :class:`~.planning.LabelPlan`
        promised, so the realised one can be reported against it.
    kappa: Measured inter-rater agreement on the double-labelled subset. An
        interval computed from labels that two reviewers disagree about is
        narrower than the evidence supports, so a low value widens it.
    kappa_floor: Below this, the recall interval is widened by ``1/kappa``
        and the reason recorded on the metric. ``CLAUDE.md`` names a +/-5pp
        recall interval at kappa 0.5 as meaningless; this makes it wide
        instead of meaningless.

Returns:
    The estimate, with exact and estimated quantities in separate fields.

Raises:
    EstimationError: If the flagged census is inconsistent, if no labels
        were drawn from the unflagged pool, or if the confirmed count
        exceeds the reviewed one.

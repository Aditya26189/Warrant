# Data origins and evidence lineage

This chapter separates the origin of a question, the origin of an answer,
the source of a label and the calculation that produces a reported number.

## Categories

| Evidence | Example | Scope |
|---|---|---|
| Model measurement on public questions | TriviaQA generations and probe scores | Recorded model behavior under a particular matching rule |
| Handcrafted challenge | Hinglish PII and benign near-boundary cases | Behavior on authored cases and synthetic identifiers |
| Controlled demonstration | Gate and drift replay | Enumerated states or constructed streams |
| Simulation | Votes, sampling coverage and monitoring years | A specified generating process |
| Released-record accounting | Terminal-Bench final records | What the pinned exported files identify |
| Bounded feasibility inspection | Stopping-feedback sources | Availability of the fields required for a predeclared question |

`data_source: measured` does not mean naturally sampled customer traffic.
A detector can be measured on a constructed challenge.

## TriviaQA lineage

The [TriviaQA paper](https://aclanthology.org/P17-1147/) identifies the source
question-answer collection. The project loader selects and deduplicates
questions, constructs prompts and splits by question identity.

The project records answers from the named Qwen model under its declared
generation settings. The detector labels concern those responses, not merely
the dataset's original evidence documents.

The [matching rules](../../controlplane/extract/triviaqa.py) produce correctness
labels. Lenient alias matching is not independent human adjudication. Strict
matching supplies a sensitivity comparison, not an automatically superior
gold standard.

The manifest records model/layer, system prompt, decoding and response-length
settings. The [loader](../../controlplane/extract/model.py) does not pass an
explicit immutable revision in its `from_pretrained` calls. Its provenance
method records model name and configuration facts rather than a complete
weight hash. Downloading the same identifier later must not be assumed to
reconstruct the exact historical weights.

## Frozen manifest inventory

| Manifest | Rows | Positive share | Recorded content hash |
|---|---:|---:|---|
| [triviaqa-600](../../evalsets/triviaqa-600.json) | 2400 | 0.466667 | `e77c64f908491ad1751ccbc0a05f85343591cd0f9b876022f1b7342bedde31b0` |
| [triviaqa-2400-t960](../../evalsets/triviaqa-2400-t960.json) | 2400 | 0.466667 | `3c481c8f9ba5cd407400017621c4daf3a2370b020a1149a55ca8cc6951da5621` |
| [hinglish-pii-200](../../evalsets/hinglish-pii-200.json) | 200 | 0.510000 | `39b541efa4299f4db51fb955d16f3a74f78079c93d0f69a86570983bf6d6a639` |
| [hinglish-pii-200b](../../evalsets/hinglish-pii-200b.json) | 200 | 0.510000 | `1e2dee9d8fa91cba144e6c8f74e4632250e9ac3150deea49389bb49402451e5b` |
| [hard-negatives-200](../../evalsets/hard-negatives-200.json) | 200 | 0.000000 | `d28e4de2024de10d1e4be564f9bd361175399eac23735a7bef6540386029854c` |
| [canary-20-triviaqa](../../evalsets/canary-20-triviaqa.json) | 20 | 1.000000 | `82a5a11c2b3a847d06d7236eec3d3b03b7a095f68e16b9079b7a23f2fa780507` |
| [banking-dual-24](../../evalsets/banking-dual-24.json) | 24 | 0.541667 | `09bbdbd6a316536b492ef1b15a70486b64a7f44d92de9c5ec7cc3326fa95b7cc` |

This table is rendered from committed manifest fields. The recorded content
hash identifies the project's canonicalized content. A raw-file SHA-256 in the
audit identifies exact JSON bytes; these serve different purposes.

## A resplit is not a new corpus

`triviaqa-2400-t960` derives from the same original items with a changed
declared partition. Its construction records source hashes and the resplit
rationale.

It supports a within-project comparison, not an independently collected
benchmark. An earlier and later test metric need pairing on common held-out
items before their difference is attributed to a model/training change.

A whole manifest's base rate can differ from the rate of its evaluated test
split. State the denominator rather than inferring it from the file name.

## Constructed long context

The transfer path changes prompt context used for feature extraction while
reusing the original short-context responses and labels. It does not generate
a new long-context response for every target row.

Thus it measures representation transfer relative to fixed recorded outcomes.
The expanded manifests and extraction caches are large and not all committed.
See [reproduction](reproduction.md) for the resulting boundary.

## Handcrafted PII and benign cases

The PII sets cross hand-authored scenarios with systematic disclosure forms.
Identifiers are synthetic. Positive enrichment means that measured precision
belongs to the challenge distribution.

The companion `200b` set changes the seed and expands forms beyond the base
inventory. This is a useful variant check, not independently authored
production validation.

The benign challenge renders a smaller set of scenarios in repeated framings.
Those are dependent rows. Historical row-binomial intervals remain historical,
not independent-unit assurance.

Canaries are selected regression tripwires. The TriviaQA canaries were chosen
using known probe behavior on training examples. Passing that control detects
some changes; it is not independent evidence that the probe is generally good.

## Simulations and workflow examples

Sampling coverage, allocation effects, label plans, score-free votes and
recheck comparisons use declared scenarios. No real customer label expenditure,
commercial judge or production monitoring program was measured by those runs.

The action-gate study counts behavior on authored workflows. Exactness of its
count does not make the set representative of production users or attackers.

## Released agent-evaluation records

The unscored-trial study pins the official
[Terminal-Bench release](https://huggingface.co/datasets/harborframework/terminal-bench-2-leaderboard/tree/572b2614be2c0cb2527e14f5b1e4026f1072e6c1).
The reviewed portable bundle retains scalar projections, original and derived
hashes, source URLs and third-party notices.

A released final record is not an authoritative original execution roster.
Retries, omitted attempts, export causes and historical website adjudication
need additional primary evidence.

The present documentation audit inspects retained artifacts and source
references. It does not redownload or independently adjudicate the complete
original corpus. Earlier acquisition and replay receipts retain their own
dates and scope.

## Feasibility data

The stopping-feedback study inspected bounded source examples for aligned
usage/time or expense information. Tokenizable transcripts can answer some
proxy questions, but do not automatically supply comparable original suffix
expense.

Its STOP concerns the predeclared mechanism and inspected inputs. It is not a
zero-effect estimate for a policy that was never fitted.

## Licensing and availability

MIT code licensing does not replace the terms of a dataset, model or bundled
third-party input. Preserve the
[portable-input notices](../../experiments/unscored_trials/portable_inputs/NOTICE.md).

The development repository was private during preprint preparation. The
prepared archival package includes tracked source and retained CPU evidence;
it does not automatically include untracked private review packages, real
private labels or ignored extraction caches.

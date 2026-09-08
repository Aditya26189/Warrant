# Certifying detectors we did not build

Warrant bounds a detector's false-positive rate at a budget you choose, or
refuses to. Every number this project had published until now was about its own
detector, on its own corpus. This is the same machinery pointed at software
written by other people, on public data this project did not construct.

Everything below runs on a laptop CPU. No GPU, no paid API, no vendor was
contacted.

## What was measured

Seven detector–task pairings, each certified across twenty false-positive
budgets from 0.01 to 0.20.

| detector | version / revision | task | source data |
|---|---|---|---|
| `presidio-analyzer` | 2.2.364 | five entity types: EMAIL_ADDRESS, CREDIT_CARD, IP_ADDRESS, PHONE_NUMBER, URL | `ai4privacy/pii-masking-200k` |
| `protectai/deberta-v3-base-prompt-injection-v2` | `90c9989b` | prompt injection | `deepset/prompt-injections` |
| `probe-qwen2.5-7b-instruct-T1-last_token` (ours) | frozen scores | answer incorrectness | this project's `triviaqa-600` |

Results: **[`results/external/MATRIX.md`](../results/external/MATRIX.md)**.

Every detector ran at its documented default configuration. Nothing was tuned,
in either direction, and each row records the exact configuration used, a link
to where that default is documented, and the one command that reproduces it.

## How a task is defined

For the PII rows the question is **per entity type**: *does this text contain a
credit card number?* — not *is this text clean?*

That is forced by the data, and the reason is worth stating because it changes
what the numbers mean. Every row of `ai4privacy/pii-masking-200k` contains some
PII. As a "contains PII" task it is single-class: there are no negatives, so
there is no false-positive rate to bound and no warrant to issue.

Defining the task per entity type recovers negatives from the dataset's own
annotations — a row is negative for CREDIT_CARD if it carries no credit-card
span, even though it carries other PII. The alternative, pairing these positives
with negatives from some general corpus, would have been worse: a Wikipedia
sentence naming a person **does** contain PII, so labelling it negative would
put wrong labels into a false-positive rate.

## What the numbers say

Two of the five Presidio entity types — EMAIL_ADDRESS and URL — separate the
data completely: recall 1.000, with no false positives on roughly 1870 negative
items, at every budget on the grid. IP_ADDRESS reaches recall 1.000 from a 0.10
budget upward.

CREDIT_CARD is the outlier at recall 0.070 [0.030, 0.117], flat across every
budget. **That is a property of this pairing, and reading it as a verdict on
Presidio would be wrong.** Presidio's credit-card recognizer validates a
checksum; the dataset's numbers are synthetically generated. A generated number
that does not satisfy the checksum is one the recognizer is designed to reject,
and a detector declining to fire on a string that cannot be a real card number
is behaving correctly. What the cell measures is agreement between one vendor's
validation rules and another project's synthetic generator.

PHONE_NUMBER runs 0.103 at tight budgets to 0.673 at 0.10 and above.

The prompt-injection classifier shows the shape a budget curve usually has:
recall 0.350 at a 0.01 budget rising to 0.813 at 0.20 — the trade this whole
tool exists to make legible, where a stronger promise about false positives
costs recall.

Our own detector is in the table on the same terms and is not the strongest
entry in it. That is the point of including it.

## What these numbers are not

**They are not a ranking.** The rows answer different questions on different
data. A number in one row is not comparable with a number in another. What is
comparable *within* a row is the shape across budgets.

**They are not a general claim about any detector.** Each is a measurement of
one version of one tool on one public dataset at one point in time. Presidio's
email recognizer separating perfectly on synthetic emails says the recognizer
and the generator agree; it does not establish what happens on messy production
text.

**They are all in-sample, including ours.** Each threshold is certified on the
same data it is then scored on. That is a real limitation and it applies
identically to every row, which is what makes them comparable to each other. It
also means no cell here is a warrant you should carry into production.

**A refusal is not a defect.** Tighter budgets need more clean negatives — 299
at 0.01 against 14 at 0.20 — and a detector refused at one budget on one dataset
may certify comfortably at a looser one on the same data.

## What could not be measured

Warrant was built around Indian identifier classes — Aadhaar, PAN, UPI, IFSC —
and none of them appears above. **No public dataset with labels for them was
found.** `pii-masking-200k` carries 56 entity types across its English rows and
not one is an India-specific identifier.

That is a gap in available public data rather than a finding about any detector.
It is also separable from something this project already measured: presidio-analyzer
2.2.364 exposes 19 supported entity types, none of them India-specific, which is
a *coverage* result and needs no labelled data. Certifying performance on those
identifiers needs labelled data that does not appear to exist publicly.

Also absent: anything requiring a GPU or a paid API key.

## Reproducing any of it

```bash
git clone https://github.com/Aditya26189/Warrant.git && cd Warrant
pip install -r requirements.lock.txt
python scripts/23_certify_external.py --list
python scripts/23_certify_external.py --pairing presidio-credit_card
```

Each run fetches its dataset and model at the pinned revision recorded in the
matrix, scores on CPU, and writes `results/external/<pairing>/`. Nothing is
redistributed here: no dataset rows, and no per-item scores derived from them.

Adding your own detector or dataset is three dataclasses in
`controlplane/external/registry.py`. Everything downstream — the budget grid,
the Clopper-Pearson certification, the intervals — is unchanged.

**If you think a result is wrong, the command above is how to show it.** The
configuration each detector ran at is printed beside its row. A measurement that
a vendor can re-run and disagree with is the only kind of external claim this
project is entitled to make.

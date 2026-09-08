# The external matrix

Third-party detectors, at their documented defaults, on public datasets this project did not construct. Our own detector is in the table on the same terms as the others.

Each cell is **recall with its 95% interval** at the certified threshold for that false-positive budget. `REFUSED` means no threshold on that data could be certified at that budget. A `*` marks a point where lift's 95% lower bound does not clear 1.0.

Produced at commit `8e709dc932a6`, config `533fb74983fcd8af`, dirty `False`.

| detector | task | FPR 0.01 | FPR 0.05 | FPR 0.10 | FPR 0.20 |
|---|---|---|---|---|---|
| `protectai/deberta-v3-base-prompt-injection-v2` | is the prompt an injection attempt? | 0.350 [0.283, 0.411] | 0.616 [0.547, 0.683] | 0.729 [0.670, 0.789] | 0.813 [0.755, 0.866] |
| `probe-qwen2.5-7b-instruct-T1-last_token` | is the model's answer incorrect? | 0.011 [0.000, 0.026] * | 0.231 [0.184, 0.284] | 0.448 [0.393, 0.507] | 0.646 [0.595, 0.705] |
| `presidio-analyzer` | does the text contain a CREDIT_CARD? | 0.070 [0.030, 0.117] | 0.070 [0.030, 0.117] | 0.070 [0.030, 0.117] | 0.070 [0.030, 0.117] |
| `presidio-analyzer` | does the text contain a EMAIL_ADDRESS? | 1.000 [0.978, 1.000] | 1.000 [0.978, 1.000] | 1.000 [0.978, 1.000] | 1.000 [0.978, 1.000] |
| `presidio-analyzer` | does the text contain a IP_ADDRESS? | 0.000 [0.000, 0.029] * | 0.488 [0.403, 0.577] | 1.000 [0.971, 1.000] | 1.000 [0.971, 1.000] |
| `presidio-analyzer` | does the text contain a PHONE_NUMBER? | 0.103 [0.050, 0.163] | 0.103 [0.050, 0.163] | 0.673 [0.579, 0.762] | 0.673 [0.579, 0.762] |
| `presidio-analyzer` | does the text contain a URL? | 1.000 [0.972, 1.000] | 1.000 [0.972, 1.000] | 1.000 [0.972, 1.000] | 1.000 [0.972, 1.000] |

## What each row was run against

### `injection-deepset`

- **detector** `protectai/deberta-v3-base-prompt-injection-v2` at version/revision `90c9989b1a342275` (apache-2.0) — [source](https://huggingface.co/protectai/deberta-v3-base-prompt-injection-v2), [docs](https://huggingface.co/protectai/deberta-v3-base-prompt-injection-v2)
- **configuration**: AutoModelForSequenceClassification at the pinned revision, eval mode, truncation at the model's own max_length. The item score is softmax(logits)[INJECTION], with the INJECTION index read from the loaded config's id2label rather than assumed.
- **not tuned for this evaluation**: True
- **dataset** `deepset/prompt-injections` at revision `4f61ecb038e9c3fb`, split `train`, licence apache-2.0, accessed 2026-09-09 — [source](https://huggingface.co/datasets/deepset/prompt-injections)
- **evidence**: 546 items, 203 positive, 343 negative
- **reproduce**: `python scripts/23_certify_external.py --pairing injection-deepset`

### `ours-triviaqa`

- **detector** `probe-qwen2.5-7b-instruct-T1-last_token` at version/revision `results/scores/v` (MIT (this project)) — [source](https://github.com/Aditya26189/Warrant), [docs](https://github.com/Aditya26189/Warrant/blob/main/docs/METHODS.md)
- **configuration**: The frozen test-split scores from Phase 0/1. Same grid, same criterion, same presentation as every other row -- D37.
- **not tuned for this evaluation**: True
- **dataset** `triviaqa-600 (this project)` at revision `sha256:e77c64f90`, split `test`, licence see repository, accessed 2026-09-09 — [source](https://github.com/Aditya26189/Warrant)
- **evidence**: 600 items, 277 positive, 323 negative
- **reproduce**: `python scripts/23_certify_external.py --pairing ours-triviaqa`
- **note**: Ours, included so our own detector appears on identical terms (D37).

### `presidio-credit_card`

- **detector** `presidio-analyzer` at version/revision `2.2.364` (MIT) — [source](https://github.com/microsoft/presidio), [docs](https://microsoft.github.io/presidio/analyzer/)
- **configuration**: AnalyzerEngine() with no arguments -- the stock recognizer registry and the default spaCy en_core_web_lg NLP engine. analyze(text, language='en', entities=[<one entity>]). No threshold is passed, so the engine's own default applies; the item score is the maximum confidence Presidio returns for that entity, or 0.0 when it returns nothing.
- **not tuned for this evaluation**: True
- **dataset** `ai4privacy/pii-masking-200k` at revision `7c22e6816b8fc24b`, split `train`, licence not declared in card metadata, accessed 2026-09-09 — [source](https://huggingface.co/datasets/ai4privacy/pii-masking-200k)
- **evidence**: 2000 items, 129 positive, 1871 negative
- **reproduce**: `python scripts/23_certify_external.py --pairing presidio-credit_card`
- **note**: Every row contains PII, so a 'contains any PII' task on it is single-class and unbounded. Tasks are defined per entity type from the dataset's own span labels. DECISIONS 139.

### `presidio-email_address`

- **detector** `presidio-analyzer` at version/revision `2.2.364` (MIT) — [source](https://github.com/microsoft/presidio), [docs](https://microsoft.github.io/presidio/analyzer/)
- **configuration**: AnalyzerEngine() with no arguments -- the stock recognizer registry and the default spaCy en_core_web_lg NLP engine. analyze(text, language='en', entities=[<one entity>]). No threshold is passed, so the engine's own default applies; the item score is the maximum confidence Presidio returns for that entity, or 0.0 when it returns nothing.
- **not tuned for this evaluation**: True
- **dataset** `ai4privacy/pii-masking-200k` at revision `7c22e6816b8fc24b`, split `train`, licence not declared in card metadata, accessed 2026-09-09 — [source](https://huggingface.co/datasets/ai4privacy/pii-masking-200k)
- **evidence**: 2000 items, 163 positive, 1837 negative
- **reproduce**: `python scripts/23_certify_external.py --pairing presidio-email_address`
- **note**: Every row contains PII, so a 'contains any PII' task on it is single-class and unbounded. Tasks are defined per entity type from the dataset's own span labels. DECISIONS 139.

### `presidio-ip_address`

- **detector** `presidio-analyzer` at version/revision `2.2.364` (MIT) — [source](https://github.com/microsoft/presidio), [docs](https://microsoft.github.io/presidio/analyzer/)
- **configuration**: AnalyzerEngine() with no arguments -- the stock recognizer registry and the default spaCy en_core_web_lg NLP engine. analyze(text, language='en', entities=[<one entity>]). No threshold is passed, so the engine's own default applies; the item score is the maximum confidence Presidio returns for that entity, or 0.0 when it returns nothing.
- **not tuned for this evaluation**: True
- **dataset** `ai4privacy/pii-masking-200k` at revision `7c22e6816b8fc24b`, split `train`, licence not declared in card metadata, accessed 2026-09-09 — [source](https://huggingface.co/datasets/ai4privacy/pii-masking-200k)
- **evidence**: 2000 items, 127 positive, 1873 negative
- **reproduce**: `python scripts/23_certify_external.py --pairing presidio-ip_address`
- **note**: Every row contains PII, so a 'contains any PII' task on it is single-class and unbounded. Tasks are defined per entity type from the dataset's own span labels. DECISIONS 139.

### `presidio-phone_number`

- **detector** `presidio-analyzer` at version/revision `2.2.364` (MIT) — [source](https://github.com/microsoft/presidio), [docs](https://microsoft.github.io/presidio/analyzer/)
- **configuration**: AnalyzerEngine() with no arguments -- the stock recognizer registry and the default spaCy en_core_web_lg NLP engine. analyze(text, language='en', entities=[<one entity>]). No threshold is passed, so the engine's own default applies; the item score is the maximum confidence Presidio returns for that entity, or 0.0 when it returns nothing.
- **not tuned for this evaluation**: True
- **dataset** `ai4privacy/pii-masking-200k` at revision `7c22e6816b8fc24b`, split `train`, licence not declared in card metadata, accessed 2026-09-09 — [source](https://huggingface.co/datasets/ai4privacy/pii-masking-200k)
- **evidence**: 2000 items, 107 positive, 1893 negative
- **reproduce**: `python scripts/23_certify_external.py --pairing presidio-phone_number`
- **note**: Every row contains PII, so a 'contains any PII' task on it is single-class and unbounded. Tasks are defined per entity type from the dataset's own span labels. DECISIONS 139.

### `presidio-url`

- **detector** `presidio-analyzer` at version/revision `2.2.364` (MIT) — [source](https://github.com/microsoft/presidio), [docs](https://microsoft.github.io/presidio/analyzer/)
- **configuration**: AnalyzerEngine() with no arguments -- the stock recognizer registry and the default spaCy en_core_web_lg NLP engine. analyze(text, language='en', entities=[<one entity>]). No threshold is passed, so the engine's own default applies; the item score is the maximum confidence Presidio returns for that entity, or 0.0 when it returns nothing.
- **not tuned for this evaluation**: True
- **dataset** `ai4privacy/pii-masking-200k` at revision `7c22e6816b8fc24b`, split `train`, licence not declared in card metadata, accessed 2026-09-09 — [source](https://huggingface.co/datasets/ai4privacy/pii-masking-200k)
- **evidence**: 2000 items, 129 positive, 1871 negative
- **reproduce**: `python scripts/23_certify_external.py --pairing presidio-url`
- **note**: Every row contains PII, so a 'contains any PII' task on it is single-class and unbounded. Tasks are defined per entity type from the dataset's own span labels. DECISIONS 139.

## How to read this, and how not to

**These are not rankings.** The rows answer different questions on different data; a number in one row is not comparable with a number in another. What is comparable within a row is the shape across budgets: how much recall survives as the false-positive budget tightens.

**A refusal is not a defect.** It says the data available could not support a certified threshold at that budget. Tighter budgets need more clean negatives — 299 for 0.01 against 14 for 0.20 — and a detector refused at 0.01 on one dataset may certify comfortably at 0.05 on the same one.

**Every detector ran at its documented default.** Nothing was tuned for this evaluation, in either direction. If you believe a configuration is wrong, the reproduction command for that row is above and the configuration it used is stated beside it.

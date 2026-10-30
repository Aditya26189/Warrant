# Source and example inspection

These are convenience schema examples, not an unfiltered deployment population.
The inspection outputs preserve source URLs, SHA-256 hashes, returned revisions
and clean code identities. Raw messages, patches and transcripts remain outside
Git. Third-party observations retain [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/)
attribution; see [NOTICE](NOTICE.md).

| Source | Pinned revision | Executor information | Sample evidence |
| --- | --- | --- | --- |
| [Nebius](https://huggingface.co/datasets/nebius/SWE-rebench-openhands-trajectories/tree/35455389ab51bf5e2306bfd436ef72d0f98bf882) | `35455389ab51bf5e2306bfd436ef72d0f98bf882` | Card declares Qwen3-Coder-480B-A35B-Instruct / OpenHands 0.54.0; the row does not bind an individual executor configuration | [Summary](results/nebius_row0-summary.json) |
| [NVIDIA](https://huggingface.co/datasets/nvidia/Open-SWE-Traces/tree/4fa4c2ae9afc6b397bc50391d43450c79993c138) | `4fa4c2ae9afc6b397bc50391d43450c79993c138` | OpenHands split; row names Qwen3.8-Flash-Next, thinking enabled, xhigh; harness version absent | [Summary](results/nvidia_row0-summary.json) |

| Observed field/check | Nebius row 0 | NVIDIA v2.0/OpenHands row 0 |
| --- | --- | --- |
| Issue | `PlasmaFAIR__sdf-xarray-24` | `saltstack_libnacl_pr89` |
| Repository | `PlasmaFAIR/sdf-xarray` | `saltstack/libnacl` |
| Ordered messages | 185 | 33 |
| Assistant messages / recorded tool calls | 92 / 92 | 16 / 16 |
| Recorded final `resolved` | 0 | 0 |
| Reported partial response / truncated cells | false / none | false / none |
| Structured usage/cost/time fields located | none | none |

Counts come from the linked generated JSON, not a proposed stopping simulation.
Source response hashes are respectively
`54270287b38d6031c5c3548bf0bfcf63b6267eacbf322ffca3c3b2a07239cf75` and
`3fd9c15650a874ab5344a9d6b0ff96be865e166eb5a2b703928a0b2bebb79067`.
The engineering probes and clean scripted validation returned identical bodies.

The rows support observable message/tool history and recorded terminal labels.
Nebius's `submit` exit status is not a successful verifier result. NVIDIA's
documented `resolved=-1` denotes unavailable outcome; it must not be coded as
failure. No missing-label rate was estimated from these examples.

Candidate prefix fields would have to stop at a predetermined observable
checkpoint. Final patch, exit status, final verifier result, future messages,
final length, generated-test outcomes and NVIDIA reference/model-patch metadata
are excluded from any future prefix features. We did not fit such a model.

## Cost and population boundaries

| Accounting unit | Available evidence | Permitted interpretation |
| --- | --- | --- |
| Recorded billable usage or measured runtime/compute | Not in inspected records or typed schemas | No actual monetary/resource savings claim |
| Reconstructed transcript tokens | Saved text can be tokenized; not computed here | An explicit text-volume proxy, not recovered per-call input/cache/reasoning usage |
| Message/tool counts or UTF-8 bytes | Generated descriptive summaries | Corpus-native interaction/text units only |

The [Nebius collection report](https://nebius.com/blog/posts/openhands-trajectories-with-qwen3-coder-480b)
describes removing non-applying patches. Its released successes and failures
must not be confused with the success-only subset used for RFT training.
NVIDIA's [historical paper, sections 2.3–2.4](https://aclanthology.org/2026.findings-emnlp.131.pdf)
describes removing incomplete/environment-error, iteration-limit, malformed and
repeated-error trajectories and certain patch problems. Its pinned card records
subsequent git-hacking removal. Those historical rules cannot all be assumed for
current v2.0 without version-specific evidence. Neither release is an unfiltered
deployment stream.

The metadata tree exposes multiple NVIDIA model/harness groups. One intended
Qwen3.8-27B viewer configuration returned HTTP 500 twice; retries stopped. This
does not prove the underlying data are unavailable. Cheap same-issue linkage,
comparable selection and exact execution configuration remain unestablished.
Two distinct sample IDs do not establish corpus deduplication; no splits were
created and no zero-overlap claim is made. Release dates are not deployment time.

Bounded [footer/source notes](results/metadata-reconnaissance.json) explain why
ordinary message-column reads were avoided. Full-file Parquet hashes there are
upstream attestations, not a claim that the large files were downloaded and
independently rehashed. [Access commands](REPRODUCING.md) reproduce the accepted
small samples; they do not rebuild every exploratory metadata request.

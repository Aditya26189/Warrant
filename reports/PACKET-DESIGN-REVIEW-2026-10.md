# Evidence-package design review — 2 October 2026

## Question

Would a new `warrant package` command solve a real reviewer handoff problem,
or merely zip files the existing verifier already knows how to read?

The [existing handoff map](../docs/EVIDENCE-HANDOFF.md) names each file,
its owner, its purpose, and the correct replay command. The
[product-state map](../docs/PRODUCT-STATE.md) confirms that scored-file,
certificate, recheck-chain and scoped-release replay already exist.
October's `prepare` command adds a manifest that binds source export,
mapping and canonical scored bytes, but leaves source and mapping with their
owner. It does not copy customer data into a portable archive.

| Existing surface | Already answers | Extra value a package would have to demonstrate |
| --- | --- | --- |
| `prepare` / `verify-prepared` | Was a declared flat export transformed into the same canonical rows? | An owner can transfer the minimum permitted originals and mapping without losing their meaning or accidentally including excluded fields. |
| `certify` / `verify` | Does a retained certificate recompute on the same effective scored rows? | A second person can identify the right certificate and source rows without author guidance. |
| `release register` / `evaluate` / `verify` | Does the retained evaluation replay against the registered criterion, operating point and declared holdout? Registration alone is not a trusted timestamp. | A reviewer can see the registered spec, disjoint ID lists, context, evaluation and source in one correctly linked handoff. |
| `label-audit` / `verify-label-audit` | How sensitive is the fixed release result to label errors on the supplied rows? | The companion is presented as descriptive label sensitivity, not as a second release verdict or proof of label truth. |

The minimum contract for a **possible** future package is a manifest of
explicit relative members, hashes and their roles, plus an entry point that
calls the existing verifiers. It must refuse missing, stale, mismatched and
unexpected members separately; decline paths escaping the chosen directory;
never overwrite an existing destination; and require explicit opt-in before
copying scored rows. It must state which workflow is being packaged because
`certify` selects a threshold while `release` tests a preregistered one.
Source identifiers and group fields can still be sensitive. A checksum-only
bundle would not authenticate the author or certify the sample.

This is **not an approved implementation contract**. No permissioned customer
packet or reviewer has shown that the current file list and commands are
insufficient. The [incumbent comparison](INCUMBENT-PACKET-COMPARISON-2026-10.md)
also shows that exports and review interfaces are common. Before building,
ask a decision owner to replay one real packet using the current handoff map.
Record the specific missing file, mistaken step or unanswered question and
whether a manifest would fix it. If the owner can already reproduce the
decision and accepts the existing packet, stop package work. This preserves
the [October plan's](BUILD-PLAN-2026-10.md) evidence gate.

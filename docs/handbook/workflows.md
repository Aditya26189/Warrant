# Workflow guide

Choose a workflow by the decision you need to make. The commands below refer to
the implemented CLI; [generated help](cli-reference.md) is the authoritative
flag reference.

## Prepare an export

`prepare` maps explicit source columns into the scored-file contract. The
mapping declares label meaning and score direction. Its retained manifest makes
the transformation reviewable; the tool does not infer a scientifically valid
mapping from arbitrary data.

The public examples exercise a complete path:

```shell
python warrant.py prepare --input examples/export_certifies.csv --mapping examples/export_certifies_mapping.json --out ../warrant-review/prepared
python warrant.py verify-prepared --input examples/export_certifies.csv --mapping examples/export_certifies_mapping.json --prepared ../warrant-review/prepared
```

The prepared directory is a defined record, not a scratch folder. Preserve its
members and keep later output outside it. Exact option details and accepted
schemas are in the [input guide](../../docs/INPUT.md).

Preparation validates a mapping and its replay. It does not establish that a
positive label is correct or that rows are independently sampled.

## Certify one predeclared budget

Use `certify --budget` when the budget was selected independently of inspecting
the evaluation file. The procedure chooses an operating point and reports the
resulting rates and counts. It can refuse when the supplied independent units
cannot support the requested decision.

A detector that flags nothing can have a small false-positive rate while being
useless. That is why FPR, recall, precision and the realized flag rate answer
different questions. A supported FPR decision alone does not establish adequate
recall for an application.

The [open returned-bound issue](limitations.md) applies to the stronger
interpretation of the native adaptive numerical bound. Read that issue before
using the returned number as a calibrated population upper bound.

## Explore a frontier and retain the selection

A frontier exposes a declared grid of budgets and exact operating counts.
Looking at it is selection. A later single-budget run that ignores that
selection does not restore a predeclared question.

Retain the frontier and use the supported `--from-frontier` path when selecting
a budget from it. That path binds the chosen row to its adjusted level and
evidence. It does not validate an arbitrary unregistered search over detectors,
datasets or grids.

The [selection implementation](../../controlplane/intake/selection.py) and
[frontier implementation](../../controlplane/intake/frontier.py) describe the
implemented restrictions.

## Replay an ordinary recheck

An ordinary recheck evaluates fresh scored rows against a retained certificate.
It reports evidence about the bound separately from changes in score
distribution. A distributional change is not by itself proof of a particular
change in error rate.

Supply the retained original evidence when requesting the path that verifies
the source certificate first. The material records are the original input and
certificate, any selected frontier, the fresh batch and the recheck result.
`verify-recheck` replays this ordinary measurement.

A successful recheck replay authenticates none of those files. A party that
controls every copy can replace all of them consistently.

## Maintain a chain of rechecks

A chain makes a sequence one declared monitoring design. The horizon,
certificate, independent label units and prior history affect the result.
Continue from the current retained head rather than treating every batch as a
new independent opportunity to recertify.

The implementation separates statistical continuation from local publication:
linked records, a head, locks, interrupted-write handling and integrity checks
all matter. `verify-chain-recheck` requires the presented sequence prefix and
its scored batches. Verifying a prefix does not reveal an unpresented fork or
prove that it is the current authoritative history.

See [chain publication](../../controlplane/intake/chain_publication.py),
[chain verification](../../controlplane/intake/chain_verify.py) and the
[record guide](records-and-protocols.md).

## Register a release study

The `release` workflow freezes an already chosen operating threshold, the
application/detector identity, acceptance criteria, development IDs and holdout
membership. It then evaluates the scored holdout against that contract.

This is statistically different from `certify` choosing a threshold. Release
evaluation tests one fixed registered operating point and evaluates its declared
FPR and recall criteria together. Grouped input is unsupported by this release
protocol. Removing genuine groups does not make the IID assumption true.

Prepare the specification and identity context from the actual application
configuration. Use a future expiry appropriate to the study; a dated example
in historical documentation must be updated deliberately. The complete
register/evaluate/verify procedure is in
[the release guide](../../docs/RELEASE.md).

A registration file is not trusted notarization. Local file replacement
restrictions reduce accidental repeated evaluation; they cannot stop an owner
from copying a study or reusing the same holdout elsewhere.

## Package an evidence handoff

The handoff workflow packages a supported prepare-and-certify path into a new
local directory, verifies source mapping and certificate replay, and retains
member digests. It supports refused certificates as well as successful ones.

The original export can contain columns that preparation excluded. Packaging
therefore requires the explicit sensitive-input copy option documented in
[the input guide](../../docs/INPUT.md). This is a portability mechanism, not a
privacy filter. It does not package release studies or arbitrary chain histories.

## Keep labels and deployment assumptions separate

Second-review labels supply observed disagreement and sensitivity information.
They do not automatically change the primary certification verdict, prove
either reviewer correct or repair a biased review sample.

Likewise, recorded detector and application version strings are supplied
identity claims. Warrant does not inspect the deployed model weights, prompt,
retrieval system or running service to authenticate those strings.

## Select the right evidence record

| Question | Required retained material | Does not establish |
|---|---|---|
| Did preparation follow its mapping? | Original export, mapping, prepared rows and manifest | Correct mapping semantics or truthful labels |
| Does certification replay? | Certificate, effective scored rows, selected frontier if applicable | Population assumptions or source authenticity |
| Does one fresh recheck replay? | Exact certificate, fresh rows and ordinary result; original evidence when required | An entire monitoring history |
| Does a chain prefix replay? | Complete presented prefix and every bound batch | Absence of another fork or hidden continuation |
| Did the registered holdout clear criteria? | Contract, identity context, holdout rows and evaluation | Production approval or arbitrary repeated-study control |

For interpretation errors and schema failures, use
[troubleshooting](../../docs/TROUBLESHOOTING.md). For the statistical assumptions
behind each path, use [methods](methods.md).

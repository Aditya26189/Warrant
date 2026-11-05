# Command-line reference

Generated from the installed CLI parser, not a separately maintained flag list. Examples are explained in [the workflow guide](workflows.md). A refusal is a scientific outcome; inspect the documented exit behavior of the specific command.

## warrant

```text
usage: warrant [-h] [--version]
               {certify,verify,verify-recheck,verify-chain-recheck,recheck,plan,release,prepare,verify-prepared,handoff,chain}
               ...

Certify a detector against a false-positive budget, or refuse. Reads a CSV or JSONL of id,label,score. Nothing leaves your machine.

positional arguments:
  {certify,verify,verify-recheck,verify-chain-recheck,recheck,plan,release,prepare,verify-prepared,handoff,chain}
    certify             certify a detector from a file of scores and labels
    verify              recompute a certify record from its retained scored
                        file
    verify-recheck      replay an ordinary recheck against retained fresh
                        scored rows
    verify-chain-recheck
                        replay a retained linear chain prefix from its scored
                        batches
    recheck             is a warrant issued earlier still true on new data?
    plan                what it costs to keep a warrant true
    release             register and verify scoped holdout evidence
    prepare             map a flat scored export to a replayable local package
    verify-prepared     replay a prepared package from its original inputs
    handoff             copy and replay a prepared-export certify handoff
    chain               audit the records of a chain of rechecks

options:
  -h, --help            show this help message and exit
  --version, -V         print the version and exit

examples:
  warrant certify --input examples/certifies.csv --budget 0.05
  warrant certify --input examples/refuses.csv   --budget 0.01

the input contract is three columns: id, label (0/1, 1 = the
detector should fire), score (higher = more likely positive).
see docs/INPUT.md.
```

## warrant certify

```text
usage: warrant certify [-h] --input INPUT [--frontier] [--budget BUDGET]
                       [--out OUT] [--quiet] [--require-warrant]
                       [--from-frontier RECORD]

Picks the lowest threshold whose Clopper-Pearson upper bound on your negatives
clears the budget, then reports what the detector does there. Refuses when the
evidence cannot support the budget.

options:
  -h, --help            show this help message and exit
  --input INPUT, -i INPUT
                        path to a .csv or .jsonl with columns id, label, score
  --frontier            show every budget's exact counts instead of certifying
                        one. Costs no bootstrap, so it answers in a second
                        rather than two minutes; rates with intervals come
                        from --budget.
  --budget BUDGET, -b BUDGET
                        false-positive budget, e.g. 0.05 for 'at most 5% of
                        clean items flagged'. The 95% level holds for a budget
                        chosen before looking at this file; a budget picked
                        off --frontier is covered by the frontier's own
                        adjusted rows, not by this command (DECISIONS 192)
  --out OUT, -o OUT     write the JSON record here (default: alongside the
                        input, as <name>.warrant.json)
  --quiet, -q           print only the JSON path, not the summary
  --require-warrant     exit non-zero when the detector is REFUSED (default:
                        refusal exits 0)
  --from-frontier RECORD
                        the .frontier.json you picked --budget from; certifies
                        at that frontier's row level so the pick still holds
                        (DECISIONS 195)
```

## warrant verify

```text
usage: warrant verify [-h] --warrant WARRANT --input INPUT
                      [--frontier FRONTIER]

Check a certify record's effective-row digest and recompute its certificate.
This verifies arithmetic, not the author's identity, timestamp or deployment.
A frontier-selected record also needs its retained --frontier file.

options:
  -h, --help            show this help message and exit
  --warrant WARRANT, -w WARRANT
                        the .warrant.json record written by certify
  --input INPUT, -i INPUT
                        the retained scored CSV or JSONL used by certify
  --frontier FRONTIER   the retained frontier record, required for a selected
                        budget
```

## warrant verify-recheck

```text
usage: warrant verify-recheck [-h] --record RECORD --warrant WARRANT --input
                              INPUT [--certificate-input CERTIFICATE_INPUT]
                              [--certificate-frontier CERTIFICATE_FRONTIER]

Check an ordinary recheck's fresh-row binding and recompute its measurement.
Chained records need retained chain history and are not verified by this
command.

options:
  -h, --help            show this help message and exit
  --record RECORD       the .recheck.json record to replay
  --warrant WARRANT, -w WARRANT
                        the exact retained certificate
  --input INPUT, -i INPUT
                        the retained fresh scored CSV or JSONL
  --certificate-input CERTIFICATE_INPUT
                        the original scored file, required if the recheck says
                        VERIFIED
  --certificate-frontier CERTIFICATE_FRONTIER
                        the retained frontier for a selected certificate
```

## warrant verify-chain-recheck

```text
usage: warrant verify-chain-recheck [-h] --warrant WARRANT --pair RECORD FRESH
                                    [--certificate-input CERTIFICATE_INPUT]
                                    [--certificate-frontier CERTIFICATE_FRONTIER]

Present every link from sequence 1 through the target, each with the fresh
scored file it measured. Checks seals, links, rows and statistics. This
verifies only the presented prefix, not the current head or any unpresented
fork.

options:
  -h, --help            show this help message and exit
  --warrant WARRANT, -w WARRANT
                        the exact retained certificate
  --pair RECORD FRESH   one chained record and its fresh scored file; repeat
                        in sequence
  --certificate-input CERTIFICATE_INPUT
                        original scored file if any link claims source
                        VERIFIED
  --certificate-frontier CERTIFICATE_FRONTIER
                        retained frontier for a selected certificate
```

## warrant recheck

```text
usage: warrant recheck [-h] --warrant WARRANT --input INPUT
                       [--certificate-input FILE]
                       [--certificate-frontier RECORD] [--out OUT] [--quiet]
                       [--require-valid] [--horizon-labels N | --since RECORD]
                       [--fork]

Takes a warrant record and a fresh file of the same shape, and answers whether
the promise still holds. Two failure modes, reported separately: the false-
positive bound can break, or the score distribution can move far enough that
the old measurement no longer describes your traffic.

options:
  -h, --help            show this help message and exit
  --warrant WARRANT, -w WARRANT
                        the .warrant.json record produced by an earlier
                        certify
  --input INPUT, -i INPUT
                        the new .csv or .jsonl, same three columns
  --certificate-input FILE
                        replay the original certificate against its retained
                        scored export before rechecking; a mismatch or missing
                        evidence writes no record
  --certificate-frontier RECORD
                        retained frontier record, required with --certificate-
                        input when the certificate selected its budget from a
                        frontier
  --out OUT, -o OUT     write the JSON record here
  --quiet, -q
  --require-valid       exit non-zero when the warrant no longer holds
                        (default: exits 0)
  --horizon-labels N    start a chain of rechecks whose sequential false-
                        positive statistic falsely revokes a detector keeping
                        its promise with probability at most alpha over N
                        clean negatives; a revocation for a moved score
                        distribution is a separate check, outside that bound.
                        Declare N once, e.g. the negatives a year of rechecks
                        will label (DECISIONS 193)
  --since RECORD        continue the chain in this earlier .recheck.json; keep
                        every record
  --fork                continue from a record that is not the chain's latest,
                        or start a new chain while one exists; the fork is
                        recorded in the chain (DECISIONS 194). It cannot
                        reopen a warrant whose chain was revoked: re-certify
                        instead
```

## warrant plan

```text
usage: warrant plan [-h] [--warrant WARRANT] [--budget BUDGET] [--catch CATCH]
                    [--catch-multiple CATCH_MULTIPLE] [--power POWER]
                    [--negative-share NEGATIVE_SHARE]
                    [--minutes-per-label MINUTES_PER_LABEL]
                    [--cost-per-hour COST_PER_HOUR] [--currency CURRENCY]
                    [--out OUT] [--quiet]

A warrant is a claim about now. Keeping it true means re-testing it, and re-
testing costs labels. This says how many clean negatives one recheck needs to
catch a breach of the size you name, how many items you must label to get
them, and what a year of that costs at each of several cadences. It recommends
no cadence: how often to recheck depends on how fast your inputs move, which
is the thing you do not know.

options:
  -h, --help            show this help message and exit
  --warrant WARRANT, -w WARRANT
                        a .warrant.json record; takes the budget and alpha
                        from it rather than having you retype them
  --budget BUDGET, -b BUDGET
                        the certified false-positive budget (not needed with
                        --warrant)
  --catch CATCH         the false-positive rate you want to be able to catch,
                        absolute
  --catch-multiple CATCH_MULTIPLE
                        or as a multiple of the budget (default: 1.5, the same
                        reference point `recheck` reports its own detection
                        floor against)
  --power POWER         probability one recheck catches a true breach of that
                        size (default: validation.recheck_power, 0.80)
  --negative-share NEGATIVE_SHARE
                        REQUIRED: the fraction of YOUR traffic that is truly
                        negative. Deliberately not taken from the warrant
                        record -- see below
  --minutes-per-label MINUTES_PER_LABEL
                        optional; without it the plan reports counts and no
                        hours
  --cost-per-hour COST_PER_HOUR
                        optional; without it the plan reports hours and no
                        money
  --currency CURRENCY   label only, e.g. 'INR '
  --out OUT, -o OUT     write the JSON record here
  --quiet, -q
```

## warrant release

```text
usage: warrant release [-h]
                       {register,evaluate,verify,label-audit,verify-label-audit}
                       ...

positional arguments:
  {register,evaluate,verify,label-audit,verify-label-audit}
    register            freeze criteria and disjoint holdout IDs
    evaluate            measure the complete registered holdout once
    verify              recompute saved evidence and check its expiry
    label-audit         record fixed-threshold label sensitivity for a
                        retained evaluation
    verify-label-audit  replay a retained release label audit

options:
  -h, --help            show this help message and exit
```

## warrant release register

```text
usage: warrant release register [-h] --spec SPEC --development-ids
                                DEVELOPMENT_IDS --holdout-ids HOLDOUT_IDS
                                --out OUT

options:
  -h, --help            show this help message and exit
  --spec SPEC           release specification JSON
  --development-ids DEVELOPMENT_IDS
                        one development question ID per line
  --holdout-ids HOLDOUT_IDS
                        one unused holdout question ID per line
  --out OUT             new contract JSON; existing files are never replaced
```

## warrant release evaluate

```text
usage: warrant release evaluate [-h] --contract CONTRACT --input INPUT
                                --context CONTEXT [--require-valid]

options:
  -h, --help           show this help message and exit
  --contract CONTRACT  registered release contract JSON
  --input INPUT        scored holdout CSV/JSONL: id,label,score
  --context CONTEXT    scorer's identity and scope JSON
  --require-valid      exit 1 unless current status is VALID
```

## warrant release verify

```text
usage: warrant release verify [-h] --contract CONTRACT --input INPUT --context
                              CONTEXT [--require-valid] [--evidence EVIDENCE]

options:
  -h, --help           show this help message and exit
  --contract CONTRACT  registered release contract JSON
  --input INPUT        scored holdout CSV/JSONL: id,label,score
  --context CONTEXT    scorer's identity and scope JSON
  --require-valid      exit 1 unless current status is VALID
  --evidence EVIDENCE  saved evidence; default is beside the contract
```

## warrant release label-audit

```text
usage: warrant release label-audit [-h] --contract CONTRACT --input INPUT
                                   --context CONTEXT [--evidence EVIDENCE]

options:
  -h, --help           show this help message and exit
  --contract CONTRACT  registered release contract JSON
  --input INPUT        complete scored holdout, optionally with label_2
  --context CONTEXT    scorer's identity and scope JSON
  --evidence EVIDENCE  saved release evaluation; default is beside the
                       contract
```

## warrant release verify-label-audit

```text
usage: warrant release verify-label-audit [-h] --contract CONTRACT --input
                                          INPUT --context CONTEXT
                                          [--evidence EVIDENCE]
                                          [--audit AUDIT]

options:
  -h, --help           show this help message and exit
  --contract CONTRACT  registered release contract JSON
  --input INPUT        complete scored holdout, optionally with label_2
  --context CONTEXT    scorer's identity and scope JSON
  --evidence EVIDENCE  saved release evaluation; default is beside the
                       contract
  --audit AUDIT        saved label audit; default is beside the contract
```

## warrant prepare

```text
usage: warrant prepare [-h] --input INPUT --mapping MAPPING --out OUT

options:
  -h, --help            show this help message and exit
  --input INPUT, -i INPUT
                        original flat .csv, .jsonl or .ndjson export
  --mapping MAPPING     JSON mapping declaring labels, score direction and
                        groups
  --out OUT, -o OUT     new package directory; existing destinations are
                        refused
```

## warrant verify-prepared

```text
usage: warrant verify-prepared [-h] --input INPUT --mapping MAPPING --prepared
                               PREPARED

options:
  -h, --help            show this help message and exit
  --input INPUT, -i INPUT
  --mapping MAPPING
  --prepared PREPARED   directory written by warrant prepare
```

## warrant handoff

```text
usage: warrant handoff [-h] {create,verify} ...

positional arguments:
  {create,verify}
    create         publish a new local packet from already verified evidence
    verify         check packet bytes and replay both existing verifiers

options:
  -h, --help       show this help message and exit
```

## warrant handoff create

```text
usage: warrant handoff create [-h] --input INPUT --mapping MAPPING --prepared
                              PREPARED --warrant WARRANT [--frontier FRONTIER]
                              --out OUT [--include-sensitive-input]

options:
  -h, --help            show this help message and exit
  --input INPUT, -i INPUT
                        original scored export, including excluded columns
  --mapping MAPPING
  --prepared PREPARED
  --warrant WARRANT, -w WARRANT
  --frontier FRONTIER   required for a frontier-selected certificate
  --out OUT, -o OUT     new directory; existing destinations are refused
  --include-sensitive-input
                        explicitly allow copying the original source,
                        including excluded columns
```

## warrant handoff verify

```text
usage: warrant handoff verify [-h] --packet PACKET

options:
  -h, --help       show this help message and exit
  --packet PACKET
```

## warrant chain

```text
usage: warrant chain [-h] {verify} ...

Reads the recheck records a chain produced and reports what they show: forks,
restarts, missing links, edited states and links that do not extend their
predecessor. It cannot recompute the statistics, which need the labelled files
(DECISIONS 194).

positional arguments:
  {verify}
    verify    verify a set of chained recheck records

options:
  -h, --help  show this help message and exit
```

## warrant chain verify

```text
usage: warrant chain verify [-h] [--out OUT] [--quiet] [--require-clean]
                            records [records ...]

positional arguments:
  records            every .recheck-NNNN.json you kept

options:
  -h, --help         show this help message and exit
  --out OUT, -o OUT  write the JSON record here (default: chain-
                     verification.json)
  --quiet, -q
  --require-clean    exit non-zero unless all records are sealed and all
                     checks pass (default: inspection exits 0)
```

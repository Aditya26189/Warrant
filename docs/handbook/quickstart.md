# Quickstart: evaluate, refuse and replay

This tutorial exercises the existing local tool on public synthetic examples.
It demonstrates software behavior. It does not establish performance on customer
traffic or clear the [open assurance review](limitations.md).

## Requirements

The customer package declares Python 3.10 or newer. Its direct numerical
dependencies are NumPy, SciPy and PyYAML. Documentation-building and research
dependencies are separate.

Clone the repository using its current access controls. On Windows, the
long-path option is important because the retained research fixtures contain
deep paths.

```shell
git clone -c core.longpaths=true https://github.com/Aditya26189/Warrant.git
cd Warrant
python -m venv .venv
```

Activate the environment:

```shell
# Linux or macOS
source .venv/bin/activate
```

```powershell
# Windows PowerShell
.\.venv\Scripts\Activate.ps1
```

Install the customer requirements and package:

```shell
python -m pip install -r requirements-customer.txt
python -m pip install --no-deps .
warrant --help
```

The source-checkout equivalent of `warrant` is `python warrant.py`. Installing
the package makes it possible to work outside the checkout, which is preferable
for private inputs and generated outputs.

## Create a separate output directory

Keep generated examples outside the source tree so they cannot accidentally
become committed evidence or dirty a scientific run.

```shell
# Linux or macOS, from the checkout
mkdir -p ../warrant-review
```

```powershell
# Windows PowerShell, from the checkout
New-Item -ItemType Directory -Force ..\warrant-review
```

## Obtain a result

```shell
python warrant.py certify --input examples/certifies.csv --budget 0.05 --out ../warrant-review/certifies.warrant.json
```

Read the complete output, including the unit count and method caveats. The
example is constructed to exercise the certification path. Its result is not
a certificate for a real deployed detector.

At this stage the tool has processed supplied labels. It has not independently
reviewed those labels, identified their author or inspected a production system.

## Obtain a refusal

```shell
python warrant.py certify --input examples/refuses.csv --budget 0.01 --out ../warrant-review/refuses.warrant.json
```

A refusal is a normal result. By default, the command can exit successfully
while reporting `REFUSED`. A pipeline that needs a nonzero exit for refusal
must deliberately use the supported `--require-warrant` option.

Do not make a refusal disappear by deleting genuine group identifiers, choosing
a budget after viewing the result, or presenting a different detector under
the same identity. Those actions change the scientific question.

## Replay the first result

```shell
python warrant.py verify --warrant ../warrant-review/certifies.warrant.json --input examples/certifies.csv
```

A successful replay means that the material calculation matches the retained
rows under the implemented protocol. It does not prove authorship, trusted
timing, label truth or deployment identity. Successful replay of a refused
record preserves its refusal.

## Bring your own scored file

The required columns are:

```csv
id,label,score
case_a,0,0.12
case_b,1,0.87
```

These two rows only illustrate the format; they do not supply a useful
certification sample. IDs must be unique. Labels must use the declared
positive condition consistently. Scores must be finite, with larger values
meaning more likely positive. The firing convention is
`score >= threshold`.

Add `group` when rows share a real dependence unit. Add `label_2` only for
items actually reviewed a second time; leave other second labels blank.
The [input contract](../../docs/INPUT.md) documents supported formats and
rejection behavior.

## What to do next

- [Workflows](workflows.md) explains preparation, frontiers, rechecks, chains,
  release registration and portable handoffs.
- [Records and protocols](records-and-protocols.md) explains what must be
  retained.
- [Methods](methods.md) distinguishes a fixed requested budget from the
  adaptive numerical bound returned by the native procedure.
- [Testing](testing.md) explains what the example and installation checks cover.

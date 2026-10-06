# Phase 39 - The built wheel exercises the prepared refusal handoff

The installed package now has a regression for the same small grouped export
shown in the public source walkthrough. The test builds the distribution,
installs a wheel rebuilt from its source archive into a disposable target, and
runs the installed `warrant` executable through preparation, a refusal and
both replay boundaries. All 19 installed-wheel tests passed in the local
customer-only Python 3.12 environment. The build changed test coverage, not
the CLI, package metadata, statistical method or a measured detector result.

## Question and scope

The October plan calls for package and compatibility regression after the
short synthetic demonstration. Phase 38 exercised the grouped refusal with
`python warrant.py` from the checkout. The existing installed-wheel suite
covered a successful prepared certificate, an ungrouped refusal and many
other commands, but did not cover a **prepared grouped refusal** through the
installed entry point. A source path test could pass while distribution
contents or console entry-point wiring failed. This phase adds that missing
packaging boundary check using the existing synthetic export and mapping;
it does not add a new fixture or adapt a customer format.

The packaging test fixture copies the declared package files to an OS-temp
source directory, builds a direct wheel and source archive, rebuilds a wheel
from that archive, installs the rebuilt wheel into an isolated target with
`pip --no-deps`, and runs the generated console executable with that target
on `PYTHONPATH`. It strips incidental `PYTHONPATH` before building. The
separate wheel-contents test inspects both wheels. This is stronger than
importing `controlplane` from the checkout, but it still reuses the running
interpreter's preinstalled NumPy, SciPy and PyYAML dependencies.

## Work and observed result

Commit `3143865` adds one test in `tests/test_package_install.py`. It copies
the public four-row source and mapping bytes to the disposable test directory,
then runs `prepare` and `verify-prepared` through the installed command. It
certifies the generated `scored.csv` at budget `.05` and asserts a recorded
`REFUSED` outcome, including the two-independent-unit and 59-clean-unit
reason. It compares the certificate's effective-row digest with the manifest
digest and verifies the refusal record from the same prepared rows.

The test then changes only the source note that the mapping excludes from
effective rows. The installed `verify-prepared` command reports `MISMATCH`
and exits 1 against the original package. The installed certificate `verify`
command still reports `VERIFIED` and exits 0 against unchanged scored rows.
This preserves the distinction between source-byte replay and certificate
recalculation when the distribution, rather than the source CLI, is used.
Refusal itself exits 0 and writes a record; no exception or traceback is an
expected part of the flow.

The previously created Phase 34 virtual environment contains only
`requirements-customer.txt`, pytest, setuptools and wheel, with no research
stack. Its Python is 3.12.10. `pip check` found no broken requirements, and
Ruff reported no issue in the modified test. In that environment the new
case passed alone (`1 passed, 18 deselected` in 43.83 seconds), then the
entire installed-wheel module passed (`19 passed` in 293.20 seconds). This
includes the direct-wheel and source-archive rebuild fixture, installed
prepare/certify/verify commands, recheck/chain and release tests. The
complete module result is an execution result, not a collection count.

`pyproject.toml` declares Python `>=3.10`. The checked-in CI workflow
configures Linux customer jobs on 3.11 and 3.12, a Windows installed-minimum
job on 3.10, and a Linux full-suite job on 3.12. These are configuration
facts, not observed results for this local commit. This host exposes only
Python 3.12; the `py` launcher and `uv` were unavailable in the inspected
shell. The phase therefore makes a local 3.12 compatibility claim only.

## What this does not establish

The new case uses the same hand-written four-row synthetic source as Phase
38. It does not establish a customer's export schema, truthful labels,
independent conversation units, detector quality or decision usefulness. The
refusal is evidence that the shipped command reports insufficiency under its
declared assumptions; it is not a verdict on a deployed detector. The digest
and replay checks prove local consistency, not provenance authentication.

The local module did not run under Python 3.10 or 3.11, Linux or macOS. CI
declares some of those jobs but this branch has not been pushed, so no GitHub
run for its exact commit can be cited. A wheel rebuilt from a local source
archive is not the same as a published package downloaded from an index. The
fixture installs with `--no-deps` by design; dependency resolution was
covered by the earlier fresh-venv check, not by this test. A customer's actual
environment may have version combinations or filesystem constraints that
the local test does not expose.

The phase does not re-run model extraction, open the protected research test
set, or create a new scientific artifact. The old full-source suite remains
Phase 36's 2,215-test measurement; adding one packaging regression does not
retroactively make that suite a 2,216-test pass. The generated inventory below
records collection only. A passing frozen-score verifier does not prove that
the original model produced those scores unless its activation tier runs.

## Open items

Observe the configured Windows 3.10 and Linux 3.11/3.12 CI jobs for a
published commit before claiming support was exercised on those platforms.
If a supported-version job fails, reduce the failure to a source or package
reproduction and fix that concrete incompatibility. Do not infer a fix from
the CI matrix alone. A real reviewer trial still needs an owner-approved
export, label provenance, declared score direction and independent unit, and
a decision for which the incumbent packet is insufficient. The October plan's
human demand gate remains unfulfilled; this packaging pass does not advance
it.

The next useful local quality work is to inspect whether a real offline
reviewer can identify the minimum files and understand the two replay
boundaries without author assistance. If no reviewer or export is available,
record that missing observation rather than expanding the product surface.
The October 8 research refresh is separate from package compatibility and
should cite new dated evidence if it changes a build decision.

## Ledger

| Change or check | Evidence |
|---|---|
| New installed grouped-refusal regression | `3143865`; `tests/test_package_install.py` |
| Public synthetic input and mapping | `examples/export_sample.csv`, `examples/export_mapping.json` |
| Focused installed test | Python 3.12.10 customer-only venv; 1 passed, 18 deselected in 43.83 seconds |
| Entire installed-wheel module | Same venv; 19 passed in 293.20 seconds |
| Local dependency and lint checks | `pip check`: no broken requirements; `ruff check tests/test_package_install.py`: all checks passed |
| Declared Python floor and CI matrix | `pyproject.toml` `requires-python = ">=3.10"`; `.github/workflows/ci.yml` jobs described above |
| Clean test inventory | `results/test_inventory.json` generated from clean `dd455f6`; 2,223 collected, execution not implied |
| Clean installed-wheel regression | `7f5d3f4`; new case 1 passed, 18 deselected in 46.47 seconds |
| Clean documentation and inventory gate | `7f5d3f4`; 155 passed, exit 0 |
| Clean smoke and available verifier | `7f5d3f4`; smoke 7/7, claim table 92/92, frozen scores 25/25; activation tier skipped with `--no-activations` |

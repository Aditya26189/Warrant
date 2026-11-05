# Repository layout and documentation ownership

The layout separates the installed tool, reproducible research, retained
evidence and the reading material. These boundaries are useful. A large rename
would invalidate source paths, artifact identities and historical citations
without improving the scientific evidence.

## Choose a source of truth

| Question | Start here | Maintenance rule |
|---|---|---|
| What can I run? | [Quickstart](quickstart.md), [workflows](workflows.md), [command reference](cli-reference.md) | Parser help defines available flags; examples explain their use |
| What does it mean? | [Methods](methods.md), [protocols](records-and-protocols.md), [limitations](limitations.md) | Match the quantity, independent unit and declared record version |
| Where does a number come from? | [Claim ledger](claims.md), [families](claim-families.md), [data origins](data-sources.md) | Original artifacts remain immutable; matching values do not establish validity |
| How do I contribute? | [Contributor instructions](../../AGENTS.md), [rules](../CONTRIBUTING.md), [maintainer guide](developer-guide.md) | Read current context, work separately and preserve source provenance |
| Why was a decision made? | [Decision log](../../DECISIONS.md), [phase reports](../../reports/) | Historical rationale describes its original date and source |
| Which branches were accounted for? | [Integration history](../BRANCH-INTEGRATION.md), [closure review](../../reports/PHASE-56.md) | Ancestry, current-release tests, old gate evidence and local drafts are separate |
| What was published? | [Paper guide](../../paper/README.md) | The preprint tag and compiled manuscript are versioned independently of later maintenance |

The handbook is the ordered current explanation. Specialist manuals retain
more detailed contracts; archived plans and reports retain their original
assumptions. When those disagree, inspect the versioned implementation and
recorded decisions, correct the current guide, and identify the historical
text. Do not silently promote a prediction or old result into current behavior.

## Top-level map

| Path | Role | Why it stays here |
|---|---|---|
| `controlplane/` | Reusable Python implementation | The installed package keeps its deliberate historical name |
| `controlplane/intake/` | Preparation, certification, verification, rechecks, handoff and local publication | Customer workflows share one scored-file contract |
| `controlplane/release/` | Registered fixed-threshold studies | Separate design and protocol from adaptive native certification |
| `scripts/` | Thin research and maintenance entry points | Behavior lives in the library |
| `tests/` and `ci/` | Core tests and minimal-dependency selections | Executed suites and collection inventories have distinct meanings |
| `.github/workflows/` | Core, research and documentation CI | Each validates a declared surface |
| `examples/` | Small synthetic customer inputs and ordered demonstrations | Safe first workflows remain separate from benchmark findings |
| `evalsets/` | Frozen dataset manifests and retained small inputs | Changing a dataset creates a new identity |
| `results/` | Frozen scores, calculations, study results and prior gate records | Retained evidence is not a disposable build directory |
| `docs/handbook/` | Current tutorials, explanations and generated references | The strict documentation site has explicit navigation |
| `docs/` | Specialist manuals, decisions and research protocols/receipts | Many research files are evidence records rather than user-guide chapters |
| `reports/` | Dated phase and review reports | Their original source revisions remain visible |
| `experiments/` | Isolated research studies, fixtures and portable inputs | Fixtures and third-party notices travel with the study that uses them |
| `agent-stopping-feedback-study/` | Closed standalone feasibility study | Its execution/import paths and STOP decision remain stable |
| `paper/` | LaTeX manuscript, bibliography, reviewed PDF and publication tooling | Code and manuscript licenses are distinguished |
| `notebooks/` | Generated Kaggle notebooks | The builder is the source; generation is not execution |
| `kaggle/` and `kaggle-pilot/` | Retained notebook-run diagnostics | They do not replace the generated notebook sources |
| `policies/` and `demo/` | Local policy fixtures and demonstrations | They are not a deployed service |
| `round1/` | Preserved original submission | Its different assumptions and history remain identifiable |
| Root configuration/build files | Package metadata, runtime defaults, requirements, tests and build entry points | A maintainer can discover setup without navigating research archives |

## What should not be moved during closeout

Keep frozen result paths, dataset IDs, third-party notices, the original
submission and the closed studies stable. A future migration would need a
separate mapping, compatibility checks and a decision about every cited path.
Directory symmetry alone does not justify such a migration.

The uneven placement of research receipts under `docs/research/` and a
standalone study at the root are historical compromises. Navigation makes them
discoverable; a future project can use a more uniform convention. They do not
make the current implementation unreproducible.

## Checkout clutter versus repository structure

A desktop folder can contain ignored environments, caches, PDFs, private review
packages and older worktrees. A plain directory listing does not describe what
another person receives from Git.

Use:

```shell
git ls-tree --name-only HEAD
git ls-files
git status --short
git worktree list --porcelain
```

Review untracked or ignored material without adding, deleting or publishing it
as part of cosmetic cleanup. Branch merging does not include uncommitted edits.
Missing historical checkout directories are administrative residue, not a reason
to pretend their branches or tests were newly verified.

## Generated references

[The reference declaration](reference-sources.json) identifies the retained
claim receipt and selected API source files.

```shell
python scripts/audit_documentation.py --render-references
python scripts/audit_documentation.py --check-generated --links-all
python -m mkdocs build --strict --site-dir ../warrant-handbook-site
```

The first command deliberately writes all four reference pages. The second
only checks them and scans maintained root, specialist, research, example and
phase guides. It does not fetch remote URLs or inspect private root working
papers. The API catalog is selected, not a promise that every internal function
is stable.

## Documentation completeness boundary

The current guide set covers onboarding, customer workflows, records,
architecture, methods, interfaces, data origins, findings, claim provenance,
testing, reproduction, maintenance, limitations and the manuscript.

Completeness means those supported surfaces have a navigable explanation and
declared maintenance path. It does not mean every historical sentence is
scientifically validated, every research cache is shipped, or every planned
feature was built. The [closure review](../../reports/PHASE-56.md) records the
observed checks and remaining limits.

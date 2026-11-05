# Warrant documentation

Warrant evaluates what a detector's recorded evidence supports. The installed
tool reads scored, labelled records, evaluates a declared operating decision,
retains the evidence and allows its arithmetic to be replayed. The research
repository studies where those records and statistical interpretations succeed
and where they fail.

This handbook describes the consolidated implementation. A roadmap, a synthetic
demonstration and a measured result are different forms of evidence. We name
those differences throughout rather than treating every checked-in component
as a validated product.

## Choose a reading path

| You are here to | Read, in this order | Result |
|---|---|---|
| Understand the project for the first time | [Introduction](introduction.md) → [Quickstart](quickstart.md) → [Findings](findings.md) | Understand the problem, run the tool and interpret the evidence |
| Use the installed command | [Workflows](workflows.md) → [Command reference](cli-reference.md) → [Records and protocols](records-and-protocols.md) | Prepare, evaluate, retain and replay a scored file |
| Review the science | [Data origins](data-sources.md) → [Methods](methods.md) → [Claim audit](claim-audit.md) → [Preprint](technical-report.md) | Trace claims and distinguish measurements from explanations |
| Change the implementation | [Architecture](architecture.md) → [Library reference](api-reference.md) → [Testing](testing.md) → [Developer guide](developer-guide.md) | Find the correct layer and the checks that defend its contract |
| Reproduce a result | [Reproduction](reproduction.md) → [Claim families](claim-families.md) → [Individual claims](claims.md) | Identify inputs, commands, source revisions and missing materials |
| Assess readiness | [Limitations](limitations.md) → [Qualitative claim register](qualitative-claims.md) | Understand what is implemented, demonstrated, unresolved or absent |

## What to expect

**Tutorials** provide an ordered route to a result. **Conceptual chapters**
explain why the objects and methods exist. **Reference chapters** enumerate
interfaces and protocols. **Research chapters** state the experiment,
observation, interpretation and limitations separately.

The [individual claim ledger](claims.md) covers the numerical README table.
The [qualitative register](qualitative-claims.md) investigates statements about
software capability, research status and prior verification. Neither is a
certificate of scientific validity.

## Important current boundaries

- The native adaptive returned-FPR-bound interpretation remains under
  [open review](../../docs/research/fpr_reporting/issues/FPR-001-adaptive-bound.md).
- Some historical results have dirty-source provenance. Matching their values
  does not reconstruct their complete producing source state.
- Frozen-score replay can reproduce metric arithmetic without reproducing the
  original model inference, correct labels or valid sampling assumptions.
- The research portfolio contains successful demonstrations, adverse results
  and stopped studies. Their stopping decisions remain part of the result.
- This is a local toolkit and research artifact. Production operation,
  independent source adjudication and customer outcomes are separate claims.

## Documentation map

| Chapter | Purpose |
|---|---|
| [Introduction](introduction.md) | Vocabulary and the complete mental model |
| [Quickstart](quickstart.md) | A successful result, a refusal and a replay |
| [Workflows](workflows.md) | Supported operational paths and their boundaries |
| [Architecture](architecture.md) | Components, control flow, trust and persistence |
| [Methods](methods.md) | Statistical quantities, assumptions and inference |
| [Data sources](data-sources.md) | Dataset construction and evidence lineage |
| [Findings](findings.md) | What worked, what failed and what remains an explanation |
| [Claim-audit guide](claim-audit.md) | How to read the evidence investigation |
| [Claim families](claim-families.md) | Shared methods, writers, inputs and limits |
| [Claim ledger](claims.md) | One entry for every README-table claim |
| [Qualitative claims](qualitative-claims.md) | Capability and verification statements |
| [Command reference](cli-reference.md) | Parser-derived command help |
| [Library reference](api-reference.md) | Selected implementation contracts |
| [Records and protocols](records-and-protocols.md) | Versioning, grouping, identity and replay |
| [Testing](testing.md) | Positive checks, negative controls and known gaps |
| [Reproduction](reproduction.md) | CPU, cached-activation and GPU paths |
| [Developer guide](developer-guide.md) | Contributor and maintainer procedures |
| [Limitations](limitations.md) | Open issues and the evidence needed to close them |
| [Sources](sources.md) | Primary references and the role each plays |
| [Technical preprint](technical-report.md) | LaTeX manuscript, PDF and Zenodo preparation |
| [Notebook discussion](discussion-cell.md) | Concise closing scientific discussion |

The [older documentation index](../README.md) retains specialized contracts and
historical material. For the prior consolidation, consult the
[branch audit](../BRANCH-INTEGRATION.md). A historical phase report describes
its named source; it does not automatically describe every later revision.

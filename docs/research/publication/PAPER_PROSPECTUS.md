# What Does a Low False-Positive Rate Establish?

## A reproducible evidence audit of prompt-injection detectors

27 October 2026. Working manuscript prospectus, not a completed submission.
This advances the [initial direction assessment](TMLR_DIRECTION_20261027.md).
The existing B1 protocol, taxonomy and human-verification gates remain binding;
the paper-level analyses below are proposals for a successful pilot's follow-up.

## Research decision

Make **the consequences of reconstructing evaluation evidence** the candidate
contribution. The central question is whether a reader can recover the actual
false-positive proposition and whether that proposition is supported by the
reported method, operating point, decision units and observations.

The paper must teach something specific about evaluation practice. A checklist,
a binomial calculator, a list of absent intervals, or a single bug in our own
software is insufficient. Useful evidence could be a repeated, independently
verified mechanism that changes an assurance interpretation, or a substantive
source-supported discrepancy under the paper's own stated assumptions. A
carefully verified positive finding that claims do match their evidence must
also be retained. No unfavorable conclusion is assumed.

This direction has a concrete connection to existing work and modest compute
needs. Its limiting resource is reliable source interpretation. More engineering
does not remove the need for the independent human review already specified.

## Draft opening argument

Input prompt-injection detectors classify benign as well as malicious inputs.
Their false-positive evaluations therefore concern a particular benign
population, a decision convention and an operating point. An observed rate
describes the evaluated decisions. Inferring a future population rate also
requires a defensible sampling model and a procedure that matches the asserted
guarantee. The same numerical rate may support different conclusions when
these conditions differ.

These distinctions are familiar in statistics. Their empirical consequences
for reading detector evaluations are the proposed object of this study. We
would trace explicit propositions to their source evidence, preserve missing
and ambiguous information, and reconstruct the conclusion only when the
method's required assumptions and input quantities are available. The study
would distinguish evidence that is incomplete from evidence that contradicts
a proposition. It would assess each method under the guarantee it actually
asserts, including valid marginal or high-probability guarantees.

The intended contribution is a source-verifiable empirical account of which
interpretations are justified, which cannot be evaluated from the available
record, and which evaluation mechanisms explain substantive differences.
No results sentence or completed-study abstract is warranted yet.

## What we can already defend

The [exact diagnostic](EXACT_WITNESS.md) independently reproduces the known
Warrant example through exhaustive rational multinomial enumeration. Its
[retained artifact](../../../results/publication/assurance_semantics.json)
has clean-source provenance. A nominal confidence value returned after rank
selection can fail its coverage interpretation even though the requested
budget is satisfied. The mathematical note identifies the complete event
partition and assumptions. The code does not import production statistics.

This is a worked example with deliberately limited evidential status:
synthetic, previously exposed, and about the modeled Warrant rule. It is not
an observation about other authors or a proof of a general new theorem. The
unchanged production characterization tests were rerun separately; passing
them reproduces known behavior rather than marking the open issue resolved.

## Novelty stress test: sources actually inspected in this continuation

This was targeted prior-art investigation, not a systematic search or a source
of additional sampling-frame candidates. Search topics included the two
previously unresolved close reviews, training-conditional coverage versus
binomial intervals, and prompt-injection FPR assurance audits.

| Primary source and read depth | What it occupies | Consequence for our direction |
|---|---|---|
| Coppola and Mazo, [*On Training-Conditional Conformal Prediction and Binomial Proportion Confidence Intervals*](https://arxiv.org/html/2502.07497v1), §§2–4 selected text; [arXiv metadata](https://arxiv.org/abs/2502.07497) lists TMLR (2025). OpenReview forum/final PDF challenged browser access; final-version equivalence not verified | A direct warning about misinterpreting a conformal set-prediction guarantee as Bernoulli-parameter assurance in safety certification | A generic guarantee-distinction paper is already occupied, including in the target journal. Cite and distinguish this work; do not claim the basic observation as new |
| Bian and Barber, [*Training-conditional coverage for distribution-free predictive inference*](https://arxiv.org/html/2205.03647), §2.2 and Theorem 1 selected text | Marginal versus training-conditional guarantees and conditions under which stronger control holds | A valid conformal guarantee is not a failed confidence interval. Avoid a blanket critique of conformal calibration |
| Vovk, [*Conditional Validity of Inductive Conformal Predictors*](https://proceedings.mlr.press/v25/vovk12.html), official abstract and bibliographic page only | Conditional-validity theory substantially predates this project | Prioritize careful application and attribution over a new-theory claim |
| Bista et al., [*ConformalGuard*](https://arxiv.org/html/2610.14365v1), §§1,3.2–3.3 and limitations selected text | Legitimate-event control, coarse LM scores, explicit limitations under shift | Coarse scores alone do not make a new contribution. Do not assert Warrant's returned-bound error applies to this different method; email classification is not itself our input-injection task |
| Mahendrakar, [*Near-Zero Until Someone Tries*](https://research.pranaymahendrakar.com/p/near-zero-until-someone-tries), author abstract only; linked Zenodo PDF retrieval failed | Broad static/adaptive estimand critique and absent operating-point FPR | Generic metric incomparability is occupied. Full-method equivalence remains unresolved; absence of access is not evidence of absence |
| Mourad et al., [*Securing the Prompt Pipeline*](https://www.mdpi.com/2079-9292/15/16/3700), indexed publisher abstract/introduction; direct page returned HTTP 429 and XML access failed | Broad systematic defense review and evaluation-method comparisons | Its full extraction-table overlap remains unresolved. The audit cannot yet claim globally unique scope |

The earlier [gap assessment](../fpr_reporting/PRIOR_ART_GAP.md) also identifies
the CASCADE record-level audit, NP classification and general LLM uncertainty
work. Their reviewed scope remains relevant. This continuation found no
verified equivalent sampled cross-paper assurance reconstruction, but it did
not establish that none exists. An equivalent audit can still defeat this route.

## Evidence needed for the paper's main results

For each sampled paper, preserve exact version/locator, benign population,
decision/group unit, operating-point comparator, threshold-selection policy,
claim type, method and assumption evidence. Retain numeric counts only when
explicit or exactly derivable with evidence; rounded rates do not identify n/k.
Keep all eligible arms visible and state how each contributes to paper-level
summaries so a multi-arm paper does not become many independent papers.

The approved codebook governs the actual extraction labels. At paper level,
the manuscript should show the following parallel evidence views:

- **What the authors asserted:** descriptive result, operating target or the
  specific formal/population-assurance proposition. Ambiguity remains visible.
- **What can be reconstructed:** counts, method, sampling and selection details,
  with separate inaccessible, not-reported and ambiguous reasons.
- **What follows:** the conclusion supported by that particular method under
  its assumptions, with source-specific review for any claimed discrepancy.

These are proposed presentation views, not a replacement taxonomy or permission
to extract outcomes. Fixed-threshold CP can be used where justified; otherwise
it is at most a labeled diagnostic, not a universal gold standard.

The main result must explain mechanisms, not just missingness. If a population
assurance claim cannot be evaluated because a denominator is absent, report
that limitation without calling the claim false. If a method is valid under
IID data, a hypothetical clustered deployment does not refute it under IID.
Report direct and indirect injection populations separately as required by
the existing design.

## Concrete execution path

1. Complete the already authorized B1 eligibility work. The latest integrated
   checkpoint is still incomplete; the unresolved works cannot be silently
   omitted. Leave source-checking to its existing owners and preserve their
   role/exposure limits.
2. Use the existing complete-frame approval and draw gates. Do not turn this
   prospectus into authority for selecting convenient case studies or opening
   B2. Current progress counts are not paper outcomes.
3. Complete the existing private human-first extraction sequence and sealed
   assistant first pass. Adjudicate from preserved originals. Every critical
   paper-specific finding requires human source/method verification.
4. Apply the previously approved feasibility criteria. If explicit assurance
   claims are too sparse or the results merely restate familiar arithmetic,
   stop this headline. A small pilot licenses no literature prevalence claim.
5. Only if supported, freeze a larger study with an explicit sampling estimand,
   feasible human verification and analysis plan. Determine its size from the
   question and precision needs before outcomes, not from an arbitrary journal
   target or the number of already convenient sources.

Do not select another model, dataset or large synthetic grid to make the study
look larger. Do not add a product UI. Keep the sequential-monitor route as a
separate candidate with its earlier feasibility requirements; do not mix its
exploratory results into this audit's evidence.

## Review criteria we should impose on our own manuscript

The most serious reviewer objection is that known statistical distinctions
plus a few anecdotes do not teach anything new. The response must be empirical:
source-verified mechanisms whose practical interpretive consequence can be
shown in the sampled record, with both supportive and inconclusive cases.

The next objections are selection bias, unreliable AI interpretation and
misgrading a different guarantee. Address these with the retained bounded
frame, outcome-independent eligibility, immutable first passes, independent
human extraction, adjudication and source-specific calculations. Process hashes
alone address none of those scientific objections.

Current decision: **continue this direction's existing feasibility pilot;
do not claim a TMLR-ready paper yet**. The independent exact diagnostic is now
a usable supporting artifact. The empirical contribution is still to be tested.

## Verification for this continuation

- Three new exact-diagnostic tests passed; focused Ruff passed.
- All 29 unchanged `test_certify_stage_a.py` cases passed.
- The retained diagnostic ran on clean source `a6a297a` and checked exact
  equality between exhaustive enumeration and the closed form.
- Production source, existing certificates, B1 records, frozen scores and test
  scoring logs were not changed or regenerated. No new model inference ran.
- No human review, outcome extraction, fresh statistical sign-off, publication,
  merge or push is represented as completed here.

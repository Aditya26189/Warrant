# Where this should go next

**Dated 2026-09-09. Revised 2026-09-09 after the central claim was falsified.**

> ## Correction, and it is not a small one
>
> The first version of this document recommended building `dpdp-pii-bench`, a
> public labelled benchmark for Indian PII identifiers, on the stated ground
> that **"no public labelled benchmark exists"** for Aadhaar/PAN/UPI/IFSC.
>
> **That claim is false, and the recommendation built on it is withdrawn.**
>
> ServiceNow published **REDACT** on 18 June 2026 ([arXiv 2606.19881](https://arxiv.org/abs/2606.19881),
> [repo](https://github.com/guneeshvats/REDACT-PII-Benchmark)): 13,427 records,
> 324,078 entity annotations, 51 entity types, 4,127 surface-form patterns, 25
> languages across 9 scripts, a nine-axis covering-array sampler, and a released
> evaluation harness. I cloned the repository and grepped the catalog. Findings
> in §2.
>
> How the error was made, and why it is worse than the one in §4, is recorded in
> §4 rather than hidden here.

---

## The short version

**There is no benchmark wedge. Do not build one, and do not spend five months
finding that out.**

What survives the correction is **refusal as a terminal outcome**: REDACT reports
numbers with intervals and never declines to score, and **I did not find a
commercial product that declines** — which, after being wrong twice this session
by asserting negatives from searches, is stated as a fact about my search rather
than about the market. Verifying it means trialling products, not reading their
marketing. Since writing that, the REDACT work turned up a second
one — **whether a detector has an operating point that can be tuned to your
budget at all** (§5). Both are real primitives and both are ours.

It is also a week of work for anyone who decides to copy it, and its entire
commercial premise is unverified: **it assumes someone is punished for a wrong
claim.** In a market where nobody is yet, refusal is a cost, not a feature.

That question is not a month-five question. It is the only question, and it is
answerable in two weeks by talking to compliance and validation leads without
writing a line of code.

---

## 1. What we actually have

Unchanged by the correction, because this section was an audit rather than a
projection.

**Genuinely strong:**

- **Refusal as a first-class outcome with no override.** The ACL 2026
  conformal-routing work ([2026.acl-srw.70](https://aclanthology.org/2026.acl-srw.70/))
  certifies with the same Clopper-Pearson machinery and **never abstains** — it
  routes everything under a guarantee. REDACT scores everything. Ours says *"the
  evidence does not support this"* and exits 0.
- **`warrant certify` works on anyone's CSV**, no model, no config, nothing
  leaving the machine.
- **The evidence infrastructure**: hash-chained ledger, content-hashed eval sets,
  provenance on every artifact, 1,082 tests, `make verify` at 40/40 claims and
  25/25 frozen scores.

**Weak, and it matters:**

- **Our own probe is the weakest detector in our own matrix** — recall 0.231 at a
  0.05 budget against Presidio's 1.000 on email and the injection classifier's
  0.616 (`results/external/MATRIX.md`).
- **Zero production traffic, zero external users, zero customers.**
- **Every external row is in-sample**, ours included.
- **`sampling/`, `gate/` and `economics/sizing.py` are unwritten.** The on-traffic
  warrant — clause one of the three in `CLAUDE.md` — does not exist.

---

## 2. What REDACT actually contains

I cloned it and grepped rather than reading the abstract. Catalog file
`catalog/PII_Pattern_Catalog_v4_MASTER.md` (584 KB) and
`catalog/pattern_seed_data_v4.json` (6.8 MB).

**Present:**

| identifier | evidence |
|---|---|
| **Aadhaar** | 10 catalog / 42 seed occurrences, including Devanagari surface forms: `"Aadhaar: 1234 5678 9012, UID: 123456789012, आधार: 1234 5678 9012"` |
| **PAN** | catalog line 79 — National_ID covers "40+ country systems including US SSN/ITIN, UK NINO, German Steuer-ID, French NIR, Italian Codice Fiscale, **Indian Aadhaar/PAN**" |
| **GSTIN** | pattern `TX-027`, with structure: "15-char alphanumeric: state code + PAN + entity + Z + check" |
| Indian addresses, PIN codes, phones, names, email TLDs | patterns AW-057/058, AP-047/048, TW-062/063, TP-027, WE-025, PE-043, FUN-034/035, LFN-034 |

**Absent:** `IFSC` (0 occurrences) and **UPI VPA** (0 — the three apparent "UPI"
hits are the substring inside "gro**upi**ng").

**So the honest result is two missing patterns in a 4,127-pattern catalog.** That
is a pull request. It is not a company, and it is not five months of work.

REDACT also **already published the headline finding** I proposed to discover:
Presidio at recall 0.07 on HIGH-sensitivity entities against Claude Sonnet 4.6's
0.77 on the same slice, with the abstract stating that "aggregate F1 masks an
architecture-dependent failure structure" and "the rule-based detector performs
poorly on the highest-stakes data."

And **PIIBench** ([arXiv 2604.15776](https://arxiv.org/pdf/2604.15776), April
2026) ran the consolidate-and-measure play four months earlier: ten public
datasets, 2,369,883 annotated sequences, 48 canonical entity types, eight
comparator systems.

### PIIBench is the natural experiment, and it already reported out

The withdrawn recommendation asserted that a benchmark "earns citations, and
whoever owns it is in the room for every procurement conversation."

PIIBench tests that. One author, two papers, models on HuggingFace, April to May
2026. Observed outcome: **cited by REDACT.** Not a company, not a customer, not a
contract. The citation half of the claim is confirmed. **The procurement half is
unobserved**, and I asserted it as though the two travelled together.

---

## 3. The regulatory picture, which survives

These were verified against primary sources and stand.

**EU AI Act.** Regulation (EU) 2026/1744 (Digital Omnibus on AI), in force 27
July 2026, **deferred standalone high-risk obligations to 2 December 2027** and
embedded-product high-risk to August 2028
([Holland & Knight](https://www.hklaw.com/en/insights/publications/2026/04/us-companies-face-eu-ai-acts-possible-august-2026-compliance-deadline)).
Article 50 transparency, GPAI obligations and Article 5 prohibitions apply now.

**US banking.** [SR 26-2](https://www.federalreserve.gov/supervisionreg/srletters/SR2602.htm) /
[OCC Bulletin 2026-13](https://www.occ.gov/news-issuances/bulletins/2026/bulletin-2026-13.html),
17 April 2026, for banks over $30bn: *"Generative AI and agentic AI models are
novel and rapidly evolving. As such, they are not within the scope of this
guidance."* It **does** apply to traditional statistical and non-generative,
non-agentic AI. The agencies "plan to issue in the near future a request for
information" covering AI.

**India.** DPDP Rules notified 13 November 2025; Consent Manager provisions 13
November 2026; 18-month transition ends **13 May 2027**.

### The inferential gap I papered over

The withdrawn recommendation ran: *DPDP has a hard deadline → therefore there is
budget for certifying detector false-positive rates.*

DPDP obliges an organisation to **protect personal data**. It does not oblige
anyone to **certify a detector's false-positive rate at a stated confidence
level**. Those are two unstated steps, and they are the same
"regulation-creates-budget" inference this document correctly demolished for the
EU and the US — re-imported for India one layer down, because it was the answer I
wanted.

---

## 4. The method failure, twice

**First instance (kept from the original).** A vendor blog claimed SR 26-2
extends to LLMs and agentic AI and requires independent validation because
"vendor attestations do not satisfy the requirement." It fit the product
perfectly. The primary sources say the opposite. Caught before it shipped.

**Second instance, worse.** Having written that lesson down, I then asserted
**"no public labelled benchmark exists"** on the strength of one web search that
returned no direct hit — and made it the foundation of the entire
recommendation.

Three things make it worse than the first:

1. **A negative from a search is the weakest evidence type available.** Absence
   of a result is not evidence of absence, and I treated it as proof.
2. **The disconfirming evidence was in my own search output.** The result
   *"Fine-Tuning Over Architectural Complexity: Broad-Coverage PII Detection on
   PIIBench with DeBERTa"* ([arXiv 2605.25816](https://arxiv.org/pdf/2605.25816))
   was returned to me. I read past it because it did not fit.
3. **It was the single most convenient possible finding**, which by §4's own
   rule made it the claim most in need of checking, and it got the least.

**The rule, restated so it covers both:** a convenient claim needs a primary
source, *and a convenient absence needs a positive search for the thing that
would refute it.* "I searched and found nothing" is a statement about the search.

---

## 5. What to do instead

### Do not build a competing benchmark

REDACT has eight authors, ServiceNow behind it, a released harness, and covers
Aadhaar, PAN and GSTIN already. Building a rival is fighting distribution for
ground already held.

### The IFSC/UPI gap is a contribution, and should be sized as one

IFSC and UPI VPA are genuinely absent. Adding them — checksum-valid generation,
near-miss negatives, Devanagari and code-mixed surface forms — is real, useful
work. **Fork REDACT, add the Indian slice, run `certify_fpr` over their released
harness, and offer it upstream.** MIT-licensed code; dataset terms explicitly
support "research, evaluation, auditing."

**But be clear what that is.** It is a paper. Labelling and regex-taxonomy work
with a low technical ceiling, using our infrastructure but not our actual edge,
producing an asset that monetises in citations. Weeks, not months. Worth doing
for credibility and for the `certify_fpr`-over-someone-else's-harness
demonstration. **Not a company, and not a reason to defer §5's real task.**

### What the REDACT contribution actually produced

Done, on 2026-09-09: `certify_fpr` run over REDACT's released locked split, seven
pairings, results in `results/external/redact-*` and written up in
[`docs/REDACT.md`](../docs/REDACT.md).

It turned up something the plan did not anticipate, and it is a **second
primitive alongside refusal**:

> Across twenty budgets, Presidio yields **1–3 distinct operating points**. The
> injection classifier yields 15; our probe yields 20. Presidio emits eight
> distinct scores over 1,000 records, 668 of them exactly 1.0.

A rule-based detector's confidence is a rule-fired indicator, not a rankable
score, so **a false-positive budget is not a dial you can set on it**. And an F1
table structurally cannot show this: F1 is computed wherever the detector already
sits and never varies the threshold.

So there are now two things certification says that scoring does not:

1. **Refusal** — the evidence does not support a claim at this budget.
2. **Tunability** — this detector cannot be moved to your budget at all.

Both are procurement facts. Neither is in REDACT, PIIBench, or any eval platform
surveyed. That is a stronger position than the first version of this document
had, and it is still not evidence that anyone pays for it.

### The real task: find out whether anyone is punished for a wrong claim

This is the load-bearing assumption under the entire product and it has never
been tested. Two weeks, no code:

- **Talk to eight to twelve people** who would run this: model-validation leads
  in Indian banks and NBFCs, DPO/compliance leads at Indian SaaS firms with EU
  exposure, one or two AI-assurance practices.
- **Ask what happens when a control is wrong.** Not whether they would like
  confidence intervals — everyone says yes. Ask: *has a guardrail ever been found
  wrong after deployment; what happened to whoever signed it off; what evidence
  did anyone ask for; who paid.*
- **Show them a refusal**, not a certification. `examples/refuses.csv` is the
  demo. Watch whether "we cannot tell you at this budget" reads as integrity or
  as a broken tool. That reaction is the product's whole thesis, tested.
- **Write down the answers before interpreting them**, and pre-register what
  would count as a no.

**The falsifier, registered now:** if fewer than three of twelve can name a
specific occasion where a wrong AI control claim had a consequence for someone,
then nobody is punished for a wrong claim, refusal has no buyer, and this is a
research project with unusually good infrastructure — which is a fine thing to
be, but should be known before another phase is spent.

### Meanwhile, cheap and worth doing

1. **`warrant certify` should report the frontier, not one budget.** The sweep
   machinery exists.
2. **`warrant recheck`** — compare a new file against a prior warrant. The drift
   machinery is built and has no customer-facing path, and this is the entire
   "when the number stops being true" clause.
3. **Close `DECISIONS.md` 138 or scope it out.** Open for three phases; an item
   carried indefinitely is a decision made by default.

---

## 6. What I am still not confident about

- **Whether anyone pays for any of this.** Unchanged, and now the central
  question rather than a footnote.
- **Whether refusal survives contact with a buyer.** It may read as weakness.
- **The competitive scan is still thin.** I have now been wrong once by not
  reading past the first page of results; assume the same is true of the vendor
  landscape, which I assessed largely from vendor-written comparisons.
- **Whether REDACT's Indian coverage is deep or nominal.** Aadhaar has 42 seed
  entries and Devanagari forms, which is not nominal. I did not evaluate whether
  the *generated corpus* exercises them at useful density — that is checkable
  against their released data and I have not done it.

---

## 7. The one sentence

The benchmark wedge does not exist, the only thing that is genuinely ours is the
refusal, and whether the refusal is worth anything is a question about who gets
punished for a wrong claim — which is answered by twelve conversations, not by
another phase of code.

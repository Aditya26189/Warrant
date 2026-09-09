# Where this should go next

**Dated 2026-09-09. Strategy decays; re-read the dates before acting on it.**

---

## The short version

**Stop leading with the hallucination probe. Lead with Indian PII, and build the
benchmark nobody has.**

Three things came out of the research that change the picture:

1. **The statistics are not a moat.** A peer-reviewed ACL 2026 paper certifies a
   threshold with Clopper-Pearson bounds — the same shape of guarantee
   `certify_fpr` produces. A competent competitor rebuilds our core estimator in
   about a week.
2. **Both regulatory tailwinds you would assume are later than assumed.** The EU
   AI Act's high-risk obligations were **deferred to December 2027**, and the
   revised US banking model-risk guidance **explicitly excludes generative and
   agentic AI from scope**. I nearly wrote the opposite of that second one — see
   §3.
3. **India's DPDP has a hard enforcement date of 13 May 2027**, there are already
   vendors selling Indian PII detection, and **no public labelled benchmark
   exists to check any of them.** That is the gap, in the home market, on the
   nearest real deadline.

The asset is not the detector. It is the refusal, the evidence trail, and — if
we build it — the benchmark everyone else has to be measured against.

---

## 1. What we actually have

An honest inventory, because a plan built on a flattering one is worthless.

**Genuinely strong:**

- **Refusal as a first-class outcome with no override.** Verified as
  differentiated: the ACL 2026 conformal-routing work certifies with the same
  Clopper-Pearson machinery but **never abstains** — it routes everything and
  guarantees a bound. Ours says *"the evidence does not support this"* and exits
  0. I could not find a commercial product that does this.
- **`warrant certify` works on anyone's CSV** (Phase 2). Three columns, no model,
  no config, nothing leaves the machine.
- **The external matrix** (Phase 3): seven pairings, third-party detectors at
  documented defaults, every cell carrying its version, revision, licence and a
  one-command reproduction.
- **The evidence infrastructure**: hash-chained ledger, content-hashed eval sets,
  provenance on every artifact, 992 tests, `make verify` at 40/40 claims.

**Weak, and it matters:**

- **Our own probe is the weakest detector in our own matrix.** At a 0.05 budget
  it reaches recall 0.231 while Presidio's email recognizer reaches 1.000 and the
  prompt-injection classifier reaches 0.616 (`results/external/MATRIX.md`). Any
  pitch that leads with our detector loses to a reader who opens the table.
- **Zero production traffic. Zero external users. Zero customers.** Everything
  measured is public or synthetic corpora.
- **Every external row is in-sample**, ours included.
- **The founding Indian-identifier thesis has no data behind it yet.** Phase 3
  established that no public dataset carries Aadhaar/PAN/UPI/IFSC labels, so the
  most specific claim the project wanted to make is the one it cannot currently
  support.

**Half-built and worth knowing about:** `sampling/`, `gate/` and
`economics/sizing.py` are specified and unwritten; the on-traffic warrant —
clause one of the three in `CLAUDE.md` — does not exist.

---

## 2. What the research says

### The method is published

**[Conformal LLM Routing with Distribution-Free Safety Guarantees](https://aclanthology.org/2026.acl-srw.70/)**
(ACL 2026) uses "Clopper-Pearson conformal calibration [to select] a routing
threshold that guarantees the violation rate among routed queries stays below α
with probability at least 1 − δ." Related 2026 work:
[When Can Conformal Risk Control Certify LLM Outputs?](https://arxiv.org/html/2606.29054v1)
and [Beyond Red-Teaming: Formal Guarantees of LLM Guardrail Classifiers](https://arxiv.org/html/2605.10901v1).

**Read this correctly.** It does not mean the work is wasted — it means the
technique is *respectable and reproducible*, which is what you want in something
an auditor will lean on. It does mean the defensibility has to come from
somewhere other than the estimator.

### The eval market is crowded

Patronus, Galileo, Braintrust, Future AGI, Langfuse, LangSmith, DeepEval,
Phoenix, TruLens, Arize. Several are well funded and ship runtime guardrails plus
evaluation ([Braintrust's own survey](https://www.braintrust.dev/articles/best-ai-governance-platforms-llm-applications-2026),
[Galileo's](https://galileo.ai/blog/best-ai-agent-evaluation-platforms)).

Every one of them answers *"how good is this?"* with a number. None of the
material I read describes a product that answers *"we cannot tell you, and here
is what it would take."* That is the only空 space I found.

### Both regulatory clocks are slower than assumed

**EU AI Act.** Regulation (EU) 2026/1744 (the Digital Omnibus on AI), in force
27 July 2026, **deferred standalone high-risk obligations from 2 August 2026 to
2 December 2027**, and embedded-product high-risk to August 2028
([Holland & Knight](https://www.hklaw.com/en/insights/publications/2026/04/us-companies-face-eu-ai-acts-possible-august-2026-compliance-deadline),
[CSA](https://labs.cloudsecurityalliance.org/research/csa-research-note-eu-ai-act-high-risk-deadline-omnibus-20260/)).
Article 50 transparency, GPAI obligations and Article 5 prohibitions still apply
now.

**US banking.** [SR 26-2](https://www.federalreserve.gov/supervisionreg/srletters/SR2602.htm) /
[OCC Bulletin 2026-13](https://www.occ.gov/news-issuances/bulletins/2026/bulletin-2026-13.html),
issued 17 April 2026, revises model-risk guidance for banks over $30bn — and
says plainly: *"Generative AI and agentic AI models are novel and rapidly
evolving. As such, they are not within the scope of this guidance."* The agencies
"plan to issue in the near future a request for information that addresses model
risk management generally and considers, in particular, banks' use of AI."

**India.** DPDP Rules notified 13 November 2025. Consent Manager provisions bite
**13 November 2026**; the 18-month transition ends **13 May 2027**, widely treated
as hard enforcement
([India Briefing](https://www.india-briefing.com/news/india-dpdp-compliance-timeline-enforcement-2026-27-44740.html/),
[Fisher Phillips](https://www.fisherphillips.com/en/insights/insights/indias-new-data-privacy-rules-are-here)).

**India is the nearest real deadline, and it is the home market.**

### The Indian PII gap is real, and it is a gap in *evidence*, not in tools

Tools exist and are shipping: `dpdpa-pii-scrubber`, `pii-detection-cipherx`, and
commercial DPDP vendors (Complynz claims 50+ India-specific patterns; also
dcomply, CrewCheck). What does **not** exist is a public labelled benchmark for
Aadhaar/PAN/UPI/IFSC with formal evaluation. ai4privacy carries 54–63 classes and
none of them is an Indian identifier — which Phase 3 measured independently.

So: a market of vendors making detection claims, a regulator-driven deadline
eight months out, and **no way for a buyer to check any claim.**

---

## 3. The mistake I nearly made, and why it belongs in this document

A vendor blog stated that SR 26-2 "extends the prior framework to address AI/ML
systems, LLMs, and agentic architectures" and quoted it as requiring that
"vendor attestations do not satisfy the requirement" — that institutions
"cannot transfer risk to a vendor by sourcing an AI model." It read as a perfect
fit for this product, and I was one step from building the plan on it.

The primary sources say the opposite: generative and agentic AI are **out of
scope**.

Had that gone into a deck, the first banking buyer with a compliance team would
have found it in a minute, and everything else we said would have been
discounted. This is the same failure mode the project exists to prevent, arriving
through the business plan rather than through a metric — and the same fix
applies: **go to the primary source, and treat a convenient claim as the one most
in need of checking.**

Make this a rule: **no regulatory or competitive claim in any external material
without a primary-source link and a date.**

---

## 4. The recommendation

### The wedge: become the reference measurement for Indian PII detection

**Build and publish `dpdp-pii-bench`** — a public, labelled, content-hashed
benchmark for Indian identifiers (Aadhaar, PAN, UPI VPA, IFSC, GSTIN, voter ID,
ABHA), with Hinglish and code-mixed text, then certify every available detector
against it and publish the matrix.

Why this and not something else:

- **It is a moat in a way the maths is not.** Anyone can reimplement
  Clopper-Pearson. A credible, adopted benchmark takes labelling effort and
  earns citations, and whoever owns it is in the room for every procurement
  conversation.
- **It uses what is already built.** The Presidio adapter, the eval-set
  machinery with content hashing, `certify_fpr`, the external harness, the
  matrix renderer. Phase 3's registry takes a new dataset in three dataclasses.
- **It serves a dated deadline in the home market** where the buyers are and the
  founders are.
- **It is a distribution asset.** A table showing which Indian PII detectors can
  and cannot be certified at a stated false-positive budget is something a
  compliance lead forwards. Nothing else we have is.
- **It converts our weakest position into our strongest.** We stop saying "our
  detector is good" — which the matrix disproves — and start saying "we are the
  people who measured everyone, including ourselves, and published the method."

**The credibility rule from Phase 3 carries over and gets stricter**: documented
defaults only, refusals reported neutrally, our own entries on identical terms,
and one-command reproduction for every cell. If we publish a refusal a vendor can
show was our misconfiguration, this strategy ends that day.

### What the product becomes

Not a detector. Not another eval platform. **The instrument a compliance or
validation function runs to check somebody else's claim, that produces evidence
which stays on their machine.**

The local-only property (Phase 2 D28) stops being a footnote and becomes a lead
feature: an Indian bank or hospital cannot send production PII to a US SaaS
evaluator, and every hosted competitor has that problem structurally.

---

## 5. The plan

Ordered by what unblocks the most. Each is a phase brief in the format that has
worked.

### Phase 4 — the benchmark (highest value, no gate)

- Design the taxonomy and the label rule per identifier, written before any data
  exists.
- Generate candidate items with **checksum-valid** Aadhaar (Verhoeff) and PAN
  formats, and — critically — **near-miss negatives**: checksum-invalid Aadhaar,
  PAN-shaped strings that are not PANs, IFSC-shaped non-codes. The negatives are
  where the benchmark earns its keep, and Phase 3's credit-card finding is the
  proof: a detector that validates checksums scores 0.070 against a generator
  that does not, and the number means nothing without knowing that.
- Hand-label a real subset. Publish inter-rater κ beside every warrant, per the
  standing rule.
- Content-hash and freeze. Ship the generator, not just the data.
- Certify Presidio, the two open-source Indian scrubbers, and any vendor that
  will let us, on identical terms.

**Gate:** if we cannot get κ above ~0.6 on the hand-labelled subset, the
benchmark is not publishable and the phase says so.

### Phase 5 — close the two open items, or write them off

`DECISIONS.md` 138 has been open for three phases: closed-API matrix (needs
credentials) and corpus expansion / out-of-distribution transfer (needs a GPU).
Both are cheap. **Decide: fund them or formally scope them out.** An open item
carried indefinitely is a decision made by default, and the OOD question is the
one a technical reviewer will ask first.

### Phase 6 — the on-traffic warrant

Clause one of the three in `CLAUDE.md` — *"what your error rate is on your
traffic"* — is unbuilt (`sampling/`, `economics/sizing.py`). Until it exists the
product only certifies against a fixed corpus, which is the weaker half of the
proposition. This is the largest remaining engineering gap and it is what turns a
benchmark tool into a monitoring product.

### Phase 7 — the things that make it usable by someone who is not us

Concrete improvements to what exists, in rough priority:

1. **`warrant certify` reports a curve, not a point.** It answers one budget at a
   time; the sweep machinery already exists. One run should show the whole
   frontier and what each budget costs.
2. **A refusal should say what to do next in the user's units** — "you need 262
   more clean negatives" rather than the requirement and the count separately.
3. **`--out` defaults beside the input**, which pollutes a user's directory. Make
   it a directory choice.
4. **The drift machinery has no customer-facing path.** `drift/` and the
   revocation ladder are built and reachable only from the research pipeline; a
   `warrant recheck` that compares a new file against a prior warrant is close to
   free and is the whole "when the number stops being true" clause.
5. **The gateway adapter is an adapter and not a gateway** — keep it that way,
   and either finish it as a reference integration or cut it.

### What not to do

- **Do not build a better detector.** We are worst in our own matrix, the field
  is crowded, and it is not what anyone would buy from us.
- **Do not chase EU AI Act high-risk urgency in 2026.** It moved to December
  2027. Selling against a deadline a buyer's counsel knows has been deferred is
  the fastest way to lose a room.
- **Do not claim SR 26-2 covers LLM guardrails.** It does not. Watch for the
  RFI — being early and substantive on *that* is worth more than a wrong claim
  now.
- **Do not publish anything about a named vendor without the reproduction
  command and the configuration**, per Phase 3 D34/D36.

---

## 6. What would falsify this

Written down now so it cannot be quietly dropped later:

- **Nobody adopts the benchmark.** If after publication and outreach no third
  party cites or re-runs it in six months, it is a private test set with good
  documentation, not a moat.
- **A vendor demonstrates our configuration was wrong** on a published cell.
  Recoverable once, fatal twice.
- **The DPDP deadline slips**, as the EU's did. The Consent Manager date of 13
  November 2026 is the early warning; if that moves, assume May 2027 moves.
- **An incumbent ships refusal.** It is a week of work for anyone who decides to,
  and our lead is the discipline and the evidence trail, not the idea.
- **Buyers turn out to want a number rather than an honest interval.** This is
  the real commercial risk and it is unresolved: the entire product assumes
  someone is punished for a wrong claim. In a market where nobody is yet, the
  refusal is a cost rather than a feature.

## 7. What I am not confident about

- **Whether anyone pays for this, and how much.** I found no pricing data for
  independent validation of AI controls. Nothing here establishes willingness to
  pay; it establishes that the evidence gap is real.
- **Whether the Indian PII benchmark is a business or a marketing asset.** It may
  be the thing that gets attention and something else entirely that gets bought.
- **Whether we can label to a defensible standard.** Phase 4's gate exists
  because I do not know the answer.
- **The competitive scan is thin.** I read vendor comparison content, much of it
  written by the vendors. A serious pass would trial two or three products.

---

## 8. The one sentence

We are not a detection company and should stop trying to be one; we are the
people who will tell you, with an interval and a reproduction command, whether
the thing you bought actually works — and the fastest way to prove that is worth
something is to measure every Indian PII detector on a benchmark we build and
publish, including our own, before May 2027.

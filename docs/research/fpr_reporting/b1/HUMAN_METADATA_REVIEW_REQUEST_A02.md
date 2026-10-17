# Human metadata adjudication required before B1 selection

This is a **domain-eligibility review**, not a pilot outcome extraction or a
six-paper human assignment. No human FPR sheet or results are needed.

- Work: `arxiv:2403.17710`.
- Title: *Optimization-based Prompt Injection Attack to LLM-as-a-Judge*.
- [Primary bibliographic source](https://arxiv.org/abs/2403.17710).
- Retained raw metadata ID: `http://arxiv.org/abs/2403.17710v5`.
  This is a captured metadata version, not an approved selected version;
  the cutoff-based version choice has not run.
- Captured metadata: `a02-metadata/metadata_union.jsonl`, record with that ID.
- Current domain state: **UNCLEAR**, never silently excluded or included.

The abstract describes injection into candidate responses supplied to an LLM
judge, an empirical attack evaluation, and defenses including known-answer and
perplexity detectors. It does not establish whether the defense evaluation is
a qualifying binary prompt-injection input-classification evaluation or only
end-to-end attack resistance. No FPR statement, denominator, assurance language
or numerical result is required for inclusion and none was used for this call.

The approved frame says: "If title/abstract cannot establish domain, retain
`UNCLEAR` for human metadata screening". It excludes response moderation,
jailbreak-only safety tasks and end-to-end attack-success-only defenses.
See the unchanged `PILOT_FRAME_DRAFT.md` domain section. Eligibility is about
the detector task/evaluation unit, not whether any result appears interesting.

Please return **INCLUDE**, **EXCLUDE** or **UNCLEAR** with a bibliographic/method
rationale and source/version locator. If including, identify evidence of an
English-text binary pre-answer input-classification evaluation; if excluding,
identify the applicable approved domain rule. Do not provide FPR outcomes,
sample/false-positive counts, assurance claim classifications or a completed
human extraction sheet. This ordinary metadata adjudication does not itself
change the protocol or authorize B2.

Until resolved, the complete eligible frame and seeded draw remain blocked.
Other unscreened works remain explicitly pending rather than implicitly excluded.

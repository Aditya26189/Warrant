# Applying the injection-task boundary

25 October 2026. Recorded before the next task judgments. The locked frame
already excludes harmful-content/jailbreak classification alone and requires a
separate evaluated input-injection task. This note does not add a criterion.

Judge the original evaluation's units, threat/task construction and ground-truth
labels. A model called an injection detector, a template containing adversarial
instructions, or an input-side binary decision does not by itself establish the
required experiment. A complete study limited to unsafe-content flags, refusal,
or jailbreak-versus-benign requests remains outside this domain unless it also
evaluates detection of injected instructions as a separate input task.

The same distinction applies to auxiliary repetition/known-answer probes. They
can run before an original-task answer; that resolves timing, not the empirical
task definition. Conversely, a comparator named a jailbreak model can qualify
when it is actually evaluated on the work's injection/benign input task. Do not
select on names or require the literal phrase "prompt injection" where the
primary method otherwise establishes the qualifying task.

Consider every original secondary experiment and comparator. A declared complete
method/task inventory can establish a jailbreak-only/content-only exclusion;
partial evidence or uncertain task semantics remains UNCLEAR. Do not use results,
reporting sufficiency, interestingness, sample counts or assurance statements.
Keep source-specific rationale and edge-case limitations visible for frame
approval. The approved direct/indirect scope and the earlier known-answer
input-detector domain adjudication are unchanged.

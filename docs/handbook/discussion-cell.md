# Scientific discussion

*This discussion concerns the committed study artifacts. It is not execution
output from this notebook and does not imply that every study was rerun here.*

The retained last-token probe ranks the recorded TriviaQA error labels
(AUROC 0.8256), while recall at its particular operating point is 0.0794
([C001-C004](https://github.com/Aditya26189/Warrant/blob/main/docs/handbook/claims.md)).
These are compatible findings: ranking across thresholds differs from recall
at a restrictive cut. The feature is the final prompt position **before**
generation; it is a correlational predictor of the subsequent recorded
matching-rule outcome, not a measurement of truth or belief.

Under the constructed long-context feature shift, last-token AUROC remains
0.8135, whereas mean pooling is 0.5015 and rolling maximum 0.5553.
The proposed rolling-window rescue did not hold in this transfer. Dilution,
position and distractor-extreme effects are possible explanations, not isolated
causal findings. Target features reuse the original answers and labels, so
this does not measure fresh long-context generation accuracy.

The evidence audit distinguishes reproducibility from justification: all
92 table rows match retained fields, but
15 retain direct dirty-source provenance.
A separate oracle agrees on 25 frozen-score
point targets; it does not validate labels or interval coverage.
The tied-score diagnostic also leaves the general native returned-bound
interpretation under [open review](https://github.com/Aditya26189/Warrant/blob/main/docs/research/fpr_reporting/issues/FPR-001-adaptive-bound.md).

The main lesson is to retain the estimand, independent unit, protocol, inputs
and failure history with each result. The project supports a reproducible
local evaluation toolkit and bounded research findings. Production validity,
independent source adjudication and general scientific novelty remain
unestablished. The [full discussion](https://github.com/Aditya26189/Warrant/blob/main/docs/handbook/findings.md)
separates observations, explanations and additional evidence needed.

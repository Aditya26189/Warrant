# Bounded language-declaration inspection

27 October 2026. The separately checked additional006 receipt includes a boolean
stating whether the supplied official conference-call page declares a language.
The strict release helper rejected that previously unsupported field before
writing release015. The provider and checker records remain unchanged.

Allow only the exact `additional_source_inspection.language_declaration_found`
path and actual JSON booleans. Preserve the page's source/hash/locator context
and the checker's limits in the receipt. Other inspection fields remain blocked.
A false value describes the inspected page alone; it does not establish that
every conference policy lacks a requirement, or that the paper has no English
evaluation. A true value likewise would require a separate scientific linkage
to the selected paper's qualifying experiment. This field cannot replace a
complete evaluated-arm inventory or justify a whole-work exclusion.

The regression first reproduced the unsupported-path error, then checked both
boolean values, rejected strings/numbers/null/objects and rejected another
inspection path. Existing actor separation, source binding, restriction and
held-field gates are unchanged. This is a research import repair, with no change
to production certification, domain criteria, sampling, historical evidence or B2.

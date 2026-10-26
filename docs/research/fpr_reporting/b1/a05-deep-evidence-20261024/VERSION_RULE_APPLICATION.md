# Applying the locked version rule consistently

24 October 2026. Recorded before the deeper continuation's version corrections.
This interprets the existing rule; it does not change the cutoff, preferences,
eligible universe, access policy or sampling unit. Original A05 files remain
historical evidence, including their more conservative compiler output.

The locked rule prefers an available publisher version of record by the cutoff,
then an accepted public conference edition, then the latest dated preprint. It
requires source identity and version/date evidence. It does not require a trusted
historical timestamp authenticating every exact PDF byte. The previous compiler
introduced that additional requirement for W0339 while accepting other official
editions using their publication identity/date. That inconsistency needs repair.

* An official publisher's declared edition/publication date and edition identity
  can establish the bibliographic version under review. Preserve the exact
  captured body hash and later retrieval date separately. This supports a
  bibliographic selection, not a claim that these precise bytes have been
  cryptographically authenticated as available on that historical day.
* HTTP Last-Modified is representation metadata chosen by the origin server;
  its derivation can depend on multiple representation components. A later value
  alone neither proves a new scholarly edition nor proves that content stayed
  unchanged. Preserve it as a limitation; investigate an actual revision or
  conflicting publisher edition date rather than automatically treating it as
  the publication date. See [RFC 9110, section 8.8.2](https://httpwg.org/specs/rfc9110.html#field.last-modified).
* DOI syntax is not a publication-type classifier. Establish whether the known
  DOI identifies a publisher edition, accepted version, repository preprint or
  other artifact from primary bibliographic metadata. Do not automatically give
  every non-arXiv DOI publisher priority. A registration/deposit/index timestamp
  is not a substitute for the edition's public date; Crossref distinguishes
  these event types in its [REST API filters](https://www.crossref.org/documentation/retrieve-metadata/rest-api/rest-api-filters/).
* A failed DOI lookup is an access/identity record. It does not prove that a
  higher-priority publisher edition exists, and it does not prove that none
  exists. Use the available primary publication/crosslink metadata to decide
  whether a material preferred-version question remains.
* Retain actual date precision and any conflicting primary date fields. A later
  server field does not automatically override a specific online date, while a
  known post-cutoff scholarly revision cannot be silently backdated.
* Keep a withdrawn latest arXiv version distinct from an ordinary PDF access
  error. arXiv's [version policy](https://info.arxiv.org/help/versions.html)
  explains that withdrawal adds a notice version without a full-text download.
  This does not authorize substitution of the earlier full text. The existing
  withdrawal questions remain explicit until their application is resolved.

Each actual correction must identify the primary evidence, prior row hash,
selected edition, exact body binding and remaining limitations. No method fact
transfers between editions merely because their bibliographic identities match.
New root-captured publisher metadata is not released scientific evidence until
the separately attributed source check is complete. Previously checked W0339
metadata and method facts can be reconsidered under this interpretation without
pretending a new source check or historical authentication occurred.

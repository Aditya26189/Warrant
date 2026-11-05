# Warrant technical preprint

**Aditya Singh, IIT Kharagpur · Version 1.0 · 5 November 2026**

**Warrant: Reproducible Evaluation and Evidence Management for AI Detectors**

Technical preprint; not peer reviewed. This report describes an implemented
system, bounded findings, adverse outcomes and an internal evidence audit.
No new neural architecture, production validation or established publication
contribution is claimed.

## Read and trace

- [Compiled manuscript](warrant-preprint.pdf)
- [Canonical LaTeX](warrant.tex) and [bibliography](references.bib)
- [Research findings and discussion](../docs/handbook/findings.md)
- [Every quantitative README claim](../docs/handbook/claims.md)
- [Qualitative capability investigation](../docs/handbook/qualitative-claims.md)
- [Data origins and attribution](../docs/handbook/data-sources.md)

The author identity and affiliation were supplied by the author. No degree,
email, ORCID, institutional endorsement, DOI or acceptance is inferred.

## Source structure

| Path | Purpose |
| --- | --- |
| `warrant.tex` | Layout, abstract and section assembly |
| `sections/` | Related work, design, methods, findings and limitations |
| `references.bib` | Primary-source bibliography |
| `metadata.json` | Author, version, date, status and license |
| `generated/` | Evidence-derived author and numeric macros |
| `toolchain.json` | Exact compiler downloads and SHA-256 values |
| `build.py` | Entry point into the reusable paper library |
| `build-receipt.json` | Compiler/source/output provenance |
| `visual-review.json` | Separate page inspection record |
| `zenodo-metadata.json` | Prepared metadata, with no upload operation |
| `LICENSE.md` | Manuscript/source license and third-party boundaries |

## Build and verify

Use Python 3.11 or newer for the publication toolchain. From the repository root:

```sh
python -m pip install -r requirements-customer.txt -r requirements-docs.txt
python paper/build.py --check
python paper/build.py --generate --check
```

The second command detects stale macros. The third regenerates them from
retained evidence without rerunning a model. Commit changes before compiling
a provenance-bearing PDF.

Install **Tectonic 0.17.0** using the official release URLs and hashes in
[toolchain.json](toolchain.json). Verify the downloaded archive's SHA-256 before
extraction. The first compilation downloads its TeX resource bundle. This pin
does not establish bit-identical output across arbitrary TeX environments.

From clean committed source, use a new directory outside the checkout:

```sh
python paper/build.py --engine /absolute/path/to/tectonic --out ../paper-build-v1
```

On Windows use the full path to `tectonic.exe`. The builder copies LaTeX/BibTeX
inputs into an isolated directory, compiles in untrusted mode, retains logs and
hashes, checks references and overfull boxes, and rejects source changes.
Visual inspection remains necessary. A revision needs a new commit and output
directory.

The standalone source ZIP retains generated macros. Compile it directly with
`tectonic --untrusted warrant.tex`. Python and the source/evidence snapshot are
needed to regenerate the macros, not to typeset them.

## Prepare a Zenodo deposit

The manuscript and LaTeX source use **CC BY 4.0**. Software remains MIT and
third-party inputs retain their original notices. See [LICENSE.md](LICENSE.md).

After retaining and committing the reviewed PDF:

```sh
python paper/build.py --package-out ../warrant-zenodo-v1
```

This exports the PDF, standalone LaTeX ZIP, tracked source/evidence ZIP,
metadata and checksums. `git archive HEAD` excludes ignored caches, untracked
private material and Git history. Inspect the package before publication;
tracking alone is not a license audit.

The development repository was private during preparation. Deposit the reviewed
source/evidence supplement with the PDF and LaTeX so CPU checks are accessible
without private GitHub access. Original activation replay still requires caches
and historical model identity not reconstructed by this package.

In your Zenodo account create a **Publication → Preprint** record, review the
files and metadata, and reserve or assign the DOI there. No DOI is invented
here. Depositing a preprint is not peer review. This tooling does not upload
or publish.

## Scientific boundary

Artifact agreement and separate point arithmetic do not adjudicate labels,
prove interval coverage, recover missing source states or repair FPR-001.
The manuscript preserves those distinctions and the original REPORT/STOP
outcomes of the closed studies.

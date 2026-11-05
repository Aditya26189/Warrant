"""Inspect claim provenance and independently check frozen-score point estimates.

This is a documentation audit, not an endorsement of statistical guarantees.
It never regenerates or overwrites the scientific artifacts it inspects.
"""
from __future__ import annotations

import argparse
import ast
from bisect import bisect_left, bisect_right
from dataclasses import asdict
import hashlib
import json
import math
from pathlib import Path
import re
import subprocess
from typing import Any
from urllib.parse import unquote

from .claims import check_claims, parse_claim_table, resolve


def repo_file(root: Path, name: str) -> Path:
    """Resolve a declared source path; reject traversal and missing files."""
    path = (root / name).resolve()
    if not path.is_relative_to(root.resolve()) or not path.is_file():
        raise ValueError(f"not a repository file: {name}")
    return path


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def point_oracle(labels: list[int], scores: list[float], threshold: float) -> dict:
    """Compute row point estimates without NumPy, SciPy or the metric builder.

    AUROC is the positive-versus-negative pair probability, giving tied pairs
    one half. Intervals, independence, label truth and guarantees are not tested.
    Undefined precision is reported explicitly, never interpreted as zero risk.
    """
    if not labels or len(labels) != len(scores):
        raise ValueError("labels and scores need equal, nonzero length")
    if any(type(y) is not int or y not in (0, 1) for y in labels):
        raise ValueError("labels must be integer 0/1")
    if not math.isfinite(threshold) or any(not math.isfinite(s) for s in scores):
        raise ValueError("scores and threshold must be finite")
    n = len(labels)
    positive = sum(labels)
    negative = n - positive
    flagged = [s >= threshold for s in scores]
    tp = sum(y == 1 and f for y, f in zip(labels, flagged, strict=True))
    fp = sum(y == 0 and f for y, f in zip(labels, flagged, strict=True))
    nf = sum(flagged)
    both = positive > 0 and negative > 0
    area = None
    if both:
        neg = sorted(s for y, s in zip(labels, scores, strict=True) if y == 0)
        twice_u = sum(bisect_left(neg, s) + bisect_right(neg, s)
                      for y, s in zip(labels, scores, strict=True) if y == 1)
        area = twice_u / (2 * positive * negative)
    return {
        "n_rows": n, "n_positive": positive, "n_negative": negative,
        "n_flagged": nf, "true_positives": tp, "false_positives": fp,
        "base_rate": positive / n, "auroc": area,
        "recall": tp / positive if both else None,
        "precision": tp / nf if both and nf else None,
        "flag_rate": nf / n, "fpr": fp / negative if negative else None,
        "precision_defined": bool(both and nf),
    }


def score_audit(root: Path) -> list[dict]:
    """Hash-check frozen vectors and compare defined point estimates only."""
    from ..validation.scores import load_score_set

    rows = []
    for path in sorted((root / "results/scores").glob("*.json")):
        raw = read_json(path)
        if not raw.get("content_hash"):
            raise ValueError(f"frozen score lacks a recorded content hash: {path.name}")
        score_set = load_score_set(path)  # also checks its recorded content hash
        for target in score_set.targets:
            document = read_json(repo_file(root, target.artifact))
            block = resolve(document, target.metrics_path)
            values = point_oracle(list(score_set.labels), list(score_set.scores),
                                  target.threshold)
            checked, differences, undefined = {}, [], []
            for key in ("auroc", "recall", "precision", "flag_rate"):
                expected = values[key]
                retained = block.get(key)
                if expected is None:
                    undefined.append(key)
                    if retained is not None and key != "precision":
                        differences.append(f"{key}: should be absent on a single class")
                    continue
                if retained is None or not math.isclose(
                    float(retained["value"]), expected, rel_tol=1e-12, abs_tol=1e-15,
                ):
                    differences.append(f"{key}: retained and independent points differ")
                checked[key] = expected
            rows.append({
                "score_file": path.relative_to(root).as_posix(),
                "score_sha256": digest(path), "artifact": target.artifact,
                "metrics_path": target.metrics_path, "threshold": target.threshold,
                "score_provenance_dirty": raw.get("provenance", {}).get("dirty"),
                "counts": {k: values[k] for k in (
                    "n_rows", "n_positive", "n_negative", "n_flagged",
                    "true_positives", "false_positives")},
                "defined_points_checked": checked, "undefined_quantities": undefined,
                "differences": differences, "ok": not differences,
                "intervals_independently_checked": False,
                "issuance_status_recomputed": False,
            })
    if not rows:
        raise ValueError("no frozen-score targets; an empty audit is not a pass")
    return rows


def source_flags(document: dict) -> list[str]:
    """Describe the source flags without inferring an unrecorded clean state."""
    prov = document.get("provenance")
    if not isinstance(prov, dict):
        return ["MISSING_PROVENANCE"]
    flags = []
    if prov.get("dirty") is True:
        flags.append("DIRTY_SOURCE")
    elif prov.get("dirty") is not False:
        flags.append("CLEANLINESS_NOT_RECORDED")
    if not prov.get("git_commit"):
        flags.append("SOURCE_COMMIT_NOT_RECORDED")
    return flags


def collect_audit(root: Path, registry_path: Path | None = None) -> dict:
    """Collect complete README-table coverage plus explicitly scoped oracles."""
    root = root.resolve()
    registry_path = registry_path or root / "docs/handbook/claim-families.json"
    registry = read_json(registry_path)
    by_artifact: dict[str, dict] = {}
    for family in registry["families"]:
        for field in ("question", "interpretation", "limitations", "reproduction"):
            if not family.get(field):
                raise ValueError(f"family {family['id']} lacks {field}")
        for name in family["writers"] + family["inputs"]:
            repo_file(root, name)
        for name in family["artifacts"]:
            repo_file(root, name)
            if name in by_artifact:
                raise ValueError(f"duplicate artifact classification: {name}")
            by_artifact[name] = family
    claims = parse_claim_table(root / "README.md")
    if not claims:
        raise ValueError("the README claim table is empty")
    named = {c.artifact for c in claims}
    if named != set(by_artifact):
        raise ValueError(f"unclassified or unused artifacts: {named ^ set(by_artifact)}")
    checks = check_claims(root)
    scores = score_audit(root)
    rows = []
    for index, (claim, check) in enumerate(zip(claims, checks, strict=True), 1):
        path = repo_file(root, claim.artifact)
        document = read_json(path)
        covered = []
        for target in scores:
            prefix = target["metrics_path"] + "."
            if target["artifact"] == claim.artifact and claim.field.startswith(prefix):
                metric = claim.field[len(prefix):].split(".")[0]
                if metric in target["defined_points_checked"] and claim.field.endswith(".value"):
                    covered.append({"score_file": target["score_file"],
                                    "point_oracle_ok": target["ok"],
                                    "intervals_independently_checked": False})
        family = by_artifact[claim.artifact]
        upstream = []
        for name in family["inputs"]:
            if name.endswith(".json"):
                inp = read_json(repo_file(root, name))
                if isinstance(inp, dict) and "DIRTY_SOURCE" in source_flags(inp):
                    upstream.append(name)
        rows.append({"id": f"C{index:03d}", **asdict(claim),
                     "resolved_value": resolve(document, claim.field),
                     "artifact_sha256": digest(path),
                     "artifact_match": check.ok, "artifact_match_detail": check.detail,
                     "family": family["id"], "evidence_kind": family["evidence_kind"],
                     "source_provenance": {k: document.get("provenance", {}).get(k)
                                           for k in ("git_commit", "dirty", "config_hash", "seed")},
                     "source_flags": source_flags(document),
                     "declared_input_dirty_flags": upstream,
                     "independent_point_evidence": covered,
                     "scientific_validity": "NOT_ESTABLISHED_BY_ARTIFACT_MATCH"})
    canonical = json.dumps([asdict(c) for c in claims], sort_keys=True,
                           ensure_ascii=False).encode()
    dirty = [r["id"] for r in rows if "DIRTY_SOURCE" in r["source_flags"]]
    return {"schema_version": 1, "kind": "documentation_evidence_audit",
            "claim_table_sha256": hashlib.sha256(canonical).hexdigest(),
            "registry_sha256": digest(registry_path),
            "scope": registry["scope"],
            "summary": {"claims": len(rows), "artifact_matches": sum(r["artifact_match"] for r in rows),
                        "distinct_artifacts": len(named), "families": len(registry["families"]),
                        "dirty_source_claims": len(dirty), "dirty_source_claim_ids": dirty,
                        "dirty_source_artifacts": sorted({r["artifact"] for r in rows if "DIRTY_SOURCE" in r["source_flags"]}),
                        "frozen_score_targets": len(scores),
                        "point_oracle_targets_passed": sum(r["ok"] for r in scores),
                        "claim_points_with_independent_evidence": sum(bool(r["independent_point_evidence"]) for r in rows)},
            "claims": rows, "frozen_score_point_checks": scores,
            "ok": all(r["artifact_match"] for r in rows) and all(r["ok"] for r in scores),
            "does_not_check": ["label truth", "independent sampling", "interval coverage",
                               "source reconstruction of dirty runs", "activation extraction",
                               "causal mechanisms", "production behavior", "research novelty"]}


def render_claims(report: dict, registry: dict) -> str:
    """Render a per-row ledger; family context is linked, never called proof."""
    families = {f["id"]: f for f in registry["families"]}
    s = report["summary"]
    lines = ["# Claim-by-claim evidence ledger", "",
             "This generated ledger checks retained evidence. Arithmetic agreement does not establish scientific validity.", "",
             f"Audit source: `{report['provenance']['git_commit']}`. The [machine receipt](../../results/documentation_audit/20261105/audit.json) retains hashes and explicit scope.", "",
             f"The audit covers {s['claims']} rows across {s['distinct_artifacts']} artifacts. {s['dirty_source_claims']} rows point directly to dirty-source artifacts. The independent point oracle checks {s['frozen_score_targets']} frozen-score targets, not every scientific proposition.", "",
             "Read [how to interpret this audit](claim-audit.md) and [family methods and limits](claim-families.md) first.", ""]
    for row in report["claims"]:
        f = families[row["family"]]
        lines += [f"## {row['id']}", "", f"**{row['label']}**", "",
                  f"Retained value: `{row['value']}`. Retained interval: `{row['interval']}`. Artifact equality: **{'MATCH' if row['artifact_match'] else 'MISMATCH'}**.", "",
                  f"- Evidence: [{row['artifact']}](../../{row['artifact']}); field `{row['field']}`.",
                  f"- Artifact SHA-256: `{row['artifact_sha256']}`.",
                  f"- Recorded source: `{row['source_provenance']['git_commit']}`; dirty: `{row['source_provenance']['dirty']}`; config: `{row['source_provenance']['config_hash']}`.",
                  f"- Recorded check/regeneration entry: `{row['command']}`. This is not a claim that this audit executed that command.",
                  f"- Evidence family: [{f['id']}: {f['title']}](claim-families.md#{f['id'].lower()}); type `{f['evidence_kind']}`.", "",
                  "**Why this claim is included.** " + f["question"], "",
                  "**What it means.** " + f["interpretation"], "",
                  "**Where the data and calculation come from.** " + "; ".join(
                      f"[{p}](../../{p})" for p in f["inputs"] + f["writers"]), "",
                  "**What remains unproved.** " + f["limitations"], ""]
        if row["source_flags"]:
            lines += ["**Source caution:** " + ", ".join(row["source_flags"]) + ". A matching value does not reconstruct the original working tree.", ""]
        if row["declared_input_dirty_flags"]:
            lines += ["**Upstream caution:** declared input references include dirty-source evidence: " + ", ".join(row["declared_input_dirty_flags"]) + ".", ""]
        if row["independent_point_evidence"]:
            lines += ["**Additional arithmetic check:** a separate rank/count oracle agrees with the frozen-score point estimate. Confidence intervals, label truth and warrant issuance are outside that oracle.", ""]
        else:
            lines += ["**Additional arithmetic check:** this row is not directly covered by the frozen-score point oracle. Its MATCH status is retained-field agreement, with the family's reproduction requirements stated separately.", ""]
    return "\n".join(lines)


def render_families(registry: dict) -> str:
    lines = ["# Claim families: methods, origins and limits", "",
             "This reviewed catalog supplies the scientific context for each entry in the [claim ledger](claims.md). It is a source investigation, not independent human review.", ""]
    for f in registry["families"]:
        lines += [f"## {f['id']}", "", f"### {f['title']}", "",
                  f"Evidence type: `{f['evidence_kind']}`.", "",
                  "**Question:** " + f["question"], "",
                  "**Interpretation:** " + f["interpretation"], "",
                  "**Limitations:** " + f["limitations"], "",
                  "**Reproduction boundary:** " + f["reproduction"], "",
                  "| Role | Repository evidence |", "|---|---|"]
        for key, role in (("artifacts", "Retained result"), ("inputs", "Input/source reference"), ("writers", "Writer/calculation")):
            lines += [f"| {role} | [{p}](../../{p}) |" for p in f[key]]
        lines.append("")
    return "\n".join(lines)


def markdown_links(text: str) -> list[str]:
    """Read ordinary Markdown links outside fenced examples."""
    text = re.sub(r"(?ms)^```[^\n]*\n.*?^```\s*$", "", text)
    return re.findall(r"!?\[[^\]]*\]\(([^\s)]+)(?:\s+\"[^\"]*\")?\)", text)


def check_links(root: Path, pages: list[Path]) -> list[str]:
    """Validate repository-relative file and local fragment links."""
    errors = []
    for page in pages:
        for raw in markdown_links(page.read_text(encoding="utf-8")):
            if re.match(r"[a-zA-Z][a-zA-Z0-9+.-]*:", raw):
                continue
            target, _, fragment = unquote(raw).partition("#")
            path = (page.parent / target).resolve() if target else page.resolve()
            if not path.is_relative_to(root.resolve()) or not path.exists():
                errors.append(f"{page.relative_to(root)}: missing or outside path {raw}")
                continue
            if fragment and path.is_file() and path.suffix == ".md":
                source = path.read_text(encoding="utf-8")
                headings = re.findall(r"(?m)^#{1,6}\s+(.+?)\s*$", source)
                slugs = set()
                occurrences: dict[str, int] = {}
                for h in headings:
                    slug = re.sub(r"[^\w\- ]", "", h.lower()).replace(" ", "-")
                    n = occurrences.get(slug, 0); occurrences[slug] = n + 1
                    slugs.add(slug if n == 0 else f"{slug}-{n}")
                slugs.update(re.findall(r'<[^>]+\bid=[\"\']([^\"\']+)', source))
                if fragment not in slugs:
                    errors.append(f"{page.relative_to(root)}: missing fragment {raw}")
    return errors


def public_api(root: Path, names: list[str]) -> str:
    """Render selected source symbols without importing the research runtime."""
    out = ["# Library interface reference", "",
           "The CLI and versioned records are the preferred external interfaces. These selected Python entry points are documented for maintainers; this catalog is not a promise that every internal symbol is stable.", ""]
    for name in names:
        path = repo_file(root, name)
        tree = ast.parse(path.read_text(encoding="utf-8"))
        out += [f"## {name}", "", (ast.get_docstring(tree) or "").split("\n\n")[0], ""]
        for node in tree.body:
            if not isinstance(node, (ast.FunctionDef, ast.ClassDef)) or node.name.startswith("_"):
                continue
            out += [f"### {node.name}", "", f"[Source](../../{name}#L{node.lineno})", ""]
            if isinstance(node, ast.FunctionDef):
                signature = ast.unparse(node.args)
                out += ["```python", f"{node.name}({signature})", "```", ""]
            text = ast.get_docstring(node) or "No additional public contract; inspect the linked source."
            out += [text, ""]
    return "\n".join(out)


def cli_reference() -> str:
    """Capture argparse help recursively, without executing an evaluation."""
    from ..cli import build_parser

    out = ["# Command-line reference", "",
           "Generated from the installed CLI parser, not a separately maintained flag list. Examples are explained in [the workflow guide](workflows.md). A refusal is a scientific outcome; inspect the documented exit behavior of the specific command.", ""]
    def walk(parser: argparse.ArgumentParser, title: str) -> None:
        out.extend([f"## {title}", "", "```text", parser.format_help().rstrip(), "```", ""])
        for action in parser._actions:
            if isinstance(action, argparse._SubParsersAction):
                for key, child in action.choices.items():
                    walk(child, title + " " + key)
    walk(build_parser(), "warrant")
    return "\n".join(out)


def write_audit(root: Path, destination: Path) -> dict:
    """Write new audit evidence only from clean source; never replace a run."""
    from datetime import datetime, timezone

    status = subprocess.check_output(["git", "status", "--porcelain"], cwd=root, text=True)
    if status.strip():
        raise ValueError("audit artifacts require clean committed source")
    if destination.exists():
        raise ValueError("audit destination must be new")
    report = collect_audit(root)
    if not report["ok"]:
        raise ValueError("claim or point audit failed; refusing a passing receipt")
    report["provenance"] = {
        "git_commit": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=root, text=True).strip(),
        "dirty": False, "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "method": "artifact field check plus independent frozen-score rank/count oracle",
    }
    destination.mkdir(parents=True)
    (destination / "audit.json").write_bytes((json.dumps(report, indent=2, ensure_ascii=False) + "\n").encode())
    return report

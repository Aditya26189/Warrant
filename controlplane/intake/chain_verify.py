"""Verify the records of a recheck chain as a set. ``DECISIONS.md`` 194.

A chain's guarantee holds for the chain *as kept* (193), and nothing on one
machine stops a user forking it, restarting it or editing the head sidecar
(194). What can be done is to make those visible to whoever holds the records.
This reads every record handed to it and reports what the set shows:

* **fork** -- two records continuing the same record. Two branches off one
  prefix are two tests, so a declared ``--fork`` is reported too, as declared;
* **restart** -- two chains started for the same warrant;
* **missing link** -- a record continuing one that is not in the set;
* **sequence** -- a link numbered other than its predecessor plus one;
* **digest** -- a chain state whose digest does not reproduce, or whose
  serialized derived fields disagree with the state they rebuild from;
* **malformed** -- a chain block with a value of the wrong type or outside its
  domain, such as an ``alpha`` of 0; not evidence of an edit, and not arithmetic
  the verifier will attempt;
* **extension** -- a link that does not extend its predecessor: a changed
  budget, alpha, grid or horizon, fewer units consumed, or a consumed-unit list
  that does not begin with its predecessor's;
* **continued after end** -- a link after a record that revoked or ended,
  including a record REVOKED on its score distribution while the chain itself
  was still live (194, defect 1);
* **mixed warrants** -- records from more than one warrant, each group still
  verified;
* **duplicate** -- one record under several paths, verified once. Reported so
  ``--require-clean`` sees it, not because anything forked.

A duplicated link number always surfaces as one of these -- a fork, a restart
or a link numbered wrongly for its predecessor -- and a gap as a missing link,
so neither needs a check of its own. Records written before 194 carry no
``head_check``; they are read as *unrecorded*, not flagged.

**Exit codes follow the CLI's convention** (194): findings are a result, so the
command exits 0 with them printed and recorded; ``--require-clean`` exits 1
when anything is flagged; unreadable input exits 2.

**What it cannot check.** The statistics themselves: recomputing them needs the
labelled files, which records deliberately do not hold. A set a user has pruned
to one clean branch verifies clean -- this reports what the records show, and a
missing record is visible only if a kept record points at it.
"""

from __future__ import annotations

import dataclasses
import json
from pathlib import Path
from typing import Any, Mapping, Sequence

from .chain import ChainError, ChainState, MalformedChainError, record_sha256

__all__ = [
    "ChainFinding",
    "ChainVerification",
    "RecordError",
    "load_records",
    "render_chain_verification",
    "verify_chain_records",
]


class RecordError(ValueError):
    """A file is not a readable chained recheck record. The CLI exits 2."""


@dataclasses.dataclass(frozen=True)
class ChainFinding:
    kind: str
    records: tuple[str, ...]
    detail: str

    def to_payload(self) -> dict[str, Any]:
        return {"kind": self.kind, "records": list(self.records), "detail": self.detail}


@dataclasses.dataclass(frozen=True)
class ChainVerification:
    records: tuple[str, ...]
    warrants: tuple[str, ...]
    findings: tuple[ChainFinding, ...]

    @property
    def clean(self) -> bool:
        return not self.findings

    def to_payload(self) -> dict[str, Any]:
        return {
            "kind": "chain_verification",
            "clean": self.clean,
            "records": list(self.records),
            "warrant_sha256": list(self.warrants),
            "findings": [finding.to_payload() for finding in self.findings],
            "cannot_check": (
                "The statistics are not recomputed: that needs the labelled files, "
                "which records do not hold. A set pruned to one clean branch verifies "
                "clean; a missing record is visible only if a kept record points at it. "
                "The digests are checksums, not signatures: a set rewritten with "
                "recomputed digests verifies clean, and a record without head_check "
                "cannot be told apart from one written before DECISIONS 194."
            ),
        }


def load_records(paths: Sequence[str | Path]) -> dict[str, dict[str, Any]]:
    """Read each file, refusing one that is not a chained recheck record."""
    records: dict[str, dict[str, Any]] = {}
    for raw in paths:
        path = Path(raw)
        try:
            record = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, ValueError) as exc:
            raise RecordError(f"{path}: not a readable JSON record ({exc})") from exc
        if not isinstance(record, dict) or not isinstance(record.get("chain"), dict):
            raise RecordError(f"{path}: not a chained recheck record (no chain block)")
        records[str(path)] = record
    if not records:
        raise RecordError("no records given")
    return records


def verify_chain_records(records: Mapping[str, Mapping[str, Any]]) -> ChainVerification:
    """Every check in the module docstring, over the whole set."""
    findings: list[ChainFinding] = []

    # The same record under several paths -- a backup copy beside the original --
    # is one record. Verified once, under its first path; the extra paths are
    # reported as duplicates, or two copies would read as a fork (found in review).
    paths_by_digest: dict[str, list[str]] = {}
    for name in sorted(records):
        try:
            digest = record_sha256(records[name], "record")
        except MalformedChainError as exc:
            # Cannot be digested, so cannot be matched to a parent or a child. It
            # is reported and left out of every check that follows (194, defect 3).
            findings.append(ChainFinding(
                "malformed", (name,),
                f"{exc}. The record was not checked further. Any link that continued "
                "it also reports a missing link.",
            ))
            continue
        paths_by_digest.setdefault(digest, []).append(name)
    by_digest = {digest: paths[0] for digest, paths in paths_by_digest.items()}
    for digest, paths in sorted(paths_by_digest.items(), key=lambda item: item[1][0]):
        if len(paths) > 1:
            findings.append(ChainFinding(
                "duplicate", tuple(paths),
                f"the same record under {len(paths)} paths; verified once, as {Path(paths[0]).name}",
            ))

    states: dict[str, ChainState] = {}
    for digest, name in sorted(by_digest.items(), key=lambda item: item[1]):
        try:
            states[name] = ChainState.from_payload(dict(records[name]["chain"]))
        except MalformedChainError as exc:
            findings.append(ChainFinding(
                "malformed", (name,),
                f"{exc}. The record was not checked further. Any link that continued "
                "it also reports a missing link.",
            ))
        except ChainError as exc:
            # An edit to a record changes its own digest too, so a link that
            # continued it points at a digest nothing in the set now has, and
            # reports a missing link. One cause, two findings; say so here,
            # because the continuing link cannot be named from the edited record.
            findings.append(ChainFinding(
                "digest", (name,),
                f"{exc}. Any link that continued this record also reports a missing link.",
            ))
    warrants = sorted({state.warrant_sha256 for state in states.values()})
    if len(warrants) > 1:
        findings.append(ChainFinding(
            "mixed_warrants", tuple(sorted(states)),
            f"{len(warrants)} warrants in one set; each group is verified on its own",
        ))

    for warrant in warrants:
        group = {name: state for name, state in states.items() if state.warrant_sha256 == warrant}

        starts = sorted(name for name, state in group.items() if state.previous_record_sha256 is None)
        if len(starts) > 1:
            declared = [n for n in starts if group[n].head_check == "forked"]
            findings.append(ChainFinding(
                "restart", tuple(starts),
                f"{len(starts)} chains were started for one warrant"
                + (f" ({len(declared)} declared with --fork)" if declared else "")
                + "; a fresh chain after an unfavourable record spends the guarantee",
            ))

        children: dict[str, list[str]] = {}
        for name, state in group.items():
            if state.previous_record_sha256 is not None:
                children.setdefault(state.previous_record_sha256, []).append(name)
        for parent_digest, names in sorted(children.items()):
            if len(names) > 1:
                declared = [n for n in names if group[n].head_check == "forked"]
                findings.append(ChainFinding(
                    "fork", tuple(sorted(names)),
                    f"{len(names)} records continue one record"
                    + (f"; {len(declared)} declared with --fork" if declared else "; none declared")
                    + ". Two branches off one prefix are two tests",
                ))

        for name, state in sorted(group.items()):
            parent_digest = state.previous_record_sha256
            if parent_digest is None:
                if state.sequence != 1:
                    findings.append(ChainFinding(
                        "sequence", (name,), f"a chain start numbered {state.sequence}, not 1"))
                if len(state.consumed_unit_digests) != state.units_consumed:
                    findings.append(ChainFinding(
                        "extension", (name,),
                        f"records {state.units_consumed} units consumed and lists "
                        f"{len(state.consumed_unit_digests)}"))
                continue
            parent_name = by_digest.get(parent_digest)
            if parent_name is None or parent_name not in group:
                findings.append(ChainFinding(
                    "missing_link", (name,),
                    f"continues a record not in this set (sha256 {parent_digest[:16]}...)"))
                continue
            parent = group[parent_name]
            pair = (parent_name, name)
            if state.sequence != parent.sequence + 1:
                findings.append(ChainFinding(
                    "sequence", pair, f"link {state.sequence} follows link {parent.sequence}"))
            parent_status = records[parent_name].get("status")
            if parent.revoked_at_unit is not None or parent.ended or parent_status == "REVOKED":
                if parent.revoked_at_unit is not None:
                    what = "revoked the chain"
                elif parent_status == "REVOKED":
                    what = "REVOKED the warrant on its score distribution"
                else:
                    what = "ended the chain"
                findings.append(ChainFinding(
                    "continued_after_end", pair,
                    f"the previous record {what}, and a link followed it"))
            fixed = ("p0", "alpha", "lam_lo", "lam_hi", "n_lam", "horizon_units")
            changed = [f for f in fixed if getattr(parent, f) != getattr(state, f)]
            prefix = tuple(state.consumed_unit_digests[: len(parent.consumed_unit_digests)])
            if (changed or state.units_consumed < parent.units_consumed
                    or prefix != parent.consumed_unit_digests
                    or len(state.consumed_unit_digests) != state.units_consumed):
                findings.append(ChainFinding(
                    "extension", pair,
                    "does not extend its previous record"
                    + (f" (changed: {', '.join(changed)})" if changed else "")))

    return ChainVerification(
        records=tuple(sorted(records)), warrants=tuple(warrants), findings=tuple(findings))


def render_chain_verification(verification: ChainVerification) -> str:
    """The verification for a terminal, ASCII only."""
    rule = "-" * 66
    lines = [rule, "  CHAIN VERIFICATION", rule, "",
             f"  {len(verification.records)} record(s), {len(verification.warrants)} warrant(s)", ""]
    if verification.clean:
        lines += ["  CLEAN -- nothing in these records shows a fork, a restart, a missing",
                  "  link, an edited state or a link that does not extend its predecessor."]
    else:
        lines.append(f"  {len(verification.findings)} FINDING(S)")
        for finding in verification.findings:
            names = ", ".join(Path(r).name for r in finding.records)
            lines += ["", f"  [{finding.kind}] {names}", f"      {finding.detail}"]
    lines += ["", "  What this cannot check: the statistics themselves, which need the",
              "  labelled files; a record nobody kept; and a set rewritten with",
              "  recomputed digests, which verifies clean -- the digests are",
              "  checksums, not signatures. A set pruned to one clean branch",
              "  verifies clean.", rule, ""]
    return "\n".join(lines)

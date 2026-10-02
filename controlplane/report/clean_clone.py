"""Clone this repository into a temporary directory and run the gates in it.

Block E, E.8. The Phase 10 gate, moved earlier because it is the check most
likely to fail in a way that takes hours to fix.

**What it actually catches.** Everything on a developer's machine works partly
by accident: an untracked file that was never committed, a cache the pipeline
quietly needs, a path that resolves only because of where the interpreter was
started. A fresh clone has *only what is tracked*, and running the gates inside
one is the only way to find out whether that is enough.

Lives under ``report`` rather than in the script because it writes an artifact
and because ``CLAUDE.md`` rules logic out of scripts. It is repo-level QA
rather than a measurement, and the artifact says so.

**On the verify tiers.** ``verify`` runs three checks and they do not stand or
fall together, so each gets its own row: a green exit code says *nothing
drifted*, not *everything was checked*. On a fresh clone the first two run --
the claim table against the artifacts, and every metrics block recomputed from
the frozen scores in ``results/scores/`` -- and the third skips, because the
extraction caches are ~100 MB and gitignored.

A skipped tier is recorded as skipped, never as a pass. So is a tier whose
outcome line is missing from the captured output: unknown is not success. A
gate reporting a check it could not run as green would be this project's own
failure mode, one level up.
"""

from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Optional

__all__ = [
    "GateResult",
    "StepResult",
    "run_clean_clone_gate",
    "render",
    "write_artifact",
    "write_outcome_artifact",
]


@dataclass
class StepResult:
    """One command run inside the clone."""

    name: str
    command: list[str]
    returncode: Optional[int]
    duration_seconds: float
    ok: bool
    skipped: bool = False
    detail: str = ""
    tail: str = ""


@dataclass
class GateResult:
    """The whole gate."""

    ok: bool
    commit: str
    clone_path: str
    tracked_files: int
    steps: list[StepResult] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "ok": self.ok,
            "commit": self.commit,
            "clone_path": self.clone_path,
            "tracked_files": self.tracked_files,
            "steps": [asdict(s) for s in self.steps],
            "notes": self.notes,
        }


def _run(
    name: str,
    command: list[str],
    cwd: Path,
    timeout: int,
    env: Optional[dict] = None,
) -> StepResult:
    started = time.time()
    try:
        proc = subprocess.run(
            command,
            cwd=str(cwd),
            capture_output=True,
            text=True,
            timeout=timeout,
            env=env or {**os.environ, "PYTHONIOENCODING": "utf-8"},
        )
    except subprocess.TimeoutExpired as exc:
        # A long suite can expire after substantial progress. Keep its last
        # captured lines so the failure artifact identifies where it stopped.
        def captured(value: bytes | str | None) -> str:
            if isinstance(value, bytes):
                return value.decode("utf-8", errors="replace")
            return value or ""

        combined = captured(exc.stdout) + captured(exc.stderr)
        return StepResult(
            name=name,
            command=command,
            returncode=None,
            duration_seconds=time.time() - started,
            ok=False,
            detail=f"timed out after {timeout}s",
            tail="\n".join(combined.strip().splitlines()[-25:]),
        )
    combined = (proc.stdout or "") + (proc.stderr or "")
    return StepResult(
        name=name,
        command=command,
        returncode=proc.returncode,
        duration_seconds=round(time.time() - started, 2),
        ok=proc.returncode == 0,
        detail="" if proc.returncode == 0 else f"exited {proc.returncode}",
        tail="\n".join(combined.strip().splitlines()[-25:]),
    )


def _run_suite_after_preflight(python: str, cwd: Path) -> list[StepResult]:
    """Fail early on cheap clone blockers without reporting the full suite as run.

    Decision 224: both assertions failed, or would deterministically fail, in
    Phase 25's tracked-only clone. Run them before the expensive suite and keep
    an explicit unsuccessful SKIP row if they refuse.
    """
    preflight = _run(
        "make test preflight",
        [
            python, "-m", "pytest",
            "tests/test_claims.py::test_every_stated_test_count_is_the_real_one",
            "tests/test_clean_clone.py::test_the_committed_gate_artifact_is_readable_and_passed",
            "-q",
        ],
        cwd=cwd,
        timeout=900,
    )
    full_command = [python, "-m", "pytest", "tests/", "-q"]
    if not preflight.ok:
        return [
            preflight,
            StepResult(
                name="make test",
                command=full_command,
                returncode=None,
                duration_seconds=0.0,
                ok=False,
                skipped=True,
                detail="not run because test preflight failed",
            ),
        ]
    # Decision 228: the full tracked-file suite exceeded the former one-hour
    # deadline twice. Keep every test and a finite deadline, but allow two hours.
    return [preflight, _run("make test", full_command, cwd=cwd, timeout=7200)]


#: Human-readable label per tier key, for the report. The keys themselves come
#: from verify's machine-readable contract, not from this table.
_TIER_LABELS = {
    "claim_table": "claim table vs artifacts",
    "frozen_scores": "metrics recomputed from frozen scores",
    "activations": "scores re-derived from activations",
}

#: The contract verify emits, one line per tier, last in its output:
#:     TIER|1|claim_table|OK|31/31
_TIER_LINE = re.compile(
    r"^TIER\|(?P<number>\d+)\|(?P<key>[a-z_]+)\|(?P<outcome>OK|DRIFT|SKIPPED)\|"
    r"(?P<passed>\d+)/(?P<total>\d+)\s*$"
)


def _verify_tiers(tail: str) -> list[StepResult]:
    """One row per verify tier, parsed from its machine-readable summary.

    **Why a contract and not prose.** The first version grepped the human output
    for phrases like "claims reproduce". It worked until verify grew a third
    tier, at which point the claim-table line scrolled off the captured 25-line
    tail and the gate reported a check that had passed as not having run. The
    conservative direction, and still wrong -- in the component whose whole job
    is saying accurately what happened.

    Prose moves whenever the wording improves. ``TIER|n|key|outcome|passed/total``
    does not, and verify prints it last so truncation cannot reach it.

    An explicitly skipped activation tier is tolerated because the cache is
    absent from a fresh clone. Missing, duplicate, unknown or contradictory
    tier lines are protocol failures; claim and frozen-score tiers may not be
    skipped by the default verify command. No tier lines at all is a failure,
    not an empty pass -- that means verify did not emit its contract.
    """
    seen: dict[str, StepResult] = {}
    protocol_errors: list[str] = []
    expected_numbers = {
        key: str(number) for number, key in enumerate(_TIER_LABELS, start=1)
    }
    for line in tail.splitlines():
        stripped = line.strip()
        if not stripped.startswith("TIER|"):
            continue
        match = _TIER_LINE.match(stripped)
        if not match:
            protocol_errors.append(f"malformed tier line: {stripped}")
            continue
        key = match.group("key")
        if key not in expected_numbers:
            protocol_errors.append(f"unknown tier: {key}")
            continue
        if match.group("number") != expected_numbers[key]:
            protocol_errors.append(f"wrong tier number for {key}")
            continue
        if key in seen:
            protocol_errors.append(f"duplicate tier: {key}")
            continue
        outcome = match.group("outcome")
        passed, total = match.group("passed"), match.group("total")
        passed_count, total_count = int(passed), int(total)
        if (
            passed_count > total_count
            or (outcome == "OK" and (total_count == 0 or passed_count != total_count))
            or (outcome == "SKIPPED" and (passed_count != 0 or total_count != 0))
        ):
            protocol_errors.append(
                f"contradictory tier outcome/count for {key}: "
                f"{outcome}|{passed}/{total}"
            )
            continue
        label = _TIER_LABELS.get(key, key)
        acceptable_skip = key == "activations" and outcome == "SKIPPED"
        seen[key] = StepResult(
            name=f"verify: {label}",
            command=[],
            returncode=None,
            duration_seconds=0.0,
            ok=outcome == "OK" or acceptable_skip,
            skipped=outcome == "SKIPPED",
            detail=(
                f"{passed}/{total} reproduced" if outcome == "OK"
                else "did not run" if acceptable_skip
                else "mandatory tier did not run" if outcome == "SKIPPED"
                else f"DRIFT: only {passed}/{total} reproduced"
            ),
        )

    if not seen:
        return [
            StepResult(
                name="verify: tier summary",
                command=[],
                returncode=None,
                duration_seconds=0.0,
                ok=False,
                skipped=False,
                detail=(
                    "verify emitted no TIER| lines. Either it is an older "
                    "version without the machine-readable summary, or its "
                    "output was lost. Which checks ran is unknown, and unknown "
                    "is not a pass. " + "; ".join(protocol_errors)
                ),
            )
        ]

    rows: list[StepResult] = []
    for key, label in _TIER_LABELS.items():
        if key in seen:
            rows.append(seen[key])
            continue
        rows.append(
            StepResult(
                name=f"verify: {label}",
                command=[],
                returncode=None,
                duration_seconds=0.0,
                ok=False,
                skipped=False,
                detail=(
                    "missing from verify's tier summary; the gate cannot "
                    "establish whether this check ran"
                ),
            )
        )
    if protocol_errors:
        rows.append(StepResult(
            name="verify: tier summary protocol",
            command=[], returncode=None, duration_seconds=0.0,
            ok=False, detail="; ".join(protocol_errors),
        ))
    return rows


def _remove_clone(path: Path, attempts: int = 3) -> str:
    """Delete the clone, and say so when it cannot rather than swallowing it.

    ``shutil.rmtree(ignore_errors=True)`` silently leaves the tree behind when
    Windows still holds a handle on a file -- git's pack files, most often,
    just after a subprocess exits. Two earlier gate runs each left 26 MB in the
    temp directory and reported nothing.

    Retries briefly, then returns what went wrong so the caller can put it in
    the report. A cleanup that reports success without completing is a small
    version of exactly what this gate exists to catch.

    Returns:
        An empty string on success, or a short description of the failure.
    """
    last = ""
    for attempt in range(attempts):
        shutil.rmtree(path, ignore_errors=True)
        if not path.exists():
            return ""
        last = f"still present after attempt {attempt + 1}"
        time.sleep(0.5)
    try:
        shutil.rmtree(path)
    except OSError as exc:
        return f"{type(exc).__name__}: {exc}"
    return "" if not path.exists() else last


def head_step(source_commit: str, clone_commit: str) -> StepResult:
    """Whether the clone is the commit the record will name (``DECISIONS.md`` 200).

    The source's HEAD is read before a separate ``git clone``, so a commit landing
    between the two would have the gate test one commit and name another.
    """
    matches = bool(source_commit) and source_commit == clone_commit
    return StepResult(
        name="clone matches source HEAD",
        command=["git", "rev-parse", "HEAD"],
        returncode=0 if matches else 1,
        duration_seconds=0.0,
        ok=matches,
        detail="" if matches else (
            f"the source's HEAD was {source_commit[:12] or '(unreadable)'} and the clone's is "
            f"{clone_commit[:12] or '(unreadable)'}; the gate would test a commit it does not name"
        ),
    )


def check_record(result: GateResult, before: dict, after: dict) -> Optional[str]:
    """Why the gate's record must not be written, or ``None`` when it may (200).

    ``before`` is the source's provenance taken before cloning, ``after`` at write
    time. The record may name one state only: the commit cloned, clean at clone
    time, and unchanged by the time it is written. Anything else would publish a
    pass, or a failure, for a state nobody tested.
    """
    if before.get("dirty"):
        return (
            "the source tree was dirty when it was cloned, so its uncommitted changes "
            "were not tested and the record would describe a tree that differs from "
            "the clone. Commit or stash, then rerun."
        )
    if before.get("git_commit") != result.commit:
        return (
            f"provenance before cloning names {str(before.get('git_commit'))[:12]} but the "
            f"gate cloned {result.commit[:12]}; the source moved while the gate started."
        )
    if after.get("git_commit") != result.commit or after.get("dirty"):
        return (
            f"the source changed during the run: it was {result.commit[:12]}, clean, when "
            f"cloned, and is {str(after.get('git_commit'))[:12]}"
            f"{', dirty' if after.get('dirty') else ''} now. The outcome above stands for "
            "the commit cloned, but no record is written that a later reader could pair "
            "with the wrong tree. Rerun from an unchanging checkout."
        )
    return None


def run_clean_clone_gate(
    root: Path,
    *,
    keep: bool = False,
    run_tests: bool = True,
    python: Optional[str] = None,
) -> GateResult:
    """Clone ``root``, then run smoke, test and verify inside the clone.

    Args:
        root: The repository to clone. Cloned from the local path, so the clone
            contains exactly what a ``git clone`` of the remote would once this
            branch is pushed: tracked files only, no gitignored caches.
        keep: Leave the clone on disk for inspection.
        run_tests: Run the full suite. Off makes the gate a two-minute check.
        python: Interpreter to use inside the clone. Defaults to this one, so
            the gate tests the *tree* rather than the environment. Point it at
            a venv built from requirements.lock.txt to test both.

    Returns:
        A result whose ``ok`` is False if any step failed. A step that could
        not run is recorded as skipped and does not count as a pass.
    """
    python = python or sys.executable
    commit = subprocess.run(
        ["git", "rev-parse", "HEAD"], cwd=str(root),
        capture_output=True, text=True,
    ).stdout.strip()

    clone = Path(tempfile.mkdtemp(prefix="controlplane-clean-clone-"))
    target = clone / "controlplane"
    result = GateResult(ok=True, commit=commit, clone_path=str(target), tracked_files=0)

    try:
        cloned = _run(
            "git clone",
            ["git", "clone", "--quiet", str(root), str(target)],
            cwd=clone,
            timeout=600,
        )
        result.steps.append(cloned)
        if not cloned.ok:
            result.ok = False
            return result
        clone_commit = subprocess.run(
            ["git", "rev-parse", "HEAD"], cwd=str(target), capture_output=True, text=True,
        ).stdout.strip()
        matched = head_step(commit, clone_commit)
        result.steps.append(matched)
        if not matched.ok:
            result.ok = False
            return result

        listing = subprocess.run(
            ["git", "ls-files"], cwd=str(target), capture_output=True, text=True
        )
        result.tracked_files = len([x for x in listing.stdout.splitlines() if x])
        result.notes.append(
            f"{result.tracked_files} tracked files in the clone; no gitignored "
            "caches, databases or long-context eval sets came with it."
        )

        # The notes ref carries the correction to the withdrawn claim at
        # 67167ed. A judge is told to fetch it; the gate checks it is fetchable.
        notes = _run(
            "fetch notes",
            ["git", "fetch", "origin", "refs/notes/*:refs/notes/*"],
            cwd=target,
            timeout=300,
        )
        result.steps.append(notes)

        result.steps.append(
            _run("make smoke", [python, "scripts/smoke.py"], cwd=target, timeout=600)
        )
        if run_tests:
            result.steps.extend(_run_suite_after_preflight(python, target))
        result.steps.append(
            _run("make verify", [python, "scripts/verify.py"], cwd=target, timeout=1800)
        )

        # verify runs three tiers and they do not stand or fall together. A
        # green exit code says "nothing drifted", not "everything was checked",
        # so each tier is recorded on its own row.
        #
        # The first version of this matched the literal string "SKIPPED"
        # anywhere in verify's output and filed ONE skip row saying the claim
        # table was all that ran. Once the score tier existed that was simply
        # false -- tier 2 reproduced 24 comparisons in the clone and the gate
        # reported it as not having run. Understating what was verified is the
        # safe direction to be wrong in, and it is still wrong, in a gate whose
        # whole job is saying accurately what happened.
        verify = next((s for s in result.steps if s.name == "make verify"), None)
        if verify is not None:
            result.steps.extend(_verify_tiers(verify.tail))
            ran = [s.name for s in result.steps if s.name.startswith("verify:") and not s.skipped]
            skipped = [s.name for s in result.steps if s.name.startswith("verify:") and s.skipped]
            result.notes.append(
                "verify tiers that ran in the clone: "
                + (", ".join(n.split(": ", 1)[1] for n in ran) or "none")
                + ". Skipped: "
                + (", ".join(n.split(": ", 1)[1] for n in skipped) or "none")
                + "."
            )

        result.ok = all(s.ok for s in result.steps)
        return result
    finally:
        if keep:
            result.notes.append(f"clone kept at {target}")
        else:
            leftover = _remove_clone(clone)
            if leftover:
                result.notes.append(
                    f"could not fully remove the clone at {clone}: {leftover}. "
                    "Not a gate failure -- the checks above all ran -- but it "
                    "leaves ~26 MB behind, and earlier runs did so silently."
                )


def render(result: GateResult) -> str:
    lines = [
        "clean-clone gate",
        f"  commit        {result.commit[:12]}",
        f"  tracked files {result.tracked_files}",
        "",
    ]
    for step in result.steps:
        mark = "SKIP" if step.skipped else ("OK" if step.ok else "FAIL")
        lines.append(f"  {mark:5s} {step.name:34s} {step.duration_seconds:7.1f}s")
        if step.detail:
            lines.append(f"        {step.detail}")
    for note in result.notes:
        lines.append(f"  note: {note}")
    lines.append("")
    lines.append("CLEAN CLONE GATE: " + ("PASSED" if result.ok else "FAILED"))
    if not result.ok:
        for step in result.steps:
            if not step.ok:
                lines.append("")
                lines.append(f"--- {step.name} ---")
                lines.append(step.tail)
    return "\n".join(lines)


def write_artifact(
    result: GateResult,
    path: Path,
    provenance: dict,
    *,
    provenance_taken: str = "before cloning",
    exclusive: bool = False,
) -> None:
    """Write the gate's outcome to ``results/`` with the usual provenance block.

    ``provenance_taken`` says which moment the block describes. Since 200 it is
    the clone, so its timestamp is when the tested state was cloned, not when the
    record was written; records from before 200 carry no such field.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {"provenance": provenance, "provenance_taken": provenance_taken, **result.to_dict()}
    content = json.dumps(payload, indent=2, sort_keys=False) + "\n"
    if exclusive:
        with path.open("x", encoding="utf-8") as handle:
            handle.write(content)
    else:
        path.write_text(content, encoding="utf-8")


def write_outcome_artifact(
    result: GateResult,
    requested_path: Path,
    canonical_path: Path,
    provenance: dict,
) -> Path:
    """Preserve the last passing default gate while recording every failed attempt.

    Decision 225: a failed run at the default path cannot replace the passing
    record, which the clean-clone preflight reads on its next run. An explicit
    ``--out`` remains under the caller's control.
    """
    if result.ok or requested_path.resolve() != canonical_path.resolve():
        write_artifact(result, requested_path, provenance)
        return requested_path

    if not result.commit:
        raise ValueError("a failed clone gate must identify its source commit")
    failure_path = (
        canonical_path.parent
        / "clean_clone_failures"
        / f"clean_clone-{result.commit[:12]}-{time.time_ns()}.json"
    )
    write_artifact(result, failure_path, provenance, exclusive=True)
    return failure_path

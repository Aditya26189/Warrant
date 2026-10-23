"""Freeze exact local payment candidates and a small append-only grader repair."""
import argparse
import difflib
import json
from pathlib import Path
import shutil

from experiments.grader_poc.prepare_cases import replace_once
from experiments.grader_poc.run_trial import file_hashes, git_output, write_receipt

APPEND = '''

@pytest.mark.parametrize("phase", ("single", "overlap"))
def test_no_overdraft_callback_for_nonnegative_balance(producer, phase) -> None:
    from boundary_check import run_boundary_check
    run_boundary_check(phase, producer)
'''


def prepare(tb: Path, out: Path) -> dict:
    root = Path(__file__).resolve().parents[3]
    if git_output(root, "status", "--porcelain"):
        raise RuntimeError("Commit source before preparation")
    config = json.loads((root / "experiments/grader_poc/config.json").read_bytes())
    if git_output(tb, "rev-parse", "HEAD") != config["terminal_bench_commit"] or git_output(tb, "status", "--porcelain"):
        raise ValueError("Pinned clean upstream required")
    source = tb / "tasks/payments-pipeline-fix"
    original = file_hashes(source)
    out.mkdir(parents=True, exist_ok=False)
    cases = (("reference-repaired", None, True, 1),
             ("mutant-original", "            if balance <= 0:\n", False, 1),
             ("mutant-repaired", "            if balance <= 0:\n", True, 0),
             ("equivalent-repaired", "            if 0 > balance:\n", True, 1))
    result = {"source_commit": git_output(root, "rev-parse", "HEAD"), "source_dirty": False,
              "original_hashes": original, "outer_timeout_seconds": 900, "cases": {}}
    for name, replacement, repaired, reward in cases:
        target = out / name
        shutil.copytree(source, target)
        if replacement:
            replace_once(target / "solution/worker.py", "            if balance < 0:\n", replacement)
        if repaired:
            test = target / "tests/test_state.py"
            test.write_bytes(test.read_bytes() + APPEND.encode())
            shutil.copyfile(Path(__file__).with_name("boundary_check.py"), target / "tests/boundary_check.py")
        hashes = file_hashes(target)
        changed = sorted(key for key, value in hashes.items() if original.get(key) != value)
        expected = (["solution/worker.py"] if replacement else []) + (["tests/test_state.py", "tests/boundary_check.py"] if repaired else [])
        if set(changed) != set(expected):
            raise ValueError("Unexpected task modification")
        if repaired and not (target / "tests/test_state.py").read_bytes().startswith((source / "tests/test_state.py").read_bytes()):
            raise ValueError("Existing verifier bytes changed")
        lines = []
        for relative in changed:
            previous = (source / relative).read_text().splitlines(keepends=True) if (source / relative).exists() else []
            lines.extend(difflib.unified_diff(previous, (target / relative).read_text().splitlines(keepends=True),
                         fromfile="a/" + relative if previous else "/dev/null", tofile="b/" + relative))
        (out / (name + ".patch")).write_bytes("".join(lines).encode())
        result["cases"][name] = {"hashes": hashes, "changed": changed, "expected_reward": reward}
    write_receipt(out / "manifest.json", result)
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--tb", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps({"cases": list(prepare(args.tb.resolve(), args.out.resolve())["cases"])}))

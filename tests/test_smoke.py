"""Every script actually runs. ``SPEC.md`` §10, ``test_smoke``.

**Why this exists, written after the second time it was needed.** The test suite
imports from ``controlplane/`` and never executes a script, so a script can be broken for
a whole phase without a single test failing. It has now happened twice:

* ``scripts/02_validate.py`` referenced ``RecordKind`` without importing it, for
  three commits. The guard was added to two scripts and the import to one.
* the same shape produced the ``fpr_hard_negatives`` conflation
  (``DECISIONS.md`` 040): a fix applied at one call site when the cause was a
  shared concept.

Scripts are where ``controlplane/`` is wired together, and wiring is exactly what unit
tests do not exercise. These run each one end to end at the smallest size that
still does real work, and assert the artifacts appear.

They are slow by the standards of the rest of the suite — tens of seconds each —
and that is the price of the only test that would have caught either bug.
"""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[1]

pytestmark = pytest.mark.smoke


def run_script(name: str, *args: str, out: Path) -> subprocess.CompletedProcess:
    """Run a script in a subprocess with its own results directory.

    A subprocess rather than an import, because the failure mode is a missing
    import at module scope and importing the module here would mask exactly
    that. The script has to be executed the way a person executes it.
    """
    command = [
        sys.executable,
        str(PROJECT_ROOT / "scripts" / name),
        "--config",
        str(PROJECT_ROOT / "config.yaml"),
        "--out",
        str(out),
        *args,
    ]
    result = subprocess.run(
        command,
        capture_output=True,
        text=True,
        cwd=str(PROJECT_ROOT),
        timeout=900,
        env={**__import__("os").environ, "PYTHONIOENCODING": "utf-8"},
    )
    if result.returncode != 0:
        raise AssertionError(
            f"scripts/{name} exited {result.returncode}\n"
            f"--- stdout ---\n{result.stdout[-3000:]}\n"
            f"--- stderr ---\n{result.stderr[-3000:]}"
        )
    return result


def test_smoke_build_evalsets(tmp_path: Path) -> None:
    """The eval sets build, freeze, register and verify."""
    run_script(
        "01_build_evalsets.py", "--evalsets-out", str(tmp_path / "evalsets"),
        out=tmp_path,
    )
    payload = json.loads((tmp_path / "evalset_validation.json").read_text(encoding="utf-8"))
    assert payload["runs"], "no eval set was scored"
    for run in payload["runs"]:
        assert run["warrant_status"] in ("VALID", "REFUSED")
        assert run["n_items"] > 0


def test_smoke_validate_fixture(tmp_path: Path) -> None:
    """The tier ablation runs and writes a ladder with intervals."""
    run_script("02_validate.py", "--fixture", "--smoke", out=tmp_path)
    ladder = json.loads((tmp_path / "tier_ladder-fixture.json").read_text(encoding="utf-8"))
    assert ladder["rungs"], "no rungs measured"
    for rung in ladder["rungs"].values():
        assert len(rung["controls"]) == 5
        auroc = rung["metrics"].get("auroc")
        if auroc is not None:
            assert auroc["ci_low"] <= auroc["value"] <= auroc["ci_high"]
    assert (tmp_path / "tier_ladder-fixture.png").exists()


def test_smoke_matrix(tmp_path: Path) -> None:
    """The matrix populates, routes, and renders RESULTS.md with its refusal."""
    run_script("03_matrix.py", "--smoke", out=tmp_path)

    matrix = json.loads((tmp_path / "warrant_matrix.json").read_text(encoding="utf-8"))
    summary = matrix["matrix"]["summary"]
    assert sum(summary.values()) == len(matrix["matrix"]["detectors"]) * len(
        matrix["matrix"]["envelopes"]
    ), "not every cell is accounted for"
    assert summary["UNVALIDATED"] > 0, "no cell is unvalidated; the axes are wrong"
    assert matrix["routing"], "no routing decisions recorded"

    results = (tmp_path / "RESULTS.md").read_text(encoding="utf-8")
    assert "# RESULTS" in results
    # The fixture refusal must be present, since a smoke run is all fixtures.
    assert "FIXTURE" in results
    assert "Outstanding measurement" in results


def test_smoke_policy_fixture(tmp_path: Path) -> None:
    """The three operating points issue and the bundles resolve against them.

    On a fixture cache, so this exercises the wiring rather than producing a
    result. What it asserts is the shape the Phase 7 gate needs: one detector,
    one envelope, three distinct thresholds, and every loaded profile stamped
    with the hash of the rules that decided.
    """
    run_script("07_policy.py", "--fixture", out=tmp_path)
    written = sorted(tmp_path.glob("policy-*.json"))
    assert len(written) == 1, f"expected one policy artifact, got {written}"
    payload = json.loads(written[0].read_text(encoding="utf-8"))

    points = payload["operating_points"]
    assert len(points) == 3, "one point per profile"
    warrants = [run["warrant"] for run in points]
    assert len({w["detector_id"] for w in warrants}) == 1, "three points, one detector"
    assert len({w["eval_set_id"] for w in warrants}) == 1, "three points, one envelope"
    thresholds = {w["operating_point"]["threshold"] for w in warrants}
    assert len(thresholds) == 3, "the operating points did not separate"

    comparison = payload["comparison"]
    for row in comparison["rows"]:
        assert row["rule_id"], "a decision nobody can trace to a rule"
        assert row["policy_hash"].startswith("sha256:")
        assert row["fired"] == (row["threshold"] <= comparison["request"]["detector"]["score"])


def test_smoke_paired_fixture(tmp_path: Path) -> None:
    """The paired comparison and the ROC geometry wire up end to end.

    On a fixture, so this exercises the path rather than producing a result.
    What it asserts is the shape ``DECISIONS.md`` 081 and 082 depend on: a
    verified split relationship, a paired set clean of both training splits, an
    MDD reported beside every difference, and a steeper local slope at the
    low-flag-rate operating point than at the high one.
    """
    run_script("08_paired.py", "--fixture", "--bootstrap", "200", out=tmp_path)
    payload = json.loads((tmp_path / "paired_comparison.json").read_text(encoding="utf-8"))

    relationship = payload["split_relationship"]
    assert relationship["usable"], relationship
    assert relationship["is_promotion"], (
        "the fixture must nest, or it exercises the withdrawal path instead of "
        "the comparison"
    )
    assert relationship["leaked_from_old_train"] == []
    assert relationship["leaked_from_new_train"] == []
    assert relationship["n_paired"] >= 200

    for regime in ("pinned_to_baseline_threshold", "each_at_its_own_threshold"):
        rows = payload[regime]
        assert any(r["quantity"] == "auroc" for r in rows)
        assert sum(r["quantity"].startswith("recall@") for r in rows) >= 2, (
            "the warranted quantities are the recalls; reporting only AUROC "
            "hides an operating point that moved"
        )
        for row in rows:
            # Never a difference without the sample size that could detect one.
            assert row["minimum_detectable"] > 0
            assert row["ci_low"] <= row["difference"] <= row["ci_high"]

    points = {p["operating_point_id"]: p for p in payload["roc"]["points"]}
    low, high = points["P-fixture-low"], points["P-fixture-high"]
    assert low["flag_rate"] < high["flag_rate"]
    assert low["slope"] > high["slope"], (
        "the low-flag-rate point must sit on the steeper segment; if it does "
        "not, the C.2 argument does not hold even on generated data"
    )
    assert (tmp_path / "roc_operating_points.png").exists()


@pytest.mark.skipif(
    not __import__("controlplane.detectors.presidio_adapter", fromlist=["x"]).presidio_available(),
    reason="presidio-analyzer not installed",
)
def test_smoke_detectors(tmp_path: Path) -> None:
    """The Presidio adapter runs through the unmodified warrant machinery.

    Stock only, to keep the smoke run short; the reported result measures all
    three (DECISIONS 008). What this asserts is the Phase 8 D.1 gate: stock
    Presidio is REFUSED on hinglish-pii-200 and the measured recall is in the
    refusal reason, not merely in the metrics block a reader has to go find.
    """
    run_script("09_detectors.py", "--configs", "stock", "--skip-reference", out=tmp_path)
    payload = json.loads((tmp_path / "detectors.json").read_text(encoding="utf-8"))

    runs = {
        (r["detector_id"], r["eval_set_id"]): r for r in payload["runs"]
    }
    hinglish = runs[("presidio-stock", "hinglish-pii-200")]
    assert hinglish["warrant_status"] == "REFUSED"
    reason = hinglish["status_reason"] or ""
    assert "canary" in reason, reason
    assert hinglish["metrics"]["recall"]["value"] < 0.5, (
        "stock Presidio scoring above 0.5 on Hinglish PII would be a finding, "
        "not a passing test -- check the adapter before believing it"
    )


def test_kaggle_runner_refuses_before_it_can_spend_quota() -> None:
    """The two guards on the batch runner, exercised rather than assumed.

    A push costs GPU quota and the Kaggle CLI has no cancel verb, so the only
    protection against an accidental run is a refusal that actually fires.
    Nothing here touches the network: both paths must fail before any CLI call.
    """
    import importlib.util

    spec = importlib.util.spec_from_file_location(
        "kaggle_run", PROJECT_ROOT / "scripts" / "kaggle_run.py"
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    with pytest.raises(SystemExit, match="--yes"):
        module.push(accelerator=None, timeout=None, yes=False)

    # The kernel id must resolve from committed metadata, not from a guess.
    kernel_id = module._kernel_id()
    assert "/" in kernel_id and not kernel_id.startswith("KAGGLE_USERNAME")

    metadata = json.loads(module.METADATA.read_text(encoding="utf-8"))
    # Case-sensitive, and the server silently falls back to a P100 when it does
    # not recognise the value -- which is sm_60, below this PyTorch build's
    # floor, so the run dies inside a bitsandbytes kernel two minutes in.
    assert metadata["machine_shape"] == "NvidiaTeslaT4", (
        "machine_shape must be exactly 'NvidiaTeslaT4'; an unrecognised value "
        "is not reported, it is ignored"
    )


def test_transfer_refuses_a_mismatched_cache(tmp_path) -> None:
    """A cache paired with the wrong eval set must not be scored.

    The content hash is the envelope id and the third element of every warrant
    key. Pairing a cache with another eval set would attach real activations to
    someone else's labels and publish a number for a detector-envelope pair
    nobody measured — with nothing in the output saying so.
    """
    import importlib.util

    from controlplane.evalsets.registry import save_evalset
    from controlplane.validation.synthetic import synthetic_cache, synthetic_evalset

    spec = importlib.util.spec_from_file_location(
        "transfer_script", PROJECT_ROOT / "scripts" / "04_transfer.py"
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    evalset = synthetic_evalset(
        eval_set_id="mismatch-check", n_items=40, base_rate=0.3, seed=1
    )
    other = synthetic_evalset(
        eval_set_id="mismatch-check", n_items=40, base_rate=0.7, seed=2
    )
    assert evalset.content_hash != other.content_hash

    registry = tmp_path / "evalsets"
    registry.mkdir()
    save_evalset(evalset, registry)
    cache = synthetic_cache(other, seed=2, window=8, stride=4)
    cache_path = cache.save(tmp_path / "cache.npz")

    monkey = module.PROJECT_ROOT
    try:
        module.PROJECT_ROOT = tmp_path
        with pytest.raises(SystemExit, match="mismatch"):
            module._load("mismatch-check", str(cache_path))
    finally:
        module.PROJECT_ROOT = monkey


def test_canary_is_all_positive_and_clears_its_own_threshold(tmp_path) -> None:
    """A canary must be catchable, and must be drawn only from train.

    ``canary_control`` requires recall == 1.0, so a canary holding an item the
    probe does not catch refuses every warrant forever, for a reason that has
    nothing to do with the run being validated — which is the failure the
    canary exists to end, reintroduced by the fix for it.

    Drawing from validation or test would be selection on the splits those
    exist to protect, and every downstream number would inherit it.
    """
    import importlib.util

    from controlplane.evalsets.registry import load_evalset, save_evalset
    from controlplane.validation.evalsets import TRAIN
    from controlplane.validation.synthetic import synthetic_cache, synthetic_evalset

    spec = importlib.util.spec_from_file_location(
        "canary_script", PROJECT_ROOT / "scripts" / "05_canary.py"
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    evalset = synthetic_evalset(
        eval_set_id="canary-src", n_items=400, base_rate=0.4, seed=3,
        items_per_question=2, declare_splits=True,
    )
    registry = tmp_path / "evalsets"
    registry.mkdir()
    save_evalset(evalset, registry)
    cache = synthetic_cache(evalset, seed=3, window=8, stride=4)
    cache_path = cache.save(tmp_path / "cache.npz")

    # The fixture's variants are independent noise, so four top-5% bands barely
    # intersect and no item clears them all. On real activations the variants
    # are pooled from the SAME hidden states and correlate heavily -- the frozen
    # canary below clears all three with margin. So the fixture exercises the
    # refusal, which is correct behaviour: a canary no eligible item can satisfy
    # must not be silently built at a smaller size or a lower bar.
    original = module.PROJECT_ROOT
    try:
        module.PROJECT_ROOT = tmp_path
        with pytest.raises(SystemExit, match="clear every binding"):
            module.main([
                "--config", str(PROJECT_ROOT / "config.yaml"),
                "--cache", str(cache_path),
                "--eval-set", "canary-src",
                "--n-items", "10",
                "--canary-id", "canary-under-test",
                "--evalsets-out", str(registry),
                "--out", str(tmp_path),
            ])
    finally:
        module.PROJECT_ROOT = original
    assert not (registry / "canary-under-test.json").exists(), (
        "a canary was frozen despite no item clearing every binding variant"
    )

    # And the frozen canary, which is the one every measured warrant depends on.
    frozen_path = PROJECT_ROOT / "evalsets" / "canary-20-triviaqa.json"
    if not frozen_path.exists():
        pytest.skip("no frozen canary in this checkout")
    frozen = load_evalset(frozen_path)
    assert all(item.label == 1 for item in frozen.items), (
        "a canary item labelled correct is not a known positive"
    )
    assert {item.split for item in frozen.items} == {TRAIN}, (
        "canary drew from outside train; that is selection on a protected split"
    )
    binding = frozen.construction.get("variants_required_to_catch")
    assert binding and len(binding) > 1, (
        "the canary records no binding variants, or binds only one. Built on a "
        "single aggregation it caught 20/20 there and 15/20 on another, "
        "refusing two of three ladder rungs on a control unrelated to them."
    )


def test_reconciliation_branches_are_fixed_constants() -> None:
    """The pre-registered decision rule must not be adjustable by a later run.

    A rule written down and then applied by hand is a rule with a thumb
    available to it, and this is the case that most invites one: a public
    handover asserts 0.1416 and Round 2 measured 0.0794. So the branch bounds
    are module constants rather than arguments — a run cannot widen its own
    acceptance region — and the classifier is exercised at its boundaries here
    rather than trusted.
    """
    import importlib.util

    spec = importlib.util.spec_from_file_location(
        "reconcile_script", PROJECT_ROOT / "scripts" / "06_reconcile.py"
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    # The bounds are Round 1's published CI. If these ever change, the
    # pre-registration changed, and that needs an entry rather than an edit.
    assert module.ROUND1_CI == (0.8216804377990431, 0.8878182998424411)
    assert module.DECLARED_VARIANT == "T1-last_token", (
        "the Beat 4 aggregation was declared in DECISIONS 065 before the "
        "numbers existed; changing it here is selection on the test set at the "
        "level of detector architecture"
    )

    # No argparse flag may reach the bounds or the declared variant.
    argv = module.parse_args(["--cache", "x.npz"])
    for forbidden in ("round1_ci", "declared_variant", "pooled_auroc", "tolerance"):
        assert not hasattr(argv, forbidden), (
            "%s is settable from the command line; the acceptance region must "
            "not be adjustable by the run being judged" % forbidden
        )

    assert module.classify(0.8551)[0] == "A"
    assert module.classify(module.ROUND1_CI[0])[0] == "A"
    assert module.classify(module.ROUND1_CI[1])[0] == "A"
    assert module.classify(0.7854)[0] == "B"
    assert module.classify(0.7700)[0] == "B"
    # Deliberate gap between the pooled band and Round 1's interval: neither
    # branch, which is what C exists for.
    assert module.classify(0.8150)[0] == "C"
    assert module.classify(0.9500)[0] == "C"


def test_results_is_measured_only() -> None:
    """``results/`` is the deliverable and holds no fixture artifacts.

    Two results directories — one measured, one fixture — is two answers to the
    same question with nothing declaring which is authoritative. That is the
    exact failure this product argues against, reproduced in the filesystem.

    The ``data_source`` guard cannot help here: it refuses fixture *numbers* at
    the field level, and this ambiguity is at the directory level. Fixtures are
    regenerable from a seeded generator and live under ``results/fixtures/``,
    where nothing downstream reads them.
    """
    root = PROJECT_ROOT / "results"
    if not root.exists():
        pytest.skip("no results directory in this checkout")
    stray = sorted(
        path.name for path in root.iterdir()
        if path.is_file() and "fixture" in path.name.lower()
    )
    assert not stray, (
        "fixture artifacts at the top level of results/: %s. They belong in "
        "results/fixtures/; results/ is the deliverable." % stray
    )
    assert not (root / "measured").exists(), (
        "results/measured/ exists again. There is one results directory and it "
        "is measured; a second one is a fork with no declared authority."
    )


def test_universal_refusal_is_treated_as_a_pipeline_bug() -> None:
    """A matrix where nothing is VALID is a bug signature, not a finding.

    Four cells read REFUSED for reasons unrelated to any detector in one
    session: a stale guard, a naming mismatch rendering REFUSED as UNVALIDATED,
    transfer warrants never reaching the ledger, and a missing canary refusing
    everything. All four produce conservative-looking output that reads as the
    system working, which is why none was noticed by looking at it.

    So: on an envelope where a detector is known-strong, at least one cell must
    reach VALID. Universal refusal across a populated matrix means the pipeline
    broke, not that every detector is bad.
    """
    matrix_path = PROJECT_ROOT / "results" / "warrant_matrix.json"
    if not matrix_path.exists():
        pytest.skip("no warrant matrix in this checkout")
    payload = json.loads(matrix_path.read_text(encoding="utf-8"))
    summary = payload["matrix"]["summary"]

    populated = summary.get("VALID", 0) + summary.get("REFUSED", 0)
    if not populated:
        pytest.skip("matrix has no populated cells")

    assert summary.get("VALID", 0) > 0, (
        "every one of the %d populated cells is REFUSED. That is a pipeline-bug "
        "signature -- an absent canary, a mismatched detector id, or a stale "
        "guard refuses everything and looks conservative while doing it. It has "
        "happened twice." % populated
    )

    # And the measured envelopes specifically, not just the fixture ones: the
    # naming mismatch left every measured cell reading UNVALIDATED while the
    # fixture cells stayed VALID, so a matrix-wide check alone would have passed
    # straight through it.
    measured_envelopes = {"triviaqa-600"}
    seen = {
        status
        for row in payload["matrix"]["rows"]
        for envelope, cell in row["cells"].items()
        if envelope in measured_envelopes
        for status in [cell["status"]]
    }
    if seen <= {"UNVALIDATED"}:
        raise AssertionError(
            "no measured envelope has a single populated cell. Either the "
            "extraction never ran or its warrants are not reaching the matrix; "
            "both look identical here, which is the point of checking."
        )
    """The pre-flight names the unsupported card instead of dying in CUDA."""
    notebook = json.loads(
        (PROJECT_ROOT / "notebooks" / "run_on_kaggle.ipynb").read_text(encoding="utf-8")
    )
    source = "\n".join(
        "".join(cell["source"])
        for cell in notebook["cells"]
        if cell["cell_type"] == "code"
    )
    assert "get_device_capability" in source, "no GPU capability check in the notebook"
    assert "(7, 0)" in source, "the sm_70 floor is not asserted"


def test_every_script_has_a_smoke_test() -> None:
    """A new script without a smoke test is the gap this file exists to close.

    Excludes the notebook builder, which is covered by
    ``test_notebook_is_generated_from_its_script``.
    """
    scripts = {
        path.name
        for path in (PROJECT_ROOT / "scripts").glob("*.py")
        if not path.name.startswith("_")
    }
    covered = {
        "01_build_evalsets.py",
        "02_validate.py",
        "03_matrix.py",
        # test_kaggle_runner_refuses_before_it_can_spend_quota
        "kaggle_run.py",
        # test_transfer_refuses_a_mismatched_cache
        "04_transfer.py",
        # test_canary_is_all_positive_and_clears_its_own_threshold
        "05_canary.py",
        # test_reconciliation_branches_are_fixed_constants
        "06_reconcile.py",
        # test_smoke_policy_fixture
        "07_policy.py",
        # test_smoke_paired_fixture
        "08_paired.py",
        # test_smoke_detectors
        "09_detectors.py",
        # test_smoke_feasibility
        "11_feasibility.py",
        # test_smoke_pilot_freeze
        "12_pilot_freeze.py",
        # test_smoke_pilot_null_band
        "14_pilot_null_band.py",
        # test_smoke_pilot_seed_stability
        "15_pilot_seed_stability.py",
        # test_smoke_presidio_coverage
        "17_presidio_coverage.py",
        # test_smoke_fpr_sweep
        "19_fpr_sweep.py",
        # test_smoke_calibration_power
        "21_calibration_power.py",
        # test_smoke_on_traffic
        "25_on_traffic.py",
        # test_smoke_scorefree
        "26_scorefree.py",
        # test_smoke_gate
        "27_gate.py",
        # test_smoke_recheck_schedules
        "29_recheck_schedules.py",
        # test_smoke_frontier_selection
        "30_frontier_selection.py",
        # tests/test_test_inventory.py runs it on a throwaway repository: a
        # smoke run here would rewrite this repository's README and Makefile.
        "refresh_test_inventory.py",
        # tests/test_intake.py::test_the_examples_are_reproducible_from_their_generator
        # runs it and asserts the committed examples come back byte-identical,
        # which is a stronger check than a smoke test: the examples are shipped
        # evidence and a drifted generator would silently restate them.
        "22_make_examples.py",
        # test_smoke_build_lock
        "build_lock.py",
        # test_smoke_the_smoke_check_itself
        "smoke.py",
        # test_smoke_verify_claims_only, test_verify_exits_non_zero_on_drift
        "verify.py",
    }
    exempt = {
        # Needs a GPU; its wiring is checked by the notebook's own self-check
        # and by tests/test_extraction.py for everything that runs on CPU.
        "00_extract.py",
        "build_notebooks.py",
        # Needs a GPU: it generates 24 answers and extracts activations.
        # The one piece of it that is a DECISION rather than a measurement --
        # which of the three branches in DECISIONS 101 a result lands in --
        # was moved into controlplane/evalsets/banking.py precisely so it
        # could be tested here without one. See test_banking_pilot.py.
        "13_pilot_run.py",
        # Needs the network: it measures evidence from ai4privacy at a pinned
        # revision. What it produces -- results/causal_claims.json -- is checked
        # offline by tests/test_causal_claims.py on every run, which is the
        # point of freezing the evidence rather than measuring it in the test.
        "24_causal_claims.py",
        # Needs the network: it fetches third-party models and datasets at
        # pinned revisions rather than redistributing them, and the suite must
        # run offline. Its pure parts -- the registry's provenance, the label
        # wiring, and the single-class and misaligned-score guards -- are
        # unit-tested in tests/test_external.py without touching the network.
        "23_certify_external.py",
        # Needs the extraction cache, which is gitignored and absent from a
        # clean clone, for the same reason 10_freeze_scores.py is exempt. Its
        # one piece of real logic -- certifying on one split and measuring on
        # another -- lives in sweep_fpr(certify_on=...) and is tested directly
        # in tests/test_fpr_sweep.py, including that overlapping items between
        # the two splits are refused.
        "20_fpr_sweep_oos.py",
        # Needs the extraction caches, which are gitignored, so it cannot run
        # on a clean clone by construction -- the same reason 00_extract.py is
        # exempt. What it PRODUCES is covered end to end by tests/test_scores.py,
        # which is the stronger check anyway: the frozen scores are the evidence,
        # and they are verified rather than the freezer being smoke-tested.
        "10_freeze_scores.py",
        # Needs both extraction caches and the rebuilt ledger, neither of which a
        # clean clone has, and refuses by design once the observed warrant is
        # past its 24-hour lifetime (DECISIONS 177). Its logic -- held-out rows
        # only, the expiry refusal, the criteria -- is unit-tested in
        # tests/test_revocation_trace.py, and the committed trace it writes is
        # checked there against the criteria DECISIONS 178 registered.
        "28_revocation_trace.py",
        # RECURSION. The clean-clone gate clones the repository and runs this
        # suite inside the clone. A smoke test that invoked it would clone,
        # run the suite, reach this test, clone again, and not stop. Its pure
        # parts are unit-tested in tests/test_clean_clone.py instead, and the
        # gate itself is run by hand before submission -- which is what it is
        # for. See DECISIONS.md 097.
        "clean_clone_gate.py",
    }
    uncovered = scripts - covered - exempt
    assert not uncovered, (
        f"scripts without a smoke test: {sorted(uncovered)}. Scripts are where "
        "controlplane/ is wired together, and wiring is what unit tests do not exercise."
    )


def test_notebook_is_generated_from_its_script(tmp_path: Path) -> None:
    """The committed notebook matches what its generator produces.

    Notebook JSON is not reviewable in a diff, so the generator is the source of
    truth. A hand-edited notebook would drift from it silently, and the drift
    would only surface on a GPU session an hour into a run.
    """
    subprocess.run(
        [sys.executable, str(PROJECT_ROOT / "scripts" / "build_notebooks.py"),
         "--out", str(tmp_path)],
        check=True, capture_output=True, text=True, cwd=str(PROJECT_ROOT), timeout=120,
    )
    generated = json.loads((tmp_path / "run_on_kaggle.ipynb").read_text(encoding="utf-8"))
    committed = json.loads(
        (PROJECT_ROOT / "notebooks" / "run_on_kaggle.ipynb").read_text(encoding="utf-8")
    )
    assert [c["source"] for c in generated["cells"]] == [
        c["source"] for c in committed["cells"]
    ], (
        "notebooks/run_on_kaggle.ipynb differs from what build_notebooks.py "
        "produces. Edit the script and regenerate; never hand-edit the notebook."
    )


def test_every_notebook_code_cell_compiles() -> None:
    """Every code cell in the generated notebook is valid Python.

    Written after shipping a notebook whose repo-detection cell was a syntax
    error. Two bugs stacked, and neither is visible in a notebook diff:

    * ``source`` entries carried no trailing newline. nbformat defines the field
      as a list that **concatenates** to the cell body, so a reader that
      concatenates runs the whole cell onto one line, while Kaggle — which joins
      with newlines — does not. The same notebook is therefore fine in one place
      and a syntax error in another.
    * An escaped newline inside an error message became a *real* newline in the
      generated source, splitting string literals across lines. That one is a
      syntax error everywhere, and it survived a review of the generator.

    Compiling the output is the only check that would have caught either.

    IPython magics are not Python; they are replaced with ``pass`` **preserving
    indentation**, because a magic inside an ``if`` block would otherwise break
    the block rather than the cell — which is a bug in the checker that looks
    like a bug in the notebook.
    """
    import ast
    import re

    notebook = json.loads(
        (PROJECT_ROOT / "notebooks" / "run_on_kaggle.ipynb").read_text(encoding="utf-8")
    )

    def neutralise(line: str) -> str:
        match = re.match(r"^(\s*)[!%]", line)
        return match.group(1) + "pass" if match else line

    failures = []
    code_cells = [c for c in notebook["cells"] if c["cell_type"] == "code"]
    assert code_cells, "the notebook has no code cells"

    for index, cell in enumerate(code_cells):
        source = "".join(cell["source"])
        # Try the source as written FIRST. Neutralising magics unconditionally
        # produced a false positive: a format continuation like
        #     "unsupported GPU: %s, sm %d.%d"
        #     % (name, major, minor),
        # begins a line with "%" and was rewritten to "pass", breaking an
        # expression that had been valid all along. IPython treats "%" as a
        # magic only at the start of a statement, never as a bracketed
        # continuation. A cell that parses as written needs no rewriting; only
        # one that fails can hold a magic, and there the rewrite is worth trying.
        try:
            ast.parse(source)
            continue
        except SyntaxError:
            pass
        cleaned = "\n".join(neutralise(line) for line in source.split("\n"))
        try:
            ast.parse(cleaned)
        except SyntaxError as exc:
            failures.append("code cell %d: %s at line %s" % (index, exc.msg, exc.lineno))

    assert not failures, "notebook cells do not compile:\n  " + "\n  ".join(failures)


def test_notebook_source_entries_keep_their_newlines() -> None:
    """nbformat requires ``source`` entries to concatenate to the cell body.

    Checked separately from compilation, because a malformed notebook can still
    compile under a reader that joins with newlines — and the malformed version
    is the one that breaks somewhere else.
    """
    notebook = json.loads(
        (PROJECT_ROOT / "notebooks" / "run_on_kaggle.ipynb").read_text(encoding="utf-8")
    )
    for index, cell in enumerate(notebook["cells"]):
        source = cell["source"]
        if len(source) < 2:
            continue
        missing = [i for i, line in enumerate(source[:-1]) if not line.endswith("\n")]
        assert not missing, (
            "cell %d: %d source entries lack a trailing newline. A reader that "
            "concatenates rather than joins will run the cell onto one line."
            % (index, len(missing))
        )


def test_notebook_has_no_stray_real_newlines_in_string_literals() -> None:
    """The specific corruption: an escape that became a literal line break.

    A string literal opened on one line and closed on the next is the signature.
    Compilation already catches it, but this names the cause in the failure
    message rather than reporting "invalid syntax" and leaving the reader to
    find it.
    """
    notebook = json.loads(
        (PROJECT_ROOT / "notebooks" / "run_on_kaggle.ipynb").read_text(encoding="utf-8")
    )
    offenders = []
    for index, cell in enumerate(notebook["cells"]):
        if cell["cell_type"] != "code":
            continue
        for line_number, line in enumerate(cell["source"], start=1):
            stripped = line.rstrip("\n")
            # An odd number of unescaped double quotes means the literal is
            # still open when the line ends.
            unescaped = stripped.replace('\\"', "")
            if unescaped.count('"') % 2 == 1 and '"""' not in stripped:
                offenders.append("cell %d line %d: %r" % (index, line_number, stripped))
    assert not offenders, (
        "string literals left open at end of line -- an escaped newline probably "
        "became a real one in the generator:\n  " + "\n  ".join(offenders)
    )


def test_extraction_script_imports_cleanly() -> None:
    """The GPU script's module-scope imports resolve without a GPU.

    Cannot run it end to end here, but the bug this file was written for was a
    NameError at module scope, and that is checkable without a card.
    """
    result = subprocess.run(
        [sys.executable, "-c",
         "import sys; sys.path.insert(0, '.'); "
         "import importlib.util as u; "
         "spec = u.spec_from_file_location('extract_cli', 'scripts/00_extract.py'); "
         "m = u.module_from_spec(spec); spec.loader.exec_module(m); "
         "print(m.parse_args(['--smoke']).smoke)"],
        capture_output=True, text=True, cwd=str(PROJECT_ROOT), timeout=180,
    )
    assert result.returncode == 0, (
        f"scripts/00_extract.py does not import cleanly:\n{result.stderr[-2000:]}"
    )
    assert "True" in result.stdout


# --------------------------------------------------------------------------- #
# The reproduction tiers themselves. Block E, E.4.
# --------------------------------------------------------------------------- #
# These are the commands a judge runs. A broken `make verify` is worse than a
# missing one -- it reads as verification and is not -- so the entry points are
# executed here the way a person executes them, not imported.


def _run_bare(name: str, *args: str, expect: int = 0) -> subprocess.CompletedProcess:
    """Run a script that takes no --config/--out, and assert its exit status."""
    result = subprocess.run(
        [sys.executable, str(PROJECT_ROOT / "scripts" / name), *args],
        capture_output=True, text=True, cwd=str(PROJECT_ROOT), timeout=900,
        env={**__import__("os").environ, "PYTHONIOENCODING": "utf-8"},
    )
    assert result.returncode == expect, (
        f"scripts/{name} exited {result.returncode}, expected {expect}\n"
        f"--- stdout ---\n{result.stdout[-3000:]}\n"
        f"--- stderr ---\n{result.stderr[-3000:]}"
    )
    return result


def test_smoke_the_smoke_check_itself() -> None:
    """`make smoke` -- the first thing anyone runs, and the first thing to break."""
    result = _run_bare("smoke.py")
    assert "SMOKE OK" in result.stdout
    for expected in ("package imports", "config loads", "claim table parses"):
        assert expected in result.stdout, f"smoke.py stopped checking {expected!r}"


def test_smoke_build_lock() -> None:
    """The lock generator: its CLI wiring, and its parser on the real file.

    Not a regeneration -- that resolves against PyPI and the suite runs offline.
    What is checkable without the network is what actually broke: on 2026-09-10
    the lock was a `pip freeze` carrying a pin PyPI had deleted, and CI could
    not install it. So this asserts the script imports and parses its flags, and
    that the reader it shares with `tests/test_packaging.py` reads the whole
    committed file rather than the first half of it.
    """
    import importlib.util

    result = _run_bare("build_lock.py", "--help")
    for flag in ("--upgrade", "--check"):
        assert flag in result.stdout, f"build_lock.py no longer offers {flag}"

    spec = importlib.util.spec_from_file_location(
        "build_lock", PROJECT_ROOT / "scripts" / "build_lock.py"
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    lock = (PROJECT_ROOT / "requirements.lock.txt").read_text(encoding="utf-8")
    pins = module.read_pins(lock)
    assert len(pins) > 100, (
        f"read_pins found {len(pins)} packages in requirements.lock.txt. The "
        "closure of requirements.txt is larger than that, so the parser is "
        "skipping lines -- most likely the ones carrying a marker."
    )
    marked = [
        line for line in lock.splitlines()
        if line.startswith(("bitsandbytes==", "colorama==", "nvidia-", "triton=="))
    ]
    assert marked and all(";" in line for line in marked), (
        "the platform-specific pins lost their environment markers. Without "
        "them the lock is unresolvable on the platforms they exclude, which is "
        "how it came to be uninstallable on Linux in the first place."
    )
    assert module.PYTHON_TARGET in lock, (
        "the lock header no longer names the Python it was resolved for"
    )


def test_smoke_verify_claims_only() -> None:
    """`make verify-claims` -- the fast half, which needs no cached activations."""
    result = _run_bare("verify.py", "--claims-only")
    assert "claims reproduce" in result.stdout
    assert "VERIFIED" in result.stdout
    assert "DRIFT" not in result.stdout


def test_verify_exits_non_zero_on_drift(tmp_path: Path) -> None:
    """The half that matters: verification must be able to fail.

    A checker that cannot fail is decoration. This feeds it a README with one
    number altered and asserts a non-zero exit -- the thing `make verify` relies
    on to stop a release.
    """
    readme = (PROJECT_ROOT / "README.md").read_text(encoding="utf-8")
    assert "| 0.8256 | [0.7934, 0.8567]" in readme
    tampered = tmp_path / "README.md"
    tampered.write_text(
        readme.replace("| 0.8256 | [0.7934, 0.8567]", "| 0.9999 | [0.7934, 0.8567]", 1),
        encoding="utf-8",
    )
    result = _run_bare("verify.py", "--claims-only", "--readme", str(tampered), expect=1)
    assert "DRIFT" in result.stdout
    assert "0.9999" in result.stdout or "0.9999" in result.stderr


def test_smoke_feasibility(tmp_path: Path) -> None:
    """`11_feasibility.py` derives the bound and the distance from it.

    CPU-only and seconds long, so it gets a real smoke test rather than an
    exemption. Asserts the artifact it writes is internally consistent, not
    merely that the script exited zero -- a stage that writes a plausible file
    and exits cleanly is the failure mode this suite exists for.
    """
    result = _run_bare(
        "11_feasibility.py",
        "--config", str(PROJECT_ROOT / "config.yaml"),
        "--out", str(tmp_path / "feasibility.json"),
    )
    assert "abstain on at least" in result.stdout or result.stdout == ""

    payload = json.loads((tmp_path / "feasibility.json").read_text(encoding="utf-8"))
    assert payload["measured"]["base_error_rate"] > 0
    assert payload["measured"]["envelope_id"].startswith("sha256:")

    floors = payload["abstention_floor"]
    assert len(floors) >= 3
    # Monotone in the target: a tighter risk ceiling can never need less
    # abstention. If this inverts, the inequality was mis-transcribed.
    by_target = sorted(floors, key=lambda f: -f["target_risk"])
    values = [f["floor"] for f in by_target]
    assert values == sorted(values), f"floor is not monotone in the target: {values}"

    assert payload["profiles"], "no profile was derived"
    for profile in payload["profiles"]:
        achieved = profile["achieved_risk"]
        assert achieved["efficiency"] >= 1.0, (
            f"{profile['profile']} scored {achieved['efficiency']}, below the "
            "theoretical floor -- which would mean the bound is wrong"
        )
        assert 0.0 <= achieved["residual_risk"] <= 1.0

    # The note used to say the price list was "not built". It is built now
    # (DECISIONS.md 146, 147), so what this asserts moved with it: the artifact
    # still derives no money figure, and the superseded label budget it carries
    # for traceability is labelled as superseded rather than quotable.
    note = payload["not_derived_here"]
    assert "No cost, headcount or saving figure" in note
    assert "declared estimate" in note
    assert "SUPERSEDED" in note
    for profile in payload["profiles"]:
        assert "label_plans" in profile
        assert "recall_sample_size_SUPERSEDED" in profile
        for plan in profile["label_plans"]:
            # DECISIONS.md 150: feasibility.json quotes month one only;
            # results/on_traffic/ owns the steady-state regime.
            assert plan["regime"] == "month_one_proportional"


def test_smoke_fpr_sweep(tmp_path: Path) -> None:
    """`19_fpr_sweep.py` re-analyses frozen scores and writes its three artifacts.

    CPU-only and reads only committed scores, so it gets a real smoke test
    rather than an exemption. Run over a two-point grid: the full twenty-point
    sweep takes minutes and this is about wiring, which the grid length does not
    exercise.

    Asserts the artifacts are internally consistent rather than merely present.
    A sweep that wrote a plausible file and exited zero is exactly the failure
    this suite exists for -- and the specific way it could happen here is a
    certified row carrying no metrics, or a lift whose interval does not
    bracket its own value.
    """
    out = tmp_path / "results"
    (out / "scores").mkdir(parents=True)
    for name in ("validation-T1-last_token.json",):
        shutil.copy(PROJECT_ROOT / "results" / "scores" / name, out / "scores" / name)

    _run_bare(
        "19_fpr_sweep.py",
        "--config", str(PROJECT_ROOT / "config.yaml"),
        "--score-set", "validation-T1-last_token",
        "--start", "0.05", "--stop", "0.10", "--step", "0.05",
        "--out", str(out),
    )

    sweep_dir = out / "fpr_sweep"
    for artifact in ("sweep.json", "SWEEP.md", "sweep.png"):
        assert (sweep_dir / artifact).is_file(), f"{artifact} was not written"

    payload = json.loads((sweep_dir / "sweep.json").read_text(encoding="utf-8"))
    assert payload["provenance"]["git_commit"], "no commit recorded in the sweep"
    assert payload["grid_spec"]["targets"] == [0.05, 0.10]

    sweep = payload["sweeps"][0]
    assert sweep["data_source"] == "measured"
    assert len(sweep["points"]) == 2

    for point in sweep["points"]:
        if not point["certified"]:
            # A refusal carries its reason and no numbers at all.
            assert point["reason"] and point["recall"] is None
            continue
        assert point["threshold"] is not None
        # The certified threshold must actually deliver the budget it certified.
        assert point["achieved_fpr"] <= point["target_fpr"]
        assert point["ucb"] <= point["target_fpr"]
        for name in ("recall", "precision", "flag_rate"):
            metric = point[name]
            assert metric["ci_low"] <= metric["value"] <= metric["ci_high"], (
                f"{name} sits outside its own interval"
            )
        lift = point["lift"]
        if lift is not None:
            assert lift["ci_low"] <= lift["value"] <= lift["ci_high"]
            assert point["lift_holds"] == (lift["ci_low"] > 1.0)

    markdown = (sweep_dir / "SWEEP.md").read_text(encoding="utf-8")
    assert "## Verdict" in markdown
    assert "in-sample" in markdown, "the selection caveat left the document"


def test_smoke_calibration_power(tmp_path: Path) -> None:
    """`21_calibration_power.py` answers D15 from the declared budgets alone.

    CPU, no cache, no scores -- a binomial power question about the flag rate.
    Asserts the monotonicity that makes the table meaningful rather than merely
    that it was written: a tighter tolerance always needs more items, and a
    tighter budget needs more items at a fixed tolerance.
    """
    run_script("21_calibration_power.py", out=tmp_path)
    payload = json.loads(
        (tmp_path / "calibration_power" / "calibration_power.json").read_text(
            encoding="utf-8"
        )
    )
    assert payload["n_available"] == 600
    rows = payload["budgets"]
    assert len(rows) >= 4, "the three profiles and the shipped point"

    for row in rows:
        required = [row["n_required"][f"{t:.2f}"] for t in (0.05, 0.10, 0.25, 0.50)]
        assert required == sorted(required, reverse=True), (
            f"{row['name']}: a looser tolerance asked for MORE items, which "
            "inverts the power relation"
        )
        detectable = row["smallest_detectable_at_n_available"]
        if detectable is not None:
            # The claim has to survive its own estimator.
            from controlplane.validation.calibration import n_to_detect_deviation
            assert n_to_detect_deviation(row["target_flag_rate"], detectable) <= 600
            assert row["meets_10_percent_bar"] == (detectable <= 0.10)

    by_budget = sorted(rows, key=lambda r: r["target_flag_rate"])
    tightest, loosest = by_budget[0], by_budget[-1]
    assert tightest["n_required"]["0.10"] > loosest["n_required"]["0.10"], (
        "a tighter flag-rate budget must need MORE items at the same tolerance"
    )

    text = (tmp_path / "calibration_power" / "CALIBRATION_POWER.md").read_text(
        encoding="utf-8"
    )
    assert "1441" in text, "the figure this phase quoted is not located in the table"
    assert "needs a GPU" in text, "the expansion must not read as done"


def test_smoke_pilot_freeze(tmp_path: Path) -> None:
    """`12_pilot_freeze.py` freezes prompts and measures surface distance.

    CPU only and seconds long. Asserts the draft it writes carries NO labels,
    because that is the property the corrected DECISIONS 090 turns on: on this
    set correctness is measured, and a placeholder would be indistinguishable
    from a measurement once it reached an artifact.
    """
    evalsets_out = tmp_path / "evalsets"
    _run_bare(
        "12_pilot_freeze.py",
        "--config", str(PROJECT_ROOT / "config.yaml"),
        "--evalsets-out", str(evalsets_out),
        "--out", str(tmp_path / "pilot_envelope.json"),
    )

    draft = json.loads(
        (evalsets_out / "banking-dual-24.draft.json").read_text(encoding="utf-8")
    )
    assert draft["n_items"] == 24
    assert draft["n_questions"] == 12
    assert "UNMEASURED" in draft["labels"]
    for item in draft["items"]:
        assert "label" not in item, "the frozen draft grew a correctness label"
        assert item["gold_source"] and item["gold_checked"]
        assert item["rot_class"] in ("structural", "rate")

    envelope = json.loads((tmp_path / "pilot_envelope.json").read_text(encoding="utf-8"))
    assert envelope["pilot"]["n"] == 24
    assert envelope["draft_content_hash"] == draft["content_hash"]
    # The artifact must say a small distance is not evidence the signal
    # transfers, or someone will read it as though it were.
    assert "NOT evidence" in envelope["interpretation"]


def test_smoke_pilot_null_band(tmp_path: Path) -> None:
    """`14_pilot_null_band.py` regenerates the threshold `101` routes on.

    The point of the script is that ``SATURATION_IQR_RATIO`` stops being a
    constant nobody can reproduce, so the assertions are that the artifact
    actually contains the regenerated band and both power tables -- and that
    the frozen threshold's false-alarm rate is where DECISIONS 103 says it is.

    ``--repeats`` is dropped to keep the smoke test seconds long. The committed
    artifact is built at the 20,000 default.
    """
    out = tmp_path / "pilot_null_band.json"
    _run_bare(
        "14_pilot_null_band.py",
        "--config", str(PROJECT_ROOT / "config.yaml"),
        "--n-reference", "960",
        "--repeats", "4000",
        "--out", str(out),
    )
    payload = json.loads(out.read_text(encoding="utf-8"))

    assert payload["n_reference"] == 960
    assert payload["frozen_threshold"] == 0.439

    # All three score shapes at all five sizes, or the stability claim in 103
    # rests on a table that was never built.
    for shape in ("normal", "logistic", "beta2_2"):
        for n in (12, 24, 30, 60, 120):
            assert f"{shape}/n{n}" in payload["null_band"]

    band = payload["null_band"]["normal/n12"]
    # The hand-derived 0.439 must keep landing just under the simulated p5.
    # If this drifts, the threshold and the null have come apart and the
    # pilot's routing rule is no longer the one 103 justified.
    assert 0.42 <= band["p5"] <= 0.49, band["p5"]
    assert 0.02 <= band["false_alarm_rate"] <= 0.07, band["false_alarm_rate"]

    # The finding: holding 0.439 while n grows LOSES power. If this inverts,
    # 103's whole argument for keeping n=12 has gone with it.
    frozen_12 = payload["power_frozen_threshold"]["n12/collapse0.6"]
    frozen_30 = payload["power_frozen_threshold"]["n30/collapse0.6"]
    assert frozen_30 < frozen_12, (
        f"frozen threshold gained power going 12->30 ({frozen_12} -> {frozen_30}); "
        "DECISIONS 103 says it must lose it"
    )

    # And recalibrating reverses that.
    recal_30 = payload["power_recalibrated_threshold"]["n30/collapse0.6"]
    assert recal_30 > frozen_30, (
        f"recalibrating at n=30 did not beat the frozen threshold "
        f"({recal_30} vs {frozen_30})"
    )


def test_smoke_pilot_seed_stability(tmp_path: Path) -> None:
    """`15_pilot_seed_stability.py` prices the pilot's margin, DECISIONS 114.

    Seeds and resamples are dropped hard to keep this seconds long; the
    committed artifact is built at 400 x 1000. What is asserted is the
    contract, not the value: the artifact names the fraction of seeds that
    clear, because that fraction is the verdict.
    """
    out = tmp_path / "pilot_seed_stability.json"
    _run_bare(
        "15_pilot_seed_stability.py",
        "--config", str(PROJECT_ROOT / "config.yaml"),
        "--seeds", "12",
        "--resamples", "120",
        "--out", str(out),
    )
    payload = json.loads(out.read_text(encoding="utf-8"))
    stability = payload["stability"]
    assert stability["n_clusters"] == 12
    assert 0.0 <= stability["clears_fraction"] <= 1.0
    assert stability["sd"] > 0.0, "a seed sweep with zero spread swept nothing"
    assert stability["published"] is not None
    assert "minority" in payload["verdict"] or "majority" in payload["verdict"]


def test_the_pilot_artifact_still_carries_its_scores() -> None:
    """Without them, DECISIONS 114's question needs another GPU run to ask."""
    payload = json.loads(
        (PROJECT_ROOT / "results" / "pilot_run.json").read_text(encoding="utf-8")
    )
    assert "scores" in payload, "pilot_run.json lost its scores block"
    assert len(payload["scores"]["pilot"]) == 24
    assert len(payload["scores"]["question_ids"]) == 24
    assert payload["scores"]["reference_summary"]["n"] == 960


def test_smoke_presidio_coverage(tmp_path: Path) -> None:
    """`17_presidio_coverage.py` makes the "no recogniser exists" claim citable.

    The claim was true and traced to nothing in this repository, which is the
    import path DECISIONS 113 and 117 are about. A claim about a dependency is
    checkable by running the dependency.
    """
    out = tmp_path / "presidio_coverage.json"
    _run_bare(
        "17_presidio_coverage.py",
        "--config", str(PROJECT_ROOT / "config.yaml"),
        "--out", str(out),
    )
    payload = json.loads(out.read_text(encoding="utf-8"))
    assert payload["n_supported_entities"] > 0
    assert payload["india_prefixed_entities"] == []
    for family in ("UPI", "IFSC", "AADHAAR"):
        assert family in payload["uncovered"], (
            f"stock Presidio now covers {family}; the demo's coverage claim has "
            "changed and the narration must change with it"
        )
    assert payload["presidio_version"] != "unknown"


def test_smoke_on_traffic(tmp_path: Path) -> None:
    """`25_on_traffic.py` prices labels and evidences the estimator.

    CPU-only and seconds long at a small trial count, so it gets a real smoke
    test. Run at 20 coverage trials rather than 1,000: this checks wiring, and
    wiring is not what the trial count exercises. **The coverage figure from 20
    trials is noise and is not asserted against the pre-registered band** --
    ``DECISIONS.md`` 147 registered that band for 1,000 trials and checking it
    here would be reading a number from a run too small to produce one.

    What is asserted is internal consistency, because a stage that writes a
    plausible file and exits zero is the failure this suite exists for.
    """
    _run_bare(
        "25_on_traffic.py",
        "--config", str(PROJECT_ROOT / "config.yaml"),
        "--trials", "20",
        "--out", str(tmp_path),
    )
    payload = json.loads(
        (tmp_path / "on_traffic" / "on_traffic.json").read_text(encoding="utf-8")
    )

    sensitivity = payload["sensitivity"]
    assert sensitivity["derivative"] < 0, "dR/dq must be negative by construction"
    # The two ratios DECISIONS 148 separated must stay separate and unequal.
    assert sensitivity["amplification"] != sensitivity["pool_ratio"]

    rows = payload["price_list"]
    assert rows, "no price-list row was derived"
    regimes = {str(r["regime"]).split(" ")[0] for r in rows}
    assert regimes == {"month", "steady"}, (
        f"expected both regimes, got {regimes}. DECISIONS.md 150: quoting month "
        "one at Neyman's design effect is a named silent failure."
    )
    for row in rows:
        if not row["feasible"]:
            continue
        # The whole point of DECISIONS 147: the propagated figure must exceed
        # the naive one, and by a lot.
        assert row["labels"] > row["naive_labels"]
        assert row["understatement"] > 2.0
        # And the exact basis must cost more than the normal approximation,
        # which is DECISIONS 149.
        assert row["labels_exact"] is None or row["labels_exact"] >= row["labels_normal"]

    # Month one is never cheaper than steady state at the same margin.
    for row in rows:
        if not str(row["regime"]).startswith("month") or not row["feasible"]:
            continue
        steady = next(
            (
                other
                for other in rows
                if other["subject"] == row["subject"]
                and other["margin"] == row["margin"]
                and not str(other["regime"]).startswith("month")
            ),
            None,
        )
        if steady is not None and steady["feasible"]:
            assert row["labels"] >= steady["labels"]

    assert payload["coverage"]["trials"] == 20
    assert payload["not_derived_here"], "the artifact must say what it does not derive"


def test_smoke_scorefree(tmp_path: Path) -> None:
    """`26_scorefree.py` prices what repeated sampling buys a score-free detector.

    Run at 3 draws rather than 40. **No floor from this run is asserted as a
    value** -- ``DECISIONS.md`` 152a records a wrong conclusion reached from a
    single draw, and three is not meaningfully better. What is asserted is the
    structure, which does not depend on the draw count.
    """
    _run_bare(
        "26_scorefree.py",
        "--config", str(PROJECT_ROOT / "config.yaml"),
        "--draws", "3",
        "--out", str(tmp_path),
    )
    payload = json.loads(
        (tmp_path / "scorefree" / "scorefree.json").read_text(encoding="utf-8")
    )

    assert payload["declared"]["draws_per_cell"] == 3
    assert "SIMULATED" in payload["scope"], (
        "the scope caveat must travel with the numbers; every figure here is an "
        "upper bound because a real judge's runs are correlated"
    )

    # C1: notches bound the operating points, exactly and always.
    for row in payload["tunability"]:
        assert row["notches"] == row["k"] + 1
        assert row["distinct_operating_points"] <= row["notches"]
        assert row["distinct_scores"] <= row["notches"]

    # A one-bit detector has exactly one operating point. Structural, not a draw.
    at_one = next(r for r in payload["tunability"] if r["k"] == 1)
    assert at_one["distinct_operating_points"] == 1

    # C2: the bound certified at one k does not hold at another.
    void = payload["void_at_another_k"]
    assert void["verdict"] == "VOID"
    assert void["realised_fpr_at_k1"] > void["certified_upper_bound"]
    assert void["certified_detector_id"] != void["deployed_detector_id"]

    # C4: ranking improves with k and never reaches the latent ceiling.
    ceiling = payload["ranking"]["latent_ceiling_auroc"]
    gaps = [row["gap_to_ceiling"] for row in payload["ranking"]["by_k"]]
    assert all(gap > 0 for gap in gaps)
    assert gaps == sorted(gaps, reverse=True), "AUROC must improve with k"
    assert ceiling <= 1.0


def test_smoke_gate(tmp_path: Path) -> None:
    """`27_gate.py` runs the injection and counts what the gate costs.

    Fast enough to run in full, so nothing is scaled down and every figure it
    writes is the real one.
    """
    _run_bare(
        "27_gate.py",
        "--config", str(PROJECT_ROOT / "config.yaml"),
        "--out", str(tmp_path),
    )
    payload = json.loads((tmp_path / "gate" / "gate.json").read_text(encoding="utf-8"))

    # The claim the whole package exists to make.
    evidence = payload["no_detector_evidence"]
    assert evidence["decisions_compared"] > 0
    assert evidence["identical"] == evidence["decisions_compared"]
    assert evidence["mismatches"] == []

    # The attack is refused, and not because a detector caught it.
    injection = payload["injection"]
    assert injection["detector_flagged"] is False
    blocked = [s for s in injection["steps"] if s["action"] == "BLOCK"]
    assert blocked, "the injection scenario blocked nothing"
    assert blocked[0]["tool"] == "transfer_funds"
    assert blocked[0]["consulted_detector"] is False

    # And the cost is reported as a count, not an estimate.
    cost = payload["cost"]
    assert cost["kind"] == "EXACT"
    assert 0 < cost["n_blocked"] < cost["n_workflows"], (
        "a gate that blocks nothing is not a control, and one that blocks "
        "everything is not usable"
    )
    assert "EXACT" in cost["note"] and "estimated" in cost["note"].lower()


def test_smoke_recheck_schedules(tmp_path: Path) -> None:
    """`29_recheck_schedules.py` writes every cell and applies 187's criteria.

    Scaled down to 20 simulated years, which is why `--out` is required: a
    smoke-sized study must never land where the registered one lives.
    """
    _run_bare(
        "29_recheck_schedules.py",
        "--config", str(PROJECT_ROOT / "config.yaml"),
        "--years", "20",
        "--out", str(tmp_path),
    )
    payload = json.loads(
        (tmp_path / "recheck_schedules" / "comparison.json").read_text(encoding="utf-8")
    )
    # 5 rules x 2 cadences x 4 scenarios.
    assert len(payload["cells"]) == 40
    assert set(payload["criteria"]["validity"]) == {
        f"{rule}/{cadence}"
        for rule in ("fixed", "split", "monitor", "monitor_uncapped", "e_detector")
        for cadence in ("weekly", "monthly")
    }
    assert "not any detector" in payload["what_these_are"]


def test_smoke_frontier_selection(tmp_path: Path) -> None:
    """`30_frontier_selection.py` writes every cell and applies 192's criteria.

    Scaled down, which is why `--out` is required: a smoke-sized study must
    never land where the registered one lives.
    """
    _run_bare(
        "30_frontier_selection.py",
        "--config", str(PROJECT_ROOT / "config.yaml"),
        "--replicates", "200",
        "--crosscheck-replicates", "3",
        "--out", str(tmp_path),
    )
    payload = json.loads(
        (tmp_path / "frontier_selection" / "selection.json").read_text(encoding="utf-8")
    )
    assert [cell["n"] for cell in payload["cells"]] == [150, 300, 600, 1200, 5000]
    assert set(payload["criteria"]) == {"M1_material", "M2_bonferroni_alpha", "M3_sanity"}
    assert payload["registered_run"] is False
    assert "Not a measurement" in payload["what_these_are"]

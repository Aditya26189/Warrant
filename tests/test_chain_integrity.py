"""The three chain defects Codex's independent review reproduced. DECISIONS.md 194.

Each test is written against the defect as it was found. The acceptance harness
these tests formalise -- the same scenarios through the public CLI -- failed on all
three before the fix and passes after it (``reports/PHASE-12.md`` 8.12). These
tests cannot run against the build before the fix at all: it has no
``MalformedChainError`` to import.

* a warrant REVOKED on its score distribution, with the chain still live, could
  be continued, and the verifier called that history clean;
* a chain record's serialized ``threshold``, ``mean_statistic`` and ``ended`` were
  hashed but never compared with their reconstruction, so editing one passed;
* an ``alpha`` of 0 or a NaN anywhere in a record crashed with a traceback before
  any check ran.

The first is driven through the public CLI, because the defect lived in the path
a customer takes; a unit test of ``continue_chain`` alone would not have shown
that ``warrant recheck --since`` accepted the record.
"""

from __future__ import annotations

import dataclasses
import json
import math
from pathlib import Path

import numpy as np
import pytest

from controlplane.cli import main
from controlplane.intake.chain import (
    ChainError,
    ChainState,
    MalformedChainError,
    canonical_sha256,
    continue_chain,
    feed,
    start_chain,
)
from controlplane.intake.chain_verify import verify_chain_records

WARRANT = {"status": "VALID", "budget_fpr": 0.05, "alpha": 0.05,
           "certification": {"threshold": 0.5}}


def _units(tag: str, n: int = 40, fired_every: int = 25):
    ids = [f"{tag}{i}" for i in range(n)]
    return ids, np.array([i % fired_every == 0 for i in range(n)])


def _chained(tag: str = "a", *, status: str = "VALID") -> dict:
    state = start_chain(WARRANT, horizon_units=1000, alpha=0.05)
    return {"status": status, "chain": feed(state, *_units(tag)).to_payload()}


def _findings(records: dict) -> list:
    return list(verify_chain_records(records).findings)


# --------------------------------------------------------------------------- #
# Defect 1: a warrant revoked by drift is not continued
# --------------------------------------------------------------------------- #

def _export(path: Path, *, n_neg: int, n_pos: int, shift: float, seed: int) -> Path:
    rng = np.random.default_rng(seed)
    lines = ["id,label,score"]
    lines += [f"{path.stem}-n{i},0,{rng.normal(shift, 1.0):.6f}" for i in range(n_neg)]
    lines += [f"{path.stem}-p{i},1,{rng.normal(2.0 + shift, 1.0):.6f}" for i in range(n_pos)]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path


def test_a_warrant_revoked_by_drift_is_not_continued_through_the_cli(tmp_path, capsys):
    """The customer's path, end to end.

    The shift is DOWNWARD on purpose. An upward shift raises the false-positive
    rate, revokes the chain's own statistic, and gets the continuation refused
    for that reason -- a pass that tests nothing about drift. Moving the
    distribution while firings fall leaves the chain live and the bound holding,
    which is the only configuration in which the defect existed.
    """
    warrant = tmp_path / "w.json"
    base = _export(tmp_path / "base.csv", n_neg=900, n_pos=300, shift=0.0, seed=11)
    assert main(["certify", "-i", str(base), "-b", "0.05", "-q", "-o", str(warrant)]) == 0

    shifted = _export(tmp_path / "shifted.csv", n_neg=1500, n_pos=400, shift=-1.2, seed=14)
    link1 = tmp_path / "link1.json"
    main(["recheck", "-w", str(warrant), "-i", str(shifted), "--horizon-labels", "100000",
          "-q", "-o", str(link1)])
    record = json.loads(link1.read_text(encoding="utf-8"))
    # The precondition the defect needed, asserted so a change to the fixture
    # cannot turn this back into a test of the chain's own revocation.
    assert record["status"] == "REVOKED"
    assert record["drift"]["verdict"] == "REVOKED"
    assert record["chain"]["revoked_at_unit"] is None
    assert record["now"]["bound_still_holds"] is True

    stable = _export(tmp_path / "stable.csv", n_neg=900, n_pos=300, shift=0.0, seed=12)
    link2 = tmp_path / "link2.json"
    capsys.readouterr()
    code = main(["recheck", "-w", str(warrant), "-i", str(stable), "--since", str(link1),
                 "-q", "-o", str(link2)])
    err = capsys.readouterr().err
    assert code == 2
    assert not link2.exists()
    assert "REVOKED" in err and "score distribution" in err and "re-certify" in err


def test_continue_chain_refuses_any_revoked_record_whatever_revoked_it():
    record = _chained(status="REVOKED")
    assert record["chain"]["revoked_at_unit"] is None  # the chain itself is live
    with pytest.raises(ChainError, match="score distribution"):
        continue_chain(record, WARRANT, alpha=0.05)


def _link_after(parent: dict, tag: str, *, status: str = "VALID") -> dict:
    """A second link built at the state level, as the build before the fix wrote it."""
    state = dataclasses.replace(
        ChainState.from_payload(parent["chain"]),
        sequence=2, previous_record_sha256=canonical_sha256(parent),
    )
    return {"status": status, "chain": feed(state, *_units(tag)).to_payload()}


def test_verify_flags_a_link_after_a_record_revoked_by_drift():
    revoked = _chained("a", status="REVOKED")
    after = _link_after(revoked, "b")
    findings = _findings({"r1.json": revoked, "r2.json": after})
    ended = [f for f in findings if f.kind == "continued_after_end"]
    assert len(ended) == 1
    assert "score distribution" in ended[0].detail
    assert ended[0].records == ("r1.json", "r2.json")


def test_the_same_history_with_a_valid_parent_is_clean():
    """The control: the finding comes from the status, not from the construction."""
    valid = _chained("a", status="VALID")
    after = _link_after(valid, "b")
    assert _findings({"r1.json": valid, "r2.json": after}) == []


# --------------------------------------------------------------------------- #
# Defect 2: each serialized derived field is compared with its reconstruction
# --------------------------------------------------------------------------- #

def _forgeries(chain: dict):
    """Each derived field edited alone, the digest left as it was."""
    yield "threshold", {**chain, "threshold": -1.0}
    yield "threshold", {**chain, "threshold": chain["threshold"] * 2}
    yield "mean_statistic", {**chain, "mean_statistic": 999999999.0}
    yield "mean_statistic", {**chain, "mean_statistic": math.nextafter(chain["mean_statistic"], math.inf)}
    yield "ended", {**chain, "ended": not chain["ended"]}
    # A truthy non-boolean is not the boolean it imitates.
    yield "ended", {**chain, "ended": int(chain["ended"])}


@pytest.mark.parametrize("index", range(6))
def test_each_derived_field_edited_alone_is_refused(index):
    record = _chained()
    field, forged = list(_forgeries(record["chain"]))[index]
    assert forged["state_sha256"] == record["chain"]["state_sha256"]  # not rehashed
    with pytest.raises(ChainError, match=field) as raised:
        ChainState.from_payload(forged)
    assert not isinstance(raised.value, MalformedChainError)
    findings = _findings({"r.json": {**record, "chain": forged}})
    assert [f.kind for f in findings] == ["digest"]
    assert field in findings[0].detail


def test_an_unedited_record_still_verifies_and_round_trips_exactly():
    """Exact equality needs the floats to survive JSON; this is the proof they do."""
    record = _chained()
    reread = json.loads(json.dumps(record))
    assert ChainState.from_payload(reread["chain"]).mean_statistic == reread["chain"]["mean_statistic"]
    assert _findings({"r.json": reread}) == []


def test_a_derived_field_missing_is_refused():
    record = _chained()
    chain = {k: v for k, v in record["chain"].items() if k != "ended"}
    with pytest.raises(ChainError, match="ended"):
        ChainState.from_payload(chain)


# --------------------------------------------------------------------------- #
# Defect 3: malformed values are refused before any arithmetic
# --------------------------------------------------------------------------- #

MALFORMED = [
    ("alpha", 0), ("alpha", -0.05), ("alpha", 1.0), ("alpha", float("nan")),
    ("alpha", float("inf")), ("alpha", True), ("alpha", "0.05"), ("alpha", None),
    ("p0", 0), ("p0", 1.5),
    ("horizon_units", 0), ("horizon_units", True), ("horizon_units", 1.5),
    ("units_consumed", -1), ("sequence", 0),
    ("revoked_at_unit", 0), ("revoked_at_unit", True),
]


@pytest.mark.parametrize("field,value", MALFORMED)
def test_a_malformed_value_is_refused_as_malformed(field, value):
    chain = dict(_chained()["chain"])
    if value is None:
        chain.pop(field)
    else:
        chain[field] = value
    with pytest.raises(MalformedChainError, match=field):
        ChainState.from_payload(chain)


@pytest.mark.parametrize("mutate", [
    lambda c: c["statistics"].__setitem__(0, float("nan")),
    lambda c: c["statistics"].pop(),
    lambda c: c["grid"].__setitem__("n_lam", 0),
    lambda c: c["grid"].__setitem__("lam_lo", float("inf")),
])
def test_a_malformed_grid_or_statistic_is_refused_as_malformed(mutate):
    chain = json.loads(json.dumps(_chained()["chain"]))
    mutate(chain)
    with pytest.raises(MalformedChainError):
        ChainState.from_payload(chain)


def test_nan_anywhere_in_a_record_is_a_finding_not_a_traceback():
    """Found by the acceptance harness after the first fix.

    The verifier digests each whole record before it reads the chain block, and
    the digest's encoder refuses NaN; validating the chain block alone left this
    path crashing.
    """
    record = _chained()
    record["now"] = {"achieved_fpr": float("nan")}
    findings = _findings({"r.json": record})
    assert [f.kind for f in findings] == ["malformed"]
    with pytest.raises(MalformedChainError, match="NaN or infinity"):
        continue_chain(record, WARRANT, alpha=0.05)


def test_the_cli_verifier_records_a_malformed_record_and_exits_zero(tmp_path, capsys):
    """Findings are a result and exit 0 (194); the defect was the traceback."""
    for name, value in (("zero", 0), ("nan", float("nan"))):
        record = _chained()
        record["chain"]["alpha"] = value
        path = tmp_path / f"{name}.json"
        path.write_text(json.dumps(record), encoding="utf-8")
        out = tmp_path / f"{name}.verify.json"
        assert main(["chain", "verify", str(path), "-q", "-o", str(out)]) == 0
        payload = json.loads(out.read_text(encoding="utf-8"))
        assert payload["clean"] is False
        assert [f["kind"] for f in payload["findings"]] == ["malformed"]
    assert "Traceback" not in capsys.readouterr().err

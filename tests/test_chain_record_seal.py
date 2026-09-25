"""Every stored field of a chained record is checked on verify (addendum 2026-09-17).

The derived-field defect was a class: the verifier checked its own computation
and never what was presented. A schema audit then found 197 fields of the LATEST
record -- its status, bounds, drift verdict, labels, provenance -- that could be
edited with `warrant chain verify` still reporting clean.

So this file does not list fields. It walks every leaf of real records written
by the public CLI, mutates each one alone, and asserts the verifier notices. A
field added to the record later is covered without anyone remembering to add it.
That is the rule "every stored field is either checked on verify or not stored at
all", enforced rather than hoped for.
"""

from __future__ import annotations

import copy
import json
from pathlib import Path

import numpy as np
import pytest

from controlplane.cli import main
from controlplane.intake.chain import SEAL_FIELD, seal_reproduces
from controlplane.intake.chain_verify import render_chain_verification, verify_chain_records


def _export(path: Path, *, n_neg: int, n_pos: int, seed: int, second: bool = False) -> Path:
    rng = np.random.default_rng(seed)
    lines = ["id,label,score" + (",label_2" if second else "")]
    for i in range(n_neg):
        extra = ("," + ("0" if i % 10 == 0 else "")) if second else ""
        lines.append(f"{path.stem}-n{i},0,{rng.normal(0.0, 1.0):.6f}{extra}")
    for i in range(n_pos):
        extra = ("," + ("1" if i % 10 == 0 else "")) if second else ""
        lines.append(f"{path.stem}-p{i},1,{rng.normal(2.0, 1.0):.6f}{extra}")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path


@pytest.fixture(scope="module")
def chain(tmp_path_factory):
    """A warrant and a two-link chain, written through the CLI, with label_2."""
    root = tmp_path_factory.mktemp("sealed_chain")
    warrant = root / "w.json"
    assert main(["certify", "-i", str(_export(root / "base.csv", n_neg=900, n_pos=300, seed=11)),
                 "-b", "0.05", "-q", "-o", str(warrant)]) == 0
    link1, link2 = root / "link1.json", root / "link2.json"
    assert main(["recheck", "-w", str(warrant), "-i",
                 str(_export(root / "a.csv", n_neg=900, n_pos=300, seed=12, second=True)),
                 "--horizon-labels", "100000", "-q", "-o", str(link1)]) == 0
    assert main(["recheck", "-w", str(warrant), "-i",
                 str(_export(root / "b.csv", n_neg=900, n_pos=300, seed=13, second=True)),
                 "--since", str(link1), "-q", "-o", str(link2)]) == 0
    records = {str(link1): json.loads(link1.read_text(encoding="utf-8")),
               str(link2): json.loads(link2.read_text(encoding="utf-8"))}
    return {"root": root, "warrant": warrant, "link1": link1, "link2": link2, "records": records}


def _leaves(obj, path=()):
    """Every leaf. Long lists contribute their first, middle and last element."""
    if isinstance(obj, dict):
        for key, value in obj.items():
            yield from _leaves(value, path + (key,))
    elif isinstance(obj, list):
        if not obj:
            yield path, obj
            return
        indices = sorted({0, len(obj) // 2, len(obj) - 1})
        for index in indices:
            yield from _leaves(obj[index], path + (index,))
    else:
        yield path, obj


def _mutated(value):
    if isinstance(value, bool):
        return not value
    if isinstance(value, int):
        return value + 1
    if isinstance(value, float):
        return value * 2 + 1.0
    if isinstance(value, str):
        return value + "x"
    if value is None:
        return 1
    if isinstance(value, list):
        return ["x"]
    return None


def _set(obj, path, value):
    for key in path[:-1]:
        obj = obj[key]
    obj[path[-1]] = value


def test_records_written_through_the_cli_are_sealed_and_verify_clean(chain):
    for record in chain["records"].values():
        assert SEAL_FIELD in record
        assert seal_reproduces(record) is True
    result = verify_chain_records(chain["records"])
    assert list(result.findings) == []
    assert result.unsealed == ()


def test_every_leaf_of_every_link_edited_alone_is_flagged(chain):
    """The property. Both links, every field, including the seal itself."""
    records = chain["records"]
    survivors, tried = [], 0
    for name in records:
        for path, value in _leaves(records[name]):
            new = _mutated(value)
            if new is None or new == value or not path:
                continue
            trial = copy.deepcopy(records)
            _set(trial[name], path, new)
            tried += 1
            if not verify_chain_records(trial).findings:
                survivors.append(f"{Path(name).name}:{'.'.join(map(str, path))}")
    assert tried > 400  # the walk really covered the records
    assert survivors == [], f"{len(survivors)} edits verified clean: {survivors[:20]}"


@pytest.mark.parametrize("field,value", [
    ("status", "VALID"), ("status", "REVOKED"), ("reason", "edited"),
])
def test_the_latest_records_verdict_cannot_be_edited_silently(chain, field, value):
    """The survivors that mattered most: the current verdict and its reason."""
    records = copy.deepcopy(chain["records"])
    latest = records[str(chain["link2"])]
    if latest[field] == value:
        value = value + "x"
    latest[field] = value
    kinds = [f.kind for f in verify_chain_records(records).findings]
    assert "digest" in kinds


def test_the_cli_verifier_flags_an_edited_latest_record(chain, tmp_path):
    record = copy.deepcopy(chain["records"][str(chain["link2"])])
    record["now"]["achieved_fpr"] = 0.0
    edited = tmp_path / "link2.edited.json"
    edited.write_text(json.dumps(record), encoding="utf-8")
    out = tmp_path / "v.json"
    assert main(["chain", "verify", str(chain["link1"]), str(edited), "-q", "-o", str(out)]) == 0
    payload = json.loads(out.read_text(encoding="utf-8"))
    assert payload["clean"] is False
    assert any("seal does not reproduce" in f["detail"] for f in payload["findings"])


def test_an_edited_since_record_is_not_continued(chain, tmp_path, capsys):
    """Otherwise an edited latest record, its sidecar deleted, could go on."""
    record = copy.deepcopy(chain["records"][str(chain["link2"])])
    record["reason"] = record["reason"] + " (edited)"
    edited = tmp_path / "link2.edited.json"
    edited.write_text(json.dumps(record), encoding="utf-8")
    head = Path(str(chain["warrant"]) + ".chain-head")
    head_bytes = head.read_bytes()
    third = _export(tmp_path / "c.csv", n_neg=900, n_pos=300, seed=14)
    out = tmp_path / "link3.json"
    capsys.readouterr()
    code = main(["recheck", "-w", str(chain["warrant"]), "-i", str(third), "--since", str(edited),
                 "--fork", "-q", "-o", str(out)])
    assert code == 2 and not out.exists()
    assert head.read_bytes() == head_bytes
    assert "seal does not reproduce" in capsys.readouterr().err


def test_an_unsealed_record_is_inspectable_but_not_verified_or_dated(chain):
    """No structural defect is inferred, but absent integrity cannot pass (207)."""
    legacy = copy.deepcopy(chain["records"][str(chain["link1"])])
    del legacy[SEAL_FIELD]
    assert seal_reproduces(legacy) is None
    result = verify_chain_records({"legacy.json": legacy})
    assert list(result.findings) == []
    assert result.unsealed == ("legacy.json",)
    payload = result.to_payload()
    assert payload["unsealed"] == ["legacy.json"]
    assert "were not" in payload["unsealed_meaning"]
    assert "age is unknown" in render_chain_verification(result)
    assert not result.clean and result.structurally_clean
    assert payload["integrity_status"] == "UNVERIFIED"


def test_the_seal_covers_provenance_as_written(chain):
    """Sealed over the document as read back, so the file on disk reproduces it."""
    on_disk = json.loads(Path(chain["link2"]).read_text(encoding="utf-8"))
    assert "provenance" in on_disk
    assert seal_reproduces(on_disk) is True
    on_disk["provenance"]["git_commit"] = "0" * 40
    assert seal_reproduces(on_disk) is False

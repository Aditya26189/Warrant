"""Negative controls for source classification and the independent point oracle."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from controlplane.report.documentation_audit import (
    check_links, collect_audit, point_oracle, repo_file, score_audit,
    source_flags, write_audit,
)

ROOT = Path(__file__).resolve().parents[1]


def test_rank_count_oracle_handles_ties_and_exact_threshold() -> None:
    r = point_oracle([0, 0, 1, 1], [0.1, 0.7, 0.7, 0.9], 0.7)
    assert r['auroc'] == 0.875
    assert r['recall'] == 1 and r['precision'] == 2 / 3
    assert r['flag_rate'] == 3 / 4 and r['false_positives'] == 1


def test_reversing_label_polarity_reverses_auc() -> None:
    r = point_oracle([1, 1, 0, 0], [0.1, 0.7, 0.7, 0.9], 0.7)
    assert r['auroc'] == 0.125


def test_all_tied_scores_are_chance_ranking() -> None:
    assert point_oracle([0, 1, 0, 1], [0.5] * 4, 0.5)['auroc'] == 0.5


def test_no_flags_does_not_mean_precision_is_measured_zero() -> None:
    r = point_oracle([0, 1], [0.1, 0.2], 0.9)
    assert r['precision'] is None and not r['precision_defined']
    assert r['flag_rate'] == 0 and r['recall'] == 0


def test_single_class_withholds_the_ranking_triplet() -> None:
    r = point_oracle([0, 0], [0.1, 0.9], 0.5)
    assert all(r[k] is None for k in ('auroc', 'recall', 'precision'))
    assert r['fpr'] == 0.5


@pytest.mark.parametrize('labels,scores,threshold', [
    ([], [], 0.5), ([0], [0.1, 0.2], 0.5), ([True], [0.1], 0.5),
    ([2], [0.1], 0.5), ([0], [float('nan')], 0.5),
    ([0], [0.1], float('inf')),
])
def test_oracle_refuses_invalid_observations(labels, scores, threshold) -> None:
    with pytest.raises(ValueError):
        point_oracle(labels, scores, threshold)


def test_missing_and_dirty_provenance_are_not_clean() -> None:
    assert source_flags({}) == ['MISSING_PROVENANCE']
    assert 'DIRTY_SOURCE' in source_flags({'provenance': {'dirty': True}})
    assert 'CLEANLINESS_NOT_RECORDED' in source_flags({'provenance': {'git_commit': 'x'}})
    assert source_flags({'provenance': {'dirty': False, 'git_commit': 'x'}}) == []


def test_repo_sources_cannot_escape_the_checkout(tmp_path: Path) -> None:
    root = tmp_path / 'repo'; root.mkdir()
    (tmp_path / 'outside.txt').write_text('preserve', encoding='utf-8')
    with pytest.raises(ValueError):
        repo_file(root, '../outside.txt')


def test_link_check_catches_missing_paths_and_fragments(tmp_path: Path) -> None:
    page = tmp_path / 'index.md'
    page.write_text('# Introduction\n[ok](#introduction)\n[bad](missing.md)\n[bad fragment](#absent)\n', encoding='utf-8')
    errors = check_links(tmp_path, [page])
    assert len(errors) == 2
    assert any('missing.md' in e for e in errors)
    assert any('#absent' in e for e in errors)


def test_fenced_command_examples_are_not_followed_as_links(tmp_path: Path) -> None:
    page = tmp_path / 'index.md'
    page.write_text('# Guide\n```text\n[example](not-a-file.md)\n```\n', encoding='utf-8')
    assert check_links(tmp_path, [page]) == []


def test_empty_score_audit_is_not_success(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match='no frozen-score'):
        score_audit(tmp_path)


def test_artifact_generation_refuses_dirty_source(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr('subprocess.check_output', lambda *a, **k: ' M README.md\n')
    with pytest.raises(ValueError, match='clean committed'):
        write_audit(tmp_path, tmp_path / 'new')
    assert not (tmp_path / 'new').exists()


def test_artifact_generation_never_replaces_a_run(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr('subprocess.check_output', lambda *a, **k: '')
    target = tmp_path / 'run'; target.mkdir()
    (target / 'evidence').write_bytes(b'preserve')
    with pytest.raises(ValueError, match='must be new'):
        write_audit(tmp_path, target)
    assert (target / 'evidence').read_bytes() == b'preserve'


def test_real_claims_are_complete_but_source_cautions_remain() -> None:
    r = collect_audit(ROOT)
    assert r['ok'] and r['summary']['claims'] == 92
    assert r['summary']['dirty_source_claims'] == 15
    assert r['summary']['frozen_score_targets'] == 25
    assert r['summary']['point_oracle_targets_passed'] == 25
    assert any(x['id'] == 'C006' and 'DIRTY_SOURCE' in x['source_flags'] for x in r['claims'])
    assert all(x['scientific_validity'] == 'NOT_ESTABLISHED_BY_ARTIFACT_MATCH' for x in r['claims'])


def test_a_new_unclassified_artifact_requires_source_review(tmp_path: Path) -> None:
    registry = json.loads((ROOT / 'docs/handbook/claim-families.json').read_text(encoding='utf-8'))
    registry['families'][0]['artifacts'] = []
    path = tmp_path / 'registry.json'; path.write_text(json.dumps(registry), encoding='utf-8')
    with pytest.raises(ValueError, match='unclassified'):
        collect_audit(ROOT, path)


def test_audit_cli_smoke() -> None:
    import subprocess
    import sys
    run = subprocess.run(
        [sys.executable, str(ROOT / "scripts/audit_documentation.py"), "--help"],
        cwd=ROOT, capture_output=True, text=True, timeout=120,
    )
    assert run.returncode == 0 and "--out" in run.stdout and "--links" in run.stdout

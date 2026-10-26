"""Meaningful boundary checks for the restricted independent-review intake."""
from __future__ import annotations

import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

import prepare_a04_handoff as p

SPEC = importlib.util.spec_from_file_location("intake_verifier", p.BASE / "a04-handoff-source/verify_package.py")
v = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(v)


def fixture() -> tuple[list, list, list]:
    """Build synthetic complete memberships without reading historical decisions."""
    works, metadata = [], []
    for n in range(372):
        members = []
        for j in range(18 if n == 0 else 1):
            source_id = f"https://arxiv.org/abs/2501.{n * 18 + j:05d}v1"
            members.append({"source": "arxiv", "source_id": source_id})
            metadata.append({
                "source": "arxiv", "source_id": source_id, "doi": "", "published": "2025-01-01T00:00:00Z",
                "updated": "2025-01-01T00:00:00Z", "year": "", "month": "",
                "title": "WITHHELD_TITLE_FINDING", "normalized_title": "withheld title finding",
                "abstract": "FORBIDDEN_RESULT_PROSE", "disposition": "FORBIDDEN_OLD_DECISION",
            })
        works.append({"work_id": f"arxiv:2501.{n:05d}", "identifiers": [f"arxiv:2501.{n:05d}"],
                      "members": members, "domain_eligibility": "FORBIDDEN_OLD_DECISION",
                      "version_selection": "FORBIDDEN_OLD_DECISION"})
    sentinels = [{"work_id": f"arxiv:2401.{n:05d}", "exclude_versions": "ALL",
                  "title_or_context_label": "FORBIDDEN_SENTINEL_FINDING",
                  "source_urls": ["https://example.invalid/FORBIDDEN_RESULT_PROSE"],
                  "prior_exposure_basis": "FORBIDDEN_RESULT_PROSE"} for n in range(65)]
    return works, metadata, sentinels


class HandoffChecks(unittest.TestCase):
    def setUp(self) -> None:
        temp_parent = Path(p.git("rev-parse", "--show-toplevel")) / ".venv/a04-handoff-tests"
        temp_parent.mkdir(parents=True, exist_ok=True)
        self.temp = tempfile.TemporaryDirectory(dir=temp_parent)
        if not Path(self.temp.name).resolve().is_relative_to(temp_parent.resolve()):
            raise ValueError("Test cleanup target is outside its intended workspace")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.works, self.metadata, self.sentinels = fixture()
        inventory, reviews, sentinels, _ = p.project(self.works, self.metadata, self.sentinels)
        self.files = {name: (p.BASE / "a04-handoff-source" / name).read_bytes() for name in p.STATIC}
        self.files.update({"CANDIDATE_INVENTORY.json": p.canonical(inventory),
                           "ELIGIBILITY_REVIEW_BLANK.json": p.canonical(reviews),
                           "SENTINEL_IDENTIFIERS.json": p.canonical(sentinels)})
        self.write()

    def write(self) -> None:
        for name, content in self.files.items():
            (self.root / name).write_bytes(content)
        (self.root / "MANIFEST.json").write_bytes(p.canonical({
            "files": {name: p.digest(content) for name, content in self.files.items()},
            "independent_review": "NOT_STARTED", "draw": "BLOCKED"}))

    def change_json(self, name: str, edit) -> None:
        value = json.loads(self.files[name])
        edit(value)
        self.files[name] = p.canonical(value)
        self.write()

    def test_complete_blank_package_passes(self) -> None:
        self.assertEqual(v.verify(self.root)["members"], 389)

    def test_previous_judgments_titles_abstracts_and_exposures_not_copied(self) -> None:
        for filename in ("CANDIDATE_INVENTORY.json", "ELIGIBILITY_REVIEW_BLANK.json", "SENTINEL_IDENTIFIERS.json"):
            for forbidden in (b"FORBIDDEN", b"WITHHELD_TITLE_FINDING", b"withheld title finding"):
                self.assertNotIn(forbidden, self.files[filename])

    def test_input_membership_duplication_rejected(self) -> None:
        self.works[1]["members"] = self.works[0]["members"]
        with self.assertRaisesRegex(ValueError, "membership"):
            p.project(self.works, self.metadata, self.sentinels)

    def test_extra_openreview_source_rejected(self) -> None:
        self.metadata[0]["source"] = "openreview"
        with self.assertRaisesRegex(ValueError, "out-of-frame"):
            p.project(self.works, self.metadata, self.sentinels)

    def test_result_bearing_extra_file_rejected(self) -> None:
        (self.root / "previous_judgments.json").write_text("{}", encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "Unexpected"):
            v.verify(self.root)

    def test_tampered_bytes_rejected(self) -> None:
        (self.root / "READ_FIRST.md").write_bytes(b"changed")
        with self.assertRaisesRegex(ValueError, "Hash mismatch"):
            v.verify(self.root)

    def test_fabricated_review_rejected_even_with_updated_hash(self) -> None:
        self.change_json("ELIGIBILITY_REVIEW_BLANK.json", lambda x: x[0].update(decision="INCLUDE"))
        with self.assertRaisesRegex(ValueError, "not blank"):
            v.verify(self.root)

    def test_fabricated_freshness_attestation_rejected(self) -> None:
        self.change_json("REVIEWER_INTAKE_BLANK.json", lambda x: x.update(status="FRESH"))
        with self.assertRaisesRegex(ValueError, "not blank"):
            v.verify(self.root)

    def test_extra_source_prose_field_rejected_even_with_updated_hash(self) -> None:
        self.change_json("CANDIDATE_INVENTORY.json", lambda x: x[0].update(abstract="result"))
        with self.assertRaisesRegex(ValueError, "Unexpected work"):
            v.verify(self.root)

    def test_missing_member_rejected(self) -> None:
        self.change_json("CANDIDATE_INVENTORY.json", lambda x: x[0]["members"].pop())
        with self.assertRaisesRegex(ValueError, "membership"):
            v.verify(self.root)

    def test_draw_status_cannot_be_unblocked(self) -> None:
        manifest = json.loads((self.root / "MANIFEST.json").read_text(encoding="utf-8"))
        manifest["draw"] = "APPROVED"
        (self.root / "MANIFEST.json").write_bytes(p.canonical(manifest))
        with self.assertRaisesRegex(ValueError, "gate"):
            v.verify(self.root)


if __name__ == "__main__":
    unittest.main(verbosity=2)

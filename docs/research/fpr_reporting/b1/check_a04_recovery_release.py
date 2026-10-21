"""Adversarial provenance and boundary checks for recovery release."""
from __future__ import annotations

import copy
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import fitz

import a04_evidence as e
import a04_recovery_release as r
import a04_semantic_release as s


class SupportChecks(unittest.TestCase):
    def setUp(self) -> None:
        self.row = {"criterion_support": {k: {"reused_evidence_ids": [], "new_fact_ids": [],
                    "further_controlled_evidence_needed": True, "limitation_codes": ["UNRESOLVED_METHOD_CONTEXT"]}
                    for k in r.METHOD_CRITERIA}}

    def test_maps_and_lists_preserve_explicit_uncertainty(self) -> None:
        expected = r.supports(self.row)
        row = {"criterion_support": [{"criterion": k, **v} for k, v in expected.items()]}
        self.assertEqual(r.supports(row), expected)
        self.assertTrue(all(x['further_controlled_evidence_needed'] for x in expected.values()))

    def test_missing_duplicate_extra_and_wrong_type_rejected(self) -> None:
        for mutation in ("missing", "duplicate", "extra", "type"):
            row = copy.deepcopy(self.row)
            key = next(iter(r.METHOD_CRITERIA))
            if mutation == "missing":
                del row['criterion_support'][key]
            elif mutation == "duplicate":
                row['criterion_support'] = [{"criterion": k, **v} for k, v in row['criterion_support'].items()]
                row['criterion_support'].append(row['criterion_support'][0])
            elif mutation == "extra":
                row['criterion_support'][key]['eligibility_decision'] = 'INCLUDE'
            else:
                row['criterion_support'][key]['further_controlled_evidence_needed'] = 'yes'
            with self.subTest(mutation=mutation), self.assertRaises(ValueError):
                r.supports(row)

    def test_findings_cannot_enter_limitation_code(self) -> None:
        with self.assertRaises(ValueError):
            r.codes(['accuracy improves'])
        self.assertFalse(r.utc('2026-10-21T13:00:00+05:30'))
        self.assertFalse(r.utc(None))
        self.assertTrue(r.utc('2026-10-21T07:00:00Z'))

    def test_transfer_projections_strip_private_cache_paths(self) -> None:
        binding = {'body': {'raw_path': 'private', 'sha256': 'hash'}, 'member_id': 'M0001'}
        self.assertNotIn('private', str(r.public_binding(binding)))
        bib = {'provenance': {'attempts': [{'raw_path': 'private', 'raw_source_sha256': 'hash'}]}}
        self.assertNotIn('private', str(r.public_bibliography(bib)))


class FactChecks(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory(dir=Path('.venv/a04-recovery-tests'))
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.path = self.root / 'primary.html'
        text = 'The detector classifies untrusted instructions before the target answers.'
        raw = ('<section id="S3"><p class="ltx_p">' + text + '</p></section>').encode()
        self.path.write_bytes(raw)
        self.actor = s.ACTORS['01']
        self.row = {'actor_id': self.actor, 'context_checked_member_ids': ['M0001']}
        self.binding = {'member_id': 'M0001', 'method_release_supported': True, 'captured_version_id': 'arxiv:2501.00001v1',
                        'body': {'raw_path': str(self.path), 'sha256': e.sha(raw), 'url': 'https://arxiv.org/html/2501.00001v1', 'kind': 'HTML'}}
        stamp = '2026-10-21T07:00:00+00:00'
        self.fact = {'fact_id': 'fixture', 'member_id': 'M0001', 'fact_kind': 'PRE_TARGET_TIMING',
                     'method_fact': text, 'source_url': self.binding['body']['url'], 'version': 'arxiv:2501.00001v1',
                     'raw_source_sha256': e.sha(raw), 'restriction_checked_by': self.actor, 'checked_utc': stamp,
                     'limitation': 'Method chronology only.',
                     'second_local_semantic_pass': {'actor_id': self.actor, 'checked_utc': stamp, 'status': 'CHECKED', 'literal_quotation_words': 0},
                     'addresses_criteria': ['before_target_answer'], 'experiment_scope': 'input detector',
                     'source_binding_basis': 'EXACT_VERSION_SELF_LINK',
                     'locator': {'format': 'HTML', 'evidence_paragraphs': [{'global_p_ltx_p_ordinal': 0, 'section_id': 'S3', 'paragraph_text_sha256': e.sha(text.encode())}]}}

    def test_actual_paragraph_hash_and_context_required(self) -> None:
        self.assertEqual(r.validate_fact(self.fact, self.row, self.binding), [])
        self.fact['locator']['evidence_paragraphs'][0]['section_id'] = 'S4'
        self.assertIn('HTML_PARAGRAPH_HASH_OR_SECTION_CHANGED', r.validate_fact(self.fact, self.row, self.binding))

    def test_unavailable_or_unchecked_source_cannot_release(self) -> None:
        self.binding['method_release_supported'] = False
        self.assertTrue(r.validate_fact(self.fact, self.row, self.binding))
        self.binding['method_release_supported'] = True
        self.row['context_checked_member_ids'] = []
        self.assertTrue(r.validate_fact(self.fact, self.row, self.binding))

    def test_different_version_actor_or_criterion_rejected(self) -> None:
        for field, value in [('version', 'arxiv:2501.00001v2'), ('restriction_checked_by', '/root'), ('addresses_criteria', ['accuracy'])]:
            fact = copy.deepcopy(self.fact)
            fact[field] = value
            with self.subTest(field=field):
                self.assertTrue(r.validate_fact(fact, self.row, self.binding))

    def test_findings_numbers_and_unattested_second_pass_quarantined(self) -> None:
        for field, value in [('method_fact', 'The detector achieves superior accuracy.'), ('method_fact', 'The corpus has 100 samples.'),
                             ('experiment_scope', 'best performance'), ('second_local_semantic_pass', {})]:
            fact = copy.deepcopy(self.fact)
            fact[field] = value
            with self.subTest(field=field):
                self.assertTrue(r.validate_fact(fact, self.row, self.binding))

    def test_optional_proof_mismatch_cannot_be_ignored(self) -> None:
        self.fact['source_binding_receipt_sha256'] = '0' * 64
        self.binding['member_id'] = 'M0001'
        self.assertIn('OPTIONAL_SOURCE_PROOF_COMMITMENT_CHANGED', r.validate_optional_proofs(self.fact, self.binding))

    def test_unsupported_extra_field_cannot_leak(self) -> None:
        self.fact['performance_note'] = 'Superior results'
        self.assertIn('UNEXPECTED_RECOVERY_FACT_FIELDS', r.validate_fact(self.fact, self.row, self.binding))

    def test_tables_abstracts_and_wrong_paragraph_hash_are_rejected(self) -> None:
        raw = b'<section id="S3"><table><p class="ltx_p">The method classifies inputs.</p></table></section>'
        self.path.write_bytes(raw)
        self.binding['body']['sha256'] = e.sha(raw)
        self.fact['raw_source_sha256'] = e.sha(raw)
        self.fact['locator']['evidence_paragraphs'][0]['paragraph_text_sha256'] = e.sha(b'The method classifies inputs.')
        self.assertIn('HTML_PROTECTED_SOURCE_CONTAINER', r.validate_fact(self.fact, self.row, self.binding))

    def test_pdf_actual_rgb_render_proof_and_private_path_guard(self) -> None:
        path = self.root / 'primary.pdf'
        with fitz.open() as pdf:
            pdf.new_page().insert_text((40, 60), 'Primary method chronology')
            path.write_bytes(pdf.tobytes())
        with fitz.open(path) as pdf:
            png = pdf[0].get_pixmap(matrix=fitz.Matrix(2, 2), alpha=False).tobytes('png')
            text_sha = e.sha(pdf[0].get_text().encode())
        image = self.root / 'page.png'
        image.write_bytes(png)
        body = {'raw_path': str(path), 'sha256': e.sha(path.read_bytes())}
        locator = {'format': 'PDF', 'method_section_locator': 'Methods page', 'evidence_pages': [{
            'page_number_1based': 1, 'page_text_sha256': text_sha, 'rendered_page_sha256': e.sha(png), 'rendered_page_path': str(image)}]}
        with patch.object(r.r, 'CACHE', self.root):
            self.assertEqual(r.pdf_locator(locator, body), [])
            image.write_bytes(b'changed')
            self.assertIn('PDF_RENDER_HASH_CHANGED', r.pdf_locator(locator, body))
        with patch.object(r.r, 'CACHE', self.root / 'other'), patch.object(r.e, 'read', return_value={'cache_root': str(self.root / 'other')}):
            self.assertIn('PDF_RENDER_OUTSIDE_APPROVED_CACHE', r.pdf_locator(locator, body))


if __name__ == '__main__':
    unittest.main(verbosity=2)

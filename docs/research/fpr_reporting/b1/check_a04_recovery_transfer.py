"""Reject transport corruption and accidental disclosure before delivery."""
import io
import json
import unittest
import zipfile
from pathlib import Path

import verify_a04_recovery_transfer as v


class ArchiveBoundaryChecks(unittest.TestCase):
    def test_expected_digest_is_checked_before_archive_parse(self):
        with self.assertRaisesRegex(ValueError, 'DIGEST_MISMATCH'):
            v.archive(b'not the authentic original', '0' * 64)

    def test_private_paths_and_prior_dispositions_rejected_recursively(self):
        for item in [{'x':[{'raw_path':'private'}]}, {'current_decision':'UNCLEAR'}, {'eligibility_decision':'INCLUDE'}]:
            with self.subTest(item=item), self.assertRaises(ValueError):
                v.private_keys(item)
        v.private_keys({'eligibility_decision':None, 'source_url':'https://arxiv.org/abs/2501.00001v1'})

    def test_manifest_does_not_allow_undeclared_payload(self):
        stream = io.BytesIO()
        with zipfile.ZipFile(stream,'w') as z:
            z.writestr('MANIFEST.json', json.dumps({'files':{}}))
            z.writestr('private-report.md','unrestricted text')
        with self.assertRaisesRegex(ValueError, 'FILE_COVERAGE'):
            v.archive(stream.getvalue())

    def test_path_traversal_and_duplicate_names_fail(self):
        for name in ('../outside','folder/raw'):
            stream = io.BytesIO()
            with zipfile.ZipFile(stream,'w') as z:
                z.writestr(name,'raw')
            with self.subTest(name=name), self.assertRaisesRegex(ValueError,'FLAT_UNIQUE'):
                v.archive(stream.getvalue())

    def test_public_pdf_locator_must_not_carry_render_path(self):
        page={'page_number_1based':1,'page_text_sha256':'a'*64,'rendered_page_sha256':'b'*64}
        locator={'format':'PDF','method_section_locator':'Methods','evidence_pages':[page]}
        self.assertTrue(v.public_locator(locator))
        page['rendered_page_path']='private'
        self.assertFalse(v.public_locator(locator))


class ActualFrozenTransferChecks(unittest.TestCase):
    def test_real_original_verifiers_and_recovery_contract(self):
        root=Path('docs/research/fpr_reporting/b1/a04-provisional-recovery-v1-20261021/transfer')
        if not root.exists():
            self.skipTest('Actual completed-role transfer not frozen yet; mandatory rerun after freeze')
        result=v.verify(root)
        self.assertEqual(result['verification'],'PASS')
        self.assertEqual(result['independent_eligibility_decisions'],0)
        self.assertEqual(len(result['original_archive_verifiers']),3)


if __name__=='__main__':
    unittest.main()

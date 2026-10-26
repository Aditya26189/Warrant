"""Reject transport corruption and accidental disclosure before delivery."""
import io
import json
import subprocess
import sys
import tempfile
import types
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
        process=subprocess.run([sys.executable,'-I',str((root/'verify_recovery.py').resolve())],capture_output=True,text=True,check=True)
        result=json.loads(process.stdout)
        self.assertEqual(result['verification'],'PASS')
        self.assertEqual(result['independent_eligibility_decisions'],0)
        self.assertEqual(len(result['original_archive_verifiers']),3)

    def test_rehashed_finding_is_rejected_by_actual_release_verifier(self):
        root=Path('docs/research/fpr_reporting/b1/a04-provisional-recovery-v1-20261021/transfer')
        if not root.exists():
            self.skipTest('Actual completed-role transfer not frozen yet; mandatory rerun after freeze')
        module=types.ModuleType('actual_recovery_verifier')
        exec(compile((root/'verify_recovery.py').read_bytes(),'actual_recovery_verifier','exec'),module.__dict__)
        with tempfile.TemporaryDirectory(dir=Path('.venv/a04-recovery-tests')) as temporary:
            copied=Path(temporary)
            for source in root.iterdir():
                (copied/source.name).write_bytes(source.read_bytes())
            files=module.archive((copied/'RECOVERY_CONTROLLED_EVIDENCE.zip').read_bytes())
            facts=json.loads(files['RECOVERY_METHOD_FACTS.json'])
            facts[0]['method_fact']='The detector achieves superior accuracy.'
            files['RECOVERY_METHOD_FACTS.json']=module.canonical(facts)
            manifest=json.loads(files['MANIFEST.json'])
            manifest['files']['RECOVERY_METHOD_FACTS.json']=module.sha(files['RECOVERY_METHOD_FACTS.json'])
            files['MANIFEST.json']=module.canonical(manifest)
            stream=io.BytesIO()
            with zipfile.ZipFile(stream,'w') as z:
                for name,raw in files.items():
                    z.writestr(name,raw)
            (copied/'RECOVERY_CONTROLLED_EVIDENCE.zip').write_bytes(stream.getvalue())
            outer=json.loads((copied/'MANIFEST.json').read_bytes())
            outer['files']['RECOVERY_CONTROLLED_EVIDENCE.zip']=module.sha(stream.getvalue())
            (copied/'MANIFEST.json').write_bytes(module.canonical(outer))
            with self.assertRaisesRegex(ValueError,'METHOD_BOUNDARY'):
                module.verify(copied,run_originals=False)


if __name__=='__main__':
    unittest.main()

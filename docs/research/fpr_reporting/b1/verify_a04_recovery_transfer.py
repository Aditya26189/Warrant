"""Offline verifier for the new recovery wrapper and unchanged original archives.

Run from the extracted wrapper with Python isolated mode. First verify the outer
ZIP SHA256 from the out-of-band delivery instruction. No synthetic archives or
hash overrides authenticate original transfers.
"""
from __future__ import annotations
import hashlib
import io
import json
import re
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path

PINS = {
    'FRESH_REVIEWER_INTAKE.zip': ('48c903779bda205c2af6231da92cca8b70e6ba9755cfa175f526c107e23e7290', 'verify_package.py'),
    'RESTRICTED_EVIDENCE_SUPPLEMENT.zip': ('066c27ae28ad941ea9ebf963f3fc5d854b2bcd39d1fb060a16b52b5cc4294c08', 'verify_evidence.py'),
    'CONSOLIDATED_RESTRICTED_EVIDENCE.zip': ('8158e43ee8ad8c55854aab59c526b979b7e5a89b23f804eb65b408b384621a71', 'verify_semantic.py'),
}
OUTER = set(PINS) | {'RECOVERY_CONTROLLED_EVIDENCE.zip', 'READ_FIRST_RECOVERY.md', 'verify_recovery.py'}
INNER = {'RECOVERY_METHOD_FACTS.json', 'RECOVERY_EVIDENCE_RECEIPTS.json', 'CONTROLLED_REQUEST_RESPONSES.json',
         'RECOVERY_SOURCE_BINDINGS.json', 'RECOVERY_IDENTITY_EVIDENCE.json', 'OFFICIAL_BIBLIOGRAPHIC_EVIDENCE.json',
         'REGISTERED_DOI_EVIDENCE.json', 'REGISTRATION_FOLLOWUP_EVIDENCE.json', 'BIBLIOGRAPHIC_CROSSLINKS.json',
         'SOURCE_GAP_REQUESTS.json', 'CHECKER_ROLE_RECEIPTS.json', 'README.md'}
METHOD_CRITERIA = {'input_injection_task', 'binary_evaluation', 'before_target_answer', 'english_evaluation'}
ACTORS = {'/root/a04_semantic_restriction', '/root/a04_semantic_restriction_02', '/root/a04_semantic_restriction_03'}
KINDS = {'INPUT_TASK', 'EVALUATION_UNIT', 'BINARY_PROCEDURE', 'PRE_TARGET_TIMING', 'ENGLISH_EVALUATION', 'DATASET_PROVENANCE', 'METHOD_BOUNDARY'}
OUTCOME = re.compile('__OUTCOME_PATTERN__', re.I)
SPELLED = re.compile('__SPELLED_COUNT_PATTERN__', re.I)
SAFE_LIMITATION = '__SAFE_LIMITATION__'
FACT_FIELDS = {'evidence_id', 'review_id', 'work_id', 'member_id', 'fact_kind', 'method_fact', 'source_url', 'version',
               'raw_source_sha256', 'restriction_checked_by', 'checked_utc', 'limitation', 'addresses_criteria', 'experiment_scope',
               'locator', 'source_binding_evidence_id', 'source_binding_basis', 'source_checker_record_sha256', 'eligibility_decision'}


def sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def canonical(value: object) -> bytes:
    return (json.dumps(value, ensure_ascii=True, sort_keys=True, indent=2) + '\n').encode()


def archive(raw: bytes, expected: str | None = None) -> dict:
    """Require original bytes first and safe exact file/manifest coverage."""
    if expected is not None and sha(raw) != expected:
        raise ValueError('ARCHIVE_DIGEST_MISMATCH')
    with zipfile.ZipFile(io.BytesIO(raw)) as zipped:
        names = zipped.namelist()
        if len(names) != len(set(names)) or any(Path(n).name != n or n in {'.', '..'} for n in names):
            raise ValueError('ARCHIVE_NOT_FLAT_UNIQUE')
        if zipped.testzip():
            raise ValueError('ARCHIVE_CRC_FAILURE')
        files = {n: zipped.read(n) for n in names}
    manifest = json.loads(files['MANIFEST.json'])
    if set(files) != set(manifest['files']) | {'MANIFEST.json'}:
        raise ValueError('MANIFEST_FILE_COVERAGE')
    if any(sha(files[n]) != digest for n, digest in manifest['files'].items()):
        raise ValueError('MANIFEST_FILE_HASH')
    return files


def private_keys(value: object) -> None:
    """Reject custodian cache paths and review-status fields from public evidence."""
    if isinstance(value, dict):
        if set(value) & {'raw_path', 'rendered_page_path', 'source_binding_path', 'current_decision', 'current_status', 'decision'}:
            raise ValueError('PRIVATE_OR_PRIOR_DECISION_FIELD')
        if 'eligibility_decision' in value and value['eligibility_decision'] is not None:
            raise ValueError('ELIGIBILITY_DECISION_NOT_BLANK')
        for item in value.values():
            private_keys(item)
    elif isinstance(value, list):
        for item in value:
            private_keys(item)


def public_locator(value: dict) -> bool:
    digest = lambda x: isinstance(x, str) and re.fullmatch(r'[0-9a-f]{64}', x)
    if value.get('format') == 'HTML':
        return set(value) == {'format', 'evidence_paragraphs'} and bool(value['evidence_paragraphs']) and all(
            set(x) == {'global_p_ltx_p_ordinal', 'section_id', 'paragraph_text_sha256'}
            and type(x['global_p_ltx_p_ordinal']) is int and x['global_p_ltx_p_ordinal'] >= 0
            and digest(x['paragraph_text_sha256']) for x in value['evidence_paragraphs'])
    if value.get('format') == 'PDF':
        return set(value) == {'format', 'evidence_pages', 'method_section_locator'} and bool(value['evidence_pages']) and all(
            set(x) == {'page_number_1based', 'page_text_sha256', 'rendered_page_sha256'}
            and type(x['page_number_1based']) is int and x['page_number_1based'] >= 1
            and digest(x['page_text_sha256']) and digest(x['rendered_page_sha256']) for x in value['evidence_pages'])
    return False


def verify(root: Path, run_originals: bool = True) -> dict:
    """Validate preparation only; no assertion of actual delivery or independence."""
    names = {x.name for x in root.iterdir()}
    if names != OUTER | {'MANIFEST.json'} or any(not x.is_file() or x.is_symlink() for x in root.iterdir()):
        raise ValueError('OUTER_FILE_ALLOWLIST')
    manifest = json.loads((root / 'MANIFEST.json').read_bytes())
    if set(manifest['files']) != OUTER or any(sha((root / n).read_bytes()) != digest for n, digest in manifest['files'].items()):
        raise ValueError('OUTER_MANIFEST_OR_HASH')
    originals = {name: archive((root / name).read_bytes(), pin[0]) for name, pin in PINS.items()}
    if originals['CONSOLIDATED_RESTRICTED_EVIDENCE.zip']['BASE_EVIDENCE_SUPPLEMENT.zip'] != (root / 'RESTRICTED_EVIDENCE_SUPPLEMENT.zip').read_bytes():
        raise ValueError('ORIGINAL_NESTED_BASE_NOT_IDENTICAL')
    checks = []
    if run_originals:
        with tempfile.TemporaryDirectory(prefix='warrant-authentic-originals-') as temporary:
            for index, (name, (_, script)) in enumerate(PINS.items()):
                directory = Path(temporary) / str(index)
                directory.mkdir()
                for filename, raw in originals[name].items():
                    (directory / filename).write_bytes(raw)
                process = subprocess.run([sys.executable, '-I', str(directory / script)], cwd=directory,
                                         capture_output=True, text=True, timeout=120)
                if process.returncode:
                    raise ValueError('ORIGINAL_UNMODIFIED_VERIFIER_FAILED:' + name + ':' + process.stderr[:500])
                checks.append({'archive': name, 'verifier': script, 'exit_code': process.returncode})
    files = archive((root / 'RECOVERY_CONTROLLED_EVIDENCE.zip').read_bytes())
    if set(files) != INNER | {'MANIFEST.json'}:
        raise ValueError('RECOVERY_FILE_ALLOWLIST')
    data = {n: json.loads(raw) for n, raw in files.items() if n.endswith('.json') and n != 'MANIFEST.json'}
    for value in data.values():
        private_keys(value)
    inventory = json.loads(originals['FRESH_REVIEWER_INTAKE.zip']['CANDIDATE_INVENTORY.json'])
    crosswalk = json.loads(originals['RESTRICTED_EVIDENCE_SUPPLEMENT.zip']['SENTINEL_IDENTIFIER_CROSSWALK.json'])
    exact_all = {x['review_id'] for x in crosswalk if any(m['exclude_versions'] == 'ALL' for m in x['exact_identifier_matches'])}
    work = {x['review_id']: x for x in inventory if x['review_id'] not in exact_all}
    if len(work) != 367 or len(exact_all) != 5:
        raise ValueError('REQUEST_UNIVERSE_CHANGED')
    responses = data['CONTROLLED_REQUEST_RESPONSES.json']
    gaps = data['SOURCE_GAP_REQUESTS.json']
    if len(responses) != 367 or len(gaps) != 367 or {x['review_id'] for x in responses} != set(work) or {x['review_id'] for x in gaps} != set(work):
        raise ValueError('CONTROLLED_REQUEST_COVERAGE')
    old = {x['evidence_id']: x for x in json.loads(originals['CONSOLIDATED_RESTRICTED_EVIDENCE.zip']['SEMANTIC_METHOD_FACTS.json'])}
    facts = data['RECOVERY_METHOD_FACTS.json']
    new = {x['evidence_id']: x for x in facts}
    if len(new) != len(facts):
        raise ValueError('RECOVERY_FACT_ID_DUPLICATED')
    bindings = {x['member_id']: x for x in data['RECOVERY_SOURCE_BINDINGS.json']}
    if len(bindings) != 384 or sum(len(x['members']) for x in work.values()) != 384:
        raise ValueError('MEMBERSHIP_UNIVERSE_CHANGED')
    word_counts = {}
    for fact in facts:
        if (set(fact) != FACT_FIELDS or fact['restriction_checked_by'] not in ACTORS
                or fact['eligibility_decision'] is not None or fact['fact_kind'] not in KINDS):
            raise ValueError('RECOVERY_FACT_FIELDS_OR_ACTOR')
        if fact['review_id'] not in work or fact['work_id'] != work[fact['review_id']]['work_id']:
            raise ValueError('RECOVERY_FACT_WORK_FOREIGN_KEY')
        binding = bindings[fact['member_id']]
        expected_version = binding['captured_version_id'] or 'acl:' + binding['body']['url'].rsplit('/',1)[-1].removesuffix('.pdf') + ':publication'
        if (fact['member_id'] not in {m['member_id'] for m in work[fact['review_id']]['members']}
                or binding['review_id'] != fact['review_id'] or binding['work_id'] != fact['work_id']
                or fact['version'].removeprefix('arxiv:') != expected_version.removeprefix('arxiv:')
                or not binding['method_release_supported'] or fact['raw_source_sha256'] != binding['body']['sha256']
                or fact['source_url'] != binding['body']['url'] or not public_locator(fact['locator'])
                or fact['source_binding_evidence_id'] != binding['evidence_id']):
            raise ValueError('RECOVERY_FACT_SOURCE_BINDING')
        if (not set(fact['addresses_criteria']).issubset(METHOD_CRITERIA) or not fact['addresses_criteria']
                or any(OUTCOME.search(fact[k]) or SPELLED.search(fact[k]) for k in ('method_fact', 'experiment_scope'))
                or fact['limitation'] != SAFE_LIMITATION and (OUTCOME.search(fact['limitation']) or SPELLED.search(fact['limitation']))):
            raise ValueError('RECOVERY_METHOD_BOUNDARY')
        word_counts[fact['review_id']] = word_counts.get(fact['review_id'], 0) + len(fact['method_fact'].split())
        if word_counts[fact['review_id']] > 180:
            raise ValueError('METHOD_DISPLAY_BOUND')
    receipts = data['RECOVERY_EVIDENCE_RECEIPTS.json']
    if len(receipts) != len(new) or {x['evidence_id'] for x in receipts} != set(new):
        raise ValueError('RECOVERY_RECEIPT_COVERAGE')
    for receipt in receipts:
        fact = new[receipt['evidence_id']]
        if receipt['restricted_evidence_sha256'] != sha(canonical(fact)) or receipt['reviewer_received_utc'] is not None:
            raise ValueError('RECOVERY_RECEIPT_HASH_OR_DELIVERY')
        if receipt['restriction_checked_by'] != fact['restriction_checked_by']:
            raise ValueError('RECOVERY_RECEIPT_ACTOR')
    gap_by_id = {x['review_id']: x for x in gaps}
    criteria_count = 0
    for row in responses:
        rid = row['review_id']
        req = gap_by_id[rid]
        expected_members = {m['member_id'] for m in work[rid]['members']}
        if (row['request_id'] != req['request_id'] or row['work_id'] != work[rid]['work_id']
                or set(row['member_ids']) != expected_members or not set(row['context_checked_member_ids']).issubset(expected_members)
                or row['source_restriction_checker'] not in ACTORS or row['evidence_delivered'] or row['independent_review_completed']):
            raise ValueError('RECOVERY_RESPONSE_IDENTITY_OR_COMPLETION')
        for eid in row['reused_evidence_ids']:
            if eid not in old or old[eid]['work_id'] != row['work_id']:
                raise ValueError('RECOVERY_REUSED_REFERENCE')
        for eid in row['new_evidence_ids']:
            if eid not in new or new[eid]['work_id'] != row['work_id']:
                raise ValueError('RECOVERY_NEW_REFERENCE')
        criteria = row['criterion_evidence']
        if len(criteria) != len(req['controlled_requests']) or {x['criterion'] for x in criteria} != {x['criterion'] for x in req['controlled_requests']}:
            raise ValueError('RECOVERY_CRITERION_COVERAGE')
        criteria_count += len(criteria)
        if any(x['criterion_satisfaction_decision'] is not None for x in criteria):
            raise ValueError('CRITERION_DECISION_NOT_BLANK')
        for criterion in criteria:
            if criterion['criterion'] in METHOD_CRITERIA:
                if (not set(criterion['reused_evidence_ids']).issubset(row['reused_evidence_ids'])
                        or not set(criterion['new_evidence_ids']).issubset(row['new_evidence_ids'])
                        or type(criterion['further_controlled_evidence_needed']) is not bool
                        or any(criterion['criterion'] not in new[eid]['addresses_criteria'] for eid in criterion['new_evidence_ids'])):
                    raise ValueError('CRITERION_EVIDENCE_LINK_NOT_ATTESTED')
    if criteria_count != 1852:
        raise ValueError('CRITERION_REQUEST_COUNT_CHANGED')
    if len(data['OFFICIAL_BIBLIOGRAPHIC_EVIDENCE.json']) != 384:
        raise ValueError('OFFICIAL_BIBLIOGRAPHY_COVERAGE')
    roles = data['CHECKER_ROLE_RECEIPTS.json']
    if {x['actor_id'] for x in roles} != ACTORS or not all(x['actual_completion_report_received'] and x['shared_filesystem']
        and not x['os_isolation_claimed'] and not x['eligibility_review_claimed'] for x in roles):
        raise ValueError('ACTUAL_RESTRICTION_ROLE_COMPLETION_REQUIRED')
    return {'verification': 'PASS', 'original_archive_verifiers': checks, 'requested_works': 367,
            'requested_memberships': 384, 'criterion_responses': criteria_count, 'new_method_facts': len(facts),
            'original_semantic_facts': len(old), 'independent_eligibility_decisions': 0,
            'actual_delivery_attested_by_this_check': False, 'gate': 'FRAME_BLOCKED'}


if __name__ == '__main__':
    print(json.dumps(verify(Path(__file__).resolve().parent), sort_keys=True))

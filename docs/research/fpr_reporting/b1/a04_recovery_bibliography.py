"""Verify already-linked DOI metadata; never discover additional candidates."""
from __future__ import annotations

import concurrent.futures
import json
import re
import urllib.error
import urllib.parse
import urllib.request

import a04_evidence as e
import a04_recovery_intake as r
import a04_recovery_sources as sources


def registered_fields(message: dict, expected_doi: str) -> dict:
    """Project registration dates/identifiers, excluding abstracts and all findings."""
    if message.get('DOI', '').casefold() != expected_doi.casefold():
        raise ValueError('REGISTERED_DOI_IDENTITY_MISMATCH')
    dates = {}
    for key in ('published', 'published-print', 'published-online', 'issued', 'created', 'deposited', 'indexed'):
        value = message.get(key)
        if isinstance(value, dict):
            dates[key] = {k: v for k, v in value.items() if k in {'date-parts', 'date-time', 'timestamp'}}
    authors = [{k: e.sha(str(v).encode()) for k, v in x.items() if k in {'given', 'family', 'ORCID'}} for x in message.get('author', [])]
    relation = []
    for kind, rows in message.get('relation', {}).items():
        if not re.fullmatch(r'[a-z-]+', kind):
            continue
        for row in rows:
            if row.get('id-type') == 'doi' and re.fullmatch(r'10\.\d{4,9}/[^\s<>]+', row.get('id', '')):
                relation.append({'relation_kind': kind, 'doi': row['id']})
    return {'doi': message['DOI'], 'registration_agency': 'Crossref', 'publication_type': message.get('type'),
            'date_fields': dates, 'title_sha256': [e.sha(x.encode()) for x in message.get('title', [])],
            'title_identity_sha256': [e.sha(sources.identity_text(x).encode()) for x in message.get('title', [])],
            'author_field_sha256': authors, 'related_doi_identifiers': relation,
            'publication_container_sha256': [e.sha(x.encode()) for x in message.get('container-title', [])],
            'preferred_version_decision': None,
            'limitation_codes': ['REGISTRATION_DATES_ARE_NOT_PROOF_OF_PUBLIC_AVAILABILITY', 'REGISTERED_RELATIONS_ARE_NOT_NEW_CANDIDATES']}


def one(doi: str, members: list[str], head: str) -> dict:
    """Capture one bounded official registration response, preserving failures."""
    path = r.CACHE / 'doi-metadata' / (e.sha(doi.encode()) + '.json')
    if path.exists():
        row = e.read(path)
        if row['doi'] != doi or row['member_ids'] != members:
            raise ValueError('DOI_RESUME_INPUT_CHANGED')
        raw_path = row['provenance'].get('raw_path')
        if raw_path and e.sha(__import__('pathlib').Path(raw_path).read_bytes()) != row['provenance']['raw_source_sha256']:
            raise ValueError('DOI_RESPONSE_HASH_CHANGED')
        return row
    url = 'https://api.crossref.org/works/' + urllib.parse.quote(doi, safe='')
    provenance = {'source_url': url, 'started_utc': e.now(), 'raw_source_sha256': None}
    fields = None
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Warrant-controlled-bibliographic-verification/1.0'})
        with urllib.request.urlopen(req, timeout=25) as response:
            if response.url != url:
                raise ValueError('UNAPPROVED_DOI_API_REDIRECT')
            raw = response.read(5000001)
            if len(raw) > 5000000:
                raise ValueError('DOI_METADATA_BODY_TOO_LARGE')
            provenance['http_status'] = response.status
        payload = json.loads(raw)
        fields = registered_fields(payload['message'], doi)
        digest = e.sha(raw)
        raw_path = r.CACHE / 'doi-raw' / digest
        raw_path.parent.mkdir(parents=True, exist_ok=True)
        if raw_path.exists() and raw_path.read_bytes() != raw:
            raise ValueError('DOI_RAW_HASH_COLLISION')
        if not raw_path.exists():
            raw_path.write_bytes(raw)
        provenance.update(raw_source_sha256=digest, raw_path=str(raw_path))
    except (OSError, ValueError, KeyError) as exc:
        provenance.update(error_type=type(exc).__name__, http_status=getattr(exc, 'code', None))
    provenance['finished_utc'] = e.now()
    row = {'evidence_id': 'R01-DOI-' + e.sha(doi.encode())[:16], 'doi': doi, 'member_ids': members,
           'source_git_commit': head, 'provenance': provenance, 'registered_fields': fields,
           'eligibility_decision': None, 'selected_protocol_preferred_version': None}
    e.write_new(path, row)
    return row


def main() -> None:
    """Use only DOI links from captured official records or original metadata."""
    head = e.clean_head()
    e.baseline(e.read(e.CONFIG))
    original, metadata = sources.inputs()
    by_doi = {}
    for row in e.read(e.BASE / r.RUN / 'OFFICIAL_BIBLIOGRAPHIC_EVIDENCE.json'):
        for identifier in row['official_fields']['linked_identifiers']:
            by_doi.setdefault(identifier.removeprefix('doi:').casefold(), set()).add(row['member_id'])
    for req in original:
        doi = metadata[req['member_id']]['doi']
        if doi and re.fullmatch(r'10\.\d{4,9}/[^\s<>]+', doi):
            by_doi.setdefault(doi.casefold(), set()).add(req['member_id'])
    rows = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
        futures = [pool.submit(one, doi, sorted(members), head) for doi, members in sorted(by_doi.items())]
        for n, future in enumerate(concurrent.futures.as_completed(futures), 1):
            row = future.result()
            rows.append(row)
            print(json.dumps({'completed': n, 'total': len(futures), 'metadata_available': row['registered_fields'] is not None}), flush=True)
    e.write_new(e.BASE / r.RUN / 'REGISTERED_DOI_EVIDENCE_CUSTODIAN.json', sorted(rows, key=lambda x: x['doi']))


if __name__ == '__main__':
    main()

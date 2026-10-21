"""Bounded official followups for known DOI registration access gaps."""
from __future__ import annotations
import json
import urllib.error
import urllib.parse
import urllib.request

import a04_evidence as e
import a04_recovery_intake as r
import a04_recovery_sources as sources


def datacite_fields(attributes: dict, doi: str) -> dict:
    """Retain official dates and hashes, never abstracts or descriptive outcomes."""
    if attributes.get('doi', '').casefold() != doi.casefold():
        raise ValueError('DATACITE_DOI_IDENTITY_MISMATCH')
    return {'doi': attributes['doi'], 'registration_agency': 'DataCite',
            'publication_year': attributes.get('publicationYear'),
            'date_fields': {k: attributes.get(k) for k in ('created', 'registered', 'published', 'updated')},
            'dated_events': [{k: x[k] for k in ('date', 'dateType') if k in x} for x in attributes.get('dates', [])],
            'title_identity_sha256': [e.sha(sources.identity_text(x['title']).encode()) for x in attributes.get('titles', [])],
            'preferred_version_decision': None,
            'limitation_codes': ['REGISTERED_RESOURCE_METADATA_NOT_PROTOCOL_VERSION_DECISION']}


def main() -> None:
    """Follow only the four recorded failures, without modifying their receipts."""
    head = e.clean_head()
    rows = []
    for item in e.read(e.BASE / r.RUN / 'REGISTERED_DOI_EVIDENCE_CUSTODIAN.json'):
        if item['registered_fields'] is not None:
            continue
        doi = item['doi']
        if doi.startswith('10.5281/'):
            url = 'https://api.datacite.org/dois/' + urllib.parse.quote(doi, safe='/')
            kind = 'DATACITE'
        elif doi.startswith('10.1145/'):
            url = 'https://dl.acm.org/doi/' + doi
            kind = 'PUBLISHER_CITATION_METADATA'
        else:
            raise ValueError('UNPLANNED_REGISTRATION_GAP')
        path = r.CACHE / 'registration-followup' / (e.sha(doi.encode()) + '.json')
        if path.exists():
            row = e.read(path)
            if row['source_url'] != url:
                raise ValueError('REGISTRATION_FOLLOWUP_INPUT_CHANGED')
            if row.get('raw_path') and e.sha(__import__('pathlib').Path(row['raw_path']).read_bytes()) != row['raw_source_sha256']:
                raise ValueError('REGISTRATION_FOLLOWUP_RAW_CHANGED')
        else:
            row = {'evidence_id': 'R01-DOI-FOLLOWUP-' + e.sha(doi.encode())[:16],
                   'doi': doi, 'member_ids': item['member_ids'], 'source_url': url, 'source_kind': kind,
                   'prior_receipt_sha256': e.sha(e.encoded(item)), 'started_utc': e.now(), 'source_git_commit': head,
                   'raw_source_sha256': None, 'official_fields': None, 'eligibility_decision': None}
            try:
                req = urllib.request.Request(url, headers={'User-Agent': 'Warrant-controlled-bibliographic-verification/1.0'})
                with urllib.request.urlopen(req, timeout=25) as response:
                    if response.url != url:
                        raise ValueError('UNAPPROVED_REGISTRATION_REDIRECT')
                    raw = response.read(5000001)
                    if len(raw) > 5000000:
                        raise ValueError('REGISTRATION_BODY_TOO_LARGE')
                    row['http_status'] = response.status
                fields = datacite_fields(json.loads(raw)['data']['attributes'], doi) if kind == 'DATACITE' else sources.bibliographic_fields(raw, 'acl')
                digest = e.sha(raw)
                raw_path = r.CACHE / 'registration-followup-raw' / digest
                raw_path.parent.mkdir(parents=True, exist_ok=True)
                if not raw_path.exists():
                    raw_path.write_bytes(raw)
                elif raw_path.read_bytes() != raw:
                    raise ValueError('REGISTRATION_BODY_HASH_COLLISION')
                row.update(raw_source_sha256=digest, raw_path=str(raw_path), official_fields=fields)
            except (OSError, ValueError, KeyError) as exc:
                row.update(error_type=type(exc).__name__, http_status=getattr(exc, 'code', None))
            row['finished_utc'] = e.now()
            e.write_new(path, row)
        rows.append(row)
        print(json.dumps({'doi': doi, 'available': row['official_fields'] is not None}), flush=True)
    e.write_new(e.BASE / r.RUN / 'REGISTRATION_FOLLOWUP_CUSTODIAN.json', rows)


if __name__ == '__main__':
    main()

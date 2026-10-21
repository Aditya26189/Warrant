"""Registration metadata must remain bibliographic and identity-bound."""
import unittest
import a04_recovery_bibliography as b


class RegisteredMetadataChecks(unittest.TestCase):
    def test_wrong_doi_is_not_an_alias(self):
        with self.assertRaisesRegex(ValueError, 'IDENTITY_MISMATCH'):
            b.registered_fields({'DOI': '10.1000/other'}, '10.1000/known')

    def test_findings_abstract_titles_and_captions_withheld(self):
        row = b.registered_fields({'DOI': '10.1000/known', 'title': ['Superior accuracy'],
            'abstract': 'Zero false positives', 'caption': 'The best result',
            'author': [{'given': 'Jane', 'family': 'Doe'}], 'container-title': ['Some Journal'],
            'published': {'date-parts': [[2026, 9]], 'result': 'high performance'}, 'type': 'journal-article'}, '10.1000/known')
        encoded = str(row)
        for value in ['Superior', 'false positives', 'best result', 'Jane', 'Some Journal', 'high performance']:
            self.assertNotIn(value, encoded)
        self.assertEqual(row['date_fields']['published'], {'date-parts': [[2026, 9]]})
        self.assertIsNone(row['preferred_version_decision'])

    def test_relations_require_explicit_doi_type(self):
        row = b.registered_fields({'DOI': '10.1000/known', 'relation': {
            'is-preprint-of': [{'id-type': 'doi', 'id': '10.1000/publisher'}],
            'is-identical-to': [{'id-type': 'url', 'id': 'https://example.com/claims'}]}}, '10.1000/KNOWN')
        self.assertEqual(row['related_doi_identifiers'], [{'relation_kind': 'is-preprint-of', 'doi': '10.1000/publisher'}])

    def test_registration_creation_is_distinct_from_publication(self):
        row = b.registered_fields({'DOI': '10.1000/known', 'created': {'date-time': '2026-10-21T00:00:00Z'},
                                  'published': {'date-parts': [[2025]]}}, '10.1000/known')
        self.assertIn('created', row['date_fields'])
        self.assertIn('published', row['date_fields'])
        self.assertIn('REGISTRATION_DATES_ARE_NOT_PROOF_OF_PUBLIC_AVAILABILITY', row['limitation_codes'])


if __name__ == '__main__':
    unittest.main()

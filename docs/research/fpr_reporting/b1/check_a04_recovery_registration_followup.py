"""DataCite evidence is identity-bound, dated metadata only."""
import unittest
import a04_recovery_registration_followup as f

class DataCiteChecks(unittest.TestCase):
    def test_wrong_identity_rejected(self):
        with self.assertRaisesRegex(ValueError, 'IDENTITY_MISMATCH'):
            f.datacite_fields({'doi':'10.5281/other'}, '10.5281/known')

    def test_descriptions_and_findings_are_withheld(self):
        row = f.datacite_fields({'doi':'10.5281/known', 'titles':[{'title':'Superior accuracy'}],
            'descriptions':[{'description':'Best results'}], 'creators':[{'name':'Person'}],
            'publicationYear':2026, 'dates':[{'date':'2026-10-01', 'dateType':'Issued', 'dateInformation':'Better results'}]}, '10.5281/known')
        self.assertEqual(row['dated_events'], [{'date':'2026-10-01','dateType':'Issued'}])
        for word in ('Superior', 'Best results', 'Person', 'Better results'):
            self.assertNotIn(word, str(row))
        self.assertIsNone(row['preferred_version_decision'])

if __name__ == '__main__':
    unittest.main()

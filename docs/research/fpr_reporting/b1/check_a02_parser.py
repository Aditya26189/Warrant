"""Offline contract checks for outcome-blind metadata parsing."""
import unittest

import prepare_a02_metadata as m


class MetadataParserChecks(unittest.TestCase):
    def test_unicode_normalization(self):
        self.assertEqual(m.normalize("Prompt\u2011Injection"), "prompt injection")
        self.assertTrue(m.predicate("\uff30\uff32\uff2f\uff2d\uff30\uff34 injection", "classifier"))

    def test_predicate_uses_only_supplied_fields(self):
        self.assertFalse(m.predicate("Unrelated title", "An unrelated abstract"))
        self.assertFalse(m.predicate("Prompt injection", "No matching method word"))
        self.assertTrue(m.predicate("Prompt injection detection", ""))

    def test_dates_at_cutoff(self):
        self.assertEqual(m.date_state("2026", "October"), "UNCLEAR_DATE")
        self.assertEqual(m.date_state("2026", "September"), "IN_WINDOW")
        self.assertEqual(m.date_state("2026", "November"), "OUTSIDE_WINDOW")
        self.assertEqual(m.date_state("2023", "December"), "OUTSIDE_WINDOW")
        self.assertEqual(m.date_state("2025", ""), "UNCLEAR_DATE")

    def test_reference_parser_nested_values(self):
        raw = '@article{x, title={Nested {Prompt} Injection}, author="Last, First", year="2025", month=jun, abstract="Detect with {nested {braces}}",}'
        entry, begin, end = list(m.entries(raw))[0]
        parser = m.BibTexParser(common_strings=True)
        parser.ignore_nonstandard_types = False
        self.assertEqual(m.bibtexparser.loads(raw[begin:end], parser=parser).entries, [entry])

    def test_record_locator_and_multiple_entries(self):
        raw = '@article{one, title="one",}\n@article{two, title={two},}\n'
        rows = list(m.entries(raw))
        self.assertEqual([r[0]["ID"] for r in rows], ["one", "two"])
        for entry, begin, end in rows:
            self.assertTrue(raw[begin:end].startswith("@article{" + entry["ID"]))

    def test_malformed_value_stops(self):
        with self.assertRaises(ValueError):
            list(m.entries('@article{x, title={unterminated}'))

    def test_duplicate_fields_stop(self):
        with self.assertRaises(ValueError):
            list(m.entries('@article{x, title="one", title="two",}'))

    def test_unknown_macro_stops(self):
        with self.assertRaises(ValueError):
            list(m.entries('@article{x, title=unknown_macro,}'))

    def test_citation_fields_do_not_create_a_match(self):
        raw = '@article{x, title="Unrelated", booktitle="Prompt injection detection", year="2025", month=jun,}'
        entry, _, _ = list(m.entries(raw))[0]
        record = m.canonical_record(entry, "acl", 1, {})
        self.assertFalse(m.predicate(record["title"], record["abstract"]))
        self.assertTrue(record["abstract_missing"])


if __name__ == "__main__":
    unittest.main()

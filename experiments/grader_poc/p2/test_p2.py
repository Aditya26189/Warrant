"""Guards for the new scientific comparison, independent of target outcomes."""
import ast
from fractions import Fraction
import unittest

from experiments.grader_poc.p2.components import math_cases, mutations


class ProtocolTests(unittest.TestCase):
    def test_mutations_are_single_site_and_bounded(self) -> None:
        source = '# canary retained\ndef _matched_braces(x):\n    if x < 3:\n        return x + 1\n    return x - 1\n'
        original = ast.parse(source)
        variants = mutations(source, 2)
        self.assertEqual(len(variants), 2)
        self.assertEqual([v[2]["line"] for v in variants], [3, 4])
        def operators(tree: ast.AST) -> list:
            return [type(n).__name__ for n in ast.walk(tree) if isinstance(n, (ast.operator, ast.cmpop))]
        before = operators(original)
        for _, code, _ in variants:
            self.assertTrue(code.startswith('# canary retained\n'))
            after = operators(ast.parse(code))
            self.assertEqual(sum(a != b for a, b in zip(before, after, strict=True)), 1)

    def test_rational_labels_come_from_operands(self) -> None:
        rows = math_cases()
        self.assertTrue(rows)
        self.assertEqual({r["split"] for r in rows}, {"discovery", "held_out"})
        for row in rows:
            derivation = row["derivation"]
            value = Fraction(derivation["numerator"], derivation["denominator"])
            self.assertEqual(row["expected"], value == Fraction(row["gold"]))
            self.assertEqual(Fraction(row["gold"]) - value, derivation["offset"])

    def test_irrelevant_functions_are_not_mutated(self) -> None:
        self.assertEqual(mutations('def other(x):\n    return x + 1\n', 8), [])

    def test_mutation_preserves_python311_fstring_syntax(self) -> None:
        source = '''# canary
def _matched_braces(x):
    return x + 1
def unrelated(bound, op):
    return f"({bound}{')' if op == '<' else ']'}"
'''
        variants = mutations(source, 1)
        self.assertEqual(variants[0][1], source.replace("x + 1", "x - 1"))
        ast.parse(variants[0][1], feature_version=(3, 11))


if __name__ == "__main__":
    unittest.main()

"""Generate conventional one-span mutations without reprinting the program."""

import ast
import io
import json
import tokenize
from pathlib import Path

from experiments.grader_poc.feasibility.calibration import property_inputs
from experiments.grader_poc.feasibility.prepare import HERE as CALIBRATION, digest
from experiments.grader_poc.feasibility.run_calibration import control_code

HERE = Path(__file__).resolve().parent


def load_inputs() -> tuple[dict, dict, dict]:
    """Keep Gate1's frozen task and domain as the only data source."""
    return (
        json.loads((HERE / "config.json").read_bytes()),
        json.loads((CALIBRATION / "config.json").read_bytes()),
        json.loads((CALIBRATION / "fixtures/calibration.json").read_bytes()),
    )


def witness_inputs(config: dict, calibration: dict) -> list[dict]:
    """Reuse the existing seeded inputs without selecting against survivors."""
    assert config["seed"] == calibration["corpus"]["seed"]
    cases = [c for c in property_inputs(calibration) if c["kind"] == "seeded"]
    assert len(cases) == config["witness_count"]
    return cases


def mutations(source: str, entry_point: str, operators: list[str]) -> list[dict]:
    """Return deterministic byte-preserving edits inside the function body.

    AST positions are UTF-8 byte offsets whereas tokenize columns count
    characters. Convert each deliberately; comments/docstrings are never sites.
    """
    raw = source.encode()
    lines = source.splitlines(keepends=True)
    offsets = [0]
    for line in lines:
        offsets.append(offsets[-1] + len(line.encode()))

    def position(line: int, column: int) -> int:
        return offsets[line - 1] + column

    def span(node: ast.AST) -> tuple[int, int]:
        return (position(node.lineno, node.col_offset),
                position(node.end_lineno, node.end_col_offset))

    tokens = []
    for token in tokenize.generate_tokens(io.StringIO(source).readline):
        if token.type == tokenize.OP:
            start = position(token.start[0], len(lines[token.start[0] - 1][:token.start[1]].encode()))
            end = position(token.end[0], len(lines[token.end[0] - 1][:token.end[1]].encode()))
            tokens.append((start, end, token.string))

    tree = ast.parse(source)
    functions = [n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == entry_point]
    if len(functions) != 1:
        raise ValueError("Expected one named top-level function")
    nodes = [node for statement in functions[0].body
             if not (isinstance(statement, ast.Expr)
                     and isinstance(statement.value, ast.Constant)
                     and isinstance(statement.value.value, str))
             for node in ast.walk(statement)]
    edits = []

    def add(start: int, end: int, operator: str, replacement: str) -> None:
        if operator in operators and raw[start:end] != replacement.encode():
            edits.append((start, end, operator, replacement))

    def operator_span(left: ast.AST, right: ast.AST, symbol: str) -> tuple[int, int]:
        matches = [(s, e) for s, e, value in tokens
                   if s >= span(left)[1] and e <= span(right)[0] and value == symbol]
        if len(matches) != 1:
            raise ValueError("Ambiguous operator location")
        return matches[0]

    boundary = {ast.Lt: ("<", "<="), ast.LtE: ("<=", "<"),
                ast.Gt: (">", ">="), ast.GtE: (">=", ">")}
    negation = {ast.Lt: ("<", ">="), ast.LtE: ("<=", ">"),
                ast.Gt: (">", "<="), ast.GtE: (">=", "<"),
                ast.Eq: ("==", "!="), ast.NotEq: ("!=", "==")}
    for node in nodes:
        if isinstance(node, ast.Compare):
            operands = [node.left, *node.comparators]
            for index, op in enumerate(node.ops):
                for name, mapping in (("relational_boundary", boundary),
                                      ("comparison_negation", negation)):
                    if type(op) in mapping:
                        old, new = mapping[type(op)]
                        add(*operator_span(operands[index], operands[index + 1], old), name, new)
        elif isinstance(node, ast.BinOp) and isinstance(node.op, (ast.Add, ast.Sub)):
            old, new = ("+", "-") if isinstance(node.op, ast.Add) else ("-", "+")
            add(*operator_span(node.left, node.right, old), "arithmetic_swap", new)
        elif isinstance(node, ast.Constant):
            if type(node.value) is bool:
                add(*span(node), "boolean_flip", str(not node.value))
            elif type(node.value) in (int, float):
                for value in (node.value - 1, node.value + 1, 0):
                    add(*span(node), "numeric_offset", repr(value))
        elif isinstance(node, ast.If):
            for value in ("True", "False"):
                add(*span(node.test), "constant_guard", value)

    candidates, seen = [], set()
    for start, end, operator, replacement in sorted(set(edits)):
        candidate = raw[:start] + replacement.encode() + raw[end:]
        sha = digest(candidate)
        if sha in seen:
            continue
        seen.add(sha)
        try:
            compile(candidate, "<generated-mutation>", "exec")
            syntax = "VALID"
        except SyntaxError:
            syntax = "INVALID"
        candidates.append({"id": f"mutant-{len(candidates) + 1:03d}",
                           "operator": operator, "start_byte": start, "end_byte": end,
                           "original": raw[start:end].decode(), "replacement": replacement,
                           "syntax": syntax, "sha256": sha, "source": candidate.decode()})
    return candidates


def candidate_pool() -> dict:
    """Bind the complete pool and explicitly record any execution-cap exclusion."""
    config, calibration, fixture = load_inputs()
    assert config["task_id"] == calibration["calibration_id"] == fixture["task_id"]
    source = control_code(fixture, "reference")
    candidates = mutations(source, fixture["entry_point"], config["operators"])
    cap = config["candidate_cap"]
    return {"reference_sha256": digest(source.encode()), "candidates": candidates[:cap],
            "excluded_by_cap": candidates[cap:], "generated_count": len(candidates)}

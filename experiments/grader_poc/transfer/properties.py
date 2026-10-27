"""Prompt-derived partial properties, frozen before reserved references/tests."""

import inspect
import json
import random
from pathlib import Path

HERE = Path(__file__).resolve().parent


def config() -> dict:
    """Load declared domains without deriving them from benchmark behavior."""
    return json.loads((HERE / "config.json").read_bytes())


def in_domain(task: str, args: list) -> bool:
    """Ambiguous or unmodeled inputs abstain rather than incriminate candidates."""
    domain = config()["domains"][task]
    if task == "HumanEval/87":
        if len(args) != 2:
            return False
        rows, target = args
        valid_int = lambda x: type(x) is int and domain["minimum_integer"] <= x <= domain["maximum_integer"]
        return (type(rows) is list and len(rows) <= domain["max_rows"] and valid_int(target)
                and all(type(row) is list and len(row) <= domain["max_columns"]
                        and all(valid_int(x) for x in row) for row in rows))
    if task == "HumanEval/57":
        if len(args) != 1 or type(args[0]) is not list:
            return False
        values = args[0]
        return (domain["min_length"] <= len(values) <= domain["max_length"]
                and all(type(x) is int and domain["minimum_integer"] <= x <= domain["maximum_integer"] for x in values)
                and len(set(values)) == len(values))
    if task == "HumanEval/18":
        return (len(args) == 2 and all(type(x) is str for x in args)
                and len(args[0]) <= domain["max_text_length"]
                and domain["min_substring_length"] <= len(args[1]) <= domain["max_substring_length"]
                and all(c in domain["alphabet"] for value in args for c in value))
    raise ValueError("Unreserved task")


def expected(task: str, args: list) -> object:
    """Compute the unique specified observable within the declared partial domain."""
    if not in_domain(task, args):
        raise ValueError("OUT_OF_DECLARED_DOMAIN")
    if task == "HumanEval/87":
        rows, target = args
        coords = [(i, j) for i in range(len(rows)) for j in range(len(rows[i])) if rows[i][j] == target]
        return sorted(coords, key=lambda pair: (pair[0], -pair[1]))
    if task == "HumanEval/57":
        values = args[0]
        signs = {values[j] > values[i] for i in range(len(values)) for j in range(i + 1, len(values))}
        return len(signs) == 1
    text, substring = args
    return sum(text[i:i + len(substring)] == substring for i in range(len(text) - len(substring) + 1))


def encode(value: object) -> dict:
    """Retain type distinctions lost by JSON, especially tuple/list and bool/int."""
    if type(value) in (list, tuple):
        return {"type": type(value).__name__, "value": [encode(v) for v in value]}
    if type(value) in (bool, int, str) or value is None:
        return {"type": type(value).__name__, "value": value}
    return {"type": type(value).__name__, "repr": repr(value)}


def property_holds(task: str, args: list, observed: object) -> bool:
    """Match the documented return contract, not reference internal choices."""
    return encode(observed) == encode(expected(task, args))


def alternative_87(rows: list, target: int) -> list:
    """Construct the required ordering directly without sorting coordinates."""
    found = []
    for row_index, row in enumerate(rows):
        for column in reversed(range(len(row))):
            if row[column] == target:
                found.append((row_index, column))
    return found


def alternative_57(values: list) -> bool:
    """Track direction; equality behavior is a predeclared out-of-scope assumption."""
    rising, falling = False, False
    for index in range(1, len(values)):
        rising = rising or values[index] > values[index - 1]
        falling = falling or values[index] < values[index - 1]
        if rising and falling:
            return False
    return True


def alternative_18(text: str, substring: str) -> int:
    """Advance one character after a match so overlapping occurrences remain."""
    count, start = 0, 0
    while start <= len(text) - len(substring):
        position = text.find(substring, start)
        if position < 0:
            break
        count += 1
        start = position + 1
    return count


def alternative_code(task: str, entry_point: str) -> str:
    """Export the pre-exposure alternative, without consulting the reference."""
    function = {"HumanEval/87": alternative_87, "HumanEval/57": alternative_57,
                "HumanEval/18": alternative_18}[task]
    return inspect.getsource(function) + f"\n{entry_point} = {function.__name__}\n"


def witness_inputs(task: str) -> list[dict]:
    """Use prompt-derived edges followed by seeded inputs, never grader feedback."""
    cfg = config()
    domain = cfg["domains"][task]
    edges = {
        "HumanEval/87": [[[], 0], [[[], []], 1], [[[1, 2, 1], [1], []], 1],
                         [[[0, 0], [0, 0]], 0], [[[-3], [3, -3]], -3], [[[1]], 2]],
        "HumanEval/57": [[[0, 1]], [[1, 0]], [[-1, 0, 1]], [[1, 0, -1]], [[-1, 1, 0]], [[1, -1, 0]]],
        "HumanEval/18": [["", "a"], ["aaa", "a"], ["aaaa", "aa"], ["ababab", "aba"], ["ab", "aba"], ["bbbb", "a"]],
    }[task]
    cases = [{"args": args, "kind": "prompt_edge"} for args in edges]
    rng = random.Random(cfg["seed"])
    while len(cases) < cfg["witness_count"]:
        if task == "HumanEval/87":
            rows = [[rng.randint(domain["minimum_integer"], domain["maximum_integer"])
                     for _ in range(rng.randint(0, domain["max_columns"]))]
                    for _ in range(rng.randint(0, domain["max_rows"]))]
            args = [rows, rng.randint(domain["minimum_integer"], domain["maximum_integer"])]
        elif task == "HumanEval/57":
            args = [rng.sample(range(domain["minimum_integer"], domain["maximum_integer"] + 1),
                               rng.randint(domain["min_length"], domain["max_length"]))]
        else:
            args = [''.join(rng.choice(domain["alphabet"]) for _ in range(rng.randint(0, domain["max_text_length"]))),
                    ''.join(rng.choice(domain["alphabet"]) for _ in range(rng.randint(domain["min_substring_length"], domain["max_substring_length"])))]
        cases.append({"args": args, "kind": "seeded"})
    assert all(in_domain(task, c["args"]) for c in cases)
    return cases

"""The input contract: a customer's scored items, read strictly.

Warrant certifies a detector from **scores and labels**. Producing the scores is
the customer's problem, and that is the correct boundary rather than a
limitation: it is what lets this run against a closed-API deployment where no
probe can exist, and against a detector nobody here has ever seen.

**Three required columns**, in CSV or JSONL:

===========  ==========================================================
``id``       Unique identifier for the item. Duplicates are refused, not
             deduplicated — two rows claiming the same id mean the file
             says two different things about one item.
``label``    ``0`` or ``1``. **1 means the detector SHOULD fire** — the
             item is the thing being looked for. Inverting this yields a
             detector that looks strongly wrong rather than obviously
             inverted, so it is stated here, in ``docs/INPUT.md`` and in
             the error message when a label is not binary.
``score``    The detector's score. Higher must mean *more likely to be
             the positive class*. Any finite range; no calibration is
             assumed and none is required.
===========  ==========================================================

Optional ``group`` clusters items that are not independent — several items from
one document, one customer, one template. Everything else in the file is carried
into the artifact untouched and never used in a computation.

**Nothing is coerced, filled or dropped.** A file that does not meet the
contract fails with a message naming the column and what was expected. The one
exception is a shortage of negatives, which is a *refusal* rather than an error
(``DECISIONS.md`` 138): the tool worked and the evidence was insufficient, which
is the product's whole thesis and must not read as a crash.
"""

from __future__ import annotations

import csv
import dataclasses
import json
from pathlib import Path
from typing import Any, Optional, Sequence

import numpy as np

__all__ = [
    "GROUP_COLUMN",
    "REQUIRED_COLUMNS",
    "InputError",
    "ScoredItems",
    "load_scored_items",
]

#: The three the contract requires. Deliberately short, lowercase and obvious:
#: a person exporting from a spreadsheet has to be able to produce them without
#: reading anything.
REQUIRED_COLUMNS = ("id", "label", "score")

#: Optional. Its presence changes the unit of inference, so it is never guessed
#: at from a column that merely looks like one.
GROUP_COLUMN = "group"


class InputError(ValueError):
    """A file that does not meet the contract.

    Distinct from a refusal. This means *we cannot read what you sent*; a
    refusal means *we read it and the evidence does not support a warrant*.
    Conflating them would turn a fixable typo into an apparent verdict on the
    detector.
    """


@dataclasses.dataclass(frozen=True)
class ScoredItems:
    """One detector's scores and the ground truth they are judged against."""

    ids: tuple[str, ...]
    labels: tuple[int, ...]
    scores: tuple[float, ...]
    groups: Optional[tuple[str, ...]]
    passthrough_columns: tuple[str, ...]
    source: str

    @property
    def n(self) -> int:
        return len(self.ids)

    @property
    def n_positive(self) -> int:
        return int(sum(1 for y in self.labels if y == 1))

    @property
    def n_negative(self) -> int:
        return int(sum(1 for y in self.labels if y == 0))

    @property
    def base_rate(self) -> float:
        return self.n_positive / self.n if self.n else 0.0

    @property
    def n_units(self) -> int:
        """Independent units: distinct groups when given, otherwise items.

        The number that decides what can be certified. Two hundred items from
        twenty documents are twenty units, and certifying as though they were
        two hundred would overstate the evidence by an order of magnitude.
        """
        if self.groups is None:
            return self.n
        return len(set(self.groups))

    @property
    def equal_group_sizes(self) -> bool:
        """Whether every group holds the same number of items.

        ``certify_fpr`` bounds item-level FPR by cluster-level FPR only when
        clusters are equal-sized; with unequal sizes the bound is
        *anticonservative*, which is the direction that matters.
        """
        if self.groups is None:
            return True
        counts: dict[str, int] = {}
        for key in self.groups:
            counts[key] = counts.get(key, 0) + 1
        return len(set(counts.values())) == 1

    def as_arrays(self) -> tuple[np.ndarray, np.ndarray, Optional[np.ndarray]]:
        """``(labels, scores, groups)`` for the estimators."""
        return (
            np.asarray(self.labels),
            np.asarray(self.scores, dtype=float),
            None if self.groups is None else np.asarray(self.groups),
        )


def _rows_from_csv(path: Path) -> tuple[list[dict[str, str]], list[str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        if reader.fieldnames is None:
            raise InputError(f"{path.name} is empty: no header row to read columns from")
        return list(reader), [name.strip() for name in reader.fieldnames]


def _rows_from_jsonl(path: Path) -> tuple[list[dict[str, Any]], list[str]]:
    rows: list[dict[str, Any]] = []
    columns: list[str] = []
    for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        try:
            record = json.loads(line)
        except json.JSONDecodeError as exc:
            raise InputError(f"{path.name} line {number} is not valid JSON: {exc}") from exc
        if not isinstance(record, dict):
            raise InputError(
                f"{path.name} line {number} is a {type(record).__name__}, not an "
                "object. Each line must be one item, as a JSON object."
            )
        rows.append(record)
        for key in record:
            if key not in columns:
                columns.append(key)
    return rows, columns


def _require_columns(columns: Sequence[str], source: str) -> None:
    missing = [name for name in REQUIRED_COLUMNS if name not in columns]
    if missing:
        raise InputError(
            f"{source} is missing required column(s) {missing}. The contract is "
            f"{list(REQUIRED_COLUMNS)}: 'id' unique per item, 'label' 0 or 1 "
            "where 1 means the detector should fire, 'score' where higher means "
            f"more likely positive. Columns found: {list(columns)}. See "
            "docs/INPUT.md."
        )


def _parse_label(raw: Any, *, row: int, source: str) -> int:
    text = str(raw).strip()
    if text in {"0", "1"}:
        return int(text)
    # Accept a float that is exactly 0 or 1, since a spreadsheet export writes
    # "1.0". Anything else is refused rather than rounded: 0.7 is not a label,
    # and guessing which way it should go is how a threshold silently moves.
    try:
        value = float(text)
    except ValueError:
        value = None
    if value in (0.0, 1.0):
        return int(value)
    raise InputError(
        f"{source} row {row}: label is {raw!r}, which is not 0 or 1. Labels are "
        "binary ground truth — 1 means the detector SHOULD fire on this item, 0 "
        "means it should not. A probability or a class name is not a label here."
    )


def _parse_score(raw: Any, *, row: int, source: str) -> float:
    text = str(raw).strip()
    try:
        value = float(text)
    except ValueError as exc:
        raise InputError(
            f"{source} row {row}: score is {raw!r}, which is not a number. The "
            "score is the detector's output, any finite range, higher meaning "
            "more likely to be the positive class."
        ) from exc
    if not np.isfinite(value):
        raise InputError(
            f"{source} row {row}: score is {raw!r}. A NaN or infinity cannot be "
            "ordered against a threshold, so it is refused rather than dropped."
        )
    return value


def load_scored_items(path: str | Path) -> ScoredItems:
    """Read a customer's scored items, refusing anything that breaks the contract.

    Args:
        path: A ``.csv`` or ``.jsonl`` file.

    Returns:
        The parsed :class:`ScoredItems`.

    Raises:
        InputError: Naming the column, the row and what was expected. Never
            coerces, fills or drops.
    """
    file = Path(path)
    if not file.is_file():
        raise InputError(f"no such file: {file}")

    suffix = file.suffix.lower()
    if suffix == ".csv":
        rows, columns = _rows_from_csv(file)
    elif suffix in {".jsonl", ".ndjson"}:
        rows, columns = _rows_from_jsonl(file)
    else:
        raise InputError(
            f"{file.name} has extension {suffix or '(none)'}; this phase reads "
            ".csv and .jsonl only. The point of the contract is a format you can "
            "produce from a spreadsheet."
        )

    source = file.name
    _require_columns(columns, source)
    if not rows:
        raise InputError(f"{source} has a header but no rows.")

    ids: list[str] = []
    labels: list[int] = []
    scores: list[float] = []
    groups: list[str] = []
    has_groups = GROUP_COLUMN in columns

    for number, row in enumerate(rows, start=2 if suffix == ".csv" else 1):
        for column in REQUIRED_COLUMNS:
            if row.get(column) is None or str(row.get(column)).strip() == "":
                raise InputError(
                    f"{source} row {number}: column {column!r} is empty. Every "
                    "row needs all three of "
                    f"{list(REQUIRED_COLUMNS)}; a blank is not filled in for you."
                )
        item_id = str(row["id"]).strip()
        ids.append(item_id)
        labels.append(_parse_label(row["label"], row=number, source=source))
        scores.append(_parse_score(row["score"], row=number, source=source))
        if has_groups:
            key = row.get(GROUP_COLUMN)
            if key is None or str(key).strip() == "":
                raise InputError(
                    f"{source} row {number}: {GROUP_COLUMN!r} is present as a "
                    "column but empty on this row. A partially grouped file has "
                    "no consistent unit of inference, so it is refused rather "
                    "than treated as one group of singletons."
                )
            groups.append(str(key).strip())

    duplicates = sorted({i for i in ids if ids.count(i) > 1})
    if duplicates:
        shown = duplicates[:5]
        raise InputError(
            f"{source}: duplicate id(s) {shown}"
            + (f" and {len(duplicates) - len(shown)} more" if len(duplicates) > 5 else "")
            + ". Ids must be unique — two rows for one id mean the file makes two "
            "different claims about the same item, and nothing here can decide "
            "which one you meant."
        )

    distinct = set(labels)
    if len(distinct) < 2:
        only = distinct.pop() if distinct else None
        raise InputError(
            f"{source}: every label is {only}. A detector cannot be certified "
            "against a set with only one class — with no negatives there is no "
            "false-positive rate to bound, and with no positives there is no "
            "recall to measure. Include both."
        )

    passthrough = tuple(
        name for name in columns
        if name not in REQUIRED_COLUMNS and name != GROUP_COLUMN
    )
    return ScoredItems(
        ids=tuple(ids),
        labels=tuple(labels),
        scores=tuple(scores),
        groups=tuple(groups) if has_groups else None,
        passthrough_columns=passthrough,
        source=source,
    )

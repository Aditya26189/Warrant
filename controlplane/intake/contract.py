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
one document, one customer, one template. Optional ``label_2`` is a second
reviewer's label, blank on items that were not double-labelled; it is measured
beside the certificate and never changes it (``DECISIONS.md`` 197). Everything
else in the file is carried into the artifact untouched and never used in a
computation.

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
from collections import Counter
from pathlib import Path
from typing import Any, Optional, Sequence

import numpy as np

__all__ = [
    "GROUP_COLUMN",
    "REQUIRED_COLUMNS",
    "SECOND_LABEL_COLUMN",
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

#: Optional. A second reviewer's label on some items, blank on the rest. Read so
#: agreement can be published beside a warrant (``CLAUDE.md``: kappa next to every
#: warrant); it changes no verdict (``DECISIONS.md`` 197).
SECOND_LABEL_COLUMN = "label_2"


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
    #: ``label_2`` per item, ``None`` where the item was not double-labelled; the
    #: whole field is ``None`` when the file has no such column.
    second_labels: Optional[tuple[Optional[int], ...]] = None

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
    """Reject ambiguity before dictionary conversion can discard it.

    Codex-parallel decision 199, ``docs/decisions/CODEX-PARALLEL.md``.
    """
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.reader(handle, strict=True)
        try:
            header = next(reader, None)
            if header is None:
                raise InputError(f"{path.name} is empty: no header row to read columns from")
            columns = [name.strip() for name in header]
            if not columns or any(not name for name in columns):
                raise InputError(f"{path.name}: every CSV header must name a non-blank column")
            duplicates = sorted(name for name, count in Counter(columns).items() if count > 1)
            if duplicates:
                raise InputError(
                    f"{path.name}: duplicate CSV column(s) {duplicates} after whitespace "
                    "normalization; each field must have exactly one value per row"
                )
            rows: list[dict[str, str]] = []
            for values in reader:
                if not values:  # Preserve DictReader's treatment of empty lines.
                    continue
                if len(values) != len(columns):
                    raise InputError(
                        f"{path.name} row ending at line {reader.line_num}: "
                        f"expected {len(columns)} CSV fields, found {len(values)}; "
                        "missing or extra fields cannot be filled or dropped"
                    )
                rows.append(dict(zip(columns, values, strict=True)))
        except csv.Error as exc:
            raise InputError(
                f"{path.name} line {reader.line_num} is not valid CSV: {exc}"
            ) from exc
        return rows, columns


def _unique_json_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    """Keep JSON's last-value-wins rule out of the input contract.

    Codex-parallel decision 199, ``docs/decisions/CODEX-PARALLEL.md``.
    """
    record: dict[str, Any] = {}
    for key, value in pairs:
        if key in record:
            raise InputError(f"duplicate JSON field {key!r}; every key must be unique")
        record[key] = value
    return record


def _rows_from_jsonl(path: Path) -> tuple[list[dict[str, Any]], list[str]]:
    rows: list[dict[str, Any]] = []
    columns: list[str] = []
    for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        try:
            record = json.loads(line, object_pairs_hook=_unique_json_object)
        except json.JSONDecodeError as exc:
            raise InputError(f"{path.name} line {number} is not valid JSON: {exc}") from exc
        except InputError as exc:
            raise InputError(f"{path.name} line {number}: {exc}") from exc
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


def _parse_label(raw: Any, *, row: int, source: str, column: str = "label") -> int:
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
        f"{source} row {row}: {column} is {raw!r}, which is not 0 or 1. Labels are "
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


def load_scored_items(path: str | Path, *, require_both_classes: bool = True) -> ScoredItems:
    """Read a customer's scored items, refusing anything that breaks the contract.

    Args:
        path: A ``.csv`` or ``.jsonl`` file.
        require_both_classes: Preserve legacy certification rejection by default.
            Release evaluation opts out to retain a study with a missing
            denominator. New release registrations report REFUSED; the legacy
            protocol retains UNVALIDATED for replay (DECISIONS 185, 200).

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
    second: list[Optional[int]] = []
    has_second = SECOND_LABEL_COLUMN in columns

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
        if has_second:
            value = row.get(SECOND_LABEL_COLUMN)
            # Blank means "not double-labelled", the one blank this contract
            # accepts: a second review of every item is not what anyone runs.
            second.append(
                None if value is None or str(value).strip() == ""
                else _parse_label(value, row=number, source=source, column=SECOND_LABEL_COLUMN)
            )

    if has_second and all(value is None for value in second):
        raise InputError(
            f"{source}: {SECOND_LABEL_COLUMN!r} is present as a column but blank on "
            "every row. That is an export mistake, not a second review; fill in the "
            "items that were double-labelled, or drop the column."
        )

    duplicates = sorted(i for i, count in Counter(ids).items() if count > 1)
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
    if require_both_classes and len(distinct) < 2:
        only = distinct.pop() if distinct else None
        raise InputError(
            f"{source}: every label is {only}. A detector cannot be certified "
            "against a set with only one class — with no negatives there is no "
            "false-positive rate to bound, and with no positives there is no "
            "recall to measure. Include both."
        )

    passthrough = tuple(
        name for name in columns
        if name not in REQUIRED_COLUMNS and name not in (GROUP_COLUMN, SECOND_LABEL_COLUMN)
    )
    return ScoredItems(
        ids=tuple(ids),
        labels=tuple(labels),
        scores=tuple(scores),
        groups=tuple(groups) if has_groups else None,
        passthrough_columns=passthrough,
        source=source,
        second_labels=tuple(second) if has_second else None,
    )

"""The label queue, blinded — because anchoring biases in one direction.

``CLAUDE.md`` invariant 7: *the label queue never exposes flag status, score,
stratum, or ordering signal.*

The reason is not fairness, it is bias with a known sign. A reviewer who can see
that an item was flagged is more likely to confirm it as an error, and one who
can see it was not is less likely. Both push the estimate the same way: the
flagged stratum's confirmed count rises, the unflagged stratum's prevalence
falls, and recall ``TP/(TP + q*N_u)`` moves up on both ends. **The bias flatters
the detector**, which is the direction nobody checks.

Four leaks, and all four are closed here rather than by convention:

1. **The obvious fields.** Flag status, score, stratum, band -- withheld from
   the payload entirely, not set to ``None``, because a key that exists and is
   empty still tells a reviewer which items had something to hide.
2. **Order.** Concatenating stratum A then stratum B leaks the stratum in the
   sequence itself. The queue is shuffled with a seeded generator, so the order
   carries no signal and the run still reproduces.
3. **Identifiers.** A queue position or a source id that sorts by stratum leaks
   the same thing one level down. Every item gets an opaque queue id and the
   mapping back is held separately.
4. **Repeats.** Double-labelled items are how agreement is measured, and a
   reviewer who recognises an item they have seen answers from memory rather
   than from the item. Repeats are placed by the same shuffle, so a reviewer
   cannot tell a second pass from a first.

A reviewer who wants to bias the estimate can still do so. The queue defends
against the *unconscious* version, which is the one that happens.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from typing import Any, Iterable, Mapping, Optional, Sequence

__all__ = [
    "BlindedQueue",
    "LabelItem",
    "QueueError",
    "WITHHELD_FIELDS",
    "build_queue",
]


class QueueError(ValueError):
    """The queue was asked to carry something it must not carry."""


#: Field names that must never reach a reviewer. Checked against every payload
#: at construction, so a new field added to :class:`LabelItem` cannot leak by
#: being forgotten.
WITHHELD_FIELDS = frozenset(
    {
        "flagged",
        "flag",
        "flag_status",
        "score",
        "detector_score",
        "stratum",
        "band",
        "band_name",
        "rank",
        "position",
        "source_index",
        "prediction",
        "predicted",
        "label",
        "ground_truth",
    }
)


@dataclass(frozen=True)
class LabelItem:
    """One item awaiting review, with everything the reviewer must not see.

    Attributes:
        item_id: The operator's own identifier. Never sent to the reviewer.
        content: What the reviewer reads and judges.
        flagged: Whether the detector flagged it. Withheld.
        stratum: ``"flagged"`` or ``"unflagged"``. Withheld.
        band: Score band within the unflagged stratum, if any. Withheld.
        score: The detector's score. Withheld.
        context: Anything else the reviewer legitimately needs, such as the
            question the response answered. Keys are checked against
            :data:`WITHHELD_FIELDS`.
    """

    item_id: str
    content: str
    flagged: bool
    stratum: str
    band: Optional[str] = None
    score: Optional[float] = None
    context: Mapping[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class BlindedQueue:
    """A shuffled, opaque review queue and the key that undoes it.

    Attributes:
        payloads: What reviewers see, in the order they see it. Each is a plain
            mapping with an opaque ``queue_id``, the ``content``, and whatever
            context was declared safe.
        assignments: ``queue_id`` to ``item_id``. **Held by the estimator, not
            by the reviewer.** This is the only path from a label back to a
            stratum.
        duplicated: ``item_id`` values placed in the queue twice, for
            inter-rater agreement.
        seed: The seed the shuffle used, so the queue reproduces.
    """

    payloads: tuple[Mapping[str, Any], ...]
    assignments: Mapping[str, str]
    duplicated: tuple[str, ...]
    seed: int

    def resolve(self, queue_id: str) -> str:
        """The original ``item_id`` behind a queue position.

        Raises:
            QueueError: If the id is not in this queue. A label for an unknown
                id is a label from somewhere else, and folding it in silently
                is how a sample stops being the sample that was designed.
        """
        try:
            return self.assignments[queue_id]
        except KeyError:
            raise QueueError(
                f"{queue_id!r} is not in this queue. A label whose id this "
                "queue did not issue cannot be attributed to a stratum, and "
                "attributing it anyway would break the design."
            ) from None


def _queue_id(item_id: str, occurrence: int, seed: int) -> str:
    """An opaque, deterministic id that sorts on nothing.

    A hash of the item, its occurrence and the seed. Deterministic so the run
    reproduces; hashed so the id ordering carries no information about stratum,
    score or arrival order. The two occurrences of a double-labelled item get
    different ids, which is what stops a reviewer recognising the repeat.
    """
    digest = hashlib.sha256(
        f"{seed}:{occurrence}:{item_id}".encode("utf-8")
    ).hexdigest()
    return f"q-{digest[:16]}"


def build_queue(
    items: Iterable[LabelItem],
    *,
    seed: int,
    double_label_fraction: float = 0.0,
    safe_context_keys: Sequence[str] = (),
) -> BlindedQueue:
    """Interleave both strata into one queue a reviewer cannot read anything from.

    Args:
        items: Everything to be reviewed, from both strata.
        seed: Shuffle seed. Recorded on the queue so the order reproduces.
        double_label_fraction: Share of items to place twice, for Cohen's kappa.
            ``CLAUDE.md`` asks for ~10% **of both strata**, so the share is
            applied within each stratum rather than to the pooled list -- a
            pooled 10% lands almost entirely in whichever stratum is larger, and
            an agreement figure measured on one stratum says nothing about the
            other.
        safe_context_keys: Context keys permitted through to the reviewer.
            Anything else in ``context`` is dropped rather than passed, because
            the reviewer's payload is an allowlist.

    Returns:
        The queue and its assignment key.

    Raises:
        QueueError: If an item declares a context key that names a withheld
            field, if ``double_label_fraction`` is not in ``[0, 1)``, or if two
            items share an ``item_id``.
    """
    import random

    if not 0.0 <= double_label_fraction < 1.0:
        raise QueueError(
            f"double_label_fraction={double_label_fraction!r} must be in [0, 1)"
        )

    material = list(items)
    seen: set[str] = set()
    for item in material:
        if item.item_id in seen:
            raise QueueError(
                f"duplicate item_id {item.item_id!r}. Queue ids are derived from "
                "it, so duplicates would collide and two different items would "
                "share one label."
            )
        seen.add(item.item_id)
        leaked = sorted(set(item.context) & WITHHELD_FIELDS)
        if leaked:
            raise QueueError(
                f"item {item.item_id!r} carries {', '.join(leaked)} in its "
                "context. CLAUDE.md invariant 7 withholds these from the queue: "
                "a reviewer who can see flag status confirms flagged items more "
                "often and unflagged items less often, which moves recall up on "
                "both ends."
            )

    allowed = tuple(k for k in safe_context_keys if k not in WITHHELD_FIELDS)

    rng = random.Random(seed)
    duplicated: list[str] = []
    if double_label_fraction > 0.0:
        by_stratum: dict[str, list[LabelItem]] = {}
        for item in material:
            by_stratum.setdefault(item.stratum, []).append(item)
        for stratum in sorted(by_stratum):
            pool = sorted(by_stratum[stratum], key=lambda i: i.item_id)
            count = int(round(len(pool) * double_label_fraction))
            duplicated.extend(i.item_id for i in rng.sample(pool, min(count, len(pool))))
    duplicated.sort()

    entries: list[tuple[str, LabelItem]] = []
    repeats = set(duplicated)
    for item in material:
        entries.append((_queue_id(item.item_id, 0, seed), item))
        if item.item_id in repeats:
            entries.append((_queue_id(item.item_id, 1, seed), item))

    rng.shuffle(entries)

    payloads: list[Mapping[str, Any]] = []
    assignments: dict[str, str] = {}
    for queue_id, item in entries:
        payload: dict[str, Any] = {"queue_id": queue_id, "content": item.content}
        for key in allowed:
            if key in item.context:
                payload[key] = item.context[key]
        payloads.append(payload)
        assignments[queue_id] = item.item_id

    return BlindedQueue(
        payloads=tuple(payloads),
        assignments=assignments,
        duplicated=tuple(duplicated),
        seed=seed,
    )

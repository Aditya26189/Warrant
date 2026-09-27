"""The numeric domain a stored record's values must fall in (``DECISIONS.md`` 208).

Every record this project reads back -- a chained recheck, a release
specification -- carries numbers a customer or an editor can set. Validating one
means three things in this order:

1. it is a real number, and **not** a boolean, which is an ``int`` in Python and
   would otherwise pass every numeric check;
2. it is **representable as a finite double**;
3. only then, it is inside its declared domain.

Step 2 exists because step 3 cannot run without it. ``math.isfinite(10**1000)``
does not return ``False``: it converts to double first and raises
``OverflowError``, so the guard meant to reject the value is what crashes on it.
That was reproduced through ``warrant chain verify`` and ``warrant release
register`` on ``main`` at ``603e4e3`` (R7 of the 2026-09-23 review). An arbitrary
integer is valid JSON, so any record read from disk can carry one.

Representability is not plausibility. ``10**300`` passes this module and is still
an absurd horizon; the domain checks that follow are what bound it.
"""

from __future__ import annotations

import math

__all__ = ["NumericDomainError", "finite_double", "is_real_number"]


class NumericDomainError(ValueError):
    """A stored value is not a real number this arithmetic can use.

    A ``ValueError``, so callers that already translate those into their own
    refusal -- ``MalformedChainError`` for a chain block, the release CLI's
    documented exit 2 -- keep doing so without a new except clause.
    """


def is_real_number(value: object) -> bool:
    """Whether ``value`` is a real number rather than a boolean or a string.

    ``True`` and ``False`` are rejected: they are ``int`` in Python, so a record
    carrying ``"alpha": true`` would otherwise be read as ``alpha = 1``.
    """
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def finite_double(value: object, what: str) -> float:
    """``value`` as a finite ``float``, or :class:`NumericDomainError`.

    Args:
        value: The number as it was read back from the record.
        what: How to name the field in the message, e.g. ``"the chain's alpha"``.

    Returns:
        The value as a ``float``, which every later comparison can use.

    Raises:
        NumericDomainError: If it is not a real number, is a boolean, is NaN or
            an infinity, or is an integer too large to be a double. The message
            names the field and, for an oversized integer, says how many digits
            it has rather than printing all of them.
    """
    if not is_real_number(value):
        raise NumericDomainError(f"{what} is {value!r}, not a number")
    if isinstance(value, int):
        # The conversion is the test. A bit-length bound is not: `2**1024 - 1`
        # has 1024 bits and still overflows, because it rounds up to `2**1024`.
        # That off-by-one is this defect again, one value further along.
        try:
            return float(value)
        except OverflowError:
            digits = len(str(abs(value)))
            raise NumericDomainError(
                f"{what} is an integer of {digits} digits, which is not "
                "representable as a finite number"
            ) from None
    if not math.isfinite(value):
        raise NumericDomainError(f"{what} is {value!r}, not a finite number")
    return float(value)

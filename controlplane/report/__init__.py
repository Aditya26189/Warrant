"""Report rendering and evidence tools with optional plotting imports deferred."""

from __future__ import annotations

from importlib import import_module

__all__ = ["FIXTURE_MARKER", "ResultsRefusal", "plot_tier_ladder", "render_results"]

_EXPORTS = {
    "FIXTURE_MARKER": (".results", "FIXTURE_MARKER"),
    "ResultsRefusal": (".results", "ResultsRefusal"),
    "plot_tier_ladder": (".plots", "plot_tier_ladder"),
    "render_results": (".results", "render_results"),
}


def __getattr__(name: str):
    """Load established public exports only when callers request them."""
    if name not in _EXPORTS:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
    module, attribute = _EXPORTS[name]
    value = getattr(import_module(module, __name__), attribute)
    globals()[name] = value
    return value

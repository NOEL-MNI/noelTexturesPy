from __future__ import annotations

import importlib.util
from collections.abc import Callable
from functools import lru_cache
from typing import TypeVar

T = TypeVar('T')


@lru_cache(maxsize=None)
def is_ants_available() -> bool:
    """Return True if the optional `ants` module is importable.

    Uses `find_spec` to avoid importing ANTs just to check availability.
    """

    return importlib.util.find_spec('ants') is not None


@lru_cache(maxsize=None)
def is_antspynet_available() -> bool:
    """Return True if the optional `antspynet` module is importable."""

    return importlib.util.find_spec('antspynet') is not None


def get_ants():
    """Import and return the `ants` module.

    Raises a RuntimeError with a clear message if missing.
    """

    try:
        import ants  # type: ignore[import-untyped]

        return ants
    except Exception as exc:  # pragma: no cover
        raise RuntimeError(
            'ANTsPy is required for processing. Install the optional "ants" dependencies.'
        ) from exc


def get_brain_extraction() -> Callable[..., T]:
    """Import and return antspynet.utilities.brain_extraction."""

    try:
        from antspynet.utilities import brain_extraction  # type: ignore[import-untyped]

        return brain_extraction
    except Exception as exc:  # pragma: no cover
        raise RuntimeError(
            'ANTsPyNet is required for processing. Install the optional "ants" dependencies.'
        ) from exc


def ants_version_string() -> str:
    """Return ANTsPy version string if available, else 'unavailable'."""

    if not is_ants_available():
        return 'unavailable'

    try:
        ants = get_ants()
        return getattr(ants, '__version__', 'unknown')
    except Exception:  # pragma: no cover
        return 'unknown'

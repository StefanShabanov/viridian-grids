"""Checks.

Each module exposes `run(ctx) -> list[Finding]` and never touches the network or
produces prose. A check that cannot run returns a `skipped` finding; it never
fails the scan.
"""

from __future__ import annotations

from .base import make

__all__ = ["CHECKS", "make"]


def _modules() -> list:
    from . import availability, configuration, cookies, headers, performance, technology, tls

    return [availability, tls, headers, cookies, configuration, technology, performance]


CHECKS = _modules()

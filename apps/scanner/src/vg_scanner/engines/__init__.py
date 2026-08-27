"""Engine registry.

Two tiers, and the split is a business rule rather than a technical one:

  prospecting  what we may point at a company that has never heard of us.
               Passive: reads what a visitor reads, or is performed by a
               third party the way any online checker is.

  authorized   what we may only run once a customer has signed off. These send
               enough traffic to be indistinguishable from an attack.

`vg-scan` will not run an authorized-tier engine without --authorized, which
exists so that the promise on every report stays true.
"""

from __future__ import annotations

from .base import Engine, EngineResult, Target, engines_dir
from .nuclei import NucleiEngine
from .observatory import ObservatoryEngine
from .testssl import TestsslEngine
from .webanalyze import WebanalyzeEngine

PROSPECTING: list[Engine] = [ObservatoryEngine(), WebanalyzeEngine(), TestsslEngine()]
AUTHORIZED: list[Engine] = [NucleiEngine()]

ALL: list[Engine] = [*PROSPECTING, *AUTHORIZED]

BY_NAME = {engine.name: engine for engine in ALL}


def select(
    *, deep: bool = False, authorized: bool = False, only: list[str] | None = None
) -> list[Engine]:
    """Which engines to run for this scan.

    Light engines always; heavy ones on --deep; the authorized tier never without
    explicit authorization, whatever else is asked for.
    """
    if only:
        chosen = [BY_NAME[name] for name in only if name in BY_NAME]
    else:
        chosen = list(PROSPECTING)
        if authorized:
            chosen += AUTHORIZED

    return [
        engine
        for engine in chosen
        if (deep or not engine.heavy)
        and (authorized or not getattr(engine, "requires_authorization", False))
    ]


__all__ = [
    "ALL",
    "AUTHORIZED",
    "BY_NAME",
    "PROSPECTING",
    "Engine",
    "EngineResult",
    "Target",
    "engines_dir",
    "select",
]

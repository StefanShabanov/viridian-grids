"""Local CVE and end-of-life database.

The first version of this was a directory of JSON files with no expiry, which
gets one thing badly wrong: **new vulnerabilities are published against versions
that never change**. A site can sit on PHP 8.0.28 for a year while three more
CVEs are filed against it. A cache without a TTL would keep answering with last
year's list and sound confident about it.

So entries carry a `fetched_at` and go stale. Two questions the store answers:

  which versions have I never looked up?      -> new sites, new upgrades
  which lookups are older than N days?        -> new CVEs against old versions

After the first sweep, enriching a thousand sites is local and instant. A weekly
refresh is what keeps it true.

SQLite because it is one file, needs no server, ships with Python, and can answer
"show me every prospect running something with a critical CVE" - which a pile of
JSON files cannot.
"""

from __future__ import annotations

import json
import sqlite3
from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from pathlib import Path

DEFAULT_PATH = Path.home() / ".cache" / "viridian-grids" / "intel.db"
DEFAULT_MAX_AGE_DAYS = 30

SCHEMA = """
CREATE TABLE IF NOT EXISTS lookup (
    kind        TEXT NOT NULL,        -- 'cve' or 'eol'
    product     TEXT NOT NULL,
    version     TEXT NOT NULL,        -- '' for whole-product lookups such as eol
    payload     TEXT NOT NULL,        -- JSON
    fetched_at  TEXT NOT NULL,
    PRIMARY KEY (kind, product, version)
);
CREATE INDEX IF NOT EXISTS lookup_fetched ON lookup (fetched_at);
"""


@dataclass
class Entry:
    kind: str
    product: str
    version: str
    payload: object
    fetched_at: datetime

    def is_stale(self, max_age_days: int) -> bool:
        return self.fetched_at < datetime.now(UTC) - timedelta(days=max_age_days)


class IntelStore:
    """Version -> vulnerability and end-of-life facts, with an age on every row."""

    def __init__(self, path: Path | None = None, max_age_days: int = DEFAULT_MAX_AGE_DAYS):
        self.path = path or DEFAULT_PATH
        self.max_age_days = max_age_days
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self._connect() as db:
            db.executescript(SCHEMA)

    @contextmanager
    def _connect(self) -> Iterator[sqlite3.Connection]:
        connection = sqlite3.connect(self.path)
        try:
            yield connection
            connection.commit()
        finally:
            connection.close()

    def get(self, kind: str, product: str, version: str = "", *, allow_stale: bool = False):
        """Return the cached payload, or None when missing or too old to trust."""
        with self._connect() as db:
            row = db.execute(
                "SELECT payload, fetched_at FROM lookup WHERE kind=? AND product=? AND version=?",
                (kind, product, version),
            ).fetchone()
        if row is None:
            return None
        entry = Entry(kind, product, version, json.loads(row[0]), datetime.fromisoformat(row[1]))
        if entry.is_stale(self.max_age_days) and not allow_stale:
            return None
        return entry.payload

    def put(self, kind: str, product: str, version: str, payload: object) -> None:
        with self._connect() as db:
            db.execute(
                "INSERT OR REPLACE INTO lookup (kind, product, version, payload, fetched_at) "
                "VALUES (?, ?, ?, ?, ?)",
                (kind, product, version, json.dumps(payload), datetime.now(UTC).isoformat()),
            )

    def stale(self, kind: str = "cve") -> list[tuple[str, str, datetime]]:
        """Lookups old enough that a new CVE could have appeared since."""
        cutoff = (datetime.now(UTC) - timedelta(days=self.max_age_days)).isoformat()
        with self._connect() as db:
            rows = db.execute(
                "SELECT product, version, fetched_at FROM lookup "
                "WHERE kind=? AND fetched_at < ? ORDER BY fetched_at",
                (kind, cutoff),
            ).fetchall()
        return [(r[0], r[1], datetime.fromisoformat(r[2])) for r in rows]

    def stats(self) -> dict[str, int]:
        with self._connect() as db:
            total = db.execute("SELECT COUNT(*) FROM lookup").fetchone()[0]
            cves = db.execute("SELECT COUNT(*) FROM lookup WHERE kind='cve'").fetchone()[0]
            eol = db.execute("SELECT COUNT(*) FROM lookup WHERE kind='eol'").fetchone()[0]
        return {
            "entries": total,
            "cve_lookups": cves,
            "eol_lookups": eol,
            "stale": len(self.stale()),
        }

    def forget(self, kind: str, product: str, version: str = "") -> None:
        with self._connect() as db:
            db.execute(
                "DELETE FROM lookup WHERE kind=? AND product=? AND version=?",
                (kind, product, version),
            )

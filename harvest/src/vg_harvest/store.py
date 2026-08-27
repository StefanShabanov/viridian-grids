"""The prospect list on disk.

One row per business, keyed by domain, merged across runs so a later harvest adds
rather than replaces. The columns line up with ops/crm/prospects.template.csv, so
this file drops straight into the CRM.

It holds names, phone numbers and email addresses of identifiable people, so it is
gitignored and stays that way.
"""

from __future__ import annotations

import csv
from dataclasses import asdict, dataclass, field
from pathlib import Path

FIELDS = (
    "Domain",
    "Company",
    "Industry",
    "City",
    "Phone",
    "Email",
    "Website",
    "Source",
    "OSM id",
    "Notes",
)


@dataclass
class Row:
    domain: str
    company: str = ""
    industry: str = ""
    city: str = ""
    phone: str = ""
    email: str = ""
    website: str = ""
    source: str = ""
    osm_id: str = ""
    notes: str = ""

    def to_csv(self) -> dict[str, str]:
        return {
            "Domain": self.domain,
            "Company": self.company,
            "Industry": self.industry,
            "City": self.city,
            "Phone": self.phone,
            "Email": self.email,
            "Website": self.website,
            "Source": self.source,
            "OSM id": self.osm_id,
            "Notes": self.notes,
        }


@dataclass
class Harvest:
    rows: dict[str, Row] = field(default_factory=dict)

    def add(self, row: Row) -> bool:
        """Add a business. Returns False when the domain was already known.

        Two dentists sharing one domain is a chain, and one row is the right
        answer: we would be selling them one contract, not two.
        """
        existing = self.rows.get(row.domain)
        if existing is None:
            self.rows[row.domain] = row
            return True
        # Keep whichever record carries more contact detail.
        for key, value in asdict(row).items():
            if value and not getattr(existing, key):
                setattr(existing, key, value)
        return False

    def __len__(self) -> int:
        return len(self.rows)


def load(path: Path) -> Harvest:
    harvest = Harvest()
    if not path.exists():
        return harvest
    with path.open(encoding="utf-8-sig", newline="") as handle:
        for record in csv.DictReader(handle):
            domain = (record.get("Domain") or "").strip().lower()
            if not domain:
                continue
            harvest.rows[domain] = Row(
                domain=domain,
                company=record.get("Company", ""),
                industry=record.get("Industry", ""),
                city=record.get("City", ""),
                phone=record.get("Phone", ""),
                email=record.get("Email", ""),
                website=record.get("Website", ""),
                source=record.get("Source", ""),
                osm_id=record.get("OSM id", ""),
                notes=record.get("Notes", ""),
            )
    return harvest


def save(harvest: Harvest, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    ordered = sorted(harvest.rows.values(), key=lambda r: (r.industry, r.city, r.domain))
    # utf-8-sig so Excel opens the Cyrillic company names without an import dialog.
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(FIELDS))
        writer.writeheader()
        for row in ordered:
            writer.writerow(row.to_csv())


def write_domains(harvest: Harvest, path: Path) -> None:
    """Plain domain list, ready for `vg-scan scan -f`."""
    path.parent.mkdir(parents=True, exist_ok=True)
    domains = sorted({row.domain for row in harvest.rows.values()})
    path.write_text("\n".join(domains) + "\n", encoding="utf-8")

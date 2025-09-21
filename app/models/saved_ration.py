"""Models describing persisted rations and comparison outputs for Module 5."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, Iterable, List

from .feed import NutritionalProfile, RationFeedItem


def _now_iso() -> str:
    """Return the current UTC timestamp formatted for JSON serialization."""

    return datetime.utcnow().isoformat(timespec="seconds")


@dataclass(frozen=True)
class SavedRation:
    """Represents a ration stored on disk together with metadata."""

    name: str
    items: List[RationFeedItem]
    created_at: str = field(default_factory=_now_iso)
    updated_at: str = field(default_factory=_now_iso)

    def to_dict(self) -> Dict[str, object]:
        """Serialize the ration into a JSON friendly dictionary."""

        return {
            "name": self.name,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "items": [
                {
                    "name": item.name,
                    "quantity_kg": item.quantity_kg,
                    "use_default_profile": item.use_default_profile,
                    "manual_profile": item.manual_profile.to_dict(),
                }
                for item in self.items
            ],
        }

    @classmethod
    def from_dict(cls, data: Dict[str, object]) -> "SavedRation":
        """Recreate a :class:`SavedRation` from serialized data."""

        items: List[RationFeedItem] = []
        for raw in data.get("items", []):
            profile_data = raw.get("manual_profile", {})  # type: ignore[arg-type]
            profile = NutritionalProfile(
                protein_percent=profile_data.get("protein_percent"),
                energy_mj_per_kg_dm=profile_data.get("energy_mj_per_kg_dm"),
                dry_matter_percent=profile_data.get("dry_matter_percent"),
                fiber_percent=profile_data.get("fiber_percent"),
            )
            items.append(
                RationFeedItem(
                    name=raw.get("name", ""),  # type: ignore[arg-type]
                    quantity_kg=float(raw.get("quantity_kg", 0.0)),
                    use_default_profile=bool(raw.get("use_default_profile", True)),
                    manual_profile=profile,
                )
            )
        created = str(data.get("created_at", _now_iso()))
        updated = str(data.get("updated_at", created))
        return cls(
            name=str(data.get("name", "")),
            items=items,
            created_at=created,
            updated_at=updated,
        )

    def updated_copy(self, items: Iterable[RationFeedItem]) -> "SavedRation":
        """Return a copy with replaced items and refreshed ``updated_at`` value."""

        updated_iso = _now_iso()
        return SavedRation(
            name=self.name,
            items=list(items),
            created_at=self.created_at,
            updated_at=updated_iso,
        )


@dataclass(frozen=True)
class NutrientComparison:
    """Stores formatted information for comparing two ration nutrients."""

    label: str
    first_label: str
    second_label: str
    difference_label: str


@dataclass(frozen=True)
class FeedShareComparison:
    """Represents dry matter share comparison for a single feed."""

    feed_name: str
    first_label: str
    second_label: str
    difference_label: str


@dataclass(frozen=True)
class RationComparison:
    """Aggregates nutrient and feed share comparisons for two rations."""

    first_name: str
    second_name: str
    nutrient_cards: List[NutrientComparison] = field(default_factory=list)
    feed_share_rows: List[FeedShareComparison] = field(default_factory=list)


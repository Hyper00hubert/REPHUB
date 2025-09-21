"""Feed data models.

This module defines data structures representing feed definitions and nutritional values
used throughout the feeding calculator application. Each class contains convenience
methods to support validation and transformation logic for Module 1 (Feed data
management).
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import date
from enum import Enum
from typing import Dict, Iterable, Optional


class FeedType(str, Enum):
    """Enumerates supported feed categories."""

    ROUGHAGE = "roughage"
    CONCENTRATE = "concentrate"

    @classmethod
    def from_label(cls, label: str) -> "FeedType":
        """Return the enum value matching a user-facing label.

        The method is forgiving with regards to casing and whitespace. It raises
        ``ValueError`` when the label cannot be mapped to any known feed type.
        """

        normalized = label.strip().lower()
        mapping = {
            "objętościowa": cls.ROUGHAGE,
            "objetosciowa": cls.ROUGHAGE,
            "roughage": cls.ROUGHAGE,
            "treściwa": cls.CONCENTRATE,
            "tresciwa": cls.CONCENTRATE,
            "concentrate": cls.CONCENTRATE,
        }
        try:
            return mapping[normalized]
        except KeyError as exc:  # pragma: no cover - defensive branch
            raise ValueError(f"Unknown feed type label: {label}") from exc


@dataclass(frozen=True)
class NutritionalProfile:
    """Stores nutritional attributes for a feed item.

    All values are optional to support incomplete datasets. Percentages are expressed
    on fresh matter basis except for energy, which is already expressed per kilogram of
    dry matter (MJ/kg SM).
    """

    protein_percent: Optional[float] = None
    energy_mj_per_kg_dm: Optional[float] = None
    dry_matter_percent: Optional[float] = None
    fiber_percent: Optional[float] = None

    def merged_with(self, other: "NutritionalProfile") -> "NutritionalProfile":
        """Combine two profiles, preferring explicitly provided values.

        ``None`` values in ``self`` are replaced by ``other`` where available. The
        returned instance is a new dataclass copy, keeping the original objects intact.
        """

        data: Dict[str, Optional[float]] = self.__dict__.copy()
        for field, value in other.__dict__.items():
            if data[field] is None and value is not None:
                data[field] = value
        return NutritionalProfile(**data)

    def to_dict(self) -> Dict[str, Optional[float]]:
        """Represent the profile as a plain dictionary suitable for serialization."""

        return dict(self.__dict__)


@dataclass(frozen=True)
class FeedDefinition:
    """Represents a catalog feed entry (default or user defined)."""

    name: str
    feed_type: FeedType
    profile: NutritionalProfile
    source: Optional[str] = None
    added_on: Optional[date] = None
    is_default: bool = False

    def with_profile(self, profile: NutritionalProfile) -> "FeedDefinition":
        """Return a copy of this definition with a different profile."""

        return replace(self, profile=profile)

    def to_dict(self) -> Dict[str, Optional[str]]:
        """Serialize the feed definition to a dictionary for UI consumption."""

        data = {
            "name": self.name,
            "feed_type": self.feed_type.value,
            "source": self.source,
            "added_on": self.added_on.isoformat() if self.added_on else None,
            "is_default": self.is_default,
        }
        data.update(self.profile.to_dict())
        return data


@dataclass
class RationFeedItem:
    """Represents a feed entry in the current ration being composed by the user."""

    name: str
    quantity_kg: float
    use_default_profile: bool
    manual_profile: NutritionalProfile

    def resolve_profile(self, catalog: Iterable[FeedDefinition]) -> NutritionalProfile:
        """Return the nutritional profile that should be used for calculations.

        If ``use_default_profile`` is true, attempt to fetch the default profile from
        the provided catalog definitions. When manual values are provided, they override
        defaults as long as they are not ``None``.
        """

        if not self.use_default_profile:
            return self.manual_profile

        for definition in catalog:
            if definition.name == self.name:
                return self.manual_profile.merged_with(definition.profile)
        return self.manual_profile

    def to_dict(self) -> Dict[str, Optional[str]]:
        """Serialize the ration item for UI components."""

        data = {
            "name": self.name,
            "quantity_kg": self.quantity_kg,
            "use_default_profile": self.use_default_profile,
        }
        data.update(self.manual_profile.to_dict())
        return data

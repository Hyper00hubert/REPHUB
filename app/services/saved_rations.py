"""Persistence utilities for storing and comparing saved rations (Module 5)."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, Iterable, List, Optional

from app.models.feed import RationFeedItem
from app.models.nutrition import NutrientMeasurement, RationAnalysis
from app.models.saved_ration import (
    FeedShareComparison,
    NutrientComparison,
    RationComparison,
    SavedRation,
)


def _default_storage_path() -> Path:
    """Return the default JSON file used to persist saved rations."""

    return Path(__file__).resolve().parents[1] / "data" / "saved_rations.json"


@dataclass
class SavedRationStore:
    """Simple JSON-backed storage for named rations."""

    path: Path = field(default_factory=_default_storage_path)

    def _load_all(self) -> Dict[str, SavedRation]:
        """Return all rations stored on disk indexed by name."""

        if not self.path.exists():
            return {}
        with self.path.open("r", encoding="utf-8") as handle:
            raw = json.load(handle)
        rations = {}
        for entry in raw:
            ration = SavedRation.from_dict(entry)
            if not ration.name:
                continue
            rations[ration.name] = ration
        return rations

    def _write_all(self, rations: Iterable[SavedRation]) -> None:
        """Persist the provided collection of rations to disk."""

        self.path.parent.mkdir(parents=True, exist_ok=True)
        payload = [ration.to_dict() for ration in rations]
        with self.path.open("w", encoding="utf-8") as handle:
            json.dump(payload, handle, ensure_ascii=False, indent=2)

    def list_rations(self) -> List[SavedRation]:
        """Return saved rations ordered by last update descending."""

        rations = list(self._load_all().values())
        return sorted(rations, key=lambda item: item.updated_at, reverse=True)

    def save(self, name: str, items: Iterable[RationFeedItem]) -> SavedRation:
        """Create or update a ration entry with the provided items."""

        rations = self._load_all()
        existing = rations.get(name)
        if existing is None:
            ration = SavedRation(name=name, items=list(items))
        else:
            ration = existing.updated_copy(items)
        rations[name] = ration
        self._write_all(rations.values())
        return ration

    def load(self, name: str) -> SavedRation:
        """Return the ration with ``name`` or raise ``KeyError`` if missing."""

        rations = self._load_all()
        try:
            return rations[name]
        except KeyError as exc:
            raise KeyError(f"Saved ration '{name}' not found") from exc

    def delete(self, name: str) -> None:
        """Remove the ration entry from the persistent store."""

        rations = self._load_all()
        if name not in rations:
            raise KeyError(f"Saved ration '{name}' not found")
        del rations[name]
        self._write_all(rations.values())


def build_nutrient_comparison(
    label: str,
    first: NutrientMeasurement,
    second: NutrientMeasurement,
    unit: str,
) -> NutrientComparison:
    """Return a comparison card with formatted totals and differences."""

    first_label = _format_measurement(first, unit)
    second_label = _format_measurement(second, unit)
    difference_label = _format_difference(first, second, unit)
    return NutrientComparison(
        label=label,
        first_label=first_label,
        second_label=second_label,
        difference_label=difference_label,
    )


def _format_measurement(measurement: NutrientMeasurement, unit: str) -> str:
    """Return a string representation for a nutrient measurement."""

    if measurement.value is None:
        return "brak danych"
    suffix = f"{measurement.value:.2f} {unit}"
    if measurement.is_estimated:
        return f"{suffix} (szac.)"
    return suffix


def _format_difference(first: NutrientMeasurement, second: NutrientMeasurement, unit: str) -> str:
    """Return the signed difference between two measurements."""

    if first.value is None or second.value is None:
        return "–"
    delta = first.value - second.value
    return f"{delta:+.2f} {unit}"


def build_feed_share_rows(
    first: RationAnalysis,
    second: RationAnalysis,
) -> List[FeedShareComparison]:
    """Return dry matter share comparisons for feeds present in either ration."""

    shares: Dict[str, Dict[str, Optional[float]]] = {}
    for contribution in first.contributions:
        shares.setdefault(contribution.name, {})["first"] = contribution.dry_matter_share_percent
    for contribution in second.contributions:
        shares.setdefault(contribution.name, {})["second"] = contribution.dry_matter_share_percent

    rows: List[FeedShareComparison] = []
    for name, values in sorted(shares.items()):
        first_share = values.get("first")
        second_share = values.get("second")
        rows.append(
            FeedShareComparison(
                feed_name=name,
                first_label=_format_optional_percent(first_share),
                second_label=_format_optional_percent(second_share),
                difference_label=_format_percent_difference(first_share, second_share),
            )
        )
    return rows


def _format_optional_percent(value: Optional[float]) -> str:
    """Format optional percentage values with one decimal place."""

    if value is None:
        return "–"
    return f"{value:.1f}%"


def _format_percent_difference(
    first: Optional[float],
    second: Optional[float],
) -> str:
    """Format signed percent differences handling missing values."""

    if first is None or second is None:
        return "–"
    delta = (first or 0.0) - (second or 0.0)
    return f"{delta:+.1f}%"


def build_comparison(
    first_name: str,
    first_analysis: RationAnalysis,
    second_name: str,
    second_analysis: RationAnalysis,
) -> RationComparison:
    """Construct a :class:`RationComparison` from two analyses."""

    nutrient_cards = [
        build_nutrient_comparison(
            "Białko",
            first_analysis.totals.protein,
            second_analysis.totals.protein,
            "kg",
        ),
        build_nutrient_comparison(
            "Energia",
            first_analysis.totals.energy,
            second_analysis.totals.energy,
            "MJ",
        ),
        build_nutrient_comparison(
            "Sucha masa",
            first_analysis.totals.dry_matter,
            second_analysis.totals.dry_matter,
            "kg",
        ),
    ]
    feed_rows = build_feed_share_rows(first_analysis, second_analysis)
    return RationComparison(
        first_name=first_name,
        second_name=second_name,
        nutrient_cards=nutrient_cards,
        feed_share_rows=feed_rows,
    )


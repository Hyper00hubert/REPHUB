"""View-model style data structures for presenting information in the UI."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional

from app.models.herd import HerdProjection, ProductionType
from app.models.nutrition import NutrientMeasurement, RationAnalysis
from app.models.saved_ration import FeedShareComparison, RationComparison, SavedRation


@dataclass(frozen=True)
class FeedRowState:
    """Represents a single row in the ration feed list."""

    name: str
    feed_type_label: str
    quantity_label: str
    dry_matter_label: str
    protein_label: str
    energy_label: str
    fiber_label: str
    uses_default_profile: bool


@dataclass(frozen=True)
class NutrientCardState:
    """Describes a summary card showing nutrient totals."""

    title: str
    total_label: str
    per_animal_label: Optional[str]
    unit: str
    estimated: bool
    missing: bool = False


@dataclass(frozen=True)
class LogisticsCardState:
    """Represents a single logistics metric in the herd panel."""

    label: str
    value_label: str


@dataclass(frozen=True)
class RationScreenState:
    """Aggregates the ration feed rows, nutrient cards and warnings."""

    feed_rows: List[FeedRowState] = field(default_factory=list)
    summary_cards: List[NutrientCardState] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)


@dataclass(frozen=True)
class HerdPanelState:
    """Stores formatted herd projection results for the UI."""

    production_type_label: str
    animal_count_label: str
    per_animal_feed_label: str
    herd_nutrient_cards: List[NutrientCardState] = field(default_factory=list)
    logistics_cards: List[LogisticsCardState] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)


@dataclass(frozen=True)
class SavedRationRowState:
    """Represents a single saved ration entry with formatted metadata."""

    name: str
    subtitle: str


@dataclass(frozen=True)
class SavedComparisonCardState:
    """Summarises a nutrient comparison between two rations."""

    label: str
    first_label: str
    second_label: str
    difference_label: str


@dataclass(frozen=True)
class SavedFeedShareRowState:
    """Presents dry matter share differences for an individual feed."""

    feed_name: str
    first_label: str
    second_label: str
    difference_label: str


@dataclass(frozen=True)
class SavedRationsState:
    """Aggregates saved ration listings and optional comparison details."""

    rows: List[SavedRationRowState] = field(default_factory=list)
    comparison_cards: List[SavedComparisonCardState] = field(default_factory=list)
    feed_share_rows: List[SavedFeedShareRowState] = field(default_factory=list)
    message: Optional[str] = None


def build_feed_row_state(
    name: str,
    feed_type_label: str,
    quantity_kg: float,
    dry_matter: NutrientMeasurement,
    protein: NutrientMeasurement,
    energy: NutrientMeasurement,
    fiber: NutrientMeasurement,
    uses_default_profile: bool,
) -> FeedRowState:
    """Return a ``FeedRowState`` with nicely formatted numeric values."""

    return FeedRowState(
        name=name,
        feed_type_label=feed_type_label,
        quantity_label=f"{quantity_kg:.2f} kg",
        dry_matter_label=_format_measurement(dry_matter, "kg"),
        protein_label=_format_measurement(protein, "kg"),
        energy_label=_format_measurement(energy, "MJ"),
        fiber_label=_format_measurement(fiber, "kg"),
        uses_default_profile=uses_default_profile,
    )


def build_nutrient_card_state(
    title: str,
    totals: NutrientMeasurement,
    per_animal: Optional[NutrientMeasurement],
    unit: str,
) -> NutrientCardState:
    """Create a ``NutrientCardState`` summarising totals and per-animal values."""

    total_label = _format_measurement(totals, unit)
    per_animal_label = None
    per_animal_estimated = False
    if per_animal is not None:
        per_animal_label = _format_measurement(per_animal, unit)
        per_animal_estimated = per_animal.is_estimated
    return NutrientCardState(
        title=title,
        total_label=total_label,
        per_animal_label=per_animal_label,
        unit=unit,
        estimated=bool(totals.is_estimated or per_animal_estimated),
        missing=totals.value is None,
    )


def build_ration_screen_state(
    analysis: RationAnalysis,
    feed_rows: List[FeedRowState],
) -> RationScreenState:
    """Return a ``RationScreenState`` derived from a ration analysis."""

    per_animal = analysis.per_animal
    cards = [
        build_nutrient_card_state("Białko", analysis.totals.protein, per_animal.protein if per_animal else None, "kg"),
        build_nutrient_card_state("Energia", analysis.totals.energy, per_animal.energy if per_animal else None, "MJ"),
        build_nutrient_card_state("Sucha masa", analysis.totals.dry_matter, per_animal.dry_matter if per_animal else None, "kg"),
        build_nutrient_card_state("Włókno", analysis.totals.fiber, per_animal.fiber if per_animal else None, "kg"),
    ]
    return RationScreenState(feed_rows=feed_rows, summary_cards=cards, warnings=analysis.warnings)


def build_herd_panel_state(projection: HerdProjection) -> HerdPanelState:
    """Convert a ``HerdProjection`` into strings ready for display."""

    prod_label = _format_production_type(projection.production_type)
    herd_cards: List[NutrientCardState] = []
    if projection.herd_totals is not None:
        herd_cards = [
            build_nutrient_card_state("Białko (stado)", projection.herd_totals.protein, None, "kg"),
            build_nutrient_card_state("Energia (stado)", projection.herd_totals.energy, None, "MJ"),
            build_nutrient_card_state("Sucha masa (stado)", projection.herd_totals.dry_matter, None, "kg"),
            build_nutrient_card_state("Włókno (stado)", projection.herd_totals.fiber, None, "kg"),
        ]

    logistics = projection.logistics
    logistics_cards = [
        LogisticsCardState("Dzienne zużycie", _format_optional_number(logistics.daily_fresh_mass_kg, "kg")),
        LogisticsCardState("Miesięczne zapotrzebowanie", _format_optional_number(logistics.monthly_fresh_mass_kg, "kg")),
        LogisticsCardState("Załadunki mieszalnika", _format_optional_int(logistics.mixer_loads_per_day)),
        LogisticsCardState("Załadunki paszowozu", _format_optional_int(logistics.wagon_loads_per_day)),
        LogisticsCardState("Wystarczalność zapasu", _format_optional_number(logistics.stock_coverage_days, "dni")),
    ]

    return HerdPanelState(
        production_type_label=prod_label,
        animal_count_label=str(projection.animal_count),
        per_animal_feed_label=_format_optional_number(
            logistics.per_animal_fresh_mass_kg, "kg/szt"
        ),
        herd_nutrient_cards=herd_cards,
        logistics_cards=logistics_cards,
        warnings=projection.warnings,
    )


def build_saved_rations_state(
    rations: List[SavedRation],
    comparison: Optional[RationComparison] = None,
) -> SavedRationsState:
    """Construct a :class:`SavedRationsState` from saved rations and comparison."""

    rows = [build_saved_ration_row_state(ration) for ration in rations]
    message = None if rows else "Brak zapisanych dawek"
    cards: List[SavedComparisonCardState] = []
    shares: List[SavedFeedShareRowState] = []
    if comparison is not None:
        cards = [
            SavedComparisonCardState(
                label=card.label,
                first_label=f"{comparison.first_name}: {card.first_label}",
                second_label=f"{comparison.second_name}: {card.second_label}",
                difference_label=card.difference_label,
            )
            for card in comparison.nutrient_cards
        ]
        shares = [
            SavedFeedShareRowState(
                feed_name=row.feed_name,
                first_label=f"{comparison.first_name}: {row.first_label}",
                second_label=f"{comparison.second_name}: {row.second_label}",
                difference_label=row.difference_label,
            )
            for row in comparison.feed_share_rows
        ]
    return SavedRationsState(
        rows=rows,
        comparison_cards=cards,
        feed_share_rows=shares,
        message=message,
    )


def build_saved_ration_row_state(ration: SavedRation) -> SavedRationRowState:
    """Return a list row state summarising the saved ration metadata."""

    count = len(ration.items)
    item_label = "pasza" if count == 1 else "pasze"
    updated_label = _format_timestamp(ration.updated_at)
    subtitle = f"{count} {item_label} • zaktualizowano {updated_label}"
    return SavedRationRowState(name=ration.name, subtitle=subtitle)


def _format_measurement(measurement: NutrientMeasurement, unit: str) -> str:
    """Return a Polish human readable string for a nutrient measurement."""

    if measurement.value is None:
        return "brak danych"
    value = f"{measurement.value:.2f} {unit}"
    if measurement.is_estimated:
        return f"{value} (szac.)"
    return value


def _format_timestamp(value: str) -> str:
    """Return a user facing date representation from an ISO timestamp."""

    try:
        parsed = datetime.fromisoformat(value)
    except ValueError:
        return value
    return parsed.strftime("%Y-%m-%d %H:%M")


def _format_optional_number(value: Optional[float], unit: str) -> str:
    """Format optional floats with a unit, returning an en dash for missing data."""

    if value is None:
        return "–"
    return f"{value:.2f} {unit}"


def _format_optional_int(value: Optional[int]) -> str:
    """Format optional integers, returning an en dash for missing values."""

    if value is None:
        return "–"
    return str(value)


def _format_production_type(prod: ProductionType) -> str:
    """Return a Polish label for a ``ProductionType`` enum value."""

    return "Mleczne" if prod == ProductionType.MILK else "Opasowe"


def derive_feed_rows(
    analysis: RationAnalysis,
    feed_type_lookup: dict[str, str],
    uses_default_lookup: dict[str, bool],
) -> List[FeedRowState]:
    """Build feed row states from ration analysis and helper lookups."""

    rows: List[FeedRowState] = []
    for contribution in analysis.contributions:
        feed_type_label = feed_type_lookup.get(contribution.name, "–")
        rows.append(
            build_feed_row_state(
                name=contribution.name,
                feed_type_label=feed_type_label,
                quantity_kg=contribution.quantity_kg,
                dry_matter=contribution.dry_matter,
                protein=contribution.protein,
                energy=contribution.energy,
                fiber=contribution.fiber,
                uses_default_profile=uses_default_lookup.get(contribution.name, False),
            )
        )
    return rows


def describe_analysis(
    analysis: RationAnalysis,
    feed_type_lookup: dict[str, str],
    uses_default_lookup: dict[str, bool],
) -> RationScreenState:
    """Convenience helper to build a ``RationScreenState`` from raw inputs."""

    feed_rows = derive_feed_rows(analysis, feed_type_lookup, uses_default_lookup)
    return build_ration_screen_state(analysis, feed_rows)


def describe_projection(projection: HerdProjection) -> HerdPanelState:
    """Wrapper around :func:`build_herd_panel_state` for readability."""

    return build_herd_panel_state(projection)

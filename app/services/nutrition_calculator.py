"""Nutritional calculation services for Module 2."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, List, Optional, Set, Tuple

from app.models.feed import NutritionalProfile, RationFeedItem
from app.models.nutrition import (
    FeedContribution,
    NutrientMeasurement,
    RationAnalysis,
    RationTotals,
)
from app.services.feed_repository import FeedRepository
from app.services.validation import RationValidator


@dataclass
class NutrientAccumulator:
    """Helper accumulating nutrient values across feed contributions."""

    value: float = 0.0
    has_data: bool = False
    estimated: bool = False

    def add(self, measurement: NutrientMeasurement) -> None:
        """Add the provided measurement to the accumulator."""

        if measurement.value is None:
            self.estimated = True
            return
        self.value += measurement.value
        self.has_data = True
        if measurement.is_estimated:
            self.estimated = True

    def to_measurement(self) -> NutrientMeasurement:
        """Transform the accumulator into a :class:`NutrientMeasurement`."""

        if not self.has_data:
            return NutrientMeasurement(value=None, is_estimated=self.estimated)
        return NutrientMeasurement(value=self.value, is_estimated=self.estimated)


class RationCalculator:
    """Perform nutrient calculations for the current ration."""

    def __init__(
        self,
        repository: FeedRepository,
        validator: Optional[RationValidator] = None,
    ) -> None:
        self._repository = repository
        self._validator = validator or RationValidator()

    def calculate(
        self,
        items: Iterable[RationFeedItem],
        animal_count: int | None = None,
    ) -> RationAnalysis:
        """Calculate nutrient contributions and totals for provided ration items."""

        item_list = list(items)
        catalog = self._repository.list_feeds()

        validation = self._validator.validate(item_list, catalog)
        contributions: List[FeedContribution] = []
        warnings: List[str] = list(validation.messages())

        # Prepare accumulators for totals across all feeds.
        dry_matter_acc = NutrientAccumulator()
        protein_acc = NutrientAccumulator()
        energy_acc = NutrientAccumulator()
        fiber_acc = NutrientAccumulator()

        # Compute per-item contributions.
        for item in item_list:
            profile = item.resolve_profile(catalog)
            if item.name in validation.invalid_items:
                contribution = self._empty_contribution(item)
                contributions.append(contribution)
                continue
            invalid_fields = validation.invalid_fields.get(item.name, set())
            contribution, contribution_warnings = self._calculate_contribution(
                item, profile, invalid_fields
            )
            contributions.append(contribution)
            warnings.extend(contribution_warnings)

            dry_matter_acc.add(contribution.dry_matter)
            protein_acc.add(contribution.protein)
            energy_acc.add(contribution.energy)
            fiber_acc.add(contribution.fiber)

        totals = RationTotals(
            dry_matter=dry_matter_acc.to_measurement(),
            protein=protein_acc.to_measurement(),
            energy=energy_acc.to_measurement(),
            fiber=fiber_acc.to_measurement(),
        )

        self._append_estimation_warning("sucha masa", totals.dry_matter, warnings)
        self._append_estimation_warning("białko", totals.protein, warnings)
        self._append_estimation_warning("energia", totals.energy, warnings)
        self._append_estimation_warning("włókno", totals.fiber, warnings)

        per_animal = self._compute_per_animal_totals(totals, animal_count, warnings)
        contributions = self._apply_dry_matter_shares(contributions, totals, warnings)

        return RationAnalysis(
            contributions=contributions,
            totals=totals,
            per_animal=per_animal,
            warnings=warnings,
        )

    def _empty_contribution(self, item: RationFeedItem) -> FeedContribution:
        """Return a contribution placeholder for invalid ration items."""

        empty = NutrientMeasurement(value=None, is_estimated=True)
        return FeedContribution(
            name=item.name,
            quantity_kg=item.quantity_kg,
            dry_matter=empty,
            protein=empty,
            energy=empty,
            fiber=empty,
            dry_matter_share_percent=None,
        )

    def _calculate_contribution(
        self,
        item: RationFeedItem,
        profile: NutritionalProfile,
        invalid_fields: Set[str],
    ) -> Tuple[FeedContribution, List[str]]:
        """Compute nutrient contribution for a single ration item."""

        warnings: List[str] = []

        dry_matter = self._percentage_measurement(
            item,
            profile.dry_matter_percent,
            "sucha masa",
            warnings,
            field_key="dry_matter_percent",
            invalid_fields=invalid_fields,
        )
        protein = self._percentage_measurement(
            item,
            profile.protein_percent,
            "białko",
            warnings,
            field_key="protein_percent",
            invalid_fields=invalid_fields,
        )

        if "energy" in invalid_fields:
            energy = NutrientMeasurement(value=None, is_estimated=True)
        elif dry_matter.value is None or profile.energy_mj_per_kg_dm is None:
            energy = NutrientMeasurement(value=None, is_estimated=True)
            if profile.energy_mj_per_kg_dm is None:
                warnings.append(
                    f"Pasza '{item.name}': brak danych o energii – wynik szacowany."
                )
        else:
            energy = NutrientMeasurement(
                value=dry_matter.value * profile.energy_mj_per_kg_dm,
                is_estimated=dry_matter.is_estimated,
            )

        fiber = self._percentage_measurement(
            item,
            profile.fiber_percent,
            "włókno",
            warnings,
            field_key="fiber_percent",
            invalid_fields=invalid_fields,
        )

        contribution = FeedContribution(
            name=item.name,
            quantity_kg=item.quantity_kg,
            dry_matter=dry_matter,
            protein=protein,
            energy=energy,
            fiber=fiber,
            dry_matter_share_percent=None,
        )
        return contribution, warnings

    def _percentage_measurement(
        self,
        item: RationFeedItem,
        percent_value: float | None,
        nutrient_label: str,
        warnings: List[str],
        *,
        field_key: str,
        invalid_fields: Set[str],
    ) -> NutrientMeasurement:
        """Return nutrient measurement for percentage based attributes."""

        if field_key in invalid_fields:
            return NutrientMeasurement(value=None, is_estimated=True)
        if percent_value is None:
            warnings.append(
                f"Pasza '{item.name}': brak danych dla składnika '{nutrient_label}'."
            )
            return NutrientMeasurement(value=None, is_estimated=True)
        value = item.quantity_kg * (percent_value / 100)
        return NutrientMeasurement(value=value, is_estimated=False)

    def _compute_per_animal_totals(
        self,
        totals: RationTotals,
        animal_count: int | None,
        warnings: List[str],
    ) -> RationTotals | None:
        """Derive per-animal nutrient totals if ``animal_count`` is valid."""

        if animal_count is None:
            return None
        if animal_count <= 0:
            warnings.append("Liczba zwierząt musi być dodatnia, pominięto przeliczenie na sztukę.")
            return None

        return RationTotals(
            dry_matter=self._divide_measurement(totals.dry_matter, animal_count),
            protein=self._divide_measurement(totals.protein, animal_count),
            energy=self._divide_measurement(totals.energy, animal_count),
            fiber=self._divide_measurement(totals.fiber, animal_count),
        )

    def _divide_measurement(
        self, measurement: NutrientMeasurement, divisor: int
    ) -> NutrientMeasurement:
        """Divide nutrient values by ``divisor`` while keeping estimation metadata."""

        if measurement.value is None:
            return NutrientMeasurement(value=None, is_estimated=True)
        return NutrientMeasurement(
            value=measurement.value / divisor,
            is_estimated=measurement.is_estimated,
        )

    def _apply_dry_matter_shares(
        self,
        contributions: List[FeedContribution],
        totals: RationTotals,
        warnings: List[str],
    ) -> List[FeedContribution]:
        """Populate the dry matter share for each contribution."""

        total_dm = totals.dry_matter.value
        if total_dm in (None, 0):
            if totals.dry_matter.value is None:
                warnings.append(
                    "Nie można obliczyć udziałów suchej masy z powodu brakujących danych."
                )
            return contributions

        updated: List[FeedContribution] = []
        for contribution in contributions:
            if contribution.dry_matter.value is None:
                updated.append(contribution)
                continue
            share = (contribution.dry_matter.value / total_dm) * 100
            updated.append(
                FeedContribution(
                    name=contribution.name,
                    quantity_kg=contribution.quantity_kg,
                    dry_matter=contribution.dry_matter,
                    protein=contribution.protein,
                    energy=contribution.energy,
                    fiber=contribution.fiber,
                    dry_matter_share_percent=round(share, 2),
                )
            )
        return updated

    def _append_estimation_warning(
        self, label: str, measurement: NutrientMeasurement, warnings: List[str]
    ) -> None:
        """Add a warning when the provided measurement was estimated."""

        if measurement.is_estimated:
            warnings.append(
                f"Suma składnika '{label}' została oszacowana z powodu braków w danych."
            )


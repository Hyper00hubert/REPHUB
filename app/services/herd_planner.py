"""Herd-level planning services for Module 3."""

from __future__ import annotations

from dataclasses import dataclass
from math import ceil
from typing import Iterable, List, Optional, Tuple

from app.models.feed import RationFeedItem
from app.models.herd import HerdLogisticsSummary, HerdProjection, ProductionType
from app.models.nutrition import NutrientMeasurement, RationAnalysis, RationTotals
from app.services.nutrition_calculator import RationCalculator


@dataclass
class HerdPlanner:
    """Combine ration analytics with herd logistics calculations."""

    calculator: RationCalculator

    def plan(
        self,
        items: Iterable[RationFeedItem],
        animal_count: int,
        production_type: ProductionType,
        mixer_capacity_kg: Optional[float] = None,
        wagon_capacity_kg: Optional[float] = None,
        stock_mass_kg: Optional[float] = None,
    ) -> HerdProjection:
        """Return an aggregated herd projection for the provided parameters."""

        item_list = list(items)
        analysis = self.calculator.calculate(item_list, animal_count=animal_count)
        herd_totals, herd_warnings = self._scale_totals(analysis, animal_count)
        logistics, logistic_warnings = self._build_logistics(
            item_list,
            animal_count,
            mixer_capacity_kg,
            wagon_capacity_kg,
            stock_mass_kg,
        )

        warnings = list(analysis.warnings)
        warnings.extend(herd_warnings)
        warnings.extend(logistic_warnings)

        return HerdProjection(
            analysis=analysis,
            production_type=production_type,
            animal_count=animal_count,
            herd_totals=herd_totals,
            logistics=logistics,
            warnings=warnings,
        )

    def _scale_totals(
        self, analysis: RationAnalysis, animal_count: int
    ) -> Tuple[Optional[RationTotals], List[str]]:
        """Return ration totals scaled to the entire herd when possible."""

        warnings: List[str] = []
        if animal_count <= 0:
            warnings.append(
                "Nie można przeliczyć składników na całe stado przy niedodatniej liczbie zwierząt.",
            )
            return None, warnings

        per_animal = analysis.per_animal
        if per_animal is None:
            warnings.append(
                "Brak danych o składnikach na sztukę – pominięto przeliczenie dla stada.",
            )
            return None, warnings

        return (
            RationTotals(
                dry_matter=self._multiply_measurement(per_animal.dry_matter, animal_count),
                protein=self._multiply_measurement(per_animal.protein, animal_count),
                energy=self._multiply_measurement(per_animal.energy, animal_count),
                fiber=self._multiply_measurement(per_animal.fiber, animal_count),
            ),
            warnings,
        )

    def _multiply_measurement(
        self, measurement: NutrientMeasurement, multiplier: int
    ) -> NutrientMeasurement:
        """Scale nutrient values while keeping estimation metadata intact."""

        if measurement.value is None:
            return NutrientMeasurement(value=None, is_estimated=True)
        return NutrientMeasurement(
            value=measurement.value * multiplier,
            is_estimated=measurement.is_estimated,
        )

    def _build_logistics(
        self,
        items: Iterable[RationFeedItem],
        animal_count: int,
        mixer_capacity_kg: Optional[float],
        wagon_capacity_kg: Optional[float],
        stock_mass_kg: Optional[float],
    ) -> Tuple[HerdLogisticsSummary, List[str]]:
        """Calculate feed mass requirements and logistics indicators."""

        warnings: List[str] = []
        per_animal_fresh_mass = sum(item.quantity_kg for item in items)

        if animal_count <= 0:
            warnings.append(
                "Liczba zwierząt musi być dodatnia, aby policzyć zapotrzebowanie stada.",
            )
            daily_total = None
        else:
            daily_total = per_animal_fresh_mass * animal_count

        monthly_total = daily_total * 30 if daily_total is not None else None
        mixer_loads = self._compute_loads(daily_total, mixer_capacity_kg, "mieszalnika", warnings)
        wagon_loads = self._compute_loads(daily_total, wagon_capacity_kg, "paszowozu", warnings)
        stock_days = self._compute_stock_coverage(daily_total, stock_mass_kg, warnings)

        return (
            HerdLogisticsSummary(
                per_animal_fresh_mass_kg=per_animal_fresh_mass,
                daily_fresh_mass_kg=daily_total,
                monthly_fresh_mass_kg=monthly_total,
                mixer_loads_per_day=mixer_loads,
                wagon_loads_per_day=wagon_loads,
                stock_coverage_days=stock_days,
            ),
            warnings,
        )

    def _compute_loads(
        self,
        daily_total: Optional[float],
        capacity: Optional[float],
        label: str,
        warnings: List[str],
    ) -> Optional[int]:
        """Return number of loads needed per day for the specified capacity."""

        if capacity is None:
            return None
        if capacity <= 0:
            warnings.append(
                f"Pojemność {label} musi być dodatnia, pominięto obliczenie liczby załadunków.",
            )
            return None
        if daily_total is None:
            return None
        return int(ceil(daily_total / capacity))

    def _compute_stock_coverage(
        self,
        daily_total: Optional[float],
        stock_mass_kg: Optional[float],
        warnings: List[str],
    ) -> Optional[float]:
        """Return number of days the provided stock will last."""

        if stock_mass_kg is None:
            return None
        if stock_mass_kg <= 0:
            warnings.append("Zapas paszy musi być dodatni, aby obliczyć wystarczalność.")
            return None
        if daily_total is None or daily_total == 0:
            return None
        return round(stock_mass_kg / daily_total, 2)


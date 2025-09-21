"""Nutritional calculation result models for Module 2.

This module defines lightweight data containers describing the output of the
nutritional calculator. They are used both by the service layer and, later on,
by the KivyMD user interface. Each model stores the computed value together
with metadata explaining whether a value was estimated due to missing input
data so that the UI can display the appropriate warnings.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional


@dataclass(frozen=True)
class NutrientMeasurement:
    """Stores the numeric value of a nutrient along with estimation metadata."""

    value: Optional[float]
    is_estimated: bool = False

    def normalized(self) -> Optional[float]:
        """Return the stored value rounded to three decimals for presentation."""

        if self.value is None:
            return None
        return round(self.value, 3)


@dataclass(frozen=True)
class FeedContribution:
    """Represents a single feed's contribution to the ration totals."""

    name: str
    quantity_kg: float
    dry_matter: NutrientMeasurement
    protein: NutrientMeasurement
    energy: NutrientMeasurement
    fiber: NutrientMeasurement
    dry_matter_share_percent: Optional[float]


@dataclass(frozen=True)
class RationTotals:
    """Aggregated nutrient values for the whole ration or per animal."""

    dry_matter: NutrientMeasurement
    protein: NutrientMeasurement
    energy: NutrientMeasurement
    fiber: NutrientMeasurement


@dataclass(frozen=True)
class RationAnalysis:
    """Stores the complete output of a ration calculation run."""

    contributions: List[FeedContribution]
    totals: RationTotals
    per_animal: Optional[RationTotals]
    warnings: List[str]


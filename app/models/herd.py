"""Herd-level planning data models for Module 3.

This module defines domain structures that represent the results of the herd
planning computations. They encapsulate the derived daily and monthly feed
requirements for the whole herd together with metadata required by the user
interface layer. The models complement the nutritional outputs calculated in
Module 2 and provide a foundation for the farmer panel logic implemented later
in the KivyMD application.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import List, Optional

from app.models.nutrition import RationAnalysis, RationTotals


class ProductionType(str, Enum):
    """Enumerates supported production profiles for the herd."""

    MILK = "milk"
    BEEF = "beef"

    @classmethod
    def from_label(cls, label: str) -> "ProductionType":
        """Return the enum value matching a human readable label.

        The helper is tolerant towards casing and Polish diacritics so that UI
        inputs can be mapped safely regardless of the text entered by the user.
        An informative ``ValueError`` is raised when the label is unknown.
        """

        normalized = label.strip().lower()
        mapping = {
            "mleczne": cls.MILK,
            "produkcja mleczna": cls.MILK,
            "milk": cls.MILK,
            "opasowe": cls.BEEF,
            "produkcja opasowa": cls.BEEF,
            "beef": cls.BEEF,
        }
        try:
            return mapping[normalized]
        except KeyError as exc:  # pragma: no cover - defensive branch
            raise ValueError(f"Unknown production type label: {label}") from exc


@dataclass(frozen=True)
class HerdLogisticsSummary:
    """Stores calculated feed logistics for the entire herd."""

    per_animal_fresh_mass_kg: Optional[float]
    daily_fresh_mass_kg: Optional[float]
    monthly_fresh_mass_kg: Optional[float]
    mixer_loads_per_day: Optional[int]
    wagon_loads_per_day: Optional[int]
    stock_coverage_days: Optional[float]


@dataclass(frozen=True)
class HerdProjection:
    """Aggregates Module 3 outputs including nutrition and logistics."""

    analysis: RationAnalysis
    production_type: ProductionType
    animal_count: int
    herd_totals: Optional[RationTotals]
    logistics: HerdLogisticsSummary
    warnings: List[str]


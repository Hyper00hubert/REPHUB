"""Tests covering Module 3 herd planning computations."""

from __future__ import annotations

import pytest

from app.models.herd import ProductionType
from app.services.feed_repository import FeedRepository
from app.services.herd_planner import HerdPlanner
from app.services.nutrition_calculator import RationCalculator


@pytest.fixture()
def repository() -> FeedRepository:
    """Return a feed repository populated with default data."""

    return FeedRepository()


@pytest.fixture()
def planner(repository: FeedRepository) -> HerdPlanner:
    """Return a planner composed of the repository and ration calculator."""

    calculator = RationCalculator(repository)
    return HerdPlanner(calculator)


def _reference_items(repository: FeedRepository):
    """Return ration items matching the specification reference ration."""

    return [
        repository.create_ration_item("Kiszonka z kukurydzy", quantity_kg=12.0),
        repository.create_ration_item("Śruta sojowa", quantity_kg=4.0),
        repository.create_ration_item("Wysłodki buraczane (susz)", quantity_kg=3.0),
    ]


def test_plan_returns_combined_projection(
    planner: HerdPlanner, repository: FeedRepository
) -> None:
    """Ensure herd planner composes nutritional and logistics outputs."""

    projection = planner.plan(
        _reference_items(repository),
        animal_count=30,
        production_type=ProductionType.MILK,
        mixer_capacity_kg=500.0,
        wagon_capacity_kg=600.0,
        stock_mass_kg=25_000.0,
    )

    assert projection.analysis.totals.dry_matter.value == pytest.approx(10.06, rel=1e-3)
    assert projection.analysis.per_animal is not None

    logistics = projection.logistics
    assert logistics.per_animal_fresh_mass_kg == pytest.approx(19.0)
    assert logistics.daily_fresh_mass_kg == pytest.approx(570.0)
    assert logistics.monthly_fresh_mass_kg == pytest.approx(17_100.0)
    assert logistics.mixer_loads_per_day == 2
    assert logistics.wagon_loads_per_day == 1
    assert logistics.stock_coverage_days == pytest.approx(43.86, rel=1e-3)

    herd_totals = projection.herd_totals
    assert herd_totals is not None
    assert herd_totals.dry_matter.value == pytest.approx(
        projection.analysis.per_animal.dry_matter.value * projection.animal_count,
        rel=1e-3,
    )
    assert projection.warnings == []


def test_plan_handles_invalid_parameters(
    planner: HerdPlanner, repository: FeedRepository
) -> None:
    """Invalid numeric inputs should produce warnings and omit calculations."""

    projection = planner.plan(
        _reference_items(repository),
        animal_count=0,
        production_type=ProductionType.BEEF,
        mixer_capacity_kg=-100.0,
        wagon_capacity_kg=None,
        stock_mass_kg=-500.0,
    )

    assert projection.herd_totals is None
    assert projection.logistics.daily_fresh_mass_kg is None
    assert projection.logistics.mixer_loads_per_day is None
    assert projection.logistics.stock_coverage_days is None
    assert any("Liczba zwierząt" in warning for warning in projection.warnings)
    assert any("Pojemność" in warning for warning in projection.warnings)
    assert any("Zapas paszy" in warning for warning in projection.warnings)

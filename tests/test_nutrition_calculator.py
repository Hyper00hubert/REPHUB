"""Tests covering Module 2 nutritional calculations."""

from __future__ import annotations

import pytest

from app.models.feed import NutritionalProfile
from app.services.feed_repository import FeedRepository
from app.services.nutrition_calculator import RationCalculator


@pytest.fixture()
def repository() -> FeedRepository:
    """Return a feed repository populated with default data."""

    return FeedRepository()


@pytest.fixture()
def calculator(repository: FeedRepository) -> RationCalculator:
    """Return a calculator instance backed by the default feed repository."""

    return RationCalculator(repository)


def test_calculate_ration_totals_with_defaults(
    calculator: RationCalculator, repository: FeedRepository
) -> None:
    """Verify totals using the reference ration described in the specification."""

    items = [
        repository.create_ration_item("Kiszonka z kukurydzy", quantity_kg=12.0),
        repository.create_ration_item("Śruta sojowa", quantity_kg=4.0),
        repository.create_ration_item("Wysłodki buraczane (susz)", quantity_kg=3.0),
    ]

    result = calculator.calculate(items, animal_count=30)

    assert pytest.approx(result.totals.dry_matter.value, rel=1e-4) == 10.06
    assert not result.totals.dry_matter.is_estimated
    assert pytest.approx(result.totals.protein.value, rel=1e-4) == 3.03
    assert pytest.approx(result.totals.energy.value, rel=1e-4) == 69.99
    assert pytest.approx(result.totals.fiber.value, rel=1e-4) == 3.0

    assert result.per_animal is not None
    assert pytest.approx(result.per_animal.dry_matter.value, rel=1e-4) == 0.3353333
    assert pytest.approx(result.per_animal.energy.value, rel=1e-4) == 2.333

    shares = {item.name: item.dry_matter_share_percent for item in result.contributions}
    assert shares == {
        "Kiszonka z kukurydzy": pytest.approx(38.19, rel=1e-3),
        "Śruta sojowa": pytest.approx(34.97, rel=1e-3),
        "Wysłodki buraczane (susz)": pytest.approx(26.85, rel=1e-3),
    }

    assert result.warnings == []


def test_calculate_handles_missing_data(
    calculator: RationCalculator, repository: FeedRepository
) -> None:
    """Missing nutritional fields should trigger warnings and estimated totals."""

    manual_profile = NutritionalProfile(fiber_percent=10.0)
    item = repository.create_ration_item(
        "Test pasza",
        quantity_kg=5.0,
        use_default_profile=False,
        manual_profile=manual_profile,
    )

    result = calculator.calculate([item])

    assert result.totals.dry_matter.value is None
    assert result.totals.dry_matter.is_estimated
    assert result.totals.energy.value is None
    assert result.totals.energy.is_estimated
    assert result.contributions[0].fiber.value == pytest.approx(0.5)

    assert any("brak danych" in warning for warning in result.warnings)
    assert any("Nie można obliczyć udziałów suchej masy" in warning for warning in result.warnings)


def test_calculate_warns_on_empty_ration(calculator: RationCalculator) -> None:
    """Empty ration lists should surface a helpful warning instead of crashing."""

    result = calculator.calculate([])

    assert result.contributions == []
    assert any("Dawka nie zawiera żadnych pasz" in warning for warning in result.warnings)


def test_calculate_skips_invalid_quantities(
    calculator: RationCalculator, repository: FeedRepository
) -> None:
    """Non-positive quantities should be ignored with a dedicated validation message."""

    invalid_item = repository.create_ration_item(
        "Kiszonka z kukurydzy",
        quantity_kg=0.0,
        use_default_profile=True,
    )

    result = calculator.calculate([invalid_item])

    assert result.contributions[0].dry_matter.value is None
    assert any("ilość musi być dodatnia" in warning for warning in result.warnings)


def test_calculate_marks_out_of_range_percentages(
    calculator: RationCalculator, repository: FeedRepository
) -> None:
    """Percentages outside the 0-100 range should be ignored with warnings."""

    manual_profile = NutritionalProfile(protein_percent=150.0, dry_matter_percent=-5.0)
    item = repository.create_ration_item(
        "Eksperymentalna",
        quantity_kg=5.0,
        use_default_profile=False,
        manual_profile=manual_profile,
    )

    result = calculator.calculate([item])

    contribution = result.contributions[0]
    assert contribution.protein.value is None
    assert contribution.dry_matter.value is None
    assert any("zakresie 0-100" in warning for warning in result.warnings)


def test_calculate_marks_invalid_energy(
    calculator: RationCalculator, repository: FeedRepository
) -> None:
    """Negative energy values should be removed from calculations."""

    manual_profile = NutritionalProfile(
        protein_percent=12.0,
        dry_matter_percent=30.0,
        energy_mj_per_kg_dm=-1.0,
    )
    item = repository.create_ration_item(
        "Energia błędna",
        quantity_kg=4.0,
        use_default_profile=False,
        manual_profile=manual_profile,
    )

    result = calculator.calculate([item])

    assert result.contributions[0].energy.value is None
    assert any("energia metab." in warning for warning in result.warnings)

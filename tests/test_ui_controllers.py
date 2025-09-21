"""Tests verifying the Module 4 UI controllers and state formatting."""

from __future__ import annotations

from pathlib import Path

import pytest

from app.services import (
    FeedRepository,
    HerdPlanner,
    RationCalculator,
    RationManager,
    SavedRationStore,
)
from app.ui import AppController


@pytest.fixture
def controller(tmp_path: Path) -> AppController:
    """Return an ``AppController`` populated with the reference ration."""

    repository = FeedRepository()
    ration_manager = RationManager(repository)
    calculator = RationCalculator(repository)
    planner = HerdPlanner(calculator)
    store = SavedRationStore(path=tmp_path / "saved.json")
    controller = AppController.from_services(
        repository,
        ration_manager,
        calculator,
        planner,
        store,
    )
    controller.prepare_sample_ration()
    return controller


def test_ration_screen_state_uses_expected_formatting(controller: AppController) -> None:
    """Ration screen state should expose formatted values for the sample ration."""

    state = controller.ration_controller.build_state(animal_count=30)

    assert len(state.feed_rows) == 3
    first = state.feed_rows[0]
    assert first.name == "Kiszonka z kukurydzy"
    assert first.quantity_label == "12.00 kg"
    assert first.dry_matter_label == "3.84 kg"
    assert first.protein_label == "0.96 kg"

    cards = {card.title: card for card in state.summary_cards}
    assert cards["Białko"].total_label == "3.03 kg"
    assert cards["Białko"].per_animal_label == "0.10 kg"
    assert cards["Energia"].total_label == "69.99 MJ"
    assert cards["Sucha masa"].total_label == "10.06 kg"
    assert state.warnings == []


def test_herd_panel_state_displays_logistics(controller: AppController) -> None:
    """Herd panel should expose logistics values and derived warnings."""

    state = controller.herd_controller.build_state(
        animal_count=30,
        production_label="mleczne",
        mixer_capacity_kg=500,
        wagon_capacity_kg=500,
        stock_mass_kg=25000,
    )

    assert state.production_type_label == "Mleczne"
    assert state.animal_count_label == "30"
    assert state.per_animal_feed_label == "19.00 kg/szt"

    logistics = {card.label: card.value_label for card in state.logistics_cards}
    assert logistics["Dzienne zużycie"] == "570.00 kg"
    assert logistics["Miesięczne zapotrzebowanie"] == "17100.00 kg"
    assert logistics["Załadunki mieszalnika"] == "2"
    assert logistics["Wystarczalność zapasu"] == "43.86 dni"
    assert state.warnings == []


def test_prepare_sample_ration_populates_manager(tmp_path: Path) -> None:
    """Calling ``prepare_sample_ration`` should preload the reference diet."""

    repository = FeedRepository()
    ration_manager = RationManager(repository)
    calculator = RationCalculator(repository)
    planner = HerdPlanner(calculator)
    store = SavedRationStore(path=tmp_path / "store.json")
    controller = AppController.from_services(
        repository,
        ration_manager,
        calculator,
        planner,
        store,
    )

    assert controller.ration_controller.ration_manager.list_items() == []
    controller.prepare_sample_ration()
    assert len(controller.ration_controller.ration_manager.list_items()) == 3


def test_saved_rations_controller_persists_and_compares(controller: AppController) -> None:
    """The saved rations controller should persist entries and provide comparisons."""

    controller.saved_controller.save_current("Referencyjna")
    # Modify ration and save a variant for comparison.
    manager = controller.ration_controller.ration_manager
    item = manager.list_items()[0]
    manager.add_or_update_item(
        type(item)(
            name=item.name,
            quantity_kg=item.quantity_kg + 1.0,
            use_default_profile=item.use_default_profile,
            manual_profile=item.manual_profile,
        )
    )
    controller.saved_controller.save_current("Podbity udział")

    state = controller.saved_controller.build_state(
        comparison_pair=("Podbity udział", "Referencyjna"),
        animal_count=30,
    )

    assert any(row.name == "Referencyjna" for row in state.rows)
    assert any(card.label == "Sucha masa" for card in state.comparison_cards)
    assert state.feed_share_rows, "Comparison should list feed share differences"

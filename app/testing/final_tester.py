"""Final user walkthrough helpers that simulate an end-to-end application session."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from app.models.feed import NutritionalProfile, RationFeedItem
from app.services import (
    FeedRepository,
    HerdPlanner,
    RationCalculator,
    RationManager,
    SavedRationStore,
)
from app.ui import AppController, HerdPanelState, RationScreenState, SavedRationsState


@dataclass(frozen=True)
class WalkthroughReport:
    """Collects UI states captured during the final tester walkthrough."""

    reference_state: RationScreenState
    manual_state: RationScreenState
    final_state: RationScreenState
    herd_state: HerdPanelState
    saved_state: SavedRationsState


class FinalTester:
    """Drive a scripted scenario exercising all key modules of the application."""

    def __init__(self, storage_path: Optional[Path] = None) -> None:
        store = SavedRationStore(path=storage_path) if storage_path else SavedRationStore()
        repository = FeedRepository()
        ration_manager = RationManager(repository)
        calculator = RationCalculator(repository)
        planner = HerdPlanner(calculator)
        self._controller = AppController.from_services(
            repository,
            ration_manager,
            calculator,
            planner,
            store,
        )

    @property
    def controller(self) -> AppController:
        """Return the lazily prepared :class:`AppController` instance."""

        return self._controller

    def run_walkthrough(
        self,
        *,
        animal_count: int = 30,
        production_label: str = "mleczne",
        mixer_capacity_kg: float = 500.0,
        wagon_capacity_kg: float = 500.0,
        stock_mass_kg: float = 25_000.0,
    ) -> WalkthroughReport:
        """Execute the scripted scenario and return the captured UI states."""

        controller = self.controller
        controller.prepare_sample_ration()
        reference_state = controller.ration_controller.build_state(animal_count=animal_count)
        controller.saved_controller.save_current("Dawka referencyjna")

        manual_state = self._prepare_manual_variant(animal_count)
        controller.saved_controller.save_current("Dawka ręczna testowa")

        controller.saved_controller.load_into_manager("Dawka referencyjna")
        final_state = controller.ration_controller.build_state(animal_count=animal_count)

        herd_state = controller.herd_controller.build_state(
            animal_count=animal_count,
            production_label=production_label,
            mixer_capacity_kg=mixer_capacity_kg,
            wagon_capacity_kg=wagon_capacity_kg,
            stock_mass_kg=stock_mass_kg,
        )

        saved_state = controller.saved_controller.build_state(
            comparison_pair=("Dawka ręczna testowa", "Dawka referencyjna"),
            animal_count=animal_count,
        )

        return WalkthroughReport(
            reference_state=reference_state,
            manual_state=manual_state,
            final_state=final_state,
            herd_state=herd_state,
            saved_state=saved_state,
        )

    def _prepare_manual_variant(self, animal_count: int) -> RationScreenState:
        """Adjust the sample ration to use manual data, returning updated UI state."""

        controller = self.controller
        manager = controller.ration_controller.ration_manager
        repository = controller.ration_controller.repository
        items = manager.list_items()
        if not items:
            raise ValueError("Brak pasz w dawce – przygotuj dawkę referencyjną wcześniej.")
        base_item = items[0]
        definition = repository.get_feed(base_item.name)
        default_profile = definition.profile if definition else NutritionalProfile()
        manual_profile = NutritionalProfile(
            protein_percent=(default_profile.protein_percent or 0.0) + 1.0,
            energy_mj_per_kg_dm=None,
            dry_matter_percent=default_profile.dry_matter_percent,
            fiber_percent=default_profile.fiber_percent,
        )
        updated_item = RationFeedItem(
            name=base_item.name,
            quantity_kg=base_item.quantity_kg + 1.0,
            use_default_profile=False,
            manual_profile=manual_profile,
        )
        manager.add_or_update_item(updated_item)
        return controller.ration_controller.build_state(animal_count=animal_count)

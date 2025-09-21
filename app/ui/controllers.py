"""Controllers translating domain services into UI friendly state objects."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, Tuple

from app.models.feed import FeedType
from app.models.herd import ProductionType
from app.models.saved_ration import RationComparison
from app.services.feed_repository import FeedRepository, RationManager
from app.services.herd_planner import HerdPlanner
from app.services.nutrition_calculator import RationCalculator
from app.services.saved_rations import SavedRationStore, build_comparison

from .state import (
    HerdPanelState,
    RationScreenState,
    SavedRationsState,
    build_saved_rations_state,
    describe_analysis,
    describe_projection,
)


@dataclass
class RationScreenController:
    """Build the ration composition screen state using Module 1 and 2 services."""

    repository: FeedRepository
    ration_manager: RationManager
    calculator: RationCalculator

    def build_state(self, animal_count: Optional[int] = None) -> RationScreenState:
        """Return a :class:`RationScreenState` describing the current ration."""

        items = self.ration_manager.list_items()
        analysis = self.calculator.calculate(items, animal_count=animal_count)
        feed_type_lookup = {
            definition.name: _format_feed_type(definition.feed_type)
            for definition in self.repository.list_feeds()
        }
        uses_default_lookup = {
            item.name: item.use_default_profile for item in items
        }
        return describe_analysis(analysis, feed_type_lookup, uses_default_lookup)


@dataclass
class HerdPanelController:
    """Build the herd projection tab state using Module 3 services."""

    planner: HerdPlanner
    ration_manager: RationManager

    def build_state(
        self,
        animal_count: int,
        production_label: str,
        mixer_capacity_kg: Optional[float] = None,
        wagon_capacity_kg: Optional[float] = None,
        stock_mass_kg: Optional[float] = None,
    ) -> HerdPanelState:
        """Return formatted herd projection results for UI presentation."""

        try:
            production_type = ProductionType.from_label(production_label)
        except ValueError as exc:
            raise ValueError(f"Nieznany typ produkcji: {production_label}") from exc
        items = self.ration_manager.list_items()
        projection = self.planner.plan(
            items,
            animal_count=animal_count,
            production_type=production_type,
            mixer_capacity_kg=mixer_capacity_kg,
            wagon_capacity_kg=wagon_capacity_kg,
            stock_mass_kg=stock_mass_kg,
        )
        return describe_projection(projection)


@dataclass
class SavedRationsController:
    """Placeholder controller for Module 5 features."""

    store: SavedRationStore
    ration_manager: RationManager
    calculator: RationCalculator

    def build_state(
        self,
        comparison_pair: Optional[Tuple[str, str]] = None,
        animal_count: Optional[int] = None,
    ) -> SavedRationsState:
        """Return list of saved rations and optional comparison summary."""

        rations = self.store.list_rations()
        comparison = None
        if comparison_pair is not None:
            comparison = self.compare_rations(
                comparison_pair[0],
                comparison_pair[1],
                animal_count=animal_count,
            )
        return build_saved_rations_state(rations, comparison)

    def save_current(self, name: str) -> None:
        """Persist the ration currently held by the ration manager."""

        items = self.ration_manager.list_items()
        if not items:
            raise ValueError("Aktualna dawka jest pusta – dodaj pasze przed zapisem.")
        self.store.save(name, items)

    def load_into_manager(self, name: str) -> None:
        """Replace the current ration with a stored entry."""

        ration = self.store.load(name)
        self.ration_manager.replace_items(ration.items)

    def delete(self, name: str) -> None:
        """Remove a ration from the persistent store."""

        self.store.delete(name)

    def compare_rations(
        self,
        first: str,
        second: str,
        animal_count: Optional[int] = None,
    ) -> RationComparison:
        """Return comparison details for two saved ration entries."""

        first_ration = self.store.load(first)
        second_ration = self.store.load(second)
        first_analysis = self.calculator.calculate(first_ration.items, animal_count=animal_count)
        second_analysis = self.calculator.calculate(second_ration.items, animal_count=animal_count)
        return build_comparison(first, first_analysis, second, second_analysis)


@dataclass
class AppController:
    """High level façade wiring together screen controllers for the UI."""

    ration_controller: RationScreenController
    herd_controller: HerdPanelController
    saved_controller: SavedRationsController

    @classmethod
    def from_services(
        cls,
        repository: FeedRepository,
        ration_manager: RationManager,
        calculator: RationCalculator,
        planner: HerdPlanner,
        store: Optional[SavedRationStore] = None,
    ) -> "AppController":
        """Convenience factory to instantiate the controller tree."""

        ration = RationScreenController(repository, ration_manager, calculator)
        herd = HerdPanelController(planner, ration_manager)
        saved_store = store or SavedRationStore()
        saved = SavedRationsController(saved_store, ration_manager, calculator)
        return cls(ration_controller=ration, herd_controller=herd, saved_controller=saved)



    def prepare_sample_ration(self) -> None:
        """Populate the ration manager with the example diet if empty."""

        if self.ration_controller.ration_manager.list_items():
            return
        repository = self.ration_controller.repository
        manager = self.ration_controller.ration_manager
        samples = [
            ("Kiszonka z kukurydzy", 12.0),
            ("Śruta sojowa", 4.0),
            ("Wysłodki buraczane (susz)", 3.0),
        ]
        for name, quantity in samples:
            try:
                item = repository.create_ration_item(name=name, quantity_kg=quantity)
            except KeyError:
                # Skip feeds missing from the catalog.
                continue
            manager.add_or_update_item(item)

def _format_feed_type(feed_type: FeedType) -> str:
    """Return a Polish label for feed type values used in the UI."""

    if feed_type == FeedType.ROUGHAGE:
        return "Objętościowa"
    if feed_type == FeedType.CONCENTRATE:
        return "Treściwa"
    return feed_type.value

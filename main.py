"""Executable entry point launching the KivyMD cattle ration planner."""

from __future__ import annotations

from app.services import (
    FeedRepository,
    HerdPlanner,
    RationCalculator,
    RationManager,
    SavedRationStore,
)
from app.ui import AppController, NutritionPlannerApp


def build_controller() -> AppController:
    """Construct an :class:`AppController` wired with default services."""

    repository = FeedRepository()
    ration_manager = RationManager(repository)
    calculator = RationCalculator(repository)
    planner = HerdPlanner(calculator)
    store = SavedRationStore()
    controller = AppController.from_services(
        repository,
        ration_manager,
        calculator,
        planner,
        store,
    )
    controller.prepare_sample_ration()
    return controller


def main() -> None:
    """Launch the graphical application if KivyMD is available."""

    controller = build_controller()
    app = NutritionPlannerApp(controller, default_animal_count=30)
    app.run()  # type: ignore[attr-defined]


if __name__ == "__main__":
    main()

"""Validation helpers ensuring safe handling of incomplete or invalid inputs."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from app.models.feed import FeedDefinition, RationFeedItem
from app.models.validation import ValidationReport, ValidationSeverity


@dataclass
class RationValidator:
    """Validate ration items before nutritional calculations take place."""

    def validate(
        self,
        items: Iterable[RationFeedItem],
        catalog: Iterable[FeedDefinition],
    ) -> ValidationReport:
        """Return a report describing issues detected for ``items``.

        The validator checks general ration rules (non-empty list, positive quantities)
        and sanity ranges for nutritional values expressed as percentages or energy
        densities. The catalog is needed so that items relying on default profiles can
        be resolved prior to validation.
        """

        report = ValidationReport()
        item_list = list(items)
        if not item_list:
            report.add_issue(
                field="items",
                message="Dawka nie zawiera żadnych pasz. Dodaj pozycje, aby uzyskać wynik.",
            )
            return report

        catalog_list = list(catalog)
        for item in item_list:
            self._validate_quantity(item, report)
            profile = item.resolve_profile(catalog_list)
            self._validate_profile(item.name, profile.to_dict(), report)
        return report

    def _validate_quantity(self, item: RationFeedItem, report: ValidationReport) -> None:
        """Ensure ration quantities are strictly positive."""

        if item.quantity_kg <= 0:
            report.add_issue(
                field=f"item:{item.name}:quantity",
                message=(
                    f"Pasza '{item.name}': ilość musi być dodatnia. Pozycja została pominięta w obliczeniach."
                ),
                severity=ValidationSeverity.ERROR,
            )
            report.mark_invalid_item(item.name)

    def _validate_profile(
        self, feed_name: str, profile_dict: dict[str, float | None], report: ValidationReport
    ) -> None:
        """Validate nutrient ranges for the resolved profile values."""

        percent_fields = [
            ("dry_matter_percent", "sucha masa"),
            ("protein_percent", "białko"),
            ("fiber_percent", "włókno"),
        ]
        for field_key, label in percent_fields:
            value = profile_dict.get(field_key)
            if value is None:
                continue
            if value < 0 or value > 100:
                report.add_issue(
                    field=f"item:{feed_name}:{field_key}",
                    message=(
                        f"Pasza '{feed_name}': wartość '{label}' musi mieścić się w zakresie 0-100%. "
                        "Pominięto ją w obliczeniach."
                    ),
                    severity=ValidationSeverity.ERROR,
                )
                report.mark_invalid_field(feed_name, field_key)

        energy = profile_dict.get("energy_mj_per_kg_dm")
        if energy is None:
            return
        if energy <= 0:
            report.add_issue(
                field=f"item:{feed_name}:energy",
                message=(
                    f"Pasza '{feed_name}': energia metab. musi być dodatnia. Pominięto ją w obliczeniach."
                ),
                severity=ValidationSeverity.ERROR,
            )
            report.mark_invalid_field(feed_name, "energy")

"""Default feed dataset used to bootstrap the application."""

from __future__ import annotations

from datetime import date
from typing import Dict, List

from app.models.feed import FeedDefinition, FeedType, NutritionalProfile


def build_default_feeds() -> List[FeedDefinition]:
    """Return the list of predefined feed definitions shipped with the app."""

    today = date.today()
    defaults: Dict[str, Dict[str, float]] = {
        "Kiszonka z kukurydzy": {
            "protein_percent": 8.0,
            "energy_mj_per_kg_dm": 6.5,
            "dry_matter_percent": 32.0,
            "fiber_percent": 19.0,
            "feed_type": FeedType.ROUGHAGE,
        },
        "Kiszonka z traw": {
            "protein_percent": 14.0,
            "energy_mj_per_kg_dm": 5.8,
            "dry_matter_percent": 38.0,
            "fiber_percent": 25.0,
            "feed_type": FeedType.ROUGHAGE,
        },
        "Siano łąkowe": {
            "protein_percent": 10.0,
            "energy_mj_per_kg_dm": 5.4,
            "dry_matter_percent": 85.0,
            "fiber_percent": 28.0,
            "feed_type": FeedType.ROUGHAGE,
        },
        "Śruta sojowa": {
            "protein_percent": 45.0,
            "energy_mj_per_kg_dm": 7.5,
            "dry_matter_percent": 88.0,
            "fiber_percent": 6.0,
            "feed_type": FeedType.CONCENTRATE,
        },
        "Ziarno kukurydzy": {
            "protein_percent": 9.0,
            "energy_mj_per_kg_dm": 7.2,
            "dry_matter_percent": 86.0,
            "fiber_percent": 2.0,
            "feed_type": FeedType.CONCENTRATE,
        },
        "Wysłodki buraczane (susz)": {
            "protein_percent": 9.0,
            "energy_mj_per_kg_dm": 6.9,
            "dry_matter_percent": 90.0,
            "fiber_percent": 16.0,
            "feed_type": FeedType.CONCENTRATE,
        },
    }

    feeds: List[FeedDefinition] = []
    for name, payload in defaults.items():
        feed_type = payload.pop("feed_type")
        profile = NutritionalProfile(**payload)
        feeds.append(
            FeedDefinition(
                name=name,
                feed_type=feed_type,
                profile=profile,
                source="Średnie wartości referencyjne",
                added_on=today,
                is_default=True,
            )
        )
    return feeds

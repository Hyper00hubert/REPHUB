"""Feed repository and ration management services for Module 1."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from typing import Dict, Iterable, List, Optional

from app.data.default_feeds import build_default_feeds
from app.models.feed import FeedDefinition, FeedType, NutritionalProfile, RationFeedItem


@dataclass
class FeedRepository:
    """Keeps track of catalog feeds (default dataset and user-specified entries)."""

    _defaults: Dict[str, FeedDefinition] = field(default_factory=dict)
    _custom: Dict[str, FeedDefinition] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self._defaults:
            self._defaults = {feed.name: feed for feed in build_default_feeds()}

    # -- catalog management -------------------------------------------------
    def list_feeds(self, feed_type: Optional[FeedType] = None) -> List[FeedDefinition]:
        """Return feeds filtered by type. Custom entries override defaults by name."""

        merged = {**self._defaults, **self._custom}
        items = list(merged.values())
        if feed_type is None:
            return sorted(items, key=lambda feed: feed.name)
        return sorted(
            [feed for feed in items if feed.feed_type == feed_type],
            key=lambda feed: feed.name,
        )

    def get_feed(self, name: str) -> Optional[FeedDefinition]:
        """Return the feed definition with the given name if present."""

        return self._custom.get(name) or self._defaults.get(name)

    def add_custom_feed(
        self,
        name: str,
        feed_type: FeedType,
        profile: NutritionalProfile,
        source: Optional[str] = None,
        added_on: Optional[date] = None,
    ) -> FeedDefinition:
        """Register a user-defined feed and return its definition.

        Raises ``ValueError`` when the name already exists in either dataset. The method
        returns the saved definition for further chaining.
        """

        if name in self._defaults or name in self._custom:
            raise ValueError(f"Feed named '{name}' already exists")
        definition = FeedDefinition(
            name=name,
            feed_type=feed_type,
            profile=profile,
            source=source,
            added_on=added_on or date.today(),
            is_default=False,
        )
        self._custom[name] = definition
        return definition

    def update_feed_profile(self, name: str, profile: NutritionalProfile) -> FeedDefinition:
        """Replace the nutritional profile for an existing feed."""

        if name in self._custom:
            definition = self._custom[name].with_profile(profile)
            self._custom[name] = definition
            return definition
        if name in self._defaults:
            definition = self._defaults[name].with_profile(profile)
            self._defaults[name] = definition
            return definition
        raise KeyError(f"Feed '{name}' not found")

    def remove_feed(self, name: str) -> None:
        """Delete a custom feed from the catalog. Defaults cannot be removed."""

        if name in self._custom:
            del self._custom[name]
        elif name in self._defaults:
            raise ValueError("Cannot remove default feed entry")
        else:
            raise KeyError(f"Feed '{name}' not found")

    def reset_default_profile(self, name: str) -> FeedDefinition:
        """Restore default nutritional values by discarding custom overrides."""

        if name in self._custom:
            return self._custom[name]
        if name in self._defaults:
            defaults = build_default_feeds()
            lookup = {feed.name: feed for feed in defaults}
            definition = lookup.get(name)
            if definition is None:
                raise KeyError(f"Default feed '{name}' missing from dataset")
            self._defaults[name] = definition
            return definition
        raise KeyError(f"Feed '{name}' not found")

    # -- ration management --------------------------------------------------
    def create_ration_item(
        self,
        name: str,
        quantity_kg: float,
        use_default_profile: bool = True,
        manual_profile: Optional[NutritionalProfile] = None,
    ) -> RationFeedItem:
        """Create a ration feed item with validation and sensible defaults."""

        definition = self.get_feed(name)
        if definition is None and use_default_profile:
            raise KeyError(
                "Cannot use default values because the feed is absent from the catalog",
            )
        profile = manual_profile or NutritionalProfile()
        return RationFeedItem(
            name=name,
            quantity_kg=quantity_kg,
            use_default_profile=use_default_profile,
            manual_profile=profile,
        )

    def apply_default_profile(self, item: RationFeedItem) -> RationFeedItem:
        """Return a copy of ``item`` whose manual profile merges catalog defaults."""

        definition = self.get_feed(item.name)
        if not definition:
            return item
        merged = item.manual_profile.merged_with(definition.profile)
        return RationFeedItem(
            name=item.name,
            quantity_kg=item.quantity_kg,
            use_default_profile=item.use_default_profile,
            manual_profile=merged,
        )


@dataclass
class RationManager:
    """Handles collection-level operations on ration feed items."""

    repository: FeedRepository
    _items: Dict[str, RationFeedItem] = field(default_factory=dict)

    def list_items(self) -> List[RationFeedItem]:
        """Return all ration items sorted by name to ensure deterministic order."""

        return [self._items[key] for key in sorted(self._items)]

    def add_or_update_item(self, item: RationFeedItem) -> None:
        """Insert or replace a ration item based on its name."""

        self._items[item.name] = item

    def remove_item(self, name: str) -> None:
        """Remove a feed from the ration. Raises ``KeyError`` when missing."""

        if name not in self._items:
            raise KeyError(f"Feed '{name}' not part of the ration")
        del self._items[name]

    def replace_items(self, items: Iterable[RationFeedItem]) -> None:
        """Replace the current ration with the provided collection of items."""

        self._items = {item.name: item for item in items}

    def toggle_default_usage(self, name: str, use_default: bool) -> RationFeedItem:
        """Update the flag controlling whether catalog defaults should be applied."""

        if name not in self._items:
            raise KeyError(f"Feed '{name}' not part of the ration")
        item = self._items[name]
        updated = RationFeedItem(
            name=item.name,
            quantity_kg=item.quantity_kg,
            use_default_profile=use_default,
            manual_profile=item.manual_profile,
        )
        self._items[name] = updated
        return updated

    def resolve_profiles(self) -> Dict[str, NutritionalProfile]:
        """Return nutritional profiles for each item according to current settings."""

        catalog = self.repository.list_feeds()
        return {
            name: item.resolve_profile(catalog)
            for name, item in self._items.items()
        }

    def replace_manual_with_default(self, name: str) -> RationFeedItem:
        """Overwrite manual values with catalog defaults for a given ration item."""

        if name not in self._items:
            raise KeyError(f"Feed '{name}' not part of the ration")
        definition = self.repository.get_feed(name)
        if not definition:
            raise KeyError("Default feed definition unavailable")
        updated = RationFeedItem(
            name=name,
            quantity_kg=self._items[name].quantity_kg,
            use_default_profile=True,
            manual_profile=definition.profile,
        )
        self._items[name] = updated
        return updated

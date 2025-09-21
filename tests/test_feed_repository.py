"""Unit tests for Module 1 data management services."""

from __future__ import annotations

import pytest

from app.models.feed import FeedType, NutritionalProfile
from app.services.feed_repository import FeedRepository, RationManager


@pytest.fixture()
def repository() -> FeedRepository:
    return FeedRepository()


def test_defaults_loaded(repository: FeedRepository) -> None:
    feeds = repository.list_feeds()
    assert any(feed.name == "Kiszonka z kukurydzy" for feed in feeds)
    assert all(feed.is_default for feed in feeds)


def test_filter_by_type(repository: FeedRepository) -> None:
    roughage = repository.list_feeds(FeedType.ROUGHAGE)
    assert all(feed.feed_type == FeedType.ROUGHAGE for feed in roughage)


def test_add_custom_feed(repository: FeedRepository) -> None:
    profile = NutritionalProfile(protein_percent=12.0, dry_matter_percent=40.0)
    created = repository.add_custom_feed(
        name="Lucerna", feed_type=FeedType.ROUGHAGE, profile=profile
    )
    assert not created.is_default
    assert repository.get_feed("Lucerna") == created


def test_prevent_duplicate_name(repository: FeedRepository) -> None:
    profile = NutritionalProfile(protein_percent=12.0)
    repository.add_custom_feed("Lucerna", FeedType.ROUGHAGE, profile)
    with pytest.raises(ValueError):
        repository.add_custom_feed("Lucerna", FeedType.ROUGHAGE, profile)


def test_update_default_profile(repository: FeedRepository) -> None:
    new_profile = NutritionalProfile(protein_percent=9.5)
    updated = repository.update_feed_profile("Kiszonka z kukurydzy", new_profile)
    assert updated.profile.protein_percent == 9.5


def test_remove_custom_feed(repository: FeedRepository) -> None:
    profile = NutritionalProfile()
    repository.add_custom_feed("Test", FeedType.CONCENTRATE, profile)
    repository.remove_feed("Test")
    assert repository.get_feed("Test") is None


def test_cannot_remove_default(repository: FeedRepository) -> None:
    with pytest.raises(ValueError):
        repository.remove_feed("Kiszonka z kukurydzy")


def test_ration_manager_add_and_resolve(repository: FeedRepository) -> None:
    manager = RationManager(repository)
    item = repository.create_ration_item("Kiszonka z kukurydzy", 12.0, True)
    manager.add_or_update_item(item)
    resolved = manager.resolve_profiles()
    profile = resolved["Kiszonka z kukurydzy"]
    assert profile.dry_matter_percent == pytest.approx(32.0)


def test_replace_manual_with_default(repository: FeedRepository) -> None:
    manager = RationManager(repository)
    manual = NutritionalProfile(protein_percent=11.0)
    item = repository.create_ration_item(
        "Kiszonka z kukurydzy", 10.0, use_default_profile=False, manual_profile=manual
    )
    manager.add_or_update_item(item)
    manager.replace_manual_with_default("Kiszonka z kukurydzy")
    updated = manager.resolve_profiles()["Kiszonka z kukurydzy"]
    assert updated.protein_percent == pytest.approx(8.0)


def test_toggle_default_usage(repository: FeedRepository) -> None:
    manager = RationManager(repository)
    item = repository.create_ration_item("Ziarno kukurydzy", 5.0, True)
    manager.add_or_update_item(item)
    manager.toggle_default_usage("Ziarno kukurydzy", False)
    assert not manager.list_items()[0].use_default_profile

"""Tests for the saved rations persistence service."""

from __future__ import annotations

from pathlib import Path

import pytest

from app.models.feed import RationFeedItem
from app.services import FeedRepository
from app.services.saved_rations import SavedRationStore


def build_item(repository: FeedRepository) -> RationFeedItem:
    """Return a sample ration item from the default dataset."""

    return repository.create_ration_item(name="Kiszonka z kukurydzy", quantity_kg=12.0)


def test_saved_ration_store_roundtrip(tmp_path: Path) -> None:
    """Saved rations should persist to disk and load back correctly."""

    repository = FeedRepository()
    store = SavedRationStore(path=tmp_path / "saved.json")
    item = build_item(repository)

    saved = store.save("Referencyjna", [item])
    assert saved.name == "Referencyjna"

    loaded = store.load("Referencyjna")
    assert loaded.items[0].name == "Kiszonka z kukurydzy"

    listed = store.list_rations()
    assert [ration.name for ration in listed] == ["Referencyjna"]


def test_saved_ration_store_delete(tmp_path: Path) -> None:
    """Deleting a ration should remove it from persistent storage."""

    repository = FeedRepository()
    store = SavedRationStore(path=tmp_path / "saved.json")
    item = build_item(repository)
    store.save("Do usunięcia", [item])

    store.delete("Do usunięcia")
    assert store.list_rations() == []

    with pytest.raises(KeyError):
        store.delete("Nie istnieje")

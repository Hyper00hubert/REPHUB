"""End-to-end walkthrough tests covering the final tester module (Module 7)."""

from __future__ import annotations

from pathlib import Path

from app.testing import FinalTester


def test_final_tester_walkthrough_exercises_core_flows(tmp_path: Path) -> None:
    """Running the scripted walkthrough should produce consistent UI states."""

    tester = FinalTester(storage_path=tmp_path / "saved.json")
    report = tester.run_walkthrough()

    # Reference ration should match the preloaded sample with no warnings.
    assert len(report.reference_state.feed_rows) == 3
    assert report.reference_state.feed_rows[0].quantity_label == "12.00 kg"
    assert report.reference_state.warnings == []

    # Manual variant should mark energy as missing and trigger a warning.
    manual_first = report.manual_state.feed_rows[0]
    assert manual_first.quantity_label == "13.00 kg"
    assert manual_first.energy_label == "brak danych"
    assert any("brak danych o energii" in warning.lower() for warning in report.manual_state.warnings)

    # After reloading the reference ration the state should match the original values.
    final_first = report.final_state.feed_rows[0]
    assert final_first.quantity_label == "12.00 kg"
    assert report.final_state.warnings == []

    # Herd panel state should expose expected logistics derived from the sample ration.
    logistics = {card.label: card.value_label for card in report.herd_state.logistics_cards}
    assert logistics["Dzienne zużycie"] == "570.00 kg"
    assert logistics["Załadunki mieszalnika"] == "2"
    assert logistics["Załadunki paszowozu"] == "2"

    # Saved ration overview should list both entries and provide comparison details.
    saved_names = {row.name for row in report.saved_state.rows}
    assert {"Dawka referencyjna", "Dawka ręczna testowa"}.issubset(saved_names)
    assert report.saved_state.comparison_cards, "Comparison cards should be populated"
    assert report.saved_state.feed_share_rows, "Feed share differences should be available"

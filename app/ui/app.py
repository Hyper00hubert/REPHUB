"""KivyMD application bootstrap wiring Module 4 UI with services."""

from __future__ import annotations

from typing import List, Optional

from .controllers import AppController

try:  # pragma: no cover - optional dependency
    from kivy.metrics import dp
    from kivymd.app import MDApp
    from kivymd.uix.boxlayout import MDBoxLayout
    from kivymd.uix.button import MDRaisedButton
    from kivymd.uix.card import MDCard
    from kivymd.uix.label import MDLabel
    from kivymd.uix.list import MDList, OneLineListItem
    from kivymd.uix.screen import MDScreen
    from kivymd.uix.scrollview import MDScrollView
    from kivymd.uix.tab import MDTabs, MDTabsBase
    from kivymd.uix.textfield import MDTextField
except ImportError:  # pragma: no cover - executed only when KivyMD absent
    MDApp = None

    class NutritionPlannerApp:  # type: ignore
        """Fallback stub raised when KivyMD is not installed."""

        def __init__(self, *args, **kwargs) -> None:  # pragma: no cover - defensive
            raise ImportError(
                "KivyMD nie jest zainstalowane. Zainstaluj pakiety 'kivy' oraz 'kivymd', aby uruchomić interfejs."
            )
else:

    class _Tab(MDBoxLayout, MDTabsBase):
        """Simple helper combining box layout with tab capabilities."""

        def __init__(self, **kwargs) -> None:
            super().__init__(orientation="vertical", padding=dp(16), spacing=dp(12), **kwargs)


    class NutritionPlannerApp(MDApp):
        """Concrete KivyMD application exposing the feeding planner screens."""

        def __init__(
            self,
            controller: AppController,
            default_animal_count: Optional[int] = None,
            **kwargs,
        ) -> None:
            super().__init__(**kwargs)
            self.controller = controller
            self.controller.prepare_sample_ration()
            self._current_animal_count: Optional[int] = default_animal_count
            self._ration_feed_list: Optional[MDList] = None
            self._ration_cards_box: Optional[MDBoxLayout] = None
            self._ration_warning_box: Optional[MDBoxLayout] = None
            self._herd_result_box: Optional[MDBoxLayout] = None
            self._herd_warning_box: Optional[MDBoxLayout] = None
            self._animal_field: Optional[MDTextField] = None
            self._production_field: Optional[MDTextField] = None
            self._mixer_field: Optional[MDTextField] = None
            self._wagon_field: Optional[MDTextField] = None
            self._stock_field: Optional[MDTextField] = None
            self._saved_name_field: Optional[MDTextField] = None
            self._saved_list: Optional[MDList] = None
            self._saved_message_box: Optional[MDBoxLayout] = None
            self._saved_comparison_box: Optional[MDBoxLayout] = None
            self._saved_selected: List[str] = []

        def build(self):  # pragma: no cover - UI runtime
            self.title = "Planner dawek dla bydła"
            self.theme_cls.primary_palette = "Green"
            screen = MDScreen()
            tabs = MDTabs()
            screen.add_widget(tabs)

            ration_tab = self._build_ration_tab()
            ration_tab.text = "Dawka pokarmowa"
            tabs.add_widget(ration_tab)

            herd_tab = self._build_herd_tab()
            herd_tab.text = "Panel hodowcy"
            tabs.add_widget(herd_tab)

            saved_tab = self._build_saved_tab()
            saved_tab.text = "Zapisane dawki"
            tabs.add_widget(saved_tab)

            return screen

        # -- ration tab -----------------------------------------------------
        def _build_ration_tab(self) -> _Tab:
            tab = _Tab()
            scroll = MDScrollView()
            feed_list = MDList()
            scroll.add_widget(feed_list)
            tab.add_widget(scroll)

            cards_box = MDBoxLayout(orientation="vertical", spacing=dp(8))
            tab.add_widget(cards_box)

            warning_box = MDBoxLayout(orientation="vertical", spacing=dp(4))
            tab.add_widget(warning_box)

            self._ration_feed_list = feed_list
            self._ration_cards_box = cards_box
            self._ration_warning_box = warning_box
            self._update_ration_state()
            return tab

        def _update_ration_state(self) -> None:
            if self._ration_feed_list is None or self._ration_cards_box is None:
                return
            state = self.controller.ration_controller.build_state(
                animal_count=self._current_animal_count
            )

            self._ration_feed_list.clear_widgets()
            for row in state.feed_rows:
                description = (
                    f"{row.name} • {row.quantity_label} • SM {row.dry_matter_label} • "
                    f"Białko {row.protein_label}"
                )
                if row.energy_label != "brak danych":
                    description += f" • Energia {row.energy_label}"
                item = OneLineListItem(text=description)
                self._ration_feed_list.add_widget(item)

            self._ration_cards_box.clear_widgets()
            for card in state.summary_cards:
                card_widget = MDCard(orientation="vertical", padding=dp(12), spacing=dp(4))
                card_widget.add_widget(MDLabel(text=card.title, bold=True))
                card_widget.add_widget(MDLabel(text=f"Suma: {card.total_label}"))
                if card.per_animal_label:
                    card_widget.add_widget(MDLabel(text=f"Na sztukę: {card.per_animal_label}"))
                if card.estimated:
                    card_widget.add_widget(MDLabel(text="* wartość szacowana", font_style="Caption"))
                self._ration_cards_box.add_widget(card_widget)

            if self._ration_warning_box is not None:
                self._ration_warning_box.clear_widgets()
                if state.warnings:
                    for warning in state.warnings:
                        self._ration_warning_box.add_widget(
                            MDLabel(text=warning, theme_text_color="Error")
                        )
                else:
                    self._ration_warning_box.add_widget(
                        MDLabel(text="Brak ostrzeżeń", theme_text_color="Hint")
                    )

        # -- herd tab -------------------------------------------------------
        def _build_herd_tab(self) -> _Tab:
            tab = _Tab()

            self._animal_field = MDTextField(
                hint_text="Liczba zwierząt",
                text=str(self._current_animal_count or 30),
                helper_text="Podaj liczbę krów w stadzie",
                helper_text_mode="on_focus",
            )
            tab.add_widget(self._animal_field)

            self._production_field = MDTextField(
                hint_text="Typ produkcji (mleczne/opasowe)",
                text="mleczne",
            )
            tab.add_widget(self._production_field)

            self._mixer_field = MDTextField(hint_text="Pojemność mieszalnika (kg)")
            tab.add_widget(self._mixer_field)

            self._wagon_field = MDTextField(hint_text="Pojemność paszowozu (kg)")
            tab.add_widget(self._wagon_field)

            self._stock_field = MDTextField(hint_text="Zapas paszy w magazynie (kg)")
            tab.add_widget(self._stock_field)

            recalc_button = MDRaisedButton(text="Przelicz")
            recalc_button.bind(on_release=self._update_herd_results)
            tab.add_widget(recalc_button)

            result_box = MDBoxLayout(orientation="vertical", spacing=dp(8))
            tab.add_widget(result_box)
            self._herd_result_box = result_box

            warning_box = MDBoxLayout(orientation="vertical", spacing=dp(4))
            tab.add_widget(warning_box)
            self._herd_warning_box = warning_box

            self._update_herd_results()
            return tab

        def _update_herd_results(self, *_args) -> None:
            if self._herd_result_box is None:
                return
            animal_count = self._parse_int_field(self._animal_field)
            production_label = (self._production_field.text if self._production_field else "mleczne")
            if animal_count is None:
                self._display_herd_error("Podaj prawidłową liczbę zwierząt.")
                return
            try:
                state = self.controller.herd_controller.build_state(
                    animal_count=animal_count,
                    production_label=production_label,
                    mixer_capacity_kg=self._parse_float_field(self._mixer_field),
                    wagon_capacity_kg=self._parse_float_field(self._wagon_field),
                    stock_mass_kg=self._parse_float_field(self._stock_field),
                )
            except ValueError as exc:
                self._display_herd_error(str(exc))
                return

            self._current_animal_count = animal_count
            self._render_herd_state(state)
            self._update_ration_state()

        def _render_herd_state(self, state) -> None:
            if self._herd_result_box is None or self._herd_warning_box is None:
                return
            self._herd_result_box.clear_widgets()
            header = MDLabel(
                text=(
                    f"Typ produkcji: {state.production_type_label} | Zwierząt: {state.animal_count_label}"
                ),
                bold=True,
            )
            self._herd_result_box.add_widget(header)
            self._herd_result_box.add_widget(
                MDLabel(text=f"Dzienna porcja na sztukę: {state.per_animal_feed_label}")
            )
            for card in state.herd_nutrient_cards:
                self._herd_result_box.add_widget(MDLabel(text=f"{card.title}: {card.total_label}"))
            for card in state.logistics_cards:
                self._herd_result_box.add_widget(MDLabel(text=f"{card.label}: {card.value_label}"))

            self._herd_warning_box.clear_widgets()
            if state.warnings:
                for warning in state.warnings:
                    self._herd_warning_box.add_widget(
                        MDLabel(text=warning, theme_text_color="Error")
                    )
            else:
                self._herd_warning_box.add_widget(
                    MDLabel(text="Brak ostrzeżeń", theme_text_color="Hint")
                )

        def _display_herd_error(self, message: str) -> None:
            if self._herd_warning_box is None:
                return
            self._herd_warning_box.clear_widgets()
            self._herd_warning_box.add_widget(
                MDLabel(text=message, theme_text_color="Error")
            )

        # -- saved tab ------------------------------------------------------
        def _build_saved_tab(self) -> _Tab:
            tab = _Tab()
            self._saved_name_field = MDTextField(
                hint_text="Nazwa dawki",
                helper_text="Podaj nazwę przed zapisem",
                helper_text_mode="on_focus",
            )
            tab.add_widget(self._saved_name_field)

            button_row = MDBoxLayout(orientation="horizontal", spacing=dp(8), size_hint_y=None, height=dp(48))
            save_button = MDRaisedButton(text="💾 Zapisz aktualną")
            save_button.bind(on_release=self._on_save_current)
            load_button = MDRaisedButton(text="📂 Wczytaj zaznaczoną")
            load_button.bind(on_release=self._on_load_saved)
            delete_button = MDRaisedButton(text="🗑 Usuń zaznaczoną")
            delete_button.bind(on_release=self._on_delete_saved)
            button_row.add_widget(save_button)
            button_row.add_widget(load_button)
            button_row.add_widget(delete_button)
            tab.add_widget(button_row)

            scroll = MDScrollView()
            saved_list = MDList()
            scroll.add_widget(saved_list)
            tab.add_widget(scroll)
            self._saved_list = saved_list

            message_box = MDBoxLayout(orientation="vertical", spacing=dp(4))
            tab.add_widget(message_box)
            self._saved_message_box = message_box

            comparison_box = MDBoxLayout(orientation="vertical", spacing=dp(8))
            tab.add_widget(comparison_box)
            self._saved_comparison_box = comparison_box

            self._refresh_saved_state()
            return tab

        def _on_save_current(self, *_args) -> None:
            name = self._saved_name_field.text.strip() if self._saved_name_field else ""
            if not name:
                self._display_saved_message("Podaj nazwę dawki przed zapisem.", error=True)
                return
            try:
                self.controller.saved_controller.save_current(name)
            except ValueError as exc:
                self._display_saved_message(str(exc), error=True)
                return
            self._display_saved_message(f"Zapisano dawkę '{name}'.")
            if self._saved_name_field:
                self._saved_name_field.text = ""
            self._refresh_saved_state()

        def _on_load_saved(self, *_args) -> None:
            if not self._saved_selected:
                self._display_saved_message("Zaznacz dawkę na liście, aby ją wczytać.", error=True)
                return
            name = self._saved_selected[0]
            try:
                self.controller.saved_controller.load_into_manager(name)
            except KeyError as exc:
                self._display_saved_message(str(exc), error=True)
                return
            self._display_saved_message(f"Wczytano dawkę '{name}'.")
            self._update_ration_state()

        def _on_delete_saved(self, *_args) -> None:
            if not self._saved_selected:
                self._display_saved_message("Wybierz dawkę do usunięcia.", error=True)
                return
            name = self._saved_selected[0]
            try:
                self.controller.saved_controller.delete(name)
            except KeyError as exc:
                self._display_saved_message(str(exc), error=True)
                return
            self._display_saved_message(f"Usunięto dawkę '{name}'.")
            self._saved_selected = [item for item in self._saved_selected if item != name]
            self._refresh_saved_state()

        def _toggle_saved_selection(self, name: str) -> None:
            if name in self._saved_selected:
                self._saved_selected = [item for item in self._saved_selected if item != name]
            else:
                if len(self._saved_selected) >= 2:
                    self._saved_selected.pop(0)
                self._saved_selected.append(name)
            self._refresh_saved_state()

        def _refresh_saved_state(self) -> None:
            if self._saved_list is None or self._saved_message_box is None:
                return
            comparison_pair = None
            if len(self._saved_selected) == 2:
                comparison_pair = (self._saved_selected[0], self._saved_selected[1])
            state = self.controller.saved_controller.build_state(
                comparison_pair=comparison_pair,
                animal_count=self._current_animal_count,
            )

            self._saved_list.clear_widgets()
            for row in state.rows:
                prefix = "✅ " if row.name in self._saved_selected else ""
                item = OneLineListItem(text=f"{prefix}{row.name} — {row.subtitle}")
                item.bind(on_release=lambda _widget, value=row.name: self._toggle_saved_selection(value))
                self._saved_list.add_widget(item)

            self._saved_message_box.clear_widgets()
            if state.message:
                self._saved_message_box.add_widget(
                    MDLabel(text=state.message, theme_text_color="Hint")
                )
            else:
                self._saved_message_box.add_widget(
                    MDLabel(
                        text="Zaznacz dwie dawki, aby zobaczyć porównanie składu.",
                        theme_text_color="Hint",
                    )
                )

            if self._saved_comparison_box is not None:
                self._saved_comparison_box.clear_widgets()
                if state.comparison_cards:
                    cards_row = MDBoxLayout(orientation="horizontal", spacing=dp(8))
                    for card in state.comparison_cards:
                        widget = MDCard(orientation="vertical", padding=dp(12), spacing=dp(4))
                        widget.add_widget(MDLabel(text=card.label, bold=True))
                        widget.add_widget(MDLabel(text=card.first_label))
                        widget.add_widget(MDLabel(text=card.second_label))
                        widget.add_widget(MDLabel(text=f"Różnica: {card.difference_label}"))
                        cards_row.add_widget(widget)
                    self._saved_comparison_box.add_widget(cards_row)
                if state.feed_share_rows:
                    share_list = MDList()
                    for row in state.feed_share_rows:
                        description = (
                            f"{row.feed_name}: {row.first_label} • {row.second_label} "
                            f"({row.difference_label})"
                        )
                        share_list.add_widget(OneLineListItem(text=description))
                    scroll = MDScrollView()
                    scroll.add_widget(share_list)
                    self._saved_comparison_box.add_widget(scroll)

        def _display_saved_message(self, message: str, error: bool = False) -> None:
            if self._saved_message_box is None:
                return
            self._saved_message_box.clear_widgets()
            color = "Error" if error else "Hint"
            self._saved_message_box.add_widget(
                MDLabel(text=message, theme_text_color=color)
            )

        # -- helpers --------------------------------------------------------
        def _parse_int_field(self, field: Optional[MDTextField]) -> Optional[int]:
            if field is None:
                return None
            text = field.text.strip()
            if not text:
                return None
            try:
                return int(text)
            except ValueError:
                return None

        def _parse_float_field(self, field: Optional[MDTextField]) -> Optional[float]:
            if field is None:
                return None
            text = field.text.strip().replace(",", ".")
            if not text:
                return None
            try:
                return float(text)
            except ValueError:
                return None

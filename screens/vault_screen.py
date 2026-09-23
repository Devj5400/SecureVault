"""
screens/vault_screen.py
---------------------------
Search / filter / list all saved passwords, with reveal, copy, and delete
actions on each card.
"""

from kivy.app import App
from kivy.uix.screenmanager import Screen
from kivy.uix.label import Label
from kivy.core.clipboard import Clipboard
from kivy.metrics import dp

from core.vault import CATEGORIES
from widgets.components import PasswordCard, CategoryChip


class VaultScreen(Screen):
    active_category = "All"
    revealed_ids = None

    def on_pre_enter(self):
        self.revealed_ids = self.revealed_ids if self.revealed_ids is not None else set()
        self.active_category = "All"
        self.ids.search_input.text = ""
        self.ids.back_btn.unbind(on_release=self._go_back)
        self.ids.back_btn.bind(on_release=self._go_back)
        self.ids.search_input.unbind(text=self._on_search)
        self.ids.search_input.bind(text=self._on_search)
        self._build_filters()
        self._refresh()

    def _build_filters(self):
        row = self.ids.filter_row
        row.clear_widgets()
        for cat in ["All"] + CATEGORIES:
            chip = CategoryChip(text=cat, selected=(cat == self.active_category))
            chip.bind(on_release=lambda inst, c=cat: self._select_filter(c))
            row.add_widget(chip)

    def _select_filter(self, category):
        self.active_category = category
        self._build_filters()
        self._refresh()

    def _on_search(self, *_):
        self._refresh()

    def _refresh(self):
        vault = App.get_running_app().vault
        results = vault.search(self.ids.search_input.text, self.active_category)

        entry_list = self.ids.entry_list
        entry_list.clear_widgets()
        if not results:
            entry_list.add_widget(Label(text="No matching passwords.",
                                         color=(0.545, 0.580, 0.620, 1),
                                         size_hint_y=None, height=dp(30)))
            return

        for entry in results:
            revealed = entry["id"] in self.revealed_ids
            card = PasswordCard(
                entry_id=entry["id"], category=entry["category"], name=entry["name"],
                username=entry.get("username", ""),
                password_display=entry["password"] if revealed else "\u2022" * 10,
                revealed=revealed,
            )
            card.ids.reveal_btn.bind(on_release=lambda inst, e=entry: self._toggle_reveal(e))
            card.ids.copy_btn.bind(on_release=lambda inst, e=entry: self._copy(e))
            card.ids.delete_btn.bind(on_release=lambda inst, e=entry: self._delete(e))
            entry_list.add_widget(card)

    def _toggle_reveal(self, entry):
        if entry["id"] in self.revealed_ids:
            self.revealed_ids.discard(entry["id"])
        else:
            self.revealed_ids.add(entry["id"])
        self._refresh()

    def _copy(self, entry):
        Clipboard.copy(entry["password"])

    def _delete(self, entry):
        vault = App.get_running_app().vault
        vault.delete_entry(entry["id"])
        self._refresh()

    def _go_back(self, *_):
        self.manager.transition.direction = 'right'
        self.manager.current = 'dashboard'

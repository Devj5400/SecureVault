"""
screens/dashboard.py
-----------------------
Overview screen: stat cards (total / per-category counts) and a list of
recently added passwords, plus quick-action buttons.
"""

from kivy.app import App
from kivy.uix.screenmanager import Screen
from kivy.uix.label import Label
from kivy.metrics import dp

from widgets.components import StatCard, PasswordCard

CATEGORY_ACCENTS = {
    "Website": [0.973, 0.318, 0.286, 1],
    "Email": [0.824, 0.600, 0.133, 1],
    "Social Media": [0.137, 0.525, 0.212, 1],
}


class DashboardScreen(Screen):
    def on_pre_enter(self):
        self.ids.settings_btn.unbind(on_release=self._go_settings)
        self.ids.settings_btn.bind(on_release=self._go_settings)
        self.ids.create_btn.unbind(on_release=self._go_create)
        self.ids.create_btn.bind(on_release=self._go_create)
        self.ids.vault_btn.unbind(on_release=self._go_vault)
        self.ids.vault_btn.bind(on_release=self._go_vault)
        self._refresh()

    def _refresh(self):
        vault = App.get_running_app().vault
        stats = vault.stats()

        grid = self.ids.stats_grid
        grid.clear_widgets()
        grid.add_widget(StatCard(value=str(stats["total"]), caption="Total Passwords",
                                  accent=[0.345, 0.651, 1, 1]))
        for cat, count in stats["counts"].items():
            grid.add_widget(StatCard(value=str(count), caption=cat,
                                      accent=CATEGORY_ACCENTS.get(cat, [0.345, 0.651, 1, 1])))

        recent_list = self.ids.recent_list
        recent_list.clear_widgets()
        if not stats["recent"]:
            recent_list.add_widget(Label(
                text="No passwords yet - create your first one.",
                color=(0.545, 0.580, 0.620, 1), size_hint_y=None, height=dp(30)))
            return

        for entry in stats["recent"]:
            card = PasswordCard(
                entry_id=entry["id"], category=entry["category"], name=entry["name"],
                username=entry.get("username", ""), password_display="\u2022" * 10,
            )
            recent_list.add_widget(card)

    def _go_settings(self, *_):
        self.manager.transition.direction = 'left'
        self.manager.current = 'settings'

    def _go_create(self, *_):
        self.manager.transition.direction = 'left'
        self.manager.current = 'create'

    def _go_vault(self, *_):
        self.manager.transition.direction = 'left'
        self.manager.current = 'vault'

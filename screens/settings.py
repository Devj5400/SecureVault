"""
screens/settings.py
----------------------
Change master password, auto-lock timeout preference (UI/preference only
- actually enforcing a timeout needs a background timer tied to app-pause
events; documented as a future improvement in the README), and
export/import of an independent encrypted backup file.
"""

import os
from kivy.app import App
from kivy.uix.screenmanager import Screen
from kivy.uix.filechooser import FileChooserListView
from kivy.uix.popup import Popup
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.textinput import TextInput
from kivy.uix.label import Label
from kivy.metrics import dp

from widgets.components import RoundedButton


class SettingsScreen(Screen):
    def on_pre_enter(self):
        self.ids.back_btn.unbind(on_release=self._go_back)
        self.ids.back_btn.bind(on_release=self._go_back)
        self.ids.change_pw_btn.unbind(on_release=self._change_password)
        self.ids.change_pw_btn.bind(on_release=self._change_password)
        self.ids.export_btn.unbind(on_release=self._export)
        self.ids.export_btn.bind(on_release=self._export)
        self.ids.import_btn.unbind(on_release=self._import)
        self.ids.import_btn.bind(on_release=self._import)
        self.ids.current_pw_input.text = ""
        self.ids.new_pw_input.text = ""
        self.ids.settings_status.text = ""
        self.ids.autolock_note.text = "(Preference only - not yet enforced by a background timer.)"

    def _change_password(self, *_):
        vault = App.get_running_app().vault
        current = self.ids.current_pw_input.text
        new = self.ids.new_pw_input.text
        if not vault.unlock(current):
            self._set_status("Current password is incorrect.", ok=False)
            return
        if len(new) < 6:
            self._set_status("New password must be at least 6 characters.", ok=False)
            return
        vault.change_master_password(new)
        self._set_status("Master password updated.", ok=True)
        self.ids.current_pw_input.text = ""
        self.ids.new_pw_input.text = ""

    def _set_status(self, text, ok=True):
        self.ids.settings_status.text = text
        self.ids.settings_status.color = (0.247, 0.725, 0.314, 1) if ok else (0.973, 0.318, 0.286, 1)

    def _export(self, *_):
        self._show_password_popup("Export Encrypted Vault", self._do_export)

    def _import(self, *_):
        self._show_password_popup("Import Encrypted Vault", self._do_import, pick_file=True)

    def _show_password_popup(self, title, on_confirm, pick_file=False):
        content = BoxLayout(orientation='vertical', padding=dp(12), spacing=dp(10))
        file_chooser = None
        if pick_file:
            file_chooser = FileChooserListView(filters=["*.dat", "*.json"])
            content.add_widget(file_chooser)
        pw_input = TextInput(hint_text="Password", password=True, multiline=False,
                              size_hint_y=None, height=dp(44))
        content.add_widget(pw_input)
        status = Label(text="", color=(0.973, 0.318, 0.286, 1), size_hint_y=None, height=dp(20))
        content.add_widget(status)
        confirm_btn = RoundedButton(text="Confirm", size_hint_y=None, height=dp(44))
        content.add_widget(confirm_btn)

        popup = Popup(title=title, content=content, size_hint=(0.9, 0.7))

        def confirm(*_):
            path = None
            if pick_file:
                if not file_chooser.selection:
                    status.text = "Please choose a file."
                    return
                path = file_chooser.selection[0]
            if not pw_input.text:
                status.text = "Please enter a password."
                return
            on_confirm(path, pw_input.text, status, popup)

        confirm_btn.bind(on_release=confirm)
        popup.open()

    def _do_export(self, _path, password, status, popup):
        vault = App.get_running_app().vault
        export_path = os.path.join(os.path.expanduser("~"), "securevault_backup.json")
        try:
            vault.export_to(export_path, password)
            self._set_status(f"Exported to {export_path}", ok=True)
            popup.dismiss()
        except Exception as exc:
            status.text = f"Export failed: {exc}"

    def _do_import(self, path, password, status, popup):
        vault = App.get_running_app().vault
        try:
            vault.import_from(path, password)
            self._set_status("Vault imported successfully.", ok=True)
            popup.dismiss()
        except Exception:
            status.text = "Wrong password or invalid file."

    def _go_back(self, *_):
        self.manager.transition.direction = 'right'
        self.manager.current = 'dashboard'

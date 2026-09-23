"""
screens/login.py
--------------------
Handles both first-run vault creation and returning-user unlock, using
the shared Vault instance owned by the App.
"""

from kivy.app import App
from kivy.uix.screenmanager import Screen


class LoginScreen(Screen):
    is_new = True

    def on_pre_enter(self):
        vault = App.get_running_app().vault
        self.is_new = not vault.vault_exists()

        self.ids.subtitle_label.text = (
            "Create a master password to protect your vault"
            if self.is_new else "Welcome back - unlock your vault"
        )
        self.ids.confirm_input.opacity = 1 if self.is_new else 0
        self.ids.confirm_input.disabled = not self.is_new
        self.ids.confirm_input.height = 46 if self.is_new else 0
        self.ids.submit_btn.text = "Create Vault" if self.is_new else "Unlock"
        self.ids.error_label.text = ""
        self.ids.password_input.text = ""
        self.ids.confirm_input.text = ""
        self.ids.password_input.password = True
        self.ids.toggle_pw_btn.text = "Show"

        self.ids.submit_btn.unbind(on_release=self._submit)
        self.ids.submit_btn.bind(on_release=self._submit)
        self.ids.toggle_pw_btn.unbind(on_release=self._toggle_visibility)
        self.ids.toggle_pw_btn.bind(on_release=self._toggle_visibility)

    def _toggle_visibility(self, *_):
        pw = self.ids.password_input
        pw.password = not pw.password
        self.ids.toggle_pw_btn.text = "Hide" if not pw.password else "Show"

    def _submit(self, *_):
        vault = App.get_running_app().vault
        password = self.ids.password_input.text
        if not password:
            self.ids.error_label.text = "Please enter a master password."
            return

        if self.is_new:
            confirm = self.ids.confirm_input.text
            if password != confirm:
                self.ids.error_label.text = "Passwords do not match."
                return
            if len(password) < 6:
                self.ids.error_label.text = "Use at least 6 characters."
                return
            vault.create_new(password)
            self._go_to_dashboard()
        else:
            if vault.unlock(password):
                self._go_to_dashboard()
            else:
                self.ids.error_label.text = "Incorrect master password."

    def _go_to_dashboard(self):
        self.manager.transition.direction = 'left'
        self.manager.current = 'dashboard'

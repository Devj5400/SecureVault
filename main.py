"""
main.py
---------
SecureVault entry point.

Builds the ScreenManager, owns the single shared Vault instance, and
registers all screens. Visual styling lives entirely in securevault.kv
(auto-loaded by Kivy because it matches the App class name:
SecureVaultApp -> securevault.kv).
"""

from kivy.app import App
from kivy.uix.screenmanager import ScreenManager, FadeTransition
from kivy.core.window import Window

from core.vault import Vault
from screens.splash import SplashScreen
from screens.login import LoginScreen
from screens.dashboard import DashboardScreen
from screens.create_password import CreatePasswordScreen
from screens.vault_screen import VaultScreen
from screens.settings import SettingsScreen

Window.clearcolor = (0.051, 0.067, 0.090, 1)  # #0D1117


class SecureVaultApp(App):
    def build(self):
        self.title = "SecureVault"
        self.vault = Vault()

        sm = ScreenManager(transition=FadeTransition(duration=0.2))
        sm.add_widget(SplashScreen(name='splash'))
        sm.add_widget(LoginScreen(name='login'))
        sm.add_widget(DashboardScreen(name='dashboard'))
        sm.add_widget(CreatePasswordScreen(name='create'))
        sm.add_widget(VaultScreen(name='vault'))
        sm.add_widget(SettingsScreen(name='settings'))
        sm.current = 'splash'
        return sm


if __name__ == '__main__':
    SecureVaultApp().run()

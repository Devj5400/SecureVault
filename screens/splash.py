"""
screens/splash.py
--------------------
Animated splash screen shown briefly on startup, then transitions to the
login screen.
"""

from kivy.uix.screenmanager import Screen
from kivy.animation import Animation
from kivy.clock import Clock


class SplashScreen(Screen):
    def on_enter(self):
        logo = self.ids.logo_label
        title = self.ids.title_label
        logo.opacity = 0
        title.opacity = 0
        Animation(opacity=1, d=0.6, t='out_quad').start(logo)
        Animation(opacity=1, d=0.6, t='out_quad').start(title)
        Clock.schedule_once(self._go_to_login, 1.6)

    def _go_to_login(self, *_):
        self.manager.transition.direction = 'left'
        self.manager.current = 'login'

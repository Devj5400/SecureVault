"""
screens/create_password.py
------------------------------
Category selection + password generator (length 4-128, slider AND numeric
input kept in sync) + live entropy-based strength meter + save.
"""

from kivy.app import App
from kivy.uix.screenmanager import Screen
from kivy.core.clipboard import Clipboard
from kivy.clock import Clock

from core.generator import (
    generate_password, password_strength, clamp_length,
    MIN_LENGTH, MAX_LENGTH, DEFAULT_LENGTH,
)
from core.vault import CATEGORIES
from widgets.components import CategoryChip


class CreatePasswordScreen(Screen):
    selected_category = None

    def on_pre_enter(self):
        self.selected_category = CATEGORIES[0]
        self._build_category_chips()
        self.ids.name_input.text = ""
        self.ids.username_input.text = ""
        self.ids.error_label.text = ""
        self._suppress_sync = False
        self._set_length(DEFAULT_LENGTH, update_slider=True, update_input=True)

        self.ids.back_btn.unbind(on_release=self._go_back)
        self.ids.back_btn.bind(on_release=self._go_back)
        self.ids.cancel_btn.unbind(on_release=self._go_back)
        self.ids.cancel_btn.bind(on_release=self._go_back)
        self.ids.regen_btn.unbind(on_release=self._regenerate)
        self.ids.regen_btn.bind(on_release=self._regenerate)
        self.ids.copy_btn.unbind(on_release=self._copy)
        self.ids.copy_btn.bind(on_release=self._copy)
        self.ids.save_btn.unbind(on_release=self._save)
        self.ids.save_btn.bind(on_release=self._save)

        self.ids.length_slider.unbind(value=self._on_slider_change)
        self.ids.length_slider.bind(value=self._on_slider_change)
        self.ids.length_input.unbind(text=self._on_input_text_change)
        self.ids.length_input.bind(text=self._on_input_text_change)
        self.ids.length_input.unbind(focus=self._on_input_focus)
        self.ids.length_input.bind(focus=self._on_input_focus)
        self.ids.length_minus_btn.unbind(on_release=self._decrement)
        self.ids.length_minus_btn.bind(on_release=self._decrement)
        self.ids.length_plus_btn.unbind(on_release=self._increment)
        self.ids.length_plus_btn.bind(on_release=self._increment)

        for chk_id in ("chk_upper", "chk_lower", "chk_digits", "chk_symbols"):
            self.ids[chk_id].unbind(active=self._on_option_change)
            self.ids[chk_id].bind(active=self._on_option_change)

        self._regenerate()

    # ---- category selection -------------------------------------------------
    def _build_category_chips(self):
        row = self.ids.category_row
        row.clear_widgets()
        for cat in CATEGORIES:
            chip = CategoryChip(text=cat, selected=(cat == self.selected_category))
            chip.bind(on_release=lambda inst, c=cat: self._select_category(c))
            row.add_widget(chip)

    def _select_category(self, category):
        self.selected_category = category
        self._build_category_chips()

    # ---- length: slider <-> numeric input, kept in sync safely ----------------
    def current_length(self):
        return int(self.ids.length_slider.value)

    def _set_length(self, value, update_slider=True, update_input=True):
        """Single source of truth for changing the length. Always clamps,
        never raises, and guards against feedback loops between the slider
        and the text input while updating each other."""
        value = clamp_length(value, fallback=self.current_length() if hasattr(self, 'ids') else DEFAULT_LENGTH)
        self._suppress_sync = True
        try:
            if update_slider:
                self.ids.length_slider.value = value
            if update_input:
                self.ids.length_input.text = str(value)
        finally:
            self._suppress_sync = False
        return value

    def _on_slider_change(self, instance, value):
        if self._suppress_sync:
            return
        length = int(value)
        self._set_length(length, update_slider=False, update_input=True)
        self._regenerate()

    def _on_input_text_change(self, instance, text):
        if self._suppress_sync:
            return
        # Live-update the strength meter as they type, but don't fight the
        # slider on every keystroke (e.g. while they're still typing "12"
        # towards "128") - only clamp/resync on blur or Enter (see below).
        if text.strip().isdigit():
            preview_length = clamp_length(text)
            self.ids.length_slider.value = preview_length
            self._update_strength_preview(preview_length)

    def _on_input_focus(self, instance, has_focus):
        if has_focus:
            return
        # Focus lost: normalize whatever they typed (blank, "0", "999",
        # "abc", etc.) into a valid clamped length and regenerate.
        raw = self.ids.length_input.text
        length = clamp_length(raw, fallback=self.current_length())
        self._set_length(length, update_slider=True, update_input=True)
        self._regenerate()

    def _decrement(self, *_):
        self._set_length(self.current_length() - 1, update_slider=True, update_input=True)
        self._regenerate()

    def _increment(self, *_):
        self._set_length(self.current_length() + 1, update_slider=True, update_input=True)
        self._regenerate()

    # ---- options --------------------------------------------------------------
    def _on_option_change(self, *_):
        self._regenerate()

    def _current_options(self):
        return dict(
            use_upper=self.ids.chk_upper.active,
            use_lower=self.ids.chk_lower.active,
            use_digits=self.ids.chk_digits.active,
            use_symbols=self.ids.chk_symbols.active,
        )

    # ---- generation + strength meter -------------------------------------------
    def _regenerate(self, *_):
        length = self.current_length()
        opts = self._current_options()
        pw = generate_password(length=length, **opts)
        self.ids.pw_display.text = pw
        self._apply_strength(pw)

    def _update_strength_preview(self, length):
        """Used while the user is mid-typing a length, before we regenerate
        an actual password - shows what strength *would* result."""
        opts = self._current_options()
        self._apply_strength(length, **opts)

    def _apply_strength(self, password_or_length, **opts):
        score, label, color, entropy, crack_time = password_strength(password_or_length, **opts)
        bar = self.ids.strength_bar
        bar.score = score
        bar.label_text = label
        bar.bar_color = self._hex_to_rgba(color)
        self.ids.entropy_label.text = f"{label} - ~{entropy:.0f} bits of entropy - crack time {crack_time}"

    @staticmethod
    def _hex_to_rgba(hex_color):
        hex_color = hex_color.lstrip('#')
        r, g, b = (int(hex_color[i:i + 2], 16) / 255 for i in (0, 2, 4))
        return [r, g, b, 1]

    # ---- copy / save / navigation -----------------------------------------------
    def _copy(self, *_):
        password = self.ids.pw_display.text
        if password:
            Clipboard.copy(password)
            original = self.ids.copy_btn.text
            self.ids.copy_btn.text = "Copied!"
            Clock.schedule_once(lambda dt: setattr(self.ids.copy_btn, 'text', original), 1.2)

    def _save(self, *_):
        name = self.ids.name_input.text.strip()
        if not name:
            self.ids.error_label.text = "Please enter a name."
            return
        password = self.ids.pw_display.text
        if not password:
            self.ids.error_label.text = "Please generate a password first."
            return
        vault = App.get_running_app().vault
        vault.add_entry(self.selected_category, name, self.ids.username_input.text.strip(), password)
        self._go_back()

    def _go_back(self, *_):
        self.manager.transition.direction = 'right'
        self.manager.current = 'dashboard'

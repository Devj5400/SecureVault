"""
widgets/components.py
-------------------------
Reusable UI building blocks used across every screen: rounded buttons,
cards, stat tiles, category chips, the strength meter, and the password
list row. The visual styling for each of these lives in securevault.kv
(look for the matching rule, e.g. `<RoundedButton>:`) - this file only
defines the Python-side properties/behavior.
"""

from kivy.uix.button import Button
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.behaviors import ButtonBehavior
from kivy.properties import StringProperty, NumericProperty, ListProperty, BooleanProperty


class RoundedButton(Button):
    """A filled, rounded pill button (primary actions)."""
    bg_color = ListProperty([0.345, 0.651, 1, 1])  # default = primary blue


class OutlineButton(Button):
    """A rounded outline button (secondary actions)."""
    pass


class Card(BoxLayout):
    """A rounded, elevated container used to group related content."""
    pass


class StatCard(BoxLayout):
    """Small dashboard tile: a big number + a caption underneath."""
    value = StringProperty("0")
    caption = StringProperty("")
    accent = ListProperty([0.345, 0.651, 1, 1])


class CategoryChip(ButtonBehavior, BoxLayout):
    """Selectable rounded pill used for category selection / filtering."""
    text = StringProperty("")
    selected = BooleanProperty(False)


class StrengthBar(BoxLayout):
    """Segmented password-strength meter (score 0-4) with a label."""
    score = NumericProperty(0)
    label_text = StringProperty("")
    bar_color = ListProperty([0.545, 0.580, 0.620, 1])


class PasswordCard(BoxLayout):
    """One row in a password list: category + name, username, masked
    password, and Reveal / Copy / Delete actions (wired up by whichever
    screen creates the card, via card.ids.reveal_btn etc.)."""
    entry_id = StringProperty("")
    category = StringProperty("")
    name = StringProperty("")
    username = StringProperty("")
    password_display = StringProperty("")
    revealed = BooleanProperty(False)

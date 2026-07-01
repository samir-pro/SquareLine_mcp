"""SquareLine Studio MCP — generate SquareLine ``.spj`` projects for LVGL."""

from .board import CROWPANEL_5, PRESETS, Board
from .project import Project, Screen, Widget
from . import events, styles, widgets

__version__ = "0.2.0"

__all__ = ["Project", "Screen", "Widget", "Board", "CROWPANEL_5", "PRESETS",
           "events", "styles", "widgets"]

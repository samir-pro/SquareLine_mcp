"""SquareLine Studio MCP — generate SquareLine ``.spj`` projects for LVGL."""

from .board import CROWPANEL_5, PRESETS, Board
from .project import Project, Screen, Widget

__version__ = "0.1.0"

__all__ = ["Project", "Screen", "Widget", "Board", "CROWPANEL_5", "PRESETS"]

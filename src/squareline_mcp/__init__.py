"""SquareLine Studio MCP — generate SquareLine ``.spj`` projects for LVGL."""

from .board import CROWPANEL_5, PRESETS, Board
from .project import Project, Screen, Widget
from . import assets, events, loader, styles, widgets

__version__ = "0.4.0"


def load(path):
    """Load an existing .spj file into a Project (convenience re-export)."""
    return loader.load(path)


__all__ = ["Project", "Screen", "Widget", "Board", "CROWPANEL_5", "PRESETS",
           "assets", "events", "loader", "styles", "widgets", "load"]

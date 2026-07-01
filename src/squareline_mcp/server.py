"""
SquareLine Studio MCP server.

Exposes tools that let an MCP client (Claude, etc.) design an LVGL UI and export
it as a SquareLine Studio ``.spj`` project file, preset for the Elecrow CrowPanel
5.0" (ESP32, 800x480, LVGL 8.3.11).

Run with:  ``python -m squareline_mcp``  (stdio transport)
"""

from __future__ import annotations

import os
from dataclasses import replace
from typing import List, Optional

from mcp.server.fastmcp import FastMCP

from . import widgets
from .board import CROWPANEL_5, PRESETS
from .guide import SETUP_GUIDE
from .project import Project, Screen, Widget

mcp = FastMCP("squareline")

# The server keeps a single working project in memory across tool calls.
_project: Optional[Project] = None


def _require() -> Project:
    if _project is None:
        raise ValueError("No project yet. Call create_project first.")
    return _project


def _parse_color(color) -> List[int]:
    """Accept '#RRGGBB', '#RRGGBBAA', 'RRGGBB', or [r,g,b(,a)] -> [r,g,b,a]."""
    if color is None:
        return [0, 0, 0, 255]
    if isinstance(color, (list, tuple)):
        vals = [int(c) for c in color]
        if len(vals) == 3:
            vals.append(255)
        if len(vals) != 4:
            raise ValueError("Colour list must be [r,g,b] or [r,g,b,a]")
        return vals
    s = str(color).strip().lstrip("#")
    if len(s) in (3, 4):  # short form #rgb / #rgba
        s = "".join(ch * 2 for ch in s)
    if len(s) == 6:
        s += "ff"
    if len(s) != 8:
        raise ValueError("Colour %r must be hex #RRGGBB[AA] or an [r,g,b,a] list" % color)
    return [int(s[i:i + 2], 16) for i in (0, 2, 4, 6)]


# --- project lifecycle -------------------------------------------------------


@mcp.tool()
def create_project(name: str, preset: str = "crowpanel-5",
                   width: int = 0, height: int = 0) -> str:
    """Start a new SquareLine project (replaces any current one).

    name:   project name (used for the .spj filename and C export prefix).
    preset: board preset — one of crowpanel-5, crowpanel-7, crowpanel-4.3,
            crowpanel-2.8. Defaults to the CrowPanel 5.0" (800x480, LVGL 8.3.11).
    width/height: optional override of the preset resolution (0 = use preset).
    """
    global _project
    board = PRESETS.get(preset, CROWPANEL_5)
    board = replace(board)  # copy so overrides don't mutate the preset
    if width:
        board.width = width
    if height:
        board.height = height
    _project = Project(name=name, board=board)
    return ("Created project %r for %s (%dx%d, LVGL %s).\n"
            "Next: add_screen, then add_widget."
            % (name, board.name, board.width, board.height, board.lvgl_version))


@mcp.tool()
def add_screen(name: str) -> str:
    """Add a screen. The first screen added becomes the app's start screen."""
    p = _require()
    if any(s.name == name for s in p.screens):
        raise ValueError("Screen %r already exists" % name)
    p.screens.append(Screen(name=name))
    first = " (start screen)" if len(p.screens) == 1 else ""
    return "Added screen %r%s. Screens: %s" % (
        name, first, ", ".join(s.name for s in p.screens))


@mcp.tool()
def add_widget(screen: str, type: str, name: str,
               x: int = 0, y: int = 0, width: int = 0, height: int = 0,
               value: str = "", parent: str = "", align: str = "TOP_LEFT") -> str:
    """Add a widget to a screen (or inside a container widget).

    type:   panel, label, button, image, slider, switch, bar, arc, checkbox,
            dropdown, roller, textarea (aliases like btn/img/text/toggle work).
    x,y:    position in pixels relative to the align anchor (default TOP_LEFT).
    width/height: size in pixels (0 = the widget's sensible default).
    value:  the widget's content — label/checkbox/textarea text, image source
            path, slider/bar/arc value, dropdown/roller newline-separated options.
    parent: name of a container widget (panel/button) to nest inside; empty =
            place directly on the screen.
    align:  LVGL alignment anchor, e.g. TOP_LEFT, CENTER, TOP_MID, BOTTOM_RIGHT.
    """
    p = _require()
    key = widgets.resolve(type)
    if name in p.all_names():
        raise ValueError("Name %r is already used; names must be unique" % name)

    val = value if value != "" else None
    w = Widget(type_key=key, name=name, x=x, y=y, w=width, h=height,
               value=val, align=align)

    s = p.screen(screen)
    if parent:
        container = p.find_widget(parent)
        if not container.spec.container:
            raise ValueError("Parent %r (%s) cannot contain children"
                             % (parent, container.spec.key))
        container.children.append(w)
        where = "inside %r" % parent
    else:
        s.widgets.append(w)
        where = "on screen %r" % screen
    return "Added %s %r %s at (%d,%d) size %dx%d." % (
        key, name, where, x, y, w.w or w.spec.default_w, w.h or w.spec.default_h)


@mcp.tool()
def set_style(widget: str,
              bg_color: str = "", bg_opa: int = -1, bg_image: str = "",
              radius: int = -1, border_color: str = "", border_width: int = -1,
              text_color: str = "", text_font: str = "", text_align: str = "",
              pad: int = -1) -> str:
    """Set common style properties (DEFAULT state, MAIN part) on a widget.

    Colours accept '#RRGGBB', '#RRGGBBAA' or an r,g,b list. Only the arguments
    you pass are applied. text_font uses SquareLine font names, e.g.
    montserrat_14, montserrat_20, montserrat_28. pad sets equal padding on all
    sides. Leave numeric args as -1 / strings as "" to skip them.
    """
    p = _require()
    w = p.find_widget(widget)
    applied = []
    if bg_color:
        w.styles["bg_color"] = _parse_color(bg_color); applied.append("bg_color")
    if bg_opa >= 0:
        w.styles["bg_opa"] = bg_opa; applied.append("bg_opa")
    if bg_image:
        w.styles["bg_image"] = bg_image; applied.append("bg_image")
    if radius >= 0:
        w.styles["radius"] = radius; applied.append("radius")
    if border_color:
        w.styles["border_color"] = _parse_color(border_color); applied.append("border_color")
    if border_width >= 0:
        w.styles["border_width"] = border_width; applied.append("border_width")
    if text_color:
        w.styles["text_color"] = _parse_color(text_color); applied.append("text_color")
    if text_font:
        w.styles["text_font"] = text_font; applied.append("text_font")
    if text_align:
        w.styles["text_align"] = text_align; applied.append("text_align")
    if pad >= 0:
        w.styles["pad"] = [pad, pad, pad, pad]; applied.append("pad")
    if not applied:
        return "No style args given for %r." % widget
    return "Styled %r: %s" % (widget, ", ".join(applied))


@mcp.tool()
def set_property(widget: str, x: int = -100000, y: int = -100000,
                 width: int = -1, height: int = -1, value: str = "",
                 align: str = "", hidden: str = "", clickable: str = "",
                 checkable: str = "", disabled: str = "") -> str:
    """Update geometry / value / flags of an existing widget.

    Boolean flags (hidden/clickable/checkable/disabled) take "true"/"false".
    Leave numeric args at their sentinel (-1 / -100000) and strings empty to
    skip. Use x=-100000 sentinel because 0 is a valid coordinate.
    """
    p = _require()
    w = p.find_widget(widget)
    changed = []

    def as_bool(s):
        return str(s).strip().lower() in ("1", "true", "yes", "on")

    if x != -100000:
        w.x = x; changed.append("x")
    if y != -100000:
        w.y = y; changed.append("y")
    if width >= 0:
        w.w = width; changed.append("width")
    if height >= 0:
        w.h = height; changed.append("height")
    if value != "":
        w.value = value; changed.append("value")
    if align:
        w.align = align; changed.append("align")
    if hidden != "":
        w.hidden = as_bool(hidden); changed.append("hidden")
    if clickable != "":
        w.clickable = as_bool(clickable); changed.append("clickable")
    if checkable != "":
        w.checkable = as_bool(checkable); changed.append("checkable")
    if disabled != "":
        w.disabled = as_bool(disabled); changed.append("disabled")
    if not changed:
        return "Nothing changed on %r." % widget
    return "Updated %r: %s" % (widget, ", ".join(changed))


@mcp.tool()
def add_navigation(widget: str, target_screen: str, trigger: str = "CLICKED",
                   fade: str = "MOVE_LEFT", speed: int = 500) -> str:
    """Make a widget switch to another screen when triggered (Change Screen event).

    trigger: CLICKED, PRESSED, RELEASED, LONG_PRESSED, VALUE_CHANGED, ...
    fade:    NONE, OVER_LEFT, OVER_RIGHT, MOVE_LEFT, MOVE_RIGHT, MOVE_TOP,
             MOVE_BOTTOM, FADE_ON.
    speed:   transition time in ms.
    """
    from . import spj
    p = _require()
    w = p.find_widget(widget)
    target = p.screen(target_screen)
    w.events.append(spj.change_screen_event(trigger, target.guid, target.name,
                                             fade_mode=fade, speed=speed))
    return "%r will change to screen %r on %s." % (widget, target_screen, trigger)


@mcp.tool()
def list_project() -> str:
    """Show the current project's screens and widget tree."""
    p = _require()
    lines = ["Project: %s  (%s, %dx%d, LVGL %s)"
             % (p.name, p.board.name, p.board.width, p.board.height, p.board.lvgl_version)]
    if not p.screens:
        lines.append("  (no screens yet)")
    for s in p.screens:
        star = " *start" if s is p.screens[0] else ""
        lines.append("- Screen: %s%s" % (s.name, star))
        _tree(s.widgets, lines, 2)
    return "\n".join(lines)


def _tree(ws, lines, indent):
    for w in ws:
        extra = ""
        if w.value not in (None, ""):
            v = str(w.value).replace("\n", "\\n")
            extra = "  value=%r" % (v[:30])
        lines.append("%s%s %s  @(%d,%d) %dx%d%s"
                     % (" " * indent, w.spec.key, w.name, w.x, w.y,
                        w.w or w.spec.default_w, w.h or w.spec.default_h, extra))
        _tree(w.children, lines, indent + 2)


@mcp.tool()
def export_project(path: str = "") -> str:
    """Write the project to a ``.spj`` file and return its absolute path.

    path: destination file or directory. Empty = '<Name>.spj' in the current
    directory. A directory (or a path without .spj) gets '<Name>.spj' appended.
    """
    p = _require()
    if not p.screens:
        raise ValueError("Add at least one screen before exporting.")
    target = path or "%s.spj" % p.name
    if os.path.isdir(target) or (not target.lower().endswith(".spj")):
        target = os.path.join(target, "%s.spj" % p.name)
    target = os.path.abspath(target)
    os.makedirs(os.path.dirname(target), exist_ok=True)
    with open(target, "w", encoding="utf-8") as fh:
        fh.write(p.dumps())
    n_widgets = len(p.all_names()) - len(p.screens)
    return ("Exported %r -> %s\n(%d screen(s), %d widget(s), LVGL %s).\n"
            "Open it in SquareLine Studio via File > Open Project."
            % (p.name, target, len(p.screens), n_widgets, p.board.lvgl_version))


@mcp.tool()
def list_widget_types() -> str:
    """List the supported widget types and their default sizes."""
    lines = ["Supported widget types (type -> objtype, default size):"]
    for name in sorted(widgets.WIDGETS):
        sp = widgets.WIDGETS[name]
        lines.append("  %-10s -> %-9s %dx%d%s"
                     % (name, sp.key, sp.default_w, sp.default_h,
                        "  [container]" if sp.container else ""))
    lines.append("Aliases: " + ", ".join("%s=%s" % (a, t) for a, t in widgets.ALIASES.items()))
    return "\n".join(lines)


@mcp.tool()
def get_board_info() -> str:
    """Show the current (or default) board target and export settings."""
    b = _project.board if _project else CROWPANEL_5
    return ("Board: %s\nResolution: %dx%d, rotation %d\nLVGL: %s\n"
            "SquareLine editor format: %s\nExport: %s, colour depth %d-bit, flat_export=%s"
            % (b.name, b.width, b.height, b.rotation, b.lvgl_version,
               b.editor_version, b.board, b.color_depth, b.flat_export))


@mcp.tool()
def get_setup_guide() -> str:
    """Return the CrowPanel 5" + SquareLine + LVGL 8.3.11 Arduino setup guide."""
    return SETUP_GUIDE


def main() -> None:
    mcp.run()


if __name__ == "__main__":
    main()

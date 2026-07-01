"""
SquareLine Studio MCP server.

Design an LVGL UI through MCP tools and export it as a SquareLine Studio
``.spj`` project, preset for the Elecrow CrowPanel 5.0" (ESP32, 800x480,
LVGL 8.3.11).

Run with:  ``python -m squareline_mcp``  (stdio transport)
"""

from __future__ import annotations

import json
import os
from dataclasses import replace
from typing import Any, Dict, List, Optional

from mcp.server.fastmcp import FastMCP

from . import events, styles, widgets
from .board import CROWPANEL_5, PRESETS
from .guide import SETUP_GUIDE
from .project import Project, Screen, Widget

mcp = FastMCP("squareline")

_project: Optional[Project] = None


def _require() -> Project:
    if _project is None:
        raise ValueError("No project yet. Call create_project first.")
    return _project


def _coerce(value: str) -> Any:
    """Parse a string arg into int / JSON list / bool where sensible."""
    v = value.strip()
    if v == "":
        return ""
    try:
        return json.loads(v)          # handles ints, floats, lists, true/false
    except Exception:
        return value


def _as_bool(s: Any) -> bool:
    return str(s).strip().lower() in ("1", "true", "yes", "on")


# --- project lifecycle -------------------------------------------------------


@mcp.tool()
def create_project(name: str, preset: str = "crowpanel-5",
                   width: int = 0, height: int = 0) -> str:
    """Start a new SquareLine project (replaces any current one).

    preset: crowpanel-5 (default, 800x480), crowpanel-7, crowpanel-4.3,
    crowpanel-2.8. width/height override the preset resolution (0 = keep preset).
    """
    global _project
    board = replace(PRESETS.get(preset, CROWPANEL_5))
    if width:
        board.width = width
    if height:
        board.height = height
    _project = Project(name=name, board=board)
    return ("Created project %r for %s (%dx%d, LVGL %s). Next: add_screen."
            % (name, board.name, board.width, board.height, board.lvgl_version))


@mcp.tool()
def add_screen(name: str) -> str:
    """Add a screen. The first screen added is the app's start screen."""
    p = _require()
    if any(s.name == name for s in p.screens):
        raise ValueError("Screen %r already exists" % name)
    p.screens.append(Screen(name=name))
    first = " (start screen)" if len(p.screens) == 1 else ""
    return "Added screen %r%s." % (name, first)


@mcp.tool()
def add_widget(screen: str, type: str, name: str,
               x: int = 0, y: int = 0, width: int = 0, height: int = 0,
               value: str = "", parent: str = "", align: str = "TOP_LEFT") -> str:
    """Add a widget to a screen (or inside a container widget).

    type:  any of list_widget_types() — panel, button, label, image, slider,
           switch, bar, arc, checkbox, dropdown, roller, textarea, spinbox,
           keyboard, tabview, chart, table, meter, led, line, spinner, and more
           (aliases like btn/img/text/toggle/gauge work).
    value: the widget's main content (label/checkbox text, image source path,
           slider/bar/arc value, dropdown/roller options separated by newlines).
    parent: name of a container widget (panel/button/tabview/...) to nest inside.
    align:  LVGL anchor: TOP_LEFT, CENTER, TOP_MID, BOTTOM_RIGHT, etc.
    """
    p = _require()
    key = widgets.resolve(type)
    if name in p.all_names():
        raise ValueError("Name %r is already used; names must be unique" % name)
    w = Widget(type_key=key, name=name, x=x, y=y, w=width, h=height, align=align)
    if value != "" and w.spec.value_field:
        int_field = any(s == w.spec.value_field and it == 6 for s, it, _ in w.spec.config)
        w.set_value(_coerce(value) if int_field else value)
    s = p.screen(screen)
    if parent:
        container = p.find_widget(parent)
        if not container.spec.container:
            raise ValueError("Parent %r (%s) is not a container" % (parent, container.spec.key))
        container.children.append(w)
        where = "inside %r" % parent
    else:
        s.widgets.append(w)
        where = "on %r" % screen
    return "Added %s %r %s at (%d,%d) %dx%d." % (
        key, name, where, x, y, w.w or w.spec.default_w, w.h or w.spec.default_h)


@mcp.tool()
def set_property(widget: str, x: int = -100000, y: int = -100000,
                 width: int = -1, height: int = -1, value: str = "", align: str = "",
                 hidden: str = "", clickable: str = "", checkable: str = "",
                 disabled: str = "") -> str:
    """Update geometry / value / core flags of an existing widget.

    Boolean flags take true/false. Numeric sentinels (x/y=-100000, width/height=-1)
    and empty strings are skipped (0 is a valid coordinate, hence the sentinels).
    """
    p = _require()
    w = p.find_widget(widget)
    changed = []
    if x != -100000:
        w.x = x; changed.append("x")
    if y != -100000:
        w.y = y; changed.append("y")
    if width >= 0:
        w.w = width; changed.append("width")
    if height >= 0:
        w.h = height; changed.append("height")
    if value != "":
        w.set_value(value); changed.append("value")
    if align:
        w.align = align; changed.append("align")
    if hidden != "":
        w.hidden = _as_bool(hidden); changed.append("hidden")
    if clickable != "":
        w.clickable = _as_bool(clickable); changed.append("clickable")
    if checkable != "":
        w.checkable = _as_bool(checkable); changed.append("checkable")
    if disabled != "":
        w.disabled = _as_bool(disabled); changed.append("disabled")
    return "Updated %r: %s" % (widget, ", ".join(changed) or "nothing")


@mcp.tool()
def configure_widget(widget: str, property: str, value: str) -> str:
    """Set a widget-specific config property (from list_widget_types details).

    Examples: property="Range" value="[0,255]", property="Mode" value="SYMMETRICAL",
    property="Options" value="A\\nB\\nC", property="Number_of_points" value="20".
    Arrays/ints may be given as JSON; strings are taken literally.
    """
    p = _require()
    w = p.find_widget(widget)
    valid = {s for s, _, _ in w.spec.config}
    if property not in valid:
        raise ValueError("%s has no config %r. Valid: %s"
                         % (w.spec.key, property, ", ".join(sorted(valid)) or "none"))
    w.config[property] = _coerce(value)
    return "Set %s.%s = %r" % (widget, property, w.config[property])


@mcp.tool()
def set_flag(widget: str, flag: str, value: str = "true") -> str:
    """Set any OBJECT flag/enum on a widget by name.

    flag: Scrollable, Clickable, Hidden, Floating, Checkable, Adv_hittest,
    Event_bubble, Scroll_one, Scrollbar_mode, Scroll_direction, Press_lock, etc.
    value: true/false for flags, or the enum string for Scrollbar_mode /
    Scroll_direction.
    """
    p = _require()
    w = p.find_widget(widget)
    v: Any = _as_bool(value) if value.lower() in ("true", "false", "1", "0", "yes", "no") else value
    w.flags[flag] = v
    return "Set flag %s.%s = %r" % (widget, flag, v)


@mcp.tool()
def set_layout(widget: str, type: str = "flex", flow: str = "ROW", wrap: str = "false",
               main_align: str = "START", cross_align: str = "START",
               track_align: str = "START") -> str:
    """Give a container a Flex or Grid layout (children auto-arrange).

    type: flex | grid | none.  flow: ROW, COLUMN, ROW_WRAP, COLUMN_WRAP.
    *_align: START, END, CENTER, SPACE_EVENLY, SPACE_AROUND, SPACE_BETWEEN.
    """
    p = _require()
    w = p.find_widget(widget)
    if type.lower() == "none":
        w.layout = None
        return "Cleared layout on %r." % widget
    w.layout = {"type": type, "flow": flow, "wrap": _as_bool(wrap),
                "main_align": main_align, "cross_align": cross_align,
                "track_align": track_align}
    return "Set %s layout on %r (flow %s)." % (type, widget, flow)


@mcp.tool()
def set_style(widget: str, part: str = "main", state: str = "DEFAULT",
              bg_color: str = "", text_color: str = "", text_font: str = "",
              radius: int = -1, border_color: str = "", border_width: int = -1,
              opacity: int = -1, props_json: str = "") -> str:
    """Set style properties on a widget's part/state.

    part:  main, indicator, knob, selected, scrollbar, items, cursor, ticks,
           placeholder (widget-dependent — see list_widget_types).
    state: DEFAULT, PRESSED, CHECKED, DISABLED, FOCUSED (combine with '|').
    props_json: JSON object for any other style, e.g.
      {"shadow_color":"#000000","shadow_offset":[4,4],"pad":8,
       "bg_grad_color":"#112233","line_color":"#ff0000","image_recolor":"#00ff00"}
    Colours accept #RRGGBB, #RRGGBBAA or [r,g,b,a]. See list_styles().
    """
    p = _require()
    w = p.find_widget(widget)
    part_key = styles.resolve_part(part)  # validates
    part_name = part if part in styles.PARTS else next(
        (k for k, v in styles.PARTS.items() if v == part_key), "main")
    applied = []

    def put(k, v):
        w.set_style(k, v, part=part_name, state=state); applied.append(k)

    if bg_color:
        put("bg_color", bg_color)
    if text_color:
        put("text_color", text_color)
    if text_font:
        put("text_font", text_font)
    if radius >= 0:
        put("radius", radius)
    if border_color:
        put("border_color", border_color)
    if border_width >= 0:
        put("border_width", border_width)
    if opacity >= 0:
        put("opacity", opacity)
    if props_json:
        for k, v in json.loads(props_json).items():
            if k not in styles.STYLE_CATALOG:
                raise ValueError("Unknown style %r; see list_styles()" % k)
            put(k, v)
    if not applied:
        return "No styles given for %r." % widget
    return "Styled %r [%s/%s]: %s" % (widget, part_name, state, ", ".join(applied))


# --- events ------------------------------------------------------------------


@mcp.tool()
def add_event(widget: str, action: str, trigger: str = "CLICKED",
              target: str = "", value: str = "", params_json: str = "") -> str:
    """Attach an event action to a widget (see list_actions for names/params).

    action:  e.g. CHANGE SCREEN, BASIC_PROPERTY, LABEL_PROPERTY, SLIDER_PROPERTY,
             SET OPACITY, MODIFY FLAG, MODIFY STATE, INCREMENT SLIDER,
             STEP SPINBOX, KEYBOARD SET TARGET, CALL FUNCTION, PLAY ANIMATION...
    trigger: CLICKED, PRESSED, RELEASED, VALUE_CHANGED, LONG_PRESSED, ...
    target:  a widget/screen NAME for the action's target/object/screen param.
    value:   convenience for the action's Value param.
    params_json: JSON of remaining params by exact suffix, e.g.
             {"Property":"Position_X","Value":"20"} or
             {"Fade_mode":"MOVE_LEFT","Speed":300} or {"Flag":"HIDDEN","Action":"TOGGLE"}.
    """
    p = _require()
    w = p.find_widget(widget)
    name = events.resolve_action(action)
    params = json.loads(params_json) if params_json else {}
    pset = set(events.action_params(name))
    # map convenience 'target' to the action's guid-ref parameter
    if target:
        for cand in ("Target", "Object", "Screen_to", "Keyboard"):
            if cand in pset and cand not in params:
                params[cand] = target
                break
    if value != "" and "Value" in pset and "Value" not in params:
        params["Value"] = _coerce(value)

    def resolver(nm: str) -> str:
        return p.guid_of(nm)

    w.events.append(events.build_event(trigger, name, params, resolver))
    return "Added %s event on %r (%s)." % (name, widget, events.resolve_trigger(trigger))


@mcp.tool()
def add_navigation(widget: str, target_screen: str, trigger: str = "CLICKED",
                   fade: str = "MOVE_LEFT", speed: int = 500) -> str:
    """Convenience: make a widget switch to another screen (CHANGE SCREEN action).

    fade: NONE, OVER_LEFT/RIGHT/TOP/BOTTOM, MOVE_LEFT/RIGHT/TOP/BOTTOM, FADE_ON.
    """
    p = _require()
    w = p.find_widget(widget)
    p.screen(target_screen)  # validate exists
    params = {"Screen_to": target_screen, "Fade_mode": fade, "Speed": speed}
    w.events.append(events.build_event(trigger, "CHANGE SCREEN", params, p.guid_of))
    return "%r changes to screen %r on %s." % (widget, target_screen, events.resolve_trigger(trigger))


# --- inspection / export -----------------------------------------------------


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


def _tree(ws: List[Widget], lines: List[str], indent: int) -> None:
    for w in ws:
        val = w.config.get(w.spec.value_field) if w.spec.value_field else None
        extra = "  =%r" % (str(val)[:24]) if val not in (None, "") else ""
        ev = "  [%d event(s)]" % len(w.events) if w.events else ""
        lines.append("%s%s %s @(%d,%d) %dx%d%s%s"
                     % (" " * indent, w.spec.key, w.name, w.x, w.y,
                        w.w or w.spec.default_w, w.h or w.spec.default_h, extra, ev))
        _tree(w.children, lines, indent + 2)


@mcp.tool()
def export_project(path: str = "") -> str:
    """Write the project to a ``.spj`` file and return its absolute path."""
    p = _require()
    if not p.screens:
        raise ValueError("Add at least one screen before exporting.")
    target = path or "%s.spj" % p.name
    if os.path.isdir(target) or not target.lower().endswith(".spj"):
        target = os.path.join(target, "%s.spj" % p.name)
    target = os.path.abspath(target)
    os.makedirs(os.path.dirname(target), exist_ok=True)
    with open(target, "w", encoding="utf-8") as fh:
        fh.write(p.dumps())
    n = len(p.all_names()) - len(p.screens)
    return ("Exported %r -> %s (%d screen(s), %d widget(s)). "
            "Open in SquareLine via File > Open Project."
            % (p.name, target, len(p.screens), n))


@mcp.tool()
def list_widget_types() -> str:
    """List every supported widget type with its config props and style parts."""
    lines = ["Widget types (type -> objtype  [config]  {parts}):"]
    for name in sorted(widgets.WIDGETS):
        sp = widgets.WIDGETS[name]
        cfg = ", ".join(s for s, _, _ in sp.config) or "-"
        prt = ", ".join(pf for _, pf in sp.parts)
        tag = " [container]" if sp.container else ""
        lines.append("  %-13s -> %-10s [%s] {%s}%s" % (name, sp.key, cfg, prt, tag))
    lines.append("Aliases: " + ", ".join("%s=%s" % kv for kv in widgets.ALIASES.items()))
    return "\n".join(lines)


@mcp.tool()
def list_actions() -> str:
    """List every event action and its parameters, plus valid triggers."""
    lines = ["Event actions (action -> params):"]
    for name in sorted(events.ACTIONS):
        lines.append("  %-24s %s" % (name, ", ".join(events.action_params(name)) or "-"))
    lines.append("Triggers: " + ", ".join(events.TRIGGERS))
    return "\n".join(lines)


@mcp.tool()
def list_styles() -> str:
    """List every style property key, plus valid parts and states."""
    lines = ["Style keys: " + ", ".join(sorted(styles.STYLE_CATALOG))]
    lines.append("Parts: " + ", ".join(styles.PARTS))
    lines.append("States: " + ", ".join(styles.STATES))
    return "\n".join(lines)


@mcp.tool()
def get_board_info() -> str:
    """Show the current (or default) board target and export settings."""
    b = _project.board if _project else CROWPANEL_5
    return ("Board: %s\nResolution: %dx%d rot %d\nLVGL: %s | editor %s | %s | %d-bit | flat=%s"
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

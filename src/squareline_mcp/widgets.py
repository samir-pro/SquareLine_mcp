"""
Widget catalogue for the SquareLine ``.spj`` generator.

Each :class:`WidgetSpec` describes an LVGL / SquareLine object type: its
``saved_objtypeKey``, container flag, default geometry, the widget-specific
*config* properties appended after the shared ``OBJECT/*`` base, and the *style
parts* it exposes.

Widget-specific property names, InheritedTypes and style parts were extracted
from genuine SquareLine 1.4.x / LVGL 8.3.11 exports for these verified types:
SCREEN, PANEL, LABEL, BUTTON, IMAGE, IMGBUTTON, SLIDER, SWITCH, BAR, ARC,
ROLLER, SPINBOX, KEYBOARD, TABVIEW, TABPAGE, TEXTAREA, CHART.

The remaining types (checkbox, dropdown, line, led, spinner, table, calendar,
meter, list, buttonmatrix, tileview, win, canvas, colorwheel, animimg,
messagebox) reuse the same verified scaffolding with best-effort config; open +
re-save once in SquareLine to normalise them.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

from . import spj, styles

# A config property: (suffix, InheritedType, default_value)
Config = Tuple[str, int, Any]
# A style part: (style_property_suffix, friendly_part_name)
StylePart = Tuple[str, str]

# Human-readable style summaries per part (cosmetic; SquareLine regenerates).
_SUMMARY = {
    "main": "lv.PART.MAIN, Rectangle, Pad, Text, Transform",
    "scrollbar": "lv.PART.SCROLLBAR, Rectangle, Pad",
    "indicator": "lv.PART.INDICATOR, Rectangle, Pad",
    "knob": "lv.PART.KNOB, Rectangle, Pad",
    "selected": "lv.PART.SELECTED, Rectangle, Pad",
    "items": "lv.PART.ITEMS, Rectangle, Pad, Text",
    "cursor": "lv.PART.CURSOR, Rectangle, Pad",
    "ticks": "lv.PART.TICKS, Line, Text",
    "placeholder": "lv.PART_TEXTAREA.PLACEHOLDER, Text",
}


@dataclass
class WidgetSpec:
    key: str
    container: bool = False
    clickable: bool = True
    checkable: bool = False
    default_w: int = 100
    default_h: int = 50
    header: Optional[str] = None          # widget header suffix, e.g. "Label"
    config: List[Config] = field(default_factory=list)
    value_field: Optional[str] = None     # config suffix that `value` maps to
    parts: List[StylePart] = field(default_factory=lambda: [("Style_main", "main")])

    def summary(self, part: str) -> str:
        return _SUMMARY.get(part, "lv.PART.MAIN")


def _c(*items: Config) -> List[Config]:
    return list(items)


# NB. Range/Value defaults follow LVGL 8.3 widget defaults; SquareLine fixes any.
WIDGETS: Dict[str, WidgetSpec] = {
    # --- containers ---------------------------------------------------------
    "panel": WidgetSpec("PANEL", container=True, clickable=False, default_w=200, default_h=150,
                        parts=[("Style_main", "main"), ("Style_scrollbar", "scrollbar")]),
    "button": WidgetSpec("BUTTON", container=True, default_w=120, default_h=50),
    "tabview": WidgetSpec("TABVIEW", container=True, default_w=400, default_h=300,
                          header="Tabview",
                          config=_c(("Tab_position", spj.IT_ENUM, "TOP"),
                                    ("Tab_size", spj.IT_INT, 50)),
                          parts=[("Style_main", "main"),
                                 ("Style_buttons_main", "items"),
                                 ("Style_buttons_items", "items")]),
    "tabpage": WidgetSpec("TABPAGE", container=True, default_w=380, default_h=240,
                          header="TabPage", config=_c(("Title", spj.IT_STRING, "Tab")),
                          value_field="Title",
                          parts=[("Style_main", "main"), ("Style_scrollbar", "scrollbar")]),
    "tileview": WidgetSpec("TILEVIEW", container=True, default_w=400, default_h=300,
                           header="Tileview",
                           parts=[("Style_main", "main"), ("Style_scrollbar", "scrollbar")]),
    "window": WidgetSpec("WIN", container=True, default_w=400, default_h=300, header="Win"),
    "list": WidgetSpec("LIST", container=True, default_w=200, default_h=250, header="List",
                       parts=[("Style_main", "main"), ("Style_scrollbar", "scrollbar")]),
    "messagebox": WidgetSpec("MSGBOX", container=True, default_w=300, default_h=180, header="Msgbox"),

    # --- basic --------------------------------------------------------------
    "label": WidgetSpec("LABEL", clickable=False, default_w=120, default_h=32, header="Label",
                        config=_c(("Long_mode", spj.IT_ENUM, "WRAP"),
                                  ("Text", spj.IT_STRING, "Label"),
                                  ("Recolor", spj.IT_BOOL, False)),
                        value_field="Text"),
    "image": WidgetSpec("IMAGE", clickable=False, default_w=100, default_h=100, header="Image",
                        config=_c(("Asset", spj.IT_IMAGE, ""),
                                  ("Pivot", spj.IT_INTARRAY, [0, 0]),
                                  ("Rotation", spj.IT_INT, 0),
                                  ("Scale", spj.IT_INT, 256)),
                        value_field="Asset"),
    "imagebutton": WidgetSpec("IMGBUTTON", default_w=100, default_h=50, header="Images",
                              config=_c(("Button_state", spj.IT_ENUM, "RELEASED"),
                                        ("Image_released", spj.IT_IMAGE, ""),
                                        ("Image_pressed", spj.IT_IMAGE, ""),
                                        ("Image_disabled", spj.IT_IMAGE, ""),
                                        ("Image_checked_released", spj.IT_IMAGE, ""),
                                        ("Image_checked_pressed", spj.IT_IMAGE, ""),
                                        ("Image_checked_disabled", spj.IT_IMAGE, "")),
                              value_field="Image_released"),
    "line": WidgetSpec("LINE", clickable=False, default_w=100, default_h=100, header="Line"),
    "led": WidgetSpec("LED", clickable=False, default_w=30, default_h=30, header="Led",
                      config=_c(("Brightness", spj.IT_INT, 255))),
    "animimg": WidgetSpec("ANIMIMG", clickable=False, default_w=100, default_h=100, header="Animimg"),
    "canvas": WidgetSpec("CANVAS", clickable=False, default_w=200, default_h=150, header="Canvas"),

    # --- inputs / values ----------------------------------------------------
    "slider": WidgetSpec("SLIDER", default_w=200, default_h=20, header="Slider",
                        config=_c(("Range", spj.IT_INTARRAY, [0, 100]),
                                  ("Mode", spj.IT_ENUM, "NORMAL"),
                                  ("Value", spj.IT_INT, 50),
                                  ("Value_left", spj.IT_INT, 0)),
                        value_field="Value",
                        parts=[("Style_main", "main"), ("Style_indicator", "indicator"),
                               ("Style_knob", "knob")]),
    "switch": WidgetSpec("SWITCH", checkable=True, default_w=60, default_h=30,
                        parts=[("Style_main", "main"), ("Style_indicator", "indicator"),
                               ("Style_knob", "knob")]),
    "bar": WidgetSpec("BAR", clickable=False, default_w=200, default_h=20, header="Bar",
                     config=_c(("Range", spj.IT_INTARRAY, [0, 100]),
                               ("Value", spj.IT_INT, 70),
                               ("Mode", spj.IT_ENUM, "NORMAL"),
                               ("Value_start", spj.IT_INT, 0)),
                     value_field="Value",
                     parts=[("Style_main", "main"), ("Style_indicator", "indicator")]),
    "arc": WidgetSpec("ARC", default_w=150, default_h=150, header="Arc",
                     config=_c(("Range", spj.IT_INTARRAY, [0, 100]),
                               ("Value", spj.IT_INT, 25),
                               ("Bg_angles", spj.IT_INTARRAY, [135, 45]),
                               ("Mode", spj.IT_ENUM, "NORMAL"),
                               ("Rotation", spj.IT_INT, 0)),
                     value_field="Value",
                     parts=[("Style_main", "main"), ("Style_indicator", "indicator"),
                            ("Style_knob", "knob")]),
    "checkbox": WidgetSpec("CHECKBOX", checkable=True, default_w=120, default_h=32, header="Checkbox",
                          config=_c(("Text", spj.IT_STRING, "Checkbox")),
                          value_field="Text",
                          parts=[("Style_main", "main"), ("Style_indicator", "indicator")]),
    "dropdown": WidgetSpec("DROPDOWN", default_w=150, default_h=40, header="Dropdown",
                          config=_c(("Options", spj.IT_STRING, "Option 1\nOption 2\nOption 3"),
                                    ("Selected", spj.IT_INT, 0),
                                    ("Dir", spj.IT_ENUM, "BOTTOM")),
                          value_field="Options",
                          parts=[("Style_main", "main"), ("Style_indicator", "indicator"),
                                 ("Style_selected", "selected"), ("Style_scrollbar", "scrollbar")]),
    "roller": WidgetSpec("ROLLER", default_w=120, default_h=100, header="Roller",
                        config=_c(("Options", spj.IT_STRING, "Option 1\nOption 2\nOption 3"),
                                  ("Mode", spj.IT_ENUM, "NORMAL"),
                                  ("Selected", spj.IT_INT, 0)),
                        value_field="Options",
                        parts=[("Style_main", "main"), ("Style_selected", "selected")]),
    "textarea": WidgetSpec("TEXTAREA", default_w=200, default_h=50, header="TextArea",
                          config=_c(("Text", spj.IT_STRING, ""),
                                    ("Placeholder", spj.IT_STRING, ""),
                                    ("One_line_mode", spj.IT_BOOL, False),
                                    ("Password_mode", spj.IT_BOOL, False),
                                    ("Accepted_characters", spj.IT_STRING, ""),
                                    ("Max_text_length", spj.IT_INT, 0)),
                          value_field="Text",
                          parts=[("Style_main", "main"), ("Style_selected", "selected"),
                                 ("Style_cursor", "cursor"), ("Style_placeholder", "placeholder")]),
    "spinbox": WidgetSpec("SPINBOX", default_w=100, default_h=40, header="Spinbox",
                         config=_c(("Digit_format", spj.IT_INTARRAY, [5, 2]),
                                   ("Range", spj.IT_INTARRAY, [-1000, 1000]),
                                   ("Value", spj.IT_INT, 0)),
                         value_field="Value",
                         parts=[("Style_main", "main"), ("Style_cursor", "cursor")]),
    "keyboard": WidgetSpec("KEYBOARD", default_w=300, default_h=180,
                          config=_c(("Target_textarea", spj.IT_GUIDREF, ""),
                                    ("Mode", spj.IT_ENUM, "TEXT_LOWER")),
                          parts=[("Style_main", "main"), ("Style_items", "items")]),
    "spinner": WidgetSpec("SPINNER", clickable=False, default_w=80, default_h=80, header="Spinner",
                         config=_c(("Speed", spj.IT_INT, 1000), ("Angle", spj.IT_INT, 60)),
                         parts=[("Style_main", "main"), ("Style_indicator", "indicator")]),
    "colorwheel": WidgetSpec("COLORWHEEL", default_w=200, default_h=200, header="Colorwheel",
                            config=_c(("Mode", spj.IT_ENUM, "HUE")),
                            parts=[("Style_main", "main"), ("Style_knob", "knob")]),

    # --- data display -------------------------------------------------------
    "chart": WidgetSpec("CHART", clickable=False, default_w=300, default_h=200, header="Chart",
                       config=_c(("Chart_type", spj.IT_ENUM, "LINE"),
                                 ("Number_of_points", spj.IT_INT, 10),
                                 ("Division_lines", spj.IT_INTARRAY, [3, 5]),
                                 ("Zoom", spj.IT_INTARRAY, [256, 256]),
                                 ("X_Axis", spj.IT_HEADER, None),
                                 ("XMajor", spj.IT_INTARRAY, [10, 5]),
                                 ("XMinor", spj.IT_INTARRAY, [5, 2]),
                                 ("Labels_on_X_axis", spj.IT_BOOL, False),
                                 ("Font_size_on_X_axis", spj.IT_INT, 14),
                                 ("Primary_Y_Axis", spj.IT_HEADER, None),
                                 ("Primary_Y_range", spj.IT_INTARRAY, [0, 100]),
                                 ("PrimaryYMajor", spj.IT_INTARRAY, [10, 5]),
                                 ("PrimaryYMinor", spj.IT_INTARRAY, [5, 2]),
                                 ("Labels_on_Primary_Y_axis", spj.IT_BOOL, True),
                                 ("Font_size_on_Primary_Y_axis", spj.IT_INT, 14),
                                 ("Secondary_Y_Axis", spj.IT_HEADER, None),
                                 ("Secondary_Y_range", spj.IT_INTARRAY, [0, 100]),
                                 ("SecondaryYMajor", spj.IT_INTARRAY, [10, 5]),
                                 ("SecondaryYMinor", spj.IT_INTARRAY, [5, 2]),
                                 ("Labels_on_Secondary_Y_axis", spj.IT_BOOL, False),
                                 ("Font_size_on_Secondary_Y_axis", spj.IT_INT, 14),
                                 ("Chart_data", spj.IT_HEADER, None),
                                 ("ChartData", 12,
                                  '[{"Axis":0,"Color":[241,11,46,255],"Series":[]}]')),
                       parts=[("Style_bg", "main"), ("Style_scrollbar", "scrollbar"),
                              ("Style_items", "items"), ("Style_indicator", "indicator"),
                              ("Style_ticks", "ticks")]),
    "table": WidgetSpec("TABLE", default_w=300, default_h=200, header="Table",
                       parts=[("Style_main", "main"), ("Style_items", "items"),
                              ("Style_scrollbar", "scrollbar")]),
    "calendar": WidgetSpec("CALENDAR", default_w=300, default_h=300, header="Calendar",
                          parts=[("Style_main", "main"), ("Style_items", "items")]),
    "meter": WidgetSpec("METER", clickable=False, default_w=200, default_h=200, header="Meter",
                       parts=[("Style_main", "main"), ("Style_indicator", "indicator"),
                              ("Style_items", "items"), ("Style_ticks", "ticks")]),
    "buttonmatrix": WidgetSpec("BTNMATRIX", default_w=250, default_h=150, header="Btnmatrix",
                              config=_c(("Map", spj.IT_STRING, "Btn1\nBtn2\nBtn3")),
                              parts=[("Style_main", "main"), ("Style_items", "items")]),
}


ALIASES = {
    "container": "panel", "obj": "panel", "text": "label", "btn": "button",
    "img": "image", "picture": "image", "imgbtn": "imagebutton", "imagebtn": "imagebutton",
    "toggle": "switch", "progress": "bar", "progressbar": "bar", "gauge": "arc",
    "input": "textarea", "textfield": "textarea", "combobox": "dropdown", "select": "dropdown",
    "tabs": "tabview", "tab": "tabpage", "win": "window", "msgbox": "messagebox",
    "matrix": "buttonmatrix", "btnmatrix": "buttonmatrix", "color_picker": "colorwheel",
    "loading": "spinner", "number": "spinbox",
}


def resolve(type_name: str) -> str:
    key = (type_name or "").strip().lower().replace(" ", "").replace("_", "")
    key = ALIASES.get(key, key)
    if key not in WIDGETS:
        raise ValueError("Unknown widget type %r. Supported: %s"
                         % (type_name, ", ".join(sorted(WIDGETS))))
    return key


def config_props(spec: WidgetSpec, overrides: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Widget header + config records, applying per-instance overrides by suffix."""
    recs: List[Dict[str, Any]] = []
    if spec.header:
        recs.append(spj.p_value("%s/%s" % (spec.key, spec.header), spj.IT_HEADER, None))
    for suffix, it, default in spec.config:
        value = overrides.get(suffix, default)
        if it == spj.IT_INT and isinstance(value, str) and value != "":
            value = int(value)
        if it == spj.IT_IMAGE and value in ("", None):
            value = "-"          # SquareLine's "no image" sentinel
        recs.append(spj.p_value("%s/%s" % (spec.key, suffix), it, value))
    return recs


def style_records(spec: WidgetSpec, part_styles: Dict[str, Dict[str, Dict[str, Any]]]
                  ) -> List[Dict[str, Any]]:
    """Build every style-part record for a widget, injecting user styles.

    ``part_styles`` maps friendly part name -> state -> {friendly_key: value}.
    """
    recs = []
    for suffix, part_friendly in spec.parts:
        by_state = part_styles.get(part_friendly, {})
        states = {state: styles.build_children(kv) for state, kv in by_state.items()}
        recs.append(spj.p_style("%s/%s" % (spec.key, suffix),
                                styles.PARTS.get(part_friendly, "lv.PART.MAIN"),
                                spec.summary(part_friendly), states))
    return recs

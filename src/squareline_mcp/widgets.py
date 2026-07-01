"""
Widget catalogue for the SquareLine ``.spj`` generator.

Each entry describes an LVGL / SquareLine object type: its ``saved_objtypeKey``,
whether it can contain children, its default geometry, and the widget-specific
property records that are appended after the shared ``OBJECT/*`` base.

Verified against a genuine SquareLine 1.4.2 / LVGL 8.3.11 export: ``SCREEN``,
``PANEL`` and ``LABEL``.  The remaining widget types reuse the same verified
object/style scaffolding and add their most important value property; when in
doubt SquareLine fills in any missing widget-specific defaults on first open.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional

from . import spj


# A "value" is the natural editable content of a widget (label text, image
# source, slider value...).  Each spec knows how to turn a value into extra
# property records so the model can stay widget-agnostic.
ValueBuilder = Callable[[Any], List[Dict[str, Any]]]


@dataclass
class WidgetSpec:
    key: str                       # saved_objtypeKey
    container: bool = False        # may hold child widgets
    clickable: bool = True
    checkable: bool = False        # default checkable state (switch/checkbox)
    default_w: int = 100
    default_h: int = 50
    style_summary: str = "lv.PART.MAIN, Rectangle, Pad, Text, Transform"
    has_scrollbar: bool = False    # containers get a Style_scrollbar record
    value_key: Optional[str] = None    # human name of the value property
    value_default: Any = None
    value_builder: Optional[ValueBuilder] = None
    # extra static widget-specific records (headers/enums that always appear)
    extra: Callable[[], List[Dict[str, Any]]] = field(default=lambda: [])


def _label_value(text: str) -> List[Dict[str, Any]]:
    return [
        spj.p_header("LABEL/Label"),
        spj.p_enum("LABEL/Long_mode", "WRAP"),
        spj.p_string("LABEL/Text", text),
        spj.p_bool("LABEL/Recolor", False),
    ]


def _image_value(src: str) -> List[Dict[str, Any]]:
    return [
        spj.p_header("IMAGE/Image"),
        spj.p_image("IMAGE/Src", src or ""),
        spj.p_int("IMAGE/Rotation", 0),
        spj.p_int("IMAGE/Zoom", 256),
        spj.p_bool("IMAGE/Antialias", True),
    ]


def _ranged_value(prefix: str, value: int, vmin: int = 0, vmax: int = 100) -> List[Dict[str, Any]]:
    return [
        spj.p_header("%s/%s" % (prefix, prefix.capitalize())),
        spj.p_int("%s/Value" % prefix, value),
        spj.p_int("%s/Min" % prefix, vmin),
        spj.p_int("%s/Max" % prefix, vmax),
    ]


def _checkbox_value(text: str) -> List[Dict[str, Any]]:
    return [spj.p_header("CHECKBOX/Checkbox"), spj.p_string("CHECKBOX/Text", text)]


def _dropdown_value(options: str) -> List[Dict[str, Any]]:
    return [spj.p_header("DROPDOWN/Dropdown"), spj.p_string("DROPDOWN/Options", options)]


def _roller_value(options: str) -> List[Dict[str, Any]]:
    return [spj.p_header("ROLLER/Roller"), spj.p_string("ROLLER/Options", options)]


def _textarea_value(text: str) -> List[Dict[str, Any]]:
    return [
        spj.p_header("TEXTAREA/Textarea"),
        spj.p_string("TEXTAREA/Text", text),
        spj.p_string("TEXTAREA/Placeholder", ""),
        spj.p_bool("TEXTAREA/One_line", False),
        spj.p_bool("TEXTAREA/Password", False),
    ]


WIDGETS: Dict[str, WidgetSpec] = {
    "panel": WidgetSpec(
        key="PANEL", container=True, clickable=False, default_w=200, default_h=150,
        style_summary="lv.PART.MAIN, Rectangle, Pad, Text, Transform", has_scrollbar=True,
    ),
    "label": WidgetSpec(
        key="LABEL", clickable=False, default_w=120, default_h=32,
        style_summary="lv.PART.MAIN, Text, Rectangle, Pad, Transform",
        value_key="text", value_default="Label", value_builder=_label_value,
    ),
    "button": WidgetSpec(
        key="BUTTON", container=True, clickable=True, default_w=120, default_h=50,
        style_summary="lv.PART.MAIN, Rectangle, Pad, Text, Transform",
    ),
    "image": WidgetSpec(
        key="IMAGE", clickable=False, default_w=100, default_h=100,
        style_summary="lv.PART.MAIN, Image, Transform, Recolor",
        value_key="src", value_default="", value_builder=_image_value,
    ),
    "slider": WidgetSpec(
        key="SLIDER", clickable=True, default_w=200, default_h=20,
        style_summary="lv.PART.MAIN, Rectangle, Pad, Transform",
        value_key="value", value_default=50,
        value_builder=lambda v: _ranged_value("SLIDER", int(v)),
    ),
    "switch": WidgetSpec(
        key="SWITCH", clickable=True, checkable=True, default_w=60, default_h=30,
        style_summary="lv.PART.MAIN, Rectangle, Pad, Transform",
    ),
    "bar": WidgetSpec(
        key="BAR", clickable=False, default_w=200, default_h=20,
        style_summary="lv.PART.MAIN, Rectangle, Pad, Transform",
        value_key="value", value_default=70,
        value_builder=lambda v: _ranged_value("BAR", int(v)),
    ),
    "arc": WidgetSpec(
        key="ARC", clickable=True, default_w=150, default_h=150,
        style_summary="lv.PART.MAIN, Arc, Transform",
        value_key="value", value_default=25,
        value_builder=lambda v: _ranged_value("ARC", int(v)),
    ),
    "checkbox": WidgetSpec(
        key="CHECKBOX", clickable=True, checkable=True, default_w=120, default_h=32,
        style_summary="lv.PART.MAIN, Rectangle, Pad, Text, Transform",
        value_key="text", value_default="Checkbox", value_builder=_checkbox_value,
    ),
    "dropdown": WidgetSpec(
        key="DROPDOWN", clickable=True, default_w=150, default_h=40,
        style_summary="lv.PART.MAIN, Rectangle, Pad, Text, Transform",
        value_key="options", value_default="Option 1\nOption 2\nOption 3",
        value_builder=_dropdown_value,
    ),
    "roller": WidgetSpec(
        key="ROLLER", clickable=True, default_w=120, default_h=100,
        style_summary="lv.PART.MAIN, Rectangle, Pad, Text, Transform",
        value_key="options", value_default="Option 1\nOption 2\nOption 3",
        value_builder=_roller_value,
    ),
    "textarea": WidgetSpec(
        key="TEXTAREA", clickable=True, default_w=200, default_h=50,
        style_summary="lv.PART.MAIN, Rectangle, Pad, Text, Transform",
        value_key="text", value_default="", value_builder=_textarea_value,
    ),
}


# Friendly aliases so callers can say "btn", "img", "text", etc.
ALIASES = {
    "container": "panel",
    "obj": "panel",
    "text": "label",
    "btn": "button",
    "img": "image",
    "picture": "image",
    "toggle": "switch",
    "progress": "bar",
    "progressbar": "bar",
    "gauge": "arc",
    "input": "textarea",
    "textfield": "textarea",
    "combobox": "dropdown",
    "select": "dropdown",
}


def resolve(type_name: str) -> str:
    """Normalise a user-supplied widget type to a registry key."""
    key = (type_name or "").strip().lower().replace(" ", "").replace("_", "")
    key = ALIASES.get(key, key)
    if key not in WIDGETS:
        raise ValueError(
            "Unknown widget type %r. Supported types: %s"
            % (type_name, ", ".join(sorted(WIDGETS)))
        )
    return key


def widget_value_props(spec: WidgetSpec, value: Any) -> List[Dict[str, Any]]:
    """Build the widget-specific value records for a widget spec."""
    records: List[Dict[str, Any]] = list(spec.extra())
    if spec.value_builder is not None:
        v = value if value is not None else spec.value_default
        records += spec.value_builder(v)
    return records


def style_records(spec: WidgetSpec, prefix: str, styles: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Build the Style_main (and Style_scrollbar) records for a widget."""
    children = spj.build_style_children(styles or {})
    recs = [spj.p_style("%s/Style_main" % prefix, "lv.PART.MAIN", spec.style_summary, children)]
    if spec.has_scrollbar:
        recs.append(
            spj.p_style(
                "%s/Style_scrollbar" % prefix,
                "lv.PART.SCROLLBAR",
                "lv.PART.SCROLLBAR, Rectangle, Pad",
                [],
            )
        )
    return recs

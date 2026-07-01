"""
Full style-property catalogue and helpers.

Every style property SquareLine can set on a part/state is listed here with its
``_style/*`` strtype and InheritedType (verified against real exports). Callers
address a property by a friendly key (e.g. ``bg_color``, ``shadow_offset``).

Parts and states are open strings so any LVGL combination works, e.g.
part ``lv.PART.INDICATOR`` with state ``CHECKED|PRESSED``.
"""

from __future__ import annotations

from typing import Any, Dict, List, Tuple

from . import spj

# friendly key -> (strtype, InheritedType, kind)
# kind: "color" (-> [r,g,b,a]), "int", "enum", "image", "array" (raw int list)
STYLE_CATALOG: Dict[str, Tuple[str, int, str]] = {
    # background
    "bg_color":        ("_style/Bg_Color", spj.IT_INTARRAY, "color"),
    "bg_opa":          ("_style/Blend_opacity", spj.IT_INT, "int"),
    "opacity":         ("_style/Blend_opacity", spj.IT_INT, "int"),
    "bg_grad_color":   ("_style/Bg_gradiens_Color", spj.IT_INTARRAY, "color"),
    "bg_grad_dir":     ("_style/Gradient direction", spj.IT_ENUM, "enum"),
    "bg_grad_params":  ("_style/Bg_gradient_params", spj.IT_INTARRAY, "array"),
    "bg_image":        ("_style/Bg_Image", spj.IT_IMAGE, "image"),
    "radius":          ("_style/Bg_Radius", spj.IT_INT, "int"),
    # border
    "border_color":    ("_style/Border_Color", spj.IT_INTARRAY, "color"),
    "border_width":    ("_style/Border width", spj.IT_INT, "int"),
    "border_side":     ("_style/Border side", spj.IT_ENUM, "enum"),
    # outline
    "outline_color":   ("_style/Outline_Color", spj.IT_INTARRAY, "color"),
    "outline_params":  ("_style/Outline_params", spj.IT_INTARRAY, "array"),
    # shadow
    "shadow_color":    ("_style/Shadow_Color", spj.IT_INTARRAY, "color"),
    "shadow_offset":   ("_style/Shadow_offset", spj.IT_INTARRAY, "array"),
    "shadow_params":   ("_style/Shadow_params", spj.IT_INTARRAY, "array"),
    # line / image
    "line_color":      ("_style/Line_Color", spj.IT_INTARRAY, "color"),
    "image_recolor":   ("_style/Image_reColor", spj.IT_INTARRAY, "color"),
    # text
    "text_color":      ("_style/Text_Color", spj.IT_INTARRAY, "color"),
    "text_font":       ("_style/Text_Font", spj.IT_ENUM, "enum"),
    "text_align":      ("_style/Text_Align", spj.IT_ENUM, "enum"),
    # padding: [left, top, right, bottom]
    "pad":             ("_style/Padding", spj.IT_INTARRAY, "array"),
}

# Common LVGL parts, friendly name -> lv.PART.* string.
PARTS: Dict[str, str] = {
    "main": "lv.PART.MAIN",
    "scrollbar": "lv.PART.SCROLLBAR",
    "indicator": "lv.PART.INDICATOR",
    "knob": "lv.PART.KNOB",
    "selected": "lv.PART.SELECTED",
    "items": "lv.PART.ITEMS",
    "cursor": "lv.PART.CURSOR",
    "ticks": "lv.PART.TICKS",
    "placeholder": "lv.PART_TEXTAREA.PLACEHOLDER",
}

# Valid state names (may be combined with '|', e.g. CHECKED|PRESSED).
STATES = ["DEFAULT", "PRESSED", "CHECKED", "DISABLED", "FOCUSED", "EDITED",
          "HOVERED", "SCROLLED", "USER_1", "USER_2", "USER_3", "USER_4"]


def parse_color(color: Any) -> List[int]:
    """'#RRGGBB', '#RRGGBBAA', 'RRGGBB', short '#RGB', or [r,g,b(,a)] -> [r,g,b,a]."""
    if isinstance(color, (list, tuple)):
        vals = [int(c) for c in color]
        if len(vals) == 3:
            vals.append(255)
        if len(vals) != 4:
            raise ValueError("Colour list must be [r,g,b] or [r,g,b,a]")
        return vals
    s = str(color).strip().lstrip("#")
    if len(s) in (3, 4):
        s = "".join(ch * 2 for ch in s)
    if len(s) == 6:
        s += "ff"
    if len(s) != 8:
        raise ValueError("Colour %r must be hex #RRGGBB[AA] or an [r,g,b,a] list" % color)
    return [int(s[i:i + 2], 16) for i in (0, 2, 4, 6)]


def build_record(key: str, value: Any) -> Dict[str, Any]:
    """Turn one friendly style key + value into a ``_style/*`` property record."""
    if key not in STYLE_CATALOG:
        raise ValueError("Unknown style %r. Known: %s"
                         % (key, ", ".join(sorted(STYLE_CATALOG))))
    strtype, it, kind = STYLE_CATALOG[key]
    if kind == "color":
        value = parse_color(value)
    elif kind == "array" and not isinstance(value, (list, tuple)):
        value = [int(value)] * 4 if key == "pad" else [int(value)]
    return spj.p_value(strtype, it, value)


def build_children(styles: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Build the list of style records for one part/state from friendly keys."""
    return [build_record(k, v) for k, v in styles.items()]


def resolve_part(name: str) -> str:
    """Friendly part name or raw lv.PART.* string -> lv.PART.* string."""
    n = (name or "main").strip().lower()
    if n in PARTS:
        return PARTS[n]
    if name.startswith("lv.PART"):
        return name
    raise ValueError("Unknown part %r. Known: %s" % (name, ", ".join(PARTS)))

"""
Load an existing SquareLine ``.spj`` back into the in-memory model.

Loaded screens/widgets keep their **original node** (see ``Widget.node`` /
``Screen.node``). Edits patch that node in place and everything else is written
back verbatim on save, so ``load -> edit -> export`` is lossless even for widget
types or properties this package doesn't model semantically.
"""

from __future__ import annotations

import json
from typing import Any, Dict

from . import project as _p
from . import spj, widgets
from .board import Board

# saved_objtypeKey -> our friendly widget key (reverse of the catalogue)
OBJTYPE_TO_FRIENDLY = {spec.key: friendly for friendly, spec in widgets.WIDGETS.items()}


def board_from_info(info: Dict[str, Any]) -> Board:
    name = info.get("Name") or "Loaded"
    return Board(
        name="%s (loaded)" % name,
        width=int(info.get("width", 800)),
        height=int(info.get("height", 480)),
        board=info.get("board", "Arduino with TFT_eSPI"),
        board_version=info.get("board_version", "v1.1.2"),
        editor_version=info.get("editor_version", "1.4.2"),
        lvgl_version=info.get("lvgl_version", "8.3.11"),
        color_depth=int(info.get("BitDepth", 16)),
        rotation=int(info.get("rotation", 0)),
        flat_export=bool(info.get("flat_export", True)),
    )


def load(path: str) -> "_p.Project":
    with open(path, encoding="utf-8") as fh:
        return from_dict(json.load(fh))


def from_dict(d: Dict[str, Any]) -> "_p.Project":
    info = d.get("info", {}) or {}
    proj = _p.Project(name=info.get("Name") or "Loaded", board=board_from_info(info))
    proj.raw_info = info
    proj.animations = d.get("animations", []) or []
    proj.selected_theme = d.get("selected_theme", "") or ""
    root = d.get("root", {}) or {}
    proj.root_guid = root.get("guid")
    proj.root_props = root.get("properties", [])
    for snode in root.get("children", []):
        proj.screens.append(_load_screen(snode))
    return proj


def _load_screen(node: Dict[str, Any]) -> "_p.Screen":
    props = node.get("properties", [])
    s = _p.Screen(name=_p.prop_value(props, "OBJECT/Name") or "Screen",
                  guid=node.get("guid") or spj.new_guid())
    s.node = node
    s.widgets = [_load_widget(c) for c in node.get("children", [])]
    return s


def _load_widget(node: Dict[str, Any]) -> "_p.Widget":
    key = node.get("saved_objtypeKey", "")
    friendly = OBJTYPE_TO_FRIENDLY.get(key)
    props = node.get("properties", [])
    pos = _p.prop_value(props, "OBJECT/Position") or [0, 0]
    size = _p.prop_value(props, "OBJECT/Size") or [0, 0]
    w = _p.Widget(
        type_key=friendly or "",
        name=_p.prop_value(props, "OBJECT/Name") or key,
        x=int(pos[0]) if len(pos) > 0 else 0,
        y=int(pos[1]) if len(pos) > 1 else 0,
        w=int(size[0]) if len(size) > 0 else 0,
        h=int(size[1]) if len(size) > 1 else 0,
        align=_p.prop_value(props, "OBJECT/Align") or "TOP_LEFT",
        guid=node.get("guid") or spj.new_guid(),
    )
    w.node = node
    if friendly is None:
        w.raw_key = key
    if "children" in node:
        w.children = [_load_widget(c) for c in node["children"]]
    return w

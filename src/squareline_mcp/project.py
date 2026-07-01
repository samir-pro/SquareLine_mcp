"""
In-memory UI model and ``.spj`` assembler.

The model is intentionally small and JSON-friendly so the MCP server can mutate
it across tool calls and serialise it to a SquareLine project on demand.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from . import spj, widgets
from .board import CROWPANEL_5, Board


# --- model -------------------------------------------------------------------


@dataclass
class Widget:
    type_key: str
    name: str
    x: int = 0
    y: int = 0
    w: int = 0
    h: int = 0
    align: str = "TOP_LEFT"
    value: Any = None
    hidden: bool = False
    clickable: Optional[bool] = None      # None => widget default
    checkable: Optional[bool] = None
    disabled: bool = False
    styles: Dict[str, Any] = field(default_factory=dict)
    events: List[Dict[str, Any]] = field(default_factory=list)
    children: List["Widget"] = field(default_factory=list)
    guid: str = field(default_factory=spj.new_guid)

    @property
    def spec(self) -> widgets.WidgetSpec:
        return widgets.WIDGETS[self.type_key]


@dataclass
class Screen:
    name: str
    widgets: List[Widget] = field(default_factory=list)
    events: List[Dict[str, Any]] = field(default_factory=list)
    guid: str = field(default_factory=spj.new_guid)


@dataclass
class Project:
    name: str
    board: Board = field(default_factory=lambda: CROWPANEL_5)
    screens: List[Screen] = field(default_factory=list)

    # -- lookups -------------------------------------------------------------

    def screen(self, name: str) -> Screen:
        for s in self.screens:
            if s.name == name:
                return s
        raise KeyError("No screen named %r (have: %s)"
                       % (name, ", ".join(s.name for s in self.screens) or "none"))

    def find_widget(self, name: str) -> Widget:
        for s in self.screens:
            found = _find(s.widgets, name)
            if found is not None:
                return found
        raise KeyError("No widget named %r" % name)

    def all_names(self) -> List[str]:
        names = [s.name for s in self.screens]
        for s in self.screens:
            _collect(s.widgets, names)
        return names

    # -- serialisation -------------------------------------------------------

    def to_spj(self) -> Dict[str, Any]:
        return {
            "root": self._root_node(),
            "animations": [],
            "selected_theme": "",
            "info": self.board.info(self.name),
        }

    def dumps(self) -> str:
        return json.dumps(self.to_spj(), indent=1)

    def _root_node(self) -> Dict[str, Any]:
        return {
            "guid": spj.new_guid(),
            "deepid": 0,
            "children": [self._screen_node(s) for s in self.screens],
            "locked": False,
            "properties": [
                {
                    "nid": spj.new_nid(),
                    "strtype": "STARTEVENTS/Name",
                    "strval": "___initial_actions0",
                    "InheritedType": spj.IT_STRING,
                }
            ],
            "saved_objtypeKey": "STARTEVENTS",
        }

    def _screen_node(self, s: Screen) -> Dict[str, Any]:
        props = spj.object_base_props(name=s.name, is_screen=True)
        props += [
            spj.p_header("SCREEN/Screen"),
            spj.p_bool("SCREEN/Temporary", False),
            spj.p_bool("SCREEN/Don't export screen", False),
            spj.p_style("SCREEN/Style_main", "lv.PART.MAIN",
                        "lv.PART.MAIN, Rectangle, Pad, Text", []),
            spj.p_style("SCREEN/Style_scrollbar", "lv.PART.SCROLLBAR",
                        "lv.PART.SCROLLBAR, Rectangle, Pad", []),
        ]
        props += s.events
        return {
            "guid": s.guid,
            "deepid": spj.new_deepid(),
            "children": [self._widget_node(w) for w in s.widgets],
            "isPage": True,
            "editor_posx": 1000,
            "editor_posy": -1000,
            "locked": False,
            "properties": props,
            "saved_objtypeKey": "SCREEN",
        }

    def _widget_node(self, w: Widget) -> Dict[str, Any]:
        spec = w.spec
        width = w.w or spec.default_w
        height = w.h or spec.default_h
        props = spj.object_base_props(
            name=w.name,
            is_screen=False,
            x=w.x,
            y=w.y,
            w=width,
            h=height,
            align=w.align,
            hidden=w.hidden,
            clickable=spec.clickable if w.clickable is None else w.clickable,
            checkable=spec.checkable if w.checkable is None else w.checkable,
            disabled=w.disabled,
        )
        props += widgets.widget_value_props(spec, w.value)
        props += widgets.style_records(spec, spec.key, w.styles)
        props += w.events

        node: Dict[str, Any] = {
            "guid": w.guid,
            "deepid": spj.new_deepid(),
            "locked": False,
            "properties": props,
            "saved_objtypeKey": spec.key,
        }
        if spec.container:
            node["children"] = [self._widget_node(c) for c in w.children]
        return node


def _find(ws: List[Widget], name: str) -> Optional[Widget]:
    for w in ws:
        if w.name == name:
            return w
        hit = _find(w.children, name)
        if hit is not None:
            return hit
    return None


def _collect(ws: List[Widget], out: List[str]) -> None:
    for w in ws:
        out.append(w.name)
        _collect(w.children, out)

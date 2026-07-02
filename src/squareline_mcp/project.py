"""
In-memory UI model and ``.spj`` assembler.

The model is intentionally small and JSON-friendly so the MCP server can mutate
it across tool calls and serialise it to a SquareLine project on demand.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from . import assets, spj, styles, widgets
from .board import CROWPANEL_5, Board

# part -> state -> {friendly_style_key: value}
PartStyles = Dict[str, Dict[str, Dict[str, Any]]]


# --- raw property-list helpers (used when editing loaded nodes in place) ------

def find_prop(props: List[Dict[str, Any]], strtype: str) -> Optional[Dict[str, Any]]:
    for p in props:
        if p.get("strtype") == strtype:
            return p
    return None


def prop_value(props: List[Dict[str, Any]], strtype: str) -> Any:
    p = find_prop(props, strtype)
    if p is None:
        return None
    for k in ("strval", "integer", "intarray"):
        if k in p:
            return p[k]
    return None


def set_prop(props: List[Dict[str, Any]], strtype: str, it: int, value: Any) -> None:
    """Update an existing property record in place, or append a new one."""
    rec = spj.p_value(strtype, it, value)
    existing = find_prop(props, strtype)
    if existing is None:
        props.append(rec)
        return
    # overwrite value keys on the existing record, keep its nid
    for k in ("strval", "integer", "intarray"):
        existing.pop(k, None)
    for k in ("strval", "integer", "intarray"):
        if k in rec:
            existing[k] = rec[k]
    existing["InheritedType"] = it


@dataclass
class Widget:
    type_key: str
    name: str
    x: int = 0
    y: int = 0
    w: int = 0
    h: int = 0
    align: str = "TOP_LEFT"
    hidden: bool = False
    clickable: Optional[bool] = None
    checkable: Optional[bool] = None
    disabled: bool = False
    config: Dict[str, Any] = field(default_factory=dict)   # suffix -> value
    styles: PartStyles = field(default_factory=dict)        # part -> state -> kv
    flags: Dict[str, Any] = field(default_factory=dict)     # OBJECT/* suffix -> value
    layout: Optional[Dict[str, Any]] = None                 # flex/grid layout config
    events: List[Dict[str, Any]] = field(default_factory=list)
    children: List["Widget"] = field(default_factory=list)
    guid: str = field(default_factory=spj.new_guid)
    # Loaded widgets carry their original node; edits patch it in place so any
    # property/widget type we don't model semantically survives round-trips.
    node: Optional[Dict[str, Any]] = None
    raw_key: Optional[str] = None      # objtypeKey when it's outside our catalogue

    @property
    def spec(self) -> Optional[widgets.WidgetSpec]:
        return widgets.WIDGETS.get(self.type_key)

    @property
    def objkey(self) -> str:
        if self.raw_key:
            return self.raw_key
        sp = self.spec
        return sp.key if sp else self.type_key

    @property
    def is_container(self) -> bool:
        if self.node is not None:
            return "children" in self.node
        sp = self.spec
        return bool(sp and sp.container)

    @property
    def value_field(self) -> Optional[str]:
        sp = self.spec
        return sp.value_field if sp else None

    def _props(self) -> Optional[List[Dict[str, Any]]]:
        return self.node["properties"] if self.node is not None else None

    def rename(self, new: str) -> None:
        self.name = new
        if self._props() is not None:
            set_prop(self._props(), "OBJECT/Name", spj.IT_STRING, new)

    def set_geometry(self, x=None, y=None, w=None, h=None, align=None) -> None:
        if x is not None:
            self.x = x
        if y is not None:
            self.y = y
        if w is not None:
            self.w = w
        if h is not None:
            self.h = h
        if align is not None:
            self.align = align
        props = self._props()
        if props is not None:
            set_prop(props, "OBJECT/Position", spj.IT_INTARRAY, [self.x, self.y])
            set_prop(props, "OBJECT/Size", spj.IT_INTARRAY, [self.w, self.h])
            if align is not None:
                set_prop(props, "OBJECT/Align", spj.IT_ENUM, self.align)

    def set_state_flag(self, suffix: str, value: bool) -> None:
        setattr_map = {"Hidden": "hidden", "Clickable": "clickable",
                       "Checkable": "checkable", "Disabled": "disabled"}
        if suffix in setattr_map:
            setattr(self, setattr_map[suffix], value)
        props = self._props()
        if props is not None:
            set_prop(props, "OBJECT/%s" % suffix, spj.IT_BOOL, value)
        else:
            self.flags[suffix] = value

    def set_value(self, value: Any) -> None:
        vf = self.value_field
        if vf is None:
            raise ValueError("Widget type %r has no editable value" % self.objkey)
        self.config[vf] = value
        props = self._props()
        if props is not None:
            it = next((i for s, i, _ in self.spec.config if s == vf), spj.IT_STRING)
            set_prop(props, "%s/%s" % (self.objkey, vf), it, value)

    def set_object_flag(self, suffix: str, value: Any) -> None:
        """Set any OBJECT/* flag or enum (bool or string), dual-mode."""
        sync = {"Hidden": "hidden", "Clickable": "clickable",
                "Checkable": "checkable", "Disabled": "disabled"}
        if suffix in sync and isinstance(value, bool):
            setattr(self, sync[suffix], value)
        props = self._props()
        if props is not None:
            it = spj.IT_BOOL if isinstance(value, bool) else spj.IT_ENUM
            set_prop(props, "OBJECT/%s" % suffix, it, value)
        else:
            self.flags[suffix] = value

    def set_config(self, suffix: str, value: Any) -> None:
        self.config[suffix] = value
        props = self._props()
        if props is not None:
            cfg = self.spec.config if self.spec else []
            it = next((i for s, i, _ in cfg if s == suffix), spj.IT_STRING)
            set_prop(props, "%s/%s" % (self.objkey, suffix), it, value)

    def set_style(self, key: str, value: Any, part: str = "main", state: str = "DEFAULT") -> None:
        self.styles.setdefault(part, {}).setdefault(state, {})[key] = value
        if self.node is not None:
            _patch_style_on_node(self, key, value, part, state)

    def add_event(self, record: Dict[str, Any]) -> None:
        if self._props() is not None:
            self._props().append(record)
        else:
            self.events.append(record)


@dataclass
class Screen:
    name: str
    widgets: List[Widget] = field(default_factory=list)
    styles: PartStyles = field(default_factory=dict)
    events: List[Dict[str, Any]] = field(default_factory=list)
    guid: str = field(default_factory=spj.new_guid)
    node: Optional[Dict[str, Any]] = None

    def rename(self, new: str) -> None:
        self.name = new
        if self.node is not None:
            set_prop(self.node["properties"], "OBJECT/Name", spj.IT_STRING, new)


@dataclass
class Project:
    name: str
    board: Board = field(default_factory=lambda: CROWPANEL_5)
    screens: List[Screen] = field(default_factory=list)
    assets: assets.AssetManager = field(default_factory=assets.AssetManager)
    # Preserved verbatim when a project is loaded, so round-trips are lossless.
    raw_info: Optional[Dict[str, Any]] = None
    root_guid: Optional[str] = None
    root_props: Optional[List[Dict[str, Any]]] = None
    animations: List[Dict[str, Any]] = field(default_factory=list)
    selected_theme: str = ""

    # -- fonts / assets ------------------------------------------------------

    def used_fonts(self) -> List[str]:
        """Every distinct text_font referenced anywhere in the project."""
        found: List[str] = []

        def scan(ps: PartStyles) -> None:
            for by_state in ps.values():
                for kv in by_state.values():
                    f = kv.get("text_font")
                    if f and f not in found:
                        found.append(f)

        def walk(ws: List[Widget]) -> None:
            for w in ws:
                scan(w.styles)
                if w.node is not None:
                    scan_fonts_in_node(w.node, found)
                walk(w.children)

        for s in self.screens:
            scan(s.styles)
            if s.node is not None:
                scan_fonts_in_node(s.node, found)
            walk(s.widgets)
        return found

    def font_requirements(self) -> List[str]:
        """lv_conf.h defines needed for the built-in fonts in use."""
        reqs = []
        for f in self.used_fonts():
            sym = assets.font_lv_conf_symbol(f)
            if sym:
                reqs.append("#define %s 1" % sym)
        return reqs

    def custom_fonts(self) -> List[str]:
        """Referenced fonts that are NOT built-in (must be added in SquareLine)."""
        return [f for f in self.used_fonts() if not assets.is_builtin_font(f)]

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

    def guid_of(self, name: str) -> str:
        """Resolve a screen or widget name to its guid (for event targets)."""
        for s in self.screens:
            if s.name == name:
                return s.guid
        return self.find_widget(name).guid

    def all_names(self) -> List[str]:
        names = [s.name for s in self.screens]
        for s in self.screens:
            _collect(s.widgets, names)
        return names

    # -- structural edits ----------------------------------------------------

    def _parent_list(self, name: str) -> Optional[List[Widget]]:
        """The list (screen.widgets or container.children) that holds `name`."""
        for s in self.screens:
            lst = _owner_list(s.widgets, name)
            if lst is not None:
                return lst
        return None

    def pop_widget(self, name: str) -> Widget:
        lst = self._parent_list(name)
        if lst is None:
            raise KeyError("No widget named %r" % name)
        w = next(x for x in lst if x.name == name)
        lst.remove(w)
        return w

    def move_widget(self, name: str, parent: str = "", screen: str = "",
                    index: Optional[int] = None) -> None:
        """Re-parent / reorder a widget. Give a container `parent`, or a `screen`."""
        if parent:
            container = self.find_widget(parent)
            if not container.is_container:
                raise ValueError("%r is not a container" % parent)
            if container.name == name:
                raise ValueError("A widget cannot be its own parent")
            target = container.children
        else:
            target = self.screen(screen or self.screens[0].name).widgets
        w = self.pop_widget(name)
        if index is None or index < 0 or index > len(target):
            target.append(w)
        else:
            target.insert(index, w)

    # -- serialisation -------------------------------------------------------

    def to_spj(self) -> Dict[str, Any]:
        return {
            "root": self._root_node(),
            "animations": self.animations,
            "selected_theme": self.selected_theme,
            "info": self._info(),
        }

    def dumps(self) -> str:
        return json.dumps(self.to_spj(), indent=1)

    def _info(self) -> Dict[str, Any]:
        if self.raw_info is not None:
            info = dict(self.raw_info)
            info["Name"] = self.name
            info["name"] = "%s.spj" % self.name
            info["width"], info["height"] = self.board.width, self.board.height
            return info
        return self.board.info(self.name)

    def _root_node(self) -> Dict[str, Any]:
        return {
            "guid": self.root_guid or spj.new_guid(),
            "deepid": 0,
            "children": [self._screen_node(s) for s in self.screens],
            "locked": False,
            "properties": self.root_props if self.root_props is not None else [
                spj.p_string("STARTEVENTS/Name", "___initial_actions0"),
            ],
            "saved_objtypeKey": "STARTEVENTS",
        }

    def _screen_style(self, s: Screen, suffix: str, part: str) -> Dict[str, Any]:
        by_state = s.styles.get(part, {})
        states = {state: styles.build_children(kv) for state, kv in by_state.items()}
        summary = ("lv.PART.MAIN, Rectangle, Pad, Text" if part == "main"
                   else "lv.PART.SCROLLBAR, Rectangle, Pad")
        return spj.p_style("SCREEN/%s" % suffix, styles.PARTS[part], summary, states)

    def _screen_node(self, s: Screen) -> Dict[str, Any]:
        if s.node is not None:                       # loaded screen: reuse node
            s.node["children"] = [self._widget_node(w) for w in s.widgets]
            return s.node
        props = spj.object_base_props(name=s.name, is_screen=True)
        props += [
            spj.p_header("SCREEN/Screen"),
            spj.p_bool("SCREEN/Temporary", False),
            spj.p_bool("SCREEN/Don't export screen", False),
            self._screen_style(s, "Style_main", "main"),
            self._screen_style(s, "Style_scrollbar", "scrollbar"),
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
        if w.node is not None:                       # loaded widget: reuse node
            if "children" in w.node:
                w.node["children"] = [self._widget_node(c) for c in w.children]
            return w.node
        spec = w.spec
        width = w.w or spec.default_w
        height = w.h or spec.default_h
        props = spj.object_base_props(
            name=w.name, is_screen=False, x=w.x, y=w.y, w=width, h=height, align=w.align,
            hidden=w.hidden,
            clickable=spec.clickable if w.clickable is None else w.clickable,
            checkable=spec.checkable if w.checkable is None else w.checkable,
            disabled=w.disabled, layout=w.layout, flags=w.flags,
        )
        props += widgets.config_props(spec, w.config)
        props += widgets.style_records(spec, w.styles)
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


def _patch_style_on_node(w: Widget, key: str, value: Any, part: str, state: str) -> None:
    """Insert/replace a style record inside a loaded widget's raw node."""
    props = w.node["properties"]
    lvpart = styles.PARTS.get(part, "lv.PART.MAIN")
    rec = next((p for p in props if p.get("InheritedType") == spj.IT_STYLE
                and p.get("part") == lvpart), None)
    if rec is None:
        suffix = "Style_main" if part == "main" else "Style_%s" % part
        rec = spj.p_style("%s/%s" % (w.objkey, suffix), lvpart, lvpart, {})
        props.append(rec)
    childs = rec.setdefault("childs", [])
    st = next((c for c in childs if c.get("strtype") == "_style/StyleState"
               and c.get("strval") == state), None)
    if st is None:
        st = {"nid": spj.new_nid(), "strtype": "_style/StyleState", "strval": state,
              "childs": [], "InheritedType": spj.IT_HEADER}
        childs.append(st)
    child = styles.build_record(key, value)
    stc = st.setdefault("childs", [])
    for i, ex in enumerate(stc):
        if ex.get("strtype") == child["strtype"]:
            stc[i] = child
            break
    else:
        stc.append(child)


def scan_fonts_in_node(node: Dict[str, Any], out: List[str]) -> None:
    """Collect _style/Text_Font values anywhere inside a raw node."""
    if isinstance(node, dict):
        if node.get("strtype") == "_style/Text_Font":
            v = node.get("strval")
            if v and v not in out:
                out.append(v)
        for v in node.values():
            scan_fonts_in_node(v, out)
    elif isinstance(node, list):
        for v in node:
            scan_fonts_in_node(v, out)


def _find(ws: List[Widget], name: str) -> Optional[Widget]:
    for w in ws:
        if w.name == name:
            return w
        hit = _find(w.children, name)
        if hit is not None:
            return hit
    return None


def _owner_list(ws: List[Widget], name: str) -> Optional[List[Widget]]:
    """Return the list that directly contains a widget named `name`."""
    for w in ws:
        if w.name == name:
            return ws
        hit = _owner_list(w.children, name)
        if hit is not None:
            return hit
    return None


def _collect(ws: List[Widget], out: List[str]) -> None:
    for w in ws:
        out.append(w.name)
        _collect(w.children, out)

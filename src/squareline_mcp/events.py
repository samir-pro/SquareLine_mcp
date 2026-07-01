"""
Event & action support.

Loads the verbatim SquareLine action templates bundled in ``data/actions.json``
(extracted from genuine 1.4.x exports) and builds ``_event/EventHandler``
records. GUID-reference parameters (Target/Object/Screen_to/Keyboard/TextArea…)
are given as widget/screen *names* and resolved to guids by the caller.
"""

from __future__ import annotations

import json
import os
from typing import Any, Callable, Dict, List

from . import spj

_DATA = os.path.join(os.path.dirname(__file__), "data", "actions.json")
with open(_DATA, encoding="utf-8") as _fh:
    ACTIONS: Dict[str, Dict[str, Any]] = json.load(_fh)

# Fixed template fields the user never sets directly.
_FIXED = {"Name", "Call", "CallC", "FunctionName"}

# Event triggers (Trigger dropdown) — friendly/uppercase both accepted.
TRIGGERS = [
    "PRESSED", "CLICKED", "SHORT_CLICKED", "LONG_PRESSED", "LONG_PRESSED_REPEAT",
    "RELEASED", "PRESS_LOST", "FOCUSED", "DEFOCUSED", "VALUE_CHANGED", "READY",
    "CANCEL", "CHECKED", "UNCHECKED", "GESTURE", "KEY", "EDITED", "INSERT",
    "SCREEN_LOADED", "SCREEN_UNLOADED", "SCREEN_LOAD_START", "SCREEN_UNLOAD_START",
]


def resolve_action(name: str) -> str:
    """Accept exact action names or a few friendly aliases -> canonical name."""
    n = (name or "").strip().upper().replace("-", " ")
    aliases = {
        "SET TEXT": "LABEL_PROPERTY",
        "SET LABEL": "LABEL_PROPERTY",
        "SET PROPERTY": "BASIC_PROPERTY",
        "SET FLAG": "MODIFY FLAG",
        "SET STATE": "MODIFY STATE",
        "NEXT SCREEN": "CHANGE SCREEN",
    }
    n = aliases.get(n, n)
    if n not in ACTIONS:
        raise ValueError("Unknown action %r. Known: %s" % (name, ", ".join(sorted(ACTIONS))))
    return n


def resolve_trigger(trigger: str) -> str:
    t = (trigger or "CLICKED").strip().upper().replace(" ", "_")
    return t


def build_action(name: str, params: Dict[str, Any],
                 resolver: Callable[[str], str]) -> Dict[str, Any]:
    """Build one ``_event/action`` record from its template + user params.

    ``params`` keys are the action's parameter suffixes (Target, Property,
    Value, Screen_to, Fade_mode, …). GUID-ref params are resolved via ``resolver``.
    """
    name = resolve_action(name)
    template = ACTIONS[name]["template"]
    childs: List[Dict[str, Any]] = []
    for entry in template:
        suffix, it = entry["suffix"], entry["it"]
        strtype = "%s/%s" % (name, suffix)
        if suffix in _FIXED:
            # keep verbatim template value (action name, C call strings, etc.)
            rec = {"nid": spj.new_nid(), "strtype": strtype, "InheritedType": it}
            if entry.get("default") is not None:
                rec[entry["key"]] = entry["default"]
            childs.append(rec)
            continue
        provided = suffix in params
        value = params[suffix] if provided else entry.get("default")
        if it == spj.IT_GUIDREF:
            # Sample guids from the template are meaningless here; only keep
            # user-provided targets (resolved from a name to a real guid).
            value = resolver(str(value)) if (provided and value) else ""
        childs.append(spj.p_value(strtype, it, value))
    return {
        "nid": spj.new_nid(),
        "strtype": "_event/action",
        "strval": name,
        "childs": childs,
        "InheritedType": spj.IT_STRING,
    }


def build_event(trigger: str, action: str, params: Dict[str, Any],
                resolver: Callable[[str], str]) -> Dict[str, Any]:
    """A full ``_event/EventHandler`` record wrapping a single action."""
    return {
        "disabled": False,
        "nid": spj.new_nid(),
        "strtype": "_event/EventHandler",
        "strval": resolve_trigger(trigger),
        "childs": [
            spj.p_string("_event/name", "Event1"),
            spj.p_string("_event/condition_C", ""),
            spj.p_string("_event/condition_P", ""),
            build_action(action, params, resolver),
        ],
        "InheritedType": spj.IT_EVENT,
    }


def action_params(name: str) -> List[str]:
    return list(ACTIONS[resolve_action(name)].get("params", []))

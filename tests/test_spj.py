"""
Tests for the .spj generator. These assert the structural invariants that were
reverse-engineered from a genuine SquareLine 1.4.2 / LVGL 8.3.11 export.
"""

import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from squareline_mcp import Project, Screen, Widget  # noqa: E402
from squareline_mcp import widgets, spj  # noqa: E402


def _strtypes(node):
    return [p.get("strtype") for p in node["properties"]]


def build_project():
    p = Project(name="Demo")
    s = Screen(name="MainScreen")
    p.screens.append(s)
    s.widgets.append(Widget(type_key="label", name="Title", x=10, y=10,
                            value="Hi", styles={"text_color": [255, 255, 255, 255]}))
    panel = Widget(type_key="panel", name="Card", x=0, y=40, w=200, h=100)
    panel.children.append(Widget(type_key="button", name="Btn"))
    s.widgets.append(panel)
    return p


def test_top_level_shape():
    d = build_project().to_spj()
    assert set(d.keys()) == {"root", "animations", "selected_theme", "info"}
    assert d["root"]["saved_objtypeKey"] == "STARTEVENTS"
    assert d["root"]["deepid"] == 0


def test_info_block_matches_crowpanel():
    d = build_project().to_spj()
    info = d["info"]
    assert info["lvgl_version"] == "8.3.11"
    assert info["editor_version"] == "1.4.2"
    assert (info["width"], info["height"]) == (800, 480)
    assert info["BitDepth"] == 16
    assert info["flat_export"] is True
    assert info["name"] == "Demo.spj"


def test_screen_node():
    d = build_project().to_spj()
    scr = d["root"]["children"][0]
    assert scr["saved_objtypeKey"] == "SCREEN"
    assert scr["isPage"] is True
    st = _strtypes(scr)
    assert "OBJECT/Name" in st
    assert "SCREEN/Style_main" in st
    assert "SCREEN/Style_scrollbar" in st
    # screens have no per-widget geometry props
    assert "OBJECT/Position" not in st
    assert "OBJECT/Size" not in st


def test_label_matches_reference_object_base():
    """The verified LABEL property set from the reference export."""
    p = Project(name="X")
    s = Screen(name="S")
    p.screens.append(s)
    s.widgets.append(Widget(type_key="label", name="Desc1", value="Desc1"))
    lbl = p.to_spj()["root"]["children"][0]["children"][0]
    st = _strtypes(lbl)
    # geometry + widget value + style all present
    for expected in ["OBJECT/Name", "OBJECT/Position", "OBJECT/Size", "OBJECT/Align",
                     "LABEL/Text", "LABEL/Long_mode", "LABEL/Recolor", "LABEL/Style_main"]:
        assert expected in st, expected
    assert len(st) == 45  # exact count from the genuine export


def test_property_value_encoding():
    p = Project(name="X")
    s = Screen(name="S")
    p.screens.append(s)
    s.widgets.append(Widget(type_key="label", name="L", x=5, y=7, w=80, h=20, value="hey"))
    lbl = p.to_spj()["root"]["children"][0]["children"][0]
    by = {pr["strtype"]: pr for pr in lbl["properties"]}
    assert by["OBJECT/Position"]["intarray"] == [5, 7]
    assert by["OBJECT/Position"]["InheritedType"] == spj.IT_INTARRAY
    assert by["OBJECT/Size"]["intarray"] == [80, 20]
    assert by["LABEL/Text"]["strval"] == "hey"
    assert by["LABEL/Text"]["InheritedType"] == spj.IT_STRING
    assert by["OBJECT/Hidden"]["strval"] == "False"
    assert by["OBJECT/Hidden"]["InheritedType"] == spj.IT_BOOL


def test_container_nesting_and_leaf_has_no_children():
    d = build_project().to_spj()
    scr = d["root"]["children"][0]
    card = [c for c in scr["children"] if c["saved_objtypeKey"] == "PANEL"][0]
    assert "children" in card
    assert card["children"][0]["saved_objtypeKey"] == "BUTTON"
    label = [c for c in scr["children"] if c["saved_objtypeKey"] == "LABEL"][0]
    assert "children" not in label  # leaf widgets omit the children key


def test_change_screen_event():
    p = Project(name="X")
    a = Screen(name="A")
    b = Screen(name="B")
    p.screens += [a, b]
    btn = Widget(type_key="button", name="Go")
    a.widgets.append(btn)
    btn.events.append(spj.change_screen_event("CLICKED", b.guid, "B"))
    node = p.to_spj()["root"]["children"][0]["children"][0]
    ev = [pr for pr in node["properties"] if pr.get("strtype") == "_event/EventHandler"][0]
    assert ev["strval"] == "CLICKED"
    blob = json.dumps(ev)
    assert "CHANGE SCREEN" in blob and b.guid in blob


def test_widget_aliases():
    assert widgets.resolve("btn") == "button"
    assert widgets.resolve("Text") == "label"
    assert widgets.resolve("toggle") == "switch"
    assert widgets.resolve("progress bar") == "bar"


def test_roundtrip_json():
    d = build_project().to_spj()
    assert json.loads(json.dumps(d)) == d


if __name__ == "__main__":
    import traceback
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    failed = 0
    for fn in fns:
        try:
            fn()
            print("PASS", fn.__name__)
        except Exception:
            failed += 1
            print("FAIL", fn.__name__)
            traceback.print_exc()
    sys.exit(1 if failed else 0)

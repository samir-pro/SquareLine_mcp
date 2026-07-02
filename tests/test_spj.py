"""
Tests for the .spj generator. These assert the structural invariants that were
reverse-engineered from a genuine SquareLine 1.4.2 / LVGL 8.3.11 export.
"""

import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from squareline_mcp import Project, Screen, Widget  # noqa: E402
from squareline_mcp import widgets, spj, styles, events  # noqa: E402


def _strtypes(node):
    return [p.get("strtype") for p in node["properties"]]


def build_project():
    p = Project(name="Demo")
    s = Screen(name="MainScreen")
    p.screens.append(s)
    title = Widget(type_key="label", name="Title", x=10, y=10)
    title.set_value("Hi")
    title.set_style("text_color", [255, 255, 255, 255])
    s.widgets.append(title)
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


def test_label_object_base_present():
    p = Project(name="X")
    s = Screen(name="S")
    p.screens.append(s)
    lbl_w = Widget(type_key="label", name="Desc1")
    lbl_w.set_value("Desc1")
    s.widgets.append(lbl_w)
    lbl = p.to_spj()["root"]["children"][0]["children"][0]
    st = _strtypes(lbl)
    for expected in ["OBJECT/Name", "OBJECT/Position", "OBJECT/Size", "OBJECT/Align",
                     "LABEL/Text", "LABEL/Long_mode", "LABEL/Recolor", "LABEL/Style_main"]:
        assert expected in st, expected


def test_property_value_encoding():
    p = Project(name="X")
    s = Screen(name="S")
    p.screens.append(s)
    lw = Widget(type_key="label", name="L", x=5, y=7, w=80, h=20)
    lw.set_value("hey")
    s.widgets.append(lw)
    lbl = p.to_spj()["root"]["children"][0]["children"][0]
    by = {pr["strtype"]: pr for pr in lbl["properties"]}
    assert by["OBJECT/Position"]["intarray"] == [5, 7]
    assert by["OBJECT/Position"]["InheritedType"] == spj.IT_INTARRAY
    assert by["OBJECT/Size"]["intarray"] == [80, 20]
    assert by["LABEL/Text"]["strval"] == "hey"
    assert by["LABEL/Text"]["InheritedType"] == spj.IT_STRING
    assert by["OBJECT/Hidden"]["strval"] == "False"
    assert by["OBJECT/Hidden"]["InheritedType"] == spj.IT_BOOL


def test_all_widget_types_serialise():
    """Every catalogued widget must serialise to a valid node with a style_main."""
    for key in widgets.WIDGETS:
        p = Project(name="W")
        s = Screen(name="S")
        p.screens.append(s)
        s.widgets.append(Widget(type_key=key, name="w_" + key))
        node = p.to_spj()["root"]["children"][0]["children"][0]
        assert node["saved_objtypeKey"] == widgets.WIDGETS[key].key
        sts = _strtypes(node)
        assert any(x.endswith("/Style_main") or x.endswith("/Style_bg") for x in sts), key


def test_multi_state_style():
    p = Project(name="X")
    s = Screen(name="S")
    p.screens.append(s)
    w = Widget(type_key="button", name="B")
    w.set_style("bg_color", "#112233", part="main", state="DEFAULT")
    w.set_style("bg_color", "#445566", part="main", state="PRESSED")
    s.widgets.append(w)
    node = p.to_spj()["root"]["children"][0]["children"][0]
    sm = [pr for pr in node["properties"] if pr["strtype"] == "BUTTON/Style_main"][0]
    state_names = [c["strval"] for c in sm["childs"]]
    assert "DEFAULT" in state_names and "PRESSED" in state_names


def test_all_actions_build():
    """Every bundled action builds a structurally valid event record."""
    p = Project(name="X")
    s = Screen(name="Main")
    s2 = Screen(name="Other")
    p.screens += [s, s2]
    btn = Widget(type_key="button", name="B")
    s.widgets.append(btn)
    for action in events.ACTIONS:
        ev = events.build_event("CLICKED", action, {}, p.guid_of)
        assert ev["strtype"] == "_event/EventHandler"
        act = ev["childs"][-1]
        assert act["strtype"] == "_event/action"
        assert act["strval"] == action
        # Call/CallC templates preserved verbatim
        calls = [c for c in act["childs"] if c["strtype"].endswith("/CallC")]
        assert calls, action


def test_flags_and_layout():
    p = Project(name="X")
    s = Screen(name="S")
    p.screens.append(s)
    w = Widget(type_key="panel", name="P")
    w.flags["Scrollable"] = False
    w.layout = {"type": "flex", "flow": "COLUMN", "main_align": "CENTER"}
    s.widgets.append(w)
    node = p.to_spj()["root"]["children"][0]["children"][0]
    by = {pr["strtype"]: pr for pr in node["properties"]}
    assert by["OBJECT/Scrollable"]["strval"] == "False"
    lt = by["OBJECT/Layout_type"]
    assert lt["strval"] == "Flex_layout" and lt["Flow"] == 1 and lt["MainAlignment"] == 2


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
    btn.events.append(events.build_event("CLICKED", "CHANGE SCREEN",
                                         {"Screen_to": "B"}, p.guid_of))
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


def test_empty_image_is_dash_sentinel():
    p = Project(name="X")
    s = Screen(name="S")
    p.screens.append(s)
    s.widgets.append(Widget(type_key="image", name="Img"))   # no source
    node = p.to_spj()["root"]["children"][0]["children"][0]
    asset = [pr for pr in node["properties"] if pr["strtype"] == "IMAGE/Asset"][0]
    assert asset["strval"] == "-"


def test_font_requirements_and_custom():
    p = Project(name="X")
    s = Screen(name="S")
    p.screens.append(s)
    a = Widget(type_key="label", name="A")
    a.set_style("text_font", "montserrat_28")
    b = Widget(type_key="label", name="B")
    b.set_style("text_font", "MyCustomFont")
    s.widgets += [a, b]
    assert "montserrat_28" in p.used_fonts()
    assert "#define LV_FONT_MONTSERRAT_28 1" in p.font_requirements()
    assert p.custom_fonts() == ["MyCustomFont"]


def test_image_asset_register_and_ref():
    p = Project(name="X")
    ref = p.assets.resolve_image("/some/dir/logo.png")
    assert ref == "assets/logo.png"
    # already-registered ref passes through; '-'/'' -> none sentinel
    assert p.assets.resolve_image(ref) == "assets/logo.png"
    assert p.assets.resolve_image("") == "-"
    assert p.assets.resolve_image("-") == "-"


def test_image_export_copies_file(tmp_path=None):
    import tempfile
    p = Project(name="X")
    s = Screen(name="S")
    p.screens.append(s)
    d = tempfile.mkdtemp()
    src = os.path.join(d, "pic.png")
    with open(src, "wb") as fh:
        fh.write(b"\x89PNG\r\n\x1a\n")  # tiny fake png
    ref = p.assets.resolve_image(src)
    assert ref == "assets/pic.png"
    notes = p.assets.export_assets(d)
    assert os.path.isfile(os.path.join(d, "assets", "pic.png"))
    assert any("copied" in n for n in notes)


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

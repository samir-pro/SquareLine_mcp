"""
Build a small two-screen CrowPanel 5" UI *without* the MCP layer, using the
model directly. Run:  python examples/demo_dashboard.py  -> writes CrowDemo.spj

Then open CrowDemo.spj in SquareLine Studio (File > Open Project) and export.
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from squareline_mcp import Project, Screen, Widget, events


def _label(name, x, y, w, h, text, font=None, color=None, align="TOP_LEFT"):
    lbl = Widget(type_key="label", name=name, x=x, y=y, w=w, h=h, align=align)
    lbl.set_value(text)
    if font:
        lbl.set_style("text_font", font)
    if color:
        lbl.set_style("text_color", color)
    return lbl


def main():
    p = Project(name="CrowDemo")  # defaults to CrowPanel 5.0" 800x480 / LVGL 8.3.11

    home = Screen(name="HomeScreen")
    settings = Screen(name="SettingsScreen")
    p.screens += [home, settings]

    # --- Home screen ---
    home.widgets.append(_label("HomeTitle", 0, 24, 800, 48, "CrowPanel Dashboard",
                               font="montserrat_28", color=[255, 255, 255, 255], align="TOP_MID"))

    card = Widget(type_key="panel", name="StatusCard", x=100, y=110, w=600, h=260)
    card.set_style("bg_color", "#1E1E3C")
    card.set_style("radius", 16)
    card.set_style("border_color", "#4040FF", part="main", state="PRESSED")  # multi-state demo
    card.children.append(_label("TempLabel", 30, 30, 300, 40, "Temp: 22.5°C", font="montserrat_20"))
    bar = Widget(type_key="bar", name="TempBar", x=30, y=90, w=520)
    bar.set_value(45)
    card.children.append(bar)
    gearbtn = Widget(type_key="button", name="ToSettings", x=200, y=170, w=200, h=60)
    gearbtn.children.append(_label("GearLbl", 0, 0, 120, 32, "Settings", align="CENTER"))
    card.children.append(gearbtn)
    home.widgets.append(card)

    # --- Settings screen ---
    settings.widgets.append(_label("SetTitle", 0, 24, 800, 48, "Settings",
                                   font="montserrat_28", align="TOP_MID"))
    settings.widgets.append(Widget(type_key="switch", name="WifiSwitch", x=120, y=140))
    bright = Widget(type_key="slider", name="Brightness", x=120, y=220, w=400)
    bright.set_value(70)
    settings.widgets.append(bright)
    back = Widget(type_key="button", name="BackBtn", x=120, y=320, w=160, h=56)
    back.children.append(_label("BackLbl", 0, 0, 120, 32, "Back", align="CENTER"))
    settings.widgets.append(back)

    # --- navigation (Change Screen events) ---
    gearbtn.events.append(events.build_event("CLICKED", "CHANGE SCREEN",
                          {"Screen_to": "SettingsScreen"}, p.guid_of))
    back.events.append(events.build_event("CLICKED", "CHANGE SCREEN",
                       {"Screen_to": "HomeScreen"}, p.guid_of))

    out = os.path.abspath("CrowDemo.spj")
    with open(out, "w", encoding="utf-8") as fh:
        fh.write(p.dumps())
    print("Wrote", out)


if __name__ == "__main__":
    main()

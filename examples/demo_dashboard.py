"""
Build a small two-screen CrowPanel 5" UI *without* the MCP layer, using the
model directly. Run:  python examples/demo_dashboard.py  -> writes CrowDemo.spj

Then open CrowDemo.spj in SquareLine Studio (File > Open Project) and export.
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from squareline_mcp import Project, Screen, Widget
from squareline_mcp import spj


def main():
    p = Project(name="CrowDemo")  # defaults to CrowPanel 5.0" 800x480 / LVGL 8.3.11

    home = Screen(name="HomeScreen")
    settings = Screen(name="SettingsScreen")
    p.screens += [home, settings]

    # --- Home screen ---
    home.widgets.append(Widget(
        type_key="label", name="HomeTitle", x=0, y=24, w=800, h=48,
        align="TOP_MID", value="CrowPanel Dashboard",
        styles={"text_color": [255, 255, 255, 255], "text_font": "montserrat_28"},
    ))

    card = Widget(type_key="panel", name="StatusCard", x=100, y=110, w=600, h=260,
                  styles={"bg_color": [30, 30, 60, 255], "radius": 16, "border_width": 0})
    card.children.append(Widget(type_key="label", name="TempLabel", x=30, y=30, w=300, h=40,
                                value="Temp: 22.5°C", styles={"text_font": "montserrat_20"}))
    card.children.append(Widget(type_key="bar", name="TempBar", x=30, y=90, w=520, value=45))
    gearbtn = Widget(type_key="button", name="ToSettings", x=200, y=170, w=200, h=60)
    gearbtn.children.append(Widget(type_key="label", name="GearLbl", align="CENTER", value="Settings"))
    card.children.append(gearbtn)
    home.widgets.append(card)

    # --- Settings screen ---
    settings.widgets.append(Widget(type_key="label", name="SetTitle", x=0, y=24, w=800, h=48,
                                   align="TOP_MID", value="Settings",
                                   styles={"text_font": "montserrat_28"}))
    settings.widgets.append(Widget(type_key="switch", name="WifiSwitch", x=120, y=140))
    settings.widgets.append(Widget(type_key="slider", name="Brightness", x=120, y=220, w=400, value=70))
    back = Widget(type_key="button", name="BackBtn", x=120, y=320, w=160, h=56)
    back.children.append(Widget(type_key="label", name="BackLbl", align="CENTER", value="Back"))
    settings.widgets.append(back)

    # --- navigation ---
    gearbtn.events.append(spj.change_screen_event("CLICKED", settings.guid, settings.name))
    back.events.append(spj.change_screen_event("CLICKED", home.guid, home.name))

    out = os.path.abspath("CrowDemo.spj")
    with open(out, "w", encoding="utf-8") as fh:
        fh.write(p.dumps())
    print("Wrote", out)


if __name__ == "__main__":
    main()

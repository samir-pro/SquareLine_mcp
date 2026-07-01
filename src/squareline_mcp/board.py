"""
Board presets and the SquareLine ``info`` (project settings) block.

The default target is the Elecrow CrowPanel 5.0" HMI (ESP32, 800x480), matched
to the exact toolchain the user builds with:

  * LVGL 8.3.11  (Elecrow CrowPanel-5.0-HMI Arduino library)
  * SquareLine Studio 1.4.2 project format
  * Arduino export, flat layout, 16-bit colour
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict


@dataclass
class Board:
    name: str
    width: int = 800
    height: int = 480
    board: str = "Arduino with TFT_eSPI"
    board_version: str = "v1.1.2"
    editor_version: str = "1.4.2"
    lvgl_version: str = "8.3.11"
    color_depth: int = 16
    rotation: int = 0
    flat_export: bool = True

    def info(self, project_name: str) -> Dict[str, Any]:
        """The ``info`` block written at the top level of a ``.spj`` file."""
        return {
            "name": "%s.spj" % project_name,
            "depth": 1,
            "width": self.width,
            "height": self.height,
            "rotation": self.rotation,
            "offset_x": 0,
            "offset_y": 0,
            "shape": "RECTANGLE",
            "multilang": "DISABLE",
            "description": "",
            "board": self.board,
            "board_version": self.board_version,
            "editor_version": self.editor_version,
            "image": "",
            "force_export_images": False,
            "flat_export": self.flat_export,
            "advanced_alpha": False,
            "pointfilter": False,
            "theme_simplified": False,
            "theme_dark": False,
            "theme_color1": 5,
            "theme_color2": 0,
            "uiExportFolderPath": "",
            "projectExportFolderPath": "",
            "backup_cnt": 0,
            "autosave_cnt": 0,
            "lvgl_version": self.lvgl_version,
            "callfuncsexport": "C_FILE",
            "imageexport": "SOURCE",
            "lvgl_include_path": "lvgl.h",
            "drive_stdio": "-",
            "drive_stdio_path": "",
            "drive_posix": "-",
            "drive_posix_path": "",
            "drive_win32": "-",
            "drive_win32_path": "",
            "drive_fatfs": "-",
            "drive_fatfs_path": "",
            "naming": "Name",
            "naming_force_lowercase": False,
            "BitDepth": self.color_depth,
            "Name": project_name,
        }


# The default preset used by the MCP server unless overridden.
CROWPANEL_5 = Board(name="CrowPanel 5.0\" HMI (ESP32, 800x480)")

# A couple of sibling CrowPanel resolutions for convenience.
PRESETS: Dict[str, Board] = {
    "crowpanel-5": CROWPANEL_5,
    "crowpanel-7": Board(name="CrowPanel 7.0\" HMI", width=800, height=480),
    "crowpanel-4.3": Board(name="CrowPanel 4.3\" HMI", width=480, height=272),
    "crowpanel-2.8": Board(name="CrowPanel 2.8\" HMI", width=320, height=240),
}

"""
Font and image-asset management.

SquareLine stores **no** asset registry inside the ``.spj`` — widgets simply
reference fonts by name (``montserrat_28``) and images by a relative path
(``assets/logo.png``; ``-`` means "none"). The actual PNG/font files live in the
project's ``assets/`` folder, which SquareLine scans.

So this module:

* validates/enumerates the built-in Montserrat fonts and reports the
  ``lv_conf.h`` defines each one needs (the thing that actually trips people up
  on the CrowPanel/Arduino side);
* tracks image assets and, on export, copies their source files into the
  project's ``assets/`` folder and yields the correct ``assets/<file>`` ref.

Custom (TTF) fonts can be *referenced* by name so the ``.spj`` matches, but their
definition is not stored in the project file — you must add them once in
SquareLine's Font Manager. We surface that clearly rather than pretend otherwise.
"""

from __future__ import annotations

import os
import shutil
from dataclasses import dataclass
from typing import Dict, List, Optional

# Built-in LVGL Montserrat sizes SquareLine ships (even sizes 8..48).
BUILTIN_FONT_SIZES = list(range(8, 49, 2))
BUILTIN_FONTS = ["montserrat_%d" % s for s in BUILTIN_FONT_SIZES]

NONE_IMAGE = "-"          # SquareLine's "no image" sentinel
ASSET_DIR = "assets"      # folder name SquareLine expects next to the .spj


def is_builtin_font(name: str) -> bool:
    return name in BUILTIN_FONTS


def font_lv_conf_symbol(name: str) -> Optional[str]:
    """The lv_conf.h define a built-in font needs, e.g. LV_FONT_MONTSERRAT_28."""
    if is_builtin_font(name):
        return "LV_FONT_MONTSERRAT_%s" % name.rsplit("_", 1)[1]
    return None


@dataclass
class ImageAsset:
    name: str            # logical name (filename stem)
    source: str          # absolute/relative path to the source file (may not exist yet)
    filename: str        # destination filename inside assets/

    @property
    def ref(self) -> str:
        """The path stored in the .spj, e.g. 'assets/logo.png'."""
        return "%s/%s" % (ASSET_DIR, self.filename)


class AssetManager:
    """Per-project registry of image assets and used custom fonts."""

    def __init__(self) -> None:
        self.images: Dict[str, ImageAsset] = {}   # ref -> ImageAsset

    def register_image(self, source: str, name: str = "") -> ImageAsset:
        """Register an image; returns the asset (its .ref is what widgets store)."""
        base = os.path.basename(source)
        stem, ext = os.path.splitext(base)
        if not ext:
            ext = ".png"
        filename = "%s%s" % (name or stem, ext)
        asset = ImageAsset(name=name or stem, source=source, filename=filename)
        self.images[asset.ref] = asset
        return asset

    def resolve_image(self, value: str) -> str:
        """Turn a user value into a stored ref.

        Accepts: '' / '-'  -> NONE_IMAGE; an already-registered ref
        ('assets/x.png'); or a filesystem path -> auto-registers it.
        """
        if value in ("", NONE_IMAGE):
            return NONE_IMAGE
        if value in self.images or value.startswith(ASSET_DIR + "/"):
            return value
        return self.register_image(value).ref

    def export_assets(self, project_dir: str) -> List[str]:
        """Copy every registered image into <project_dir>/assets/.

        Returns a list of human-readable notes (copied / missing source).
        """
        notes: List[str] = []
        if not self.images:
            return notes
        dest_dir = os.path.join(project_dir, ASSET_DIR)
        os.makedirs(dest_dir, exist_ok=True)
        for asset in self.images.values():
            dest = os.path.join(dest_dir, asset.filename)
            if os.path.isfile(asset.source):
                try:
                    shutil.copyfile(asset.source, dest)
                    notes.append("copied %s -> %s" % (asset.source, asset.ref))
                except OSError as exc:
                    notes.append("FAILED to copy %s (%s)" % (asset.source, exc))
            else:
                notes.append("MISSING source for %s (%s) — add the file to %s/ yourself"
                             % (asset.ref, asset.source, ASSET_DIR))
        return notes

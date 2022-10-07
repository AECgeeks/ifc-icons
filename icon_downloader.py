from pathlib import Path
from enum import Enum
import shutil
import numpy as np
import pandas as pd
import json
from PIL import Image


material_design_icons_path = Path().resolve()  # path to material-design-icons repo
# git clone https://github.com/google/material-design-icons.git
# beware 7.5 Gb!

ifc_codepoints_path = Path().resolve() / "ifc-full-icons.json"
# https://github.com/AECgeeks/ifc-icons/raw/main/ifc-full-icons.json


class IconStyle(Enum):
    BASELINE = ""
    OUTLINED = "outlined"
    ROUND = "round"
    SHARP = "sharp"
    TWO_TONE = "twotone"


class IconSize(Enum):
    DP18 = "18dp"
    DP24 = "24dp"
    DP36 = "36dp"
    DP48 = "48dp"


class IconZoom(Enum):
    ONE = "1x"
    TWO = "2x"


rgb_black, rgb_white = (0, 0, 0), (255, 255, 255)


def invert_image_color(image_path, save_suffix=""):
    im = Image.open(image_path).convert("RGBA")
    im_array = np.array(im)
    im_array[:, :, 0:3] = 255 - im_array[:, :, 0:3]
    new_im = Image.fromarray(im_array)
    new_im.save(image_path.parent / f"{image_path.stem}{save_suffix}{image_path.suffix}")


def get_codepoints(style=IconStyle.BASELINE):
    suffix = "TwoTone" if style.value == IconStyle.TWO_TONE else style.value.capitalize()
    codepoints = material_design_icons_path / "font" / f"MaterialIcons{suffix}-Regular.codepoints"
    return pd.read_csv(codepoints, sep=" ", names=["name", "codepoint"], index_col=0)


def get_list_icons_png(style=IconStyle.BASELINE, size=IconSize.DP48, zoom=IconZoom.ONE):
    list_icons = pd.DataFrame()
    not_found = 0
    for category in (material_design_icons_path / "png").iterdir():
        for icon_name in category.iterdir():
            icon_path = icon_name / (f"materialicons{style.value}") / (size.value) / (zoom.value)
            if icon_path.exists():
                file = [f for f in icon_path.iterdir()][0]
                curr_row = pd.DataFrame([{"category": category.name, "name": icon_name.name, "file": file}])
                list_icons = pd.concat([list_icons, curr_row], axis=0, ignore_index=True)
            else:
                not_found += 1

    print(f"{list_icons.shape[0]} material design icons were found")
    print(f"{not_found} material design icons weren't found")

    codepoints = get_codepoints(style=style)
    list_icons = list_icons.set_index("name")
    list_icons = pd.merge(list_icons, codepoints, how="left", on="name")
    list_icons = list_icons.reset_index().set_index("codepoint")
    return list_icons


def get_ifc_icons_from_codepoints(style=IconStyle.BASELINE, size=IconSize.DP48, zoom=IconZoom.ONE):
    list_icons = get_list_icons_png(style=style, size=size, zoom=zoom)
    with open(ifc_codepoints_path) as f:
        ifc_icons_dict = json.load(f)
    ifc_icons_dict = {key: repr(value).replace("'", "").replace(r"\u", "") for key, value in ifc_icons_dict.items()}
    ifc_icons = pd.DataFrame.from_records(
        [(key, value) for key, value in ifc_icons_dict.items()], columns=["ifc_class", "codepoint"]
    )
    ifc_icons = pd.merge(ifc_icons, list_icons, how="left", on="codepoint").set_index("ifc_class")
    return ifc_icons


def save_ifc_icons(style=IconStyle.BASELINE, size=IconSize.DP48, zoom=IconZoom.ONE, save_path=None, overwrite=True,
                   invert_colors=True):
    save_path = Path().resolve() / "ifc_icons" if save_path is None else save_path
    ifc_icons = get_ifc_icons_from_codepoints(style=style, size=size, zoom=zoom)

    if overwrite:
        shutil.rmtree(save_path, ignore_errors=True)

    save_path.mkdir(exist_ok=True)

    for idx, row in ifc_icons.iterrows():
        save_path_full = save_path / f"{row.name}.png"
        shutil.copyfile(row["file"], save_path_full)
        if invert_colors:
            invert_image_color(save_path_full)

    print(f"{ifc_icons.shape[0]} IFC icons saved to {save_path}")


if __name__ == "__main__":
    save_ifc_icons()

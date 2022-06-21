from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *

from pathlib import Path
from os.path import exists

import numpy as np
import cv2
from PIL import Image, ImageSequence

icon_cache = {}

ICON_PATH = (Path(__file__).resolve().parent.parent / "icons").resolve()
IMAGE_PATH = (Path(__file__).resolve().parent.parent.parent).resolve()


def icon(name, from_cache = True):
    path = str((ICON_PATH / name).resolve())

    if not from_cache or path not in icon_cache:
        icon_cache[path] = QIcon(path)
    
    return icon_cache.get(path)


def imagesAsNumpy(file_path):
    if not exists(file_path):
        print("[Error] File does not exist: {}".format(file_path))
        return []

    path = file_path.lower()

    ends_with_png = path.endswith(".png")
    ends_with_tif = path.endswith(".tif")

    retval = []

    if ends_with_png:
        retval.append(openWithOpenCV(file_path))
    elif ends_with_tif:
        retval = [result[3] for result in openWithPillow(file_path)]

    return retval



def openWithOpenCV(filename):
    array = cv2.cvtColor(
        cv2.imread(filename, cv2.IMREAD_COLOR),
        cv2.COLOR_BGR2RGB
    ).astype(dtype=np.uint8, subok=True, copy=False)

    return { "pixels": array }


def openWithPillow(filename):
    image = Image.open(filename)

    retval = []

    for i, page in enumerate(ImageSequence.Iterator(image)):
        # For more information regarding these tags:
        # https://www.awaresystems.be/imaging/tiff/tifftags/search.html
        tags: dict[str, any] = page.tag_v2.named()

        samplesPerPixel = tags.get("SamplesPerPixel", 1)
        bitsPerSample = np.array(tags.get("BitsPerSample", np.ones((samplesPerPixel))))
        maxValuePerSample = 2 ** bitsPerSample - 1

        layer_data = {}
        pixels = np.array(page, dtype=np.uint8)

        if "PhotometricInterpretation" in tags:
            pi = tags["PhotometricInterpretation"]
            if pi == 0: # WhiteIsZero, Grayscale
                pixels = maxValuePerSample - pixels
                pixels = cv2.cvtColor(pixels, cv2.COLOR_GRAY2RGB)
            elif pi == 1: # BlackIsZero, Grayscale
                pixels = cv2.cvtColor(pixels, cv2.COLOR_GRAY2RGB)
            elif pi == 2: # RGB
                pass
            elif pi == 3: # Palette Color, uses ColorMap field
                if ("ColorMap" not in tags
                or ("SamplesPerPixel" in tags and tags["SamplesPerPixel"] != 1)):
                    continue

                print("TODO: Palette import")
                continue
            else:
                print("TODO: {} import".format(pi))
                continue

        if "XPosition" in tags and "XResolution" in tags:
            layer_data["offsetx"] = float(tags["XPosition"]) * float(tags["XResolution"])
            layer_data["resolutionx"] = tags["XResolution"]

        if "YPosition" in tags and "YResolution" in tags:
            layer_data["offsety"] = float(tags["YPosition"]) * float(tags["YResolution"])
            layer_data["resolutiony"] = tags["YResolution"]
        
        if "PageName" in tags:
            layer_data["name"] = str(tags["PageName"])

        if "ResolutionUnit" in tags:
            layer_data["resolution_unit"] = tags["ResolutionUnit"]
        
        layer_data["pixels"] = pixels
        retval.append(layer_data)

    return retval

from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *

from os.path import exists
from plistlib import InvalidFileException

from src.util.errors import ErrorCode
import src.util.loader as uLoader

import src.ui.sidebar.layers as sbLayers
import src.manager.layers as mgLayers

import numpy as np
import cv2
from PIL import Image, TiffImagePlugin


def numpyArrayToPixmap(array):
    if (array is None
        or len(array.shape) < 2
        or array.shape[0] == 0
        or array.shape[1] == 0
    ):
        return QPixmap()

    height, width = array.shape[0], array.shape[1]
    channels = 1 if len(array.shape) == 2 else array.shape[2]

    format = QImage.Format_RGB888
    if channels == 1:
        format = QImage.Format_Grayscale8
    
    if channels == 4:
        format = QImage.Format_RGBA8888

    if array.dtype != np.uint8:
        array = (array * 255).astype(
            dtype=np.uint8, subok=True, copy=False)

    qimage = QImage(
        array.data,
        width,
        height,
        channels * width,
        format
    )

    return QPixmap(qimage)


def createLayerFromFilePath(file_path):
    if not exists(file_path):
        print("[Error] File does not exist: {}".format(file_path))
        return FileNotFoundError()
    
    DefaultData = {
        "name": "",
        "offsetx": 0,
        "offsety": 0,
        "resolutionx": 300,
        "resolutiony": 300,
        "resolution_unit": 2,
    }

    fname = file_path.lower()
    ends_with_tif = fname.endswith(".tif") or fname.endswith(".tiff")
    ends_with_png = fname.endswith(".png")

    images = []

    if ends_with_tif:
        images += uLoader.openWithPillow(file_path)
    elif ends_with_png:
        image_data = uLoader.openWithOpenCV(file_path)
        images.append(image_data)
    else:
        return InvalidFileException()
    

    for image_data in images:
        data = DefaultData | image_data

        if sbLayers.LayerList.getInstance().layerByName(data["name"]) is not None:
            dialog = QMessageBox()
            dialog.setIcon(QMessageBox.Question)
            dialog.setTextFormat(Qt.RichText)
            dialog.setText(
                "<b>A layer with the name <i>{}</i> already exists</b>".format(
                    data["name"]
                )
            )
            dialog.setInformativeText(
                "This layer will be renamed to <i>{}</i> if no other option is chosen".format(
                    sbLayers.LayerList.getInstance().nextLayerName(data["name"], dry_run=True)
                )
            )

            overwrite_button = dialog.addButton("Overwrite", QMessageBox.DestructiveRole)
            skip_button = dialog.addButton("Skip", QMessageBox.RejectRole)
            rename_button = dialog.addButton("Rename", QMessageBox.AcceptRole)

            dialog.setDefaultButton(rename_button)

            dialog.exec()

            if dialog.clickedButton() == skip_button:
                continue
            elif dialog.clickedButton() == overwrite_button:
                sb_layer = sbLayers.LayerList.getInstance().layerByName(data["name"])
                sbLayers.LayerList.getInstance().removeLayer(sb_layer)
            else:
                pass

        be_layer, sb_layer, cv_layer = mgLayers.LayerManager.getInstance().addItem(
            file_path,
            pixels=data["pixels"],
            name=data["name"],
            initial_offset=QPointF(data["offsetx"], data["offsety"])
        )

        cv_layer.setTifXResolution(data["resolutionx"])
        cv_layer.setTifYResolution(data["resolutiony"])
        cv_layer.setTifResolutionUnit(data["resolution_unit"])

    return 


def _prepareLayersForPng(layers):
    bounds = QRectF()
    result = []

    for layer in layers:
        bounds |= layer[2].sceneBoundingRect() # Union

    for layer in layers:
        rect = layer[2].sceneBoundingRect()

        top = int(rect.top()) - int(bounds.top())
        left = int(rect.left()) - int(bounds.left())

        layer_padded = cv2.copyMakeBorder(
            layer[0].fullResolutionInterpolated(),
            top,
            int(bounds.height()) - int(rect.height()) - top,
            left,
            int(bounds.width()) - int(rect.width()) - left,
            cv2.BORDER_CONSTANT,
            value = (0, 0, 0, 0))
        
        result.append(layer_padded)

    return result


def saveAsPng(file_path, layers):
    layers = _prepareLayersForPng(layers)
    
    result = np.zeros(layers[0].shape, dtype=np.float32)

    for layer in layers:
        over_mask = layer[:,:,3]
        back_mask = 1 - over_mask

        over_mask = cv2.cvtColor(over_mask, cv2.COLOR_GRAY2RGBA)
        back_mask = cv2.cvtColor(back_mask, cv2.COLOR_GRAY2RGBA)

        result = result * back_mask + layer * over_mask

    result = np.uint8(np.clip(result, 0, 1) * 255)

    image = Image.fromarray(result, mode="RGBA")
    image.save(file_path, "PNG")

    return ErrorCode.Ok


def saveAsTif(file_path, layers):

    with TiffImagePlugin.AppendingTiffWriter(file_path, True) as tif_out:
        for layer_tuple in layers:
            be_layer, sb_layer, cv_layer = layer_tuple

            xposition = cv_layer.sceneBoundingRect().left() / float(cv_layer.tifXResolution())
            yposition = cv_layer.sceneBoundingRect().top() / float(cv_layer.tifYResolution())

            pixels = be_layer.fullResolutionInterpolated()
            pixels = np.uint8(np.clip(pixels, 0, 1) * 255)
            image = Image.fromarray(pixels)

            image.save(tif_out, format = "TIFF",
                tiffinfo = {
                    # https://www.awaresystems.be/imaging/tiff/tifftags/orientation.html
                    256: be_layer.width(), # ImageWidth
                    257: be_layer.height(), # ImageLength
                    # 258: (8, 8, 8, 8), # BitsPerSample
                    259: 1, # Compression, 1 = No compression
                    262: 2, # PhotometricInterpretation, 2 = RGB
                    # 273: (2700526, 2866926, 3033326), # StripOffsets
                    274: 1, # Orientation
                    # 277: 4, # SamplesPerPixel
                    # 278: 128, # RowsPerStrip
                    # 279: (166400, 166400, 87100), # StripByteCounts
                    282: cv_layer.tifXResolution(), # XResolution, pixels per ResolutionUnit
                    283: cv_layer.tifYResolution(), # YResolution, pixels per ResolutionUnit
                    284: 1, # PlanarConfiguration
                    285: sb_layer.name(), # PageName
                    286: xposition, # XPosition
                    287: yposition, # YPosition
                    296: cv_layer.tifResolutionUnit(), # ResolutionUnit, 2 = inch, 3 = cm
                    # 297: (1, 2), # PageNumber
                    # 338: (1,), # ExtraSamples
                    # 339: (1, 1, 1, 1), # SampleFormat
                    # 254: 2 # NewSubfileType
                }
            )
            tif_out.newFrame()
    
    return ErrorCode.Ok

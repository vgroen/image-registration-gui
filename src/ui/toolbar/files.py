from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *

from src.util.errors import ErrorCode
import src.util.layers as uLayers
import src.util.loader as uLoader

import src.manager.layers as mgLayers

class ImportFileTool(QAction):
    __instance = None

    def __init__(self):
        if ImportFileTool.__instance != None:
            raise Exception("Singleton")
        else:
            super().__init__(
                uLoader.icon("baseline_note_add_black_24dp"),
                "Open File")
            ImportFileTool.__instance = self

        self.setToolTip("Open an image file as a layer")
        self.setCheckable(False)
        self.triggered.connect(lambda _: self.openFileDialog())


    def openFileDialog(self):
        tif_ext = "*.tif *.tiff"
        png_ext = "*.png"

        extensions = str("Image files ({} {})".format(tif_ext, png_ext))
        caption = "Open Image Files"
        directory = "."

        file_dialog = QFileDialog(self.parent(), caption, directory, extensions)
        file_dialog.setAcceptMode(QFileDialog.AcceptOpen)
        file_dialog.setFileMode(QFileDialog.ExistingFiles)

        if not file_dialog.exec():
            return

        filenames = file_dialog.selectedFiles()

        for filename in filenames:
            uLayers.createLayerFromFilePath(filename)


    @staticmethod
    def getInstance():
        if ImportFileTool.__instance == None:
            ImportFileTool()
        return ImportFileTool.__instance


class ExportFileTool(QAction):
    __instance = None

    def __init__(self):
        if ExportFileTool.__instance != None:
            raise Exception("Singleton")
        else:
            super().__init__(
                uLoader.icon("baseline_save_alt_black_24dp"),
                "Export to File")
            ExportFileTool.__instance = self

        self.setToolTip("Export the layers")
        self.setCheckable(False)
        self.triggered.connect(lambda _: self.openFileDialog())


    def openFileDialog(self):
        if len(mgLayers.LayerManager.getInstance().allLayers()) == 0:
            ErrorCode.showDialog(ErrorCode.Export_NoLayers)

        tif_ext = "Multi-layer image file (*.tif *.tiff)"
        png_ext = "Single image file (*.png)"

        extensions = str("{};;{}".format(tif_ext, png_ext))
        caption = "Save As"
        directory = "."

        file_dialog = QFileDialog(self.parent(), caption, directory, extensions)
        file_dialog.setAcceptMode(QFileDialog.AcceptSave)
        file_dialog.setFileMode(QFileDialog.AnyFile)

        file_dialog.setDefaultSuffix("tif")
        file_dialog.filterSelected.connect(
            lambda f: file_dialog.setDefaultSuffix(
                "png" if f == png_ext else "tif"
            )
        )

        if not file_dialog.exec():
            return

        filename = file_dialog.selectedFiles()[0]
        exts = file_dialog.selectedNameFilter()

        fname = filename.lower()
        ends_with_tif = fname.endswith(".tif") or fname.endswith(".tiff")
        ends_with_png = fname.endswith(".png")
        ends_with_ext = ends_with_png or ends_with_tif


        layers = mgLayers.LayerManager.getInstance().allLayers()

        if ((not ends_with_ext
            and exts == png_ext
            ) or ends_with_png
        ):
            uLayers.saveAsPng(filename, layers)
        elif ((not ends_with_ext
            and exts == tif_ext
            ) or ends_with_tif
        ):
            uLayers.saveAsTif(filename, layers)


    @staticmethod
    def getInstance():
        if ExportFileTool.__instance == None:
            ExportFileTool()
        return ExportFileTool.__instance

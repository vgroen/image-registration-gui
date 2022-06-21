from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *

import src.util.loader as uLoader

class BrushTool(QAction):
    __instance = None

    def __init__(self):
        if BrushTool.__instance != None:
            raise Exception("Singleton")
        else:
            super().__init__(
                uLoader.icon("baseline_brush_black_24dp"),
                "Mask Brush")
            BrushTool.__instance = self

        self.setToolTip("Add to or remove from the mask directly")
        self.setCheckable(True)


    @staticmethod
    def getInstance():
        if BrushTool.__instance == None:
            BrushTool()
        return BrushTool.__instance

from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *

import src.util.loader as uLoader

class PanTool(QAction):
    __instance = None

    def __init__(self):
        if PanTool.__instance != None:
            raise Exception("Singleton")
        else:
            super().__init__(
                uLoader.icon("baseline_pan_tool_black_24dp"),
                "Pan View")
            PanTool.__instance = self

        self.setToolTip("Pan the view")
        self.setCheckable(True)


    @staticmethod
    def getInstance():
        if PanTool.__instance == None:
            PanTool()
        return PanTool.__instance


class MoveLayersTool(QAction):
    __instance = None

    def __init__(self):
        if MoveLayersTool.__instance != None:
            raise Exception("Singleton")
        else:
            super().__init__(
                uLoader.icon("baseline_open_with_black_24dp"),
                "Move Layers")
            MoveLayersTool.__instance = self

        self.setToolTip("Move the selected layers around")
        self.setCheckable(True)


    @staticmethod
    def getInstance():
        if MoveLayersTool.__instance == None:
            MoveLayersTool()
        return MoveLayersTool.__instance

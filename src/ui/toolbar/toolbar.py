from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *

import src.ui.toolbar.files as tbFile
import src.ui.toolbar.movement as tbMove
import src.ui.toolbar.align as tbAlign
import src.ui.toolbar.mask as tbMask

class Tool:
    NoTool = 0
    MoveLayers = 1
    PanView = 2
    MaskBrush = 3


class ToolBar(QToolBar):
    __instance = None

    toolChanged = pyqtSignal(int)

    def __init__(self):
        if ToolBar.__instance != None:
            raise Exception("Singleton")
        else:
            super().__init__("ToolBar")
            ToolBar.__instance = self
        
        self._active_tool = Tool.NoTool

        self._widgets = {}
        self.initUI()
    

    def activeTool(self):
        return self._active_tool
    
    def isActiveTool(self, tool):
        return self._active_tool == tool

    def setActiveTool(self, tool):
        self._active_tool = tool

        tbMove.MoveLayersTool.getInstance().setChecked(tool == Tool.MoveLayers)
        tbMove.PanTool.getInstance().setChecked(tool == Tool.PanView)
        tbMask.BrushTool.getInstance().setChecked(tool == Tool.MaskBrush)

        self.toolChanged.emit(tool)
    

    def initUI(self):
        self.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)

        self.addAction(tbFile.ImportFileTool.getInstance())
        self.addAction(tbFile.ExportFileTool.getInstance())

        self.addSeparator()

        self.addAction(tbMove.PanTool.getInstance())
        tbMove.PanTool.getInstance().triggered.connect(
            lambda _: self.setActiveTool(Tool.PanView))

        self.addAction(tbMove.MoveLayersTool.getInstance())
        tbMove.MoveLayersTool.getInstance().triggered.connect(
            lambda _: self.setActiveTool(Tool.MoveLayers))

        self.addSeparator()

        self.addAction(tbMask.BrushTool.getInstance())
        tbMask.BrushTool.getInstance().triggered.connect(
            lambda _: self.setActiveTool(Tool.MaskBrush))

        self.addSeparator()

        self.addAction(tbAlign.AutoAlignTool.getInstance())

        self.setActiveTool(Tool.MoveLayers)
    

    @staticmethod
    def getInstance():
        if ToolBar.__instance == None:
            ToolBar()
        return ToolBar.__instance

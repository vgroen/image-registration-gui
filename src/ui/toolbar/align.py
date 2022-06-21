from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *

import src.backend.groups as beGroups
import src.manager.groups as mgGroups

import src.util.align as uAlign
import src.util.loader as uLoader

class AutoAlignTool(QAction):
    __instance = None

    def __init__(self):
        if AutoAlignTool.__instance != None:
            raise Exception("Singleton")
        else:
            super().__init__(
                uLoader.icon("baseline_fit_screen_black_24dp"),
                "Auto Align")
            AutoAlignTool.__instance = self

        self.setToolTip("Align the currently active group")
        self.setCheckable(False)
        self.triggered.connect(
            lambda _: uAlign.createSolverFromGroup(
                mgGroups.GroupManager.getInstance().activeGroup(
                    beGroups.Group
                )
            )
        )
    

    @staticmethod
    def getInstance():
        if AutoAlignTool.__instance == None:
            AutoAlignTool()
        return AutoAlignTool.__instance

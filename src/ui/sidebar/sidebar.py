from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *

import src.ui.sidebar.groups as groups
import src.ui.sidebar.layers as layers
import src.ui.sidebar.mask as mask

class SideBar(QWidget):
    __instance = None

    def __init__(self):
        if SideBar.__instance != None:
            raise Exception("Singleton")
        else:
            super().__init__()
            SideBar.__instance = self
        
        self.initUI()
    

    def initUI(self):
        layout = QVBoxLayout()

        layer_policy = QSizePolicy(QSizePolicy.Preferred, QSizePolicy.Ignored)
        group_policy = QSizePolicy(QSizePolicy.Preferred, QSizePolicy.Ignored)
        mask_policy  = QSizePolicy(QSizePolicy.Preferred, QSizePolicy.Ignored)

        layer_policy.setVerticalStretch(1)
        group_policy.setVerticalStretch(1)
        mask_policy.setVerticalStretch(1)

        layers.LayerPane.getInstance().setSizePolicy(layer_policy)
        groups.GroupPane.getInstance().setSizePolicy(group_policy)
        mask.MaskPane.getInstance().setSizePolicy(mask_policy)

        layout.addWidget(layers.LayerPane.getInstance())
        layout.addWidget(groups.GroupPane.getInstance())
        layout.addWidget(mask.MaskPane.getInstance())

        self.setLayout(layout)


    @staticmethod
    def getInstance():
        if SideBar.__instance == None:
            SideBar()
        return SideBar.__instance

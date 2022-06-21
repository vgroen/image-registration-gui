from calendar import c
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *

import src.backend.brush as beBrush

class MaskPane(QGroupBox):
    __instance = None

    def __init__(self):
        if MaskPane.__instance != None:
            raise Exception("Singleton")
        else:
            super().__init__("Mask Options")
            MaskPane.__instance = self
        
        self._widgets = {}
        self.initUI()
    

    def initUI(self):
        self.setProperty("elevation", "02dp")

        layout = QVBoxLayout()

        form_layout = QFormLayout()

        brush_size = QSpinBox()
        brush_size.setValue(beBrush.MaskBrush.getInstance().radius())
        brush_size.setRange(1, 1000)
        brush_size.setSingleStep(1)
        brush_size.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Preferred)
        brush_size.setStepType(QSpinBox.AdaptiveDecimalStepType)
        brush_size.valueChanged.connect(beBrush.MaskBrush.getInstance().setRadius)
        self._widgets["brush_size"] = brush_size
        form_layout.addRow("Mask brush radius", brush_size)

        layout.addLayout(form_layout)

        self.setLayout(layout)


    @staticmethod
    def getInstance():
        if MaskPane.__instance == None:
            MaskPane()
        return MaskPane.__instance

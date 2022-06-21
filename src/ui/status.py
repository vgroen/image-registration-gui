from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *

class StatusBar(QWidget):
    __instance = None

    def __init__(self):
        if StatusBar.__instance != None:
            raise Exception("Singleton")
        else:
            super().__init__()
            StatusBar.__instance = self

        self.setAutoFillBackground(True)
        self.setPalette(QPalette(Qt.green))
    
        self.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)
    

    def sizeHint(self):
        super_size = super().sizeHint()
        return QSize(super_size.width(), 48)


    @staticmethod
    def getInstance():
        if StatusBar.__instance == None:
            StatusBar()
        return StatusBar.__instance

from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *

import src.ui.toolbar.toolbar as toolbar
import src.ui.canvas.canvas as canvas
import src.ui.sidebar.sidebar as sidebar

class Window(QMainWindow):
    __instance = None

    def __init__(self):
        if Window.__instance != None:
            raise Exception("Singleton")
        else:
            super().__init__()
            Window.__instance = self

        self.initUI()
    

    def initUI(self):
        self.setProperty("elevation", "00dp")

        self.addToolBar(toolbar.ToolBar.getInstance())
        
        window_layout = QVBoxLayout()
        main_layout = QHBoxLayout()

        canvas_policy = QSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred)
        sidebar_policy = QSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred)

        canvas_policy.setHorizontalStretch(2)
        sidebar_policy.setHorizontalStretch(1)

        canvas.Canvas.getInstance().setSizePolicy(canvas_policy)
        sidebar.SideBar.getInstance().setSizePolicy(sidebar_policy)

        main_layout.addWidget(canvas.Canvas.getInstance())
        main_layout.addWidget(sidebar.SideBar.getInstance())

        window_layout.addLayout(main_layout)
        # window_layout.addWidget(status.StatusBar.getInstance())

        window = QWidget()
        window.setLayout(window_layout)
        self.setCentralWidget(window)
    

    @staticmethod
    def getInstance():
        if Window.__instance == None:
            Window()
        return Window.__instance

from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *

import src.util.loader as uLoader

class IconCheckBox(QCheckBox):
    icons = []

    def __init__(self, parent = None):
        super().__init__(parent)

        self.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)

        if len(IconCheckBox.icons) == 0:
            IconCheckBox.icons.append(uLoader.icon("baseline_looks_one_black_24dp.png").pixmap(20, 20))
            IconCheckBox.icons.append(uLoader.icon("baseline_looks_two_black_24dp.png").pixmap(20, 20))
            IconCheckBox.icons.append(uLoader.icon("baseline_looks_3_black_24dp.png").pixmap(20, 20))
        
        self._icons = IconCheckBox.icons.copy()
    

    def sizeHint(self):
        return QSize(24, 24)
    

    def hitButton(self, pos: QPoint):
        return self.contentsRect().contains(pos)
    

    def setIcon(self, state: Qt.CheckState, icon: QIcon):
        # Unchecked: 0, PartiallyChecked: 1, Checked: 2
        self._icons[state] = icon.pixmap(20, 20)
    

    def paintEvent(self, event: QPaintEvent):
        bounds = self.contentsRect()
        size = bounds.height() - 4

        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        icon_index = self.checkState() 
        painter.drawPixmap(2, 2, size, size, self._icons[icon_index])

        painter.end()
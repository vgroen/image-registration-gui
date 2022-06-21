from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *

class PixmapButton(QPushButton):
    def __init__(self, pixmap, parent = None):
        super().__init__(parent)
        self._pixmap = pixmap
    

    def sizeHint(self):
        return self._pixmap.size() + QSize(2, 2)
    

    def paintEvent(self, event: QPaintEvent):
        bounds = self.contentsRect()
        size = bounds.height() - 4

        painter = QPainter(self)
        painter.setRenderHint(QPainter.SmoothPixmapTransform)
        painter.setRenderHint(QPainter.Antialiasing)

        painter.drawPixmap(2, 2, size, size, self._pixmap)

        painter.end()

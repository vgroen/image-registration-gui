from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *

import src.ui.canvas.layers as cvLayers

class GraphicsView(QGraphicsView):
    def __init__(self):
        super().__init__()

        self.setAlignment(Qt.AlignLeft | Qt.AlignTop)
        self.setRenderHints(QPainter.SmoothPixmapTransform | QPainter.Antialiasing)
        self.setTransformationAnchor(QGraphicsView.NoAnchor)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setViewportUpdateMode(QGraphicsView.FullViewportUpdate)
        self.setScene(QGraphicsScene())

        self.setProperty("elevation", "00dp")

        self._items: list[cvLayers.PixmapLayer] = []
    

    def addItem(self, item):
        if item not in self._items:
            item.setView(self)
            self._items.append(item)
            self.scene().addItem(item)
    

    def removeItem(self, item):
        if item in self._items:
            self._items.remove(item)
            self.scene().removeItem(item)
    

    def setTranslation(self, point):
        for item in self._items:
            item.setTranslation(point)
    

    def setScale(self, scale):
        cursor_pos = QCursor.pos() - self.viewport().mapToGlobal(QPoint(0, 0))
        for item in self._items:
            item.setScale(scale, cursor_pos)
    

    def wheelEvent(self, qevent: QMouseEvent):
        qevent.ignore()

    def mousePressEvent(self, qevent: QMouseEvent):
        qevent.ignore()

    def mouseMoveEvent(self, qevent: QMouseEvent):
        qevent.ignore()

    def mouseReleaseEvent(self, qevent: QMouseEvent):
        qevent.ignore()
    

    def viewMousePressEvent(self, qevent: QMouseEvent):
        super().mousePressEvent(qevent)

    def viewMouseMoveEvent(self, qevent: QMouseEvent):
        super().mouseMoveEvent(qevent)

    def viewMouseReleaseEvent(self, qevent: QMouseEvent):
        super().mouseReleaseEvent(qevent)

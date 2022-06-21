from typing import Dict

import numpy as np

from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *

import src.ui.toolbar.toolbar as toolbar
import src.ui.canvas.view as view
import src.ui.sidebar.layers as sbLayers

class Canvas(QWidget):
    __instance = None

    def __init__(self):
        if Canvas.__instance != None:
            raise Exception("Singleton")
        else:
            super().__init__()
            Canvas.__instance = self
        
        self._views: Dict[str, view.GraphicsView] = {}
        self._translation = QPointF()
        self._scale = 1
        
        self.initUI()
        self.addGraphicsView("main")
    

    def initUI(self):
        layout = QStackedLayout()
        layout.setStackingMode(QStackedLayout.StackAll)

        self.setLayout(layout)
    

    def addGraphicsView(self, name):
        graphics_view = view.GraphicsView()
        self.layout().addWidget(graphics_view)
        self._views[name] = graphics_view
    

    def getView(self, name):
        return self._views.get(name, None)
    

    def mouseDoubleClickEvent(self, qevent: QMouseEvent):
        qevent.ignore()
    

    def wheelEvent(self, qevent: QWheelEvent):
        qevent.accept()

        EventHandler.getInstance().wheelEvent(qevent)
        factor = 1 + 0.2 * np.sign(EventHandler.getInstance().deltaWheel())
        self._scale *= factor

        for name in self._views:
            self._views[name].setScale(self._scale)
    

    def mousePressEvent(self, qevent: QMouseEvent):
        qevent.accept()

        EventHandler.getInstance().mousePressEvent(qevent)

        for name in self._views:
            self._views[name].viewMousePressEvent(qevent)


    def mouseMoveEvent(self, qevent: QMouseEvent):
        qevent.accept()

        EventHandler.getInstance().mouseMoveEvent(qevent)
        factor = EventHandler.getInstance().deltaPos()
        self._translation += factor

        for name in self._views:
            self._views[name].setTranslation(self._translation)
            self._views[name].update()
            self._views[name].viewMouseMoveEvent(qevent)


    def mouseReleaseEvent(self, qevent: QMouseEvent):
        qevent.accept()

        EventHandler.getInstance().mouseReleaseEvent(qevent)

        if qevent.modifiers() != Qt.ControlModifier:
            hit = False
            for name in self._views:
                if self._views[name].itemAt(qevent.pos()) is not None:
                    hit = True
                    break

            if not hit:
                sbLayers.LayerList.getInstance().forEach(lambda l: l.setLayerSelected(False))

        for name in self._views:
            self._views[name].viewMouseReleaseEvent(qevent)


    @staticmethod
    def getInstance():
        if Canvas.__instance == None:
            Canvas()
        return Canvas.__instance


class EventHandler:
    __instance = None

    def __init__(self):
        if EventHandler.__instance != None:
            raise Exception("Singleton")
        else:
            super().__init__()
            EventHandler.__instance = self
        
        self._lastPos = QPointF()
        self._deltaPos = QPointF()
        self._deltaWheel = 0


    def deltaPos(self):
        return self._deltaPos
    
    def deltaWheel(self):
        return self._deltaWheel
    

    def wheelEvent(self, qevent: QWheelEvent):
        if qevent.modifiers() == Qt.NoModifier:
            self._deltaWheel = qevent.angleDelta().y()
    

    def mousePressEvent(self, qevent: QMouseEvent):
        self._deltaPos.setX(0)
        self._deltaPos.setY(0)

        self._lastPos = qevent.localPos()


    def mouseMoveEvent(self, qevent: QMouseEvent):
        T1 = toolbar.ToolBar.getInstance().isActiveTool(toolbar.Tool.PanView)
        T1 &= qevent.buttons() == Qt.LeftButton

        T2 = toolbar.ToolBar.getInstance().isActiveTool(toolbar.Tool.MoveLayers)
        T2 &= qevent.buttons() == Qt.RightButton

        T3 = False
        # if toolbar.ToolBar.getInstance().isActiveTool(toolbar.Tool.MaskBrush):
        #     hit_selected = False
        #     for name in Canvas.getInstance()._views:
        #         item_at = Canvas.getInstance().getView(name).itemAt(qevent.pos()) 

        #         if (item_at is not None
        #             and isinstance(item_at, cvLayers.PixmapLayer)
        #             and item_at.isLayerSelected()
        #         ):
        #             hit_selected = True
        #             break
        #     T3 = not hit_selected

        if not T1 and not T2 and not T3:
            return

        self._deltaPos.setX(qevent.localPos().x() - self._lastPos.x())
        self._deltaPos.setY(qevent.localPos().y() - self._lastPos.y())

        self._lastPos = qevent.localPos()


    def mouseReleaseEvent(self, qevent: QMouseEvent):
        self._deltaPos.setX(0)
        self._deltaPos.setY(0)

        self._lastPos = qevent.localPos()


    @staticmethod
    def getInstance():
        if EventHandler.__instance == None:
            EventHandler()
        return EventHandler.__instance

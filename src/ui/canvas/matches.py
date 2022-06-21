from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *

import src.ui.sidebar.groups as sbGroups
import src.ui.sidebar.layers as sbLayers
import src.ui.canvas.layers as cvLayers

import src.manager.layers as mgLayers

class MatchesLayer(QGraphicsItemGroup):
    
    def __init__(self):
        super().__init__()

        self._view = None

        self._position = QPointF(0, 0)

        # Transformations from view
        self._translation = QPointF(0, 0)
        self._scale = 1
        self._scale_offset = QPointF(0, 0)
        self._origin = QPointF(0.5, 0.5)

        self._reference_layer = None
        self._sidebar_group = None
        self._sidebar_layer = None

        self._pen = QPen(QColor(255, 0, 0, 130))
        self._pen.setWidth(1)

        self._items: list[MatchGraphicsItem] = []
    

    def pen(self):
        return self._pen

    def setPen(self, pen):
        self._pen = pen
        for item in self._items:
            item.setPen(self.pen())


    def remove(self):
        for item in self.childItems():
            self.removeFromGroup(item)
        self._items.clear()
        self.unlinkSideBarLayer()
        self.unlinkSideBarGroup()
        if self.view() is not None:
            self.view().removeItem(self)
    

    def setVisible(self, b):
        if (self._sidebar_group is not sbGroups.GroupPane
            .getInstance().activeGroup()
        ):
            super().setVisible(False)
        else:
            super().setVisible(b)
    

    def unlinkSideBarGroup(self):
        if self._sidebar_group is None:
            return
        
        self._sidebar_group.showMatchesChanged.disconnect(self.setVisible)
        if self._reference_layer is not None:
            self._reference_layer.visibilityChanged.disconnect(self.setVisible)
        self._sidebar_group.templateRemoved.disconnect(self.__templateRemovedSlot)
        self._sidebar_group.referenceChanged.disconnect(self.remove)
        self._sidebar_group.removed.disconnect(self.remove)
        self._reference_layer = None
        self._sidebar_group = None
    

    def linkSideBarGroup(self, group):
        if group is None or not isinstance(group, sbGroups.GroupItem):
            return
        
        self.unlinkSideBarGroup()

        self._sidebar_group = group
        self._reference_layer = self._sidebar_group.referenceLayer()
        self._sidebar_group.removed.connect(self.remove)
        self._sidebar_group.referenceChanged.connect(self.remove)
        self._sidebar_group.templateRemoved.connect(self.__templateRemovedSlot)
        self._reference_layer.visibilityChanged.connect(self.setVisible)
        self._sidebar_group.showMatchesChanged.connect(self.setVisible)
        self._sidebar_group.processStatusChanged.connect(lambda status: status and self.remove())
    

    def unlinkSideBarLayer(self):
        if self._sidebar_layer is None:
            return
        
        self._sidebar_layer.visibilityChanged.disconnect(self.setVisible)
        self._sidebar_layer = None


    def linkSideBarLayer(self, layer):
        if layer is None or not isinstance(layer, sbLayers.LayerItem):
            return
        
        self.unlinkSideBarLayer()

        self._sidebar_layer = layer
        self._sidebar_layer.visibilityChanged.connect(self.setVisible)

    
    def addMatch(self, keypoint_reference: QPointF, keypoint_template: QPointF):
        if self._sidebar_group is None or self._sidebar_layer is None:
            return

        item = MatchGraphicsItem()
        item.setReferenceLayer(
            mgLayers.LayerManager.getInstance().getLayer(
                self._sidebar_group.referenceLayer(), cvLayers.PixmapLayer
            )
        )
        item.setReferenceKeyPointPosition(keypoint_reference)
        item.setTemplateLayer(
            mgLayers.LayerManager.getInstance().getLayer(
                self._sidebar_layer, cvLayers.PixmapLayer
            )
        )
        item.setTemplateKeyPointPosition(keypoint_template)
        item.setPen(self.pen())

        self.addToGroup(item)
        self._items.append(item)

        return item
    

    def view(self):
        return self._view
    
    def setView(self, view):
        if view is None:
            return
        
        if self.view() is not None:
            self.view().removeItem(self)

        self._view = view


    def position(self):
        return self._position
    
    def setPosition(self, pos):
        self._position = pos


    def translation(self):
        return self._translation

    def setTranslation(self, point):
        self._translation = QPointF(point)
        self.setPosition(self.position())
    

    def scale(self):
        return self._scale

    def setScale(self, scalar, origin = QPointF(0, 0)):
        factor = scalar / self._scale

        self._scale = scalar

        delta = (origin - self.pos()) * (factor - 1)
        self._scale_offset += delta
        self.setPosition(self.position())


    def mousePressEvent(self, qevent: QGraphicsSceneMouseEvent):
        qevent.ignore()

    def mouseMoveEvent(self, qevent: QGraphicsSceneMouseEvent):
        qevent.ignore()

    def mouseReleaseEvent(self, qevent: QGraphicsSceneMouseEvent):
        qevent.ignore()

    def __templateRemovedSlot(self, name):
        if self._sidebar_layer.name() == name:
            self.remove()
    

class MatchGraphicsItem(QGraphicsItem):

    def __init__(self):
        super().__init__()

        self._reference_layer = None
        self._template_layer = None

        self._reference_position = QPointF()
        self._template_position = QPointF()

        self._pen = QPen(QColor(255, 0, 0, 130))
        self._pen.setWidth(1)
        self._keypoint_radius = 6
    

    def boundingRect(self):
        if self.referenceLayer() is None or self.templateLayer() is None:
            return QRectF()
        
        return self.referenceLayer().boundingRect() | self.templateLayer().boundingRect()
    

    def referenceKeyPointPosition(self):
        return self._reference_position
    
    def setReferenceKeyPointPosition(self, point):
        self._reference_position = point
    

    def templateKeyPointPosition(self):
        return self._template_position
    
    def setTemplateKeyPointPosition(self, point):
        self._template_position = point
    

    def referenceLayer(self):
        return self._reference_layer
    
    def setReferenceLayer(self, layer):
        if not isinstance(layer, cvLayers.PixmapLayer):
            self._reference_layer = None
        else:
            self._reference_layer = layer


    def templateLayer(self):
        return self._template_layer

    def setTemplateLayer(self, layer):
        if not isinstance(layer, cvLayers.PixmapLayer):
            self._template_layer = None
        else:
            self._template_layer = layer
    

    def keyPointRadius(self):
        return self._keypoint_radius
    
    def setKeyPointRadius(self, radius):
        self._keypoint_radius = radius
    

    def pen(self):
        return self._pen
    
    def setPen(self, pen):
        self._pen = pen


    def paint(self, painter: QPainter, option: QStyleOption, widget: QWidget = None):
        if self.referenceLayer() is None or self.templateLayer() is None:
            return

        painter.save()

        painter.setPen(self.pen())

        reference_center = (self.referenceLayer().scenePos()
            + self.referenceKeyPointPosition() * self.referenceLayer().scale())
        template_center = (self.templateLayer().scenePos()
            + self.templateKeyPointPosition() * self.templateLayer().scale())

        painter.drawLine(
            reference_center,
            template_center
        )

        painter.drawEllipse(
            reference_center,
            self.keyPointRadius(),
            self.keyPointRadius()
        )

        painter.drawRect(
            template_center.x() - self.keyPointRadius(),
            template_center.y() - self.keyPointRadius(),
            self.keyPointRadius() * 2,
            self.keyPointRadius() * 2
        )

        painter.restore()

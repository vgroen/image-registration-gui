from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *

import src.ui.toolbar.toolbar as toolbar
import src.ui.sidebar.layers as sbLayers
import src.backend.layers as beLayers
import src.backend.brush as beBrush
import src.ui.toolbar.toolbar as toolbar

import src.util.layers as uLayers

import numpy as np
import cv2


MaskColorRed = [0.95, 0.15, 0.30, 0.70]

class RenderMode:
    Pixels = 1
    Mask = 2
    Interpolated = 3


class PixmapLayer(QGraphicsPixmapItem):
    __SelectionPen = None


    def __init__(self):
        super().__init__()
        if PixmapLayer.__SelectionPen is None:
            pen = QPen()
            pen.setStyle(Qt.DotLine)
            pen.setWidth(2)
            pen.setColor(QColor(255, 200, 15))
            PixmapLayer.__SelectionPen = pen
        
        self.setTransformationMode(Qt.SmoothTransformation)

        self._linked_sidebar_layer = None
        self._linked_backend_layer = None

        self._view = None

        self._position = QPointF(0, 0)

        # Transformations from view
        self._translation = QPointF(0, 0)
        self._scale = 1
        self._scale_offset = QPointF(0, 0)
        self._origin = QPointF(0.5, 0.5)

        self._selected = False

        self._tif_data = {}

        self._render_mode = RenderMode.Pixels
        self._composition_mode = QPainter.CompositionMode_SourceOver
    

    def tifXResolution(self):
        return self._tif_data.get("xresolution", 300)

    def setTifXResolution(self, value):
        self._tif_data["xresolution"] = value


    def tifYResolution(self):
        return self._tif_data.get("yresolution", 300)

    def setTifYResolution(self, value):
        self._tif_data["yresolution"] = value


    def tifResolutionUnit(self):
        return self._tif_data.get("resolution_unit", 2)

    def setTifResolutionUnit(self, value):
        self._tif_data["resolution_unit"] = value
    

    def view(self):
        return self._view
    
    def setView(self, view):
        if view is None:
            return
        
        if self.view() is not None:
            self.view().removeItem(self)

        self._view = view
    

    def isLayerSelected(self):
        return self._selected

    def setLayerSelected(self, b):
        if self._selected != b:
            self._selected = b

            if toolbar.ToolBar.getInstance().isActiveTool(toolbar.Tool.MaskBrush):
                if b and self.renderMode() != RenderMode.Mask:
                    self.setRenderMode(RenderMode.Mask)
                    self.updatePixmap()
                elif not b and self.renderMode() == RenderMode.Mask:
                    self.setRenderMode(RenderMode.Pixels)
                    self.updatePixmap()

            self.update()
    

    def remove(self):
        self.unlinkSideBarLayer()
        self.unlinkBackendLayer()
        if self.view() is not None:
            self.view().removeItem(self)
    

    def unlinkSideBarLayer(self):
        if self._linked_sidebar_layer is None:
            return
        
        self._linked_sidebar_layer.setThumbnail(None)
        self._linked_sidebar_layer.compositionModeChanged.disconnect(self.__compositionModeChangedSlot)
        self._linked_sidebar_layer.indexChanged.disconnect(self.__indexChangedSlot)
        self._linked_sidebar_layer.opacityChanged.disconnect(self.setOpacity)
        self._linked_sidebar_layer.visibilityChanged.disconnect(self.setVisible)
        self._linked_sidebar_layer.selectionChanged.disconnect(self.setLayerSelected)
        self._linked_sidebar_layer = None
        

    def linkSideBarLayer(self, layer):
        if layer is None or not isinstance(layer, sbLayers.LayerItem):
            return
        
        self.unlinkSideBarLayer()

        self._linked_sidebar_layer = layer
        self._linked_sidebar_layer.removed.connect(self.remove)
        self._linked_sidebar_layer.selectionChanged.connect(self.setLayerSelected)
        self._linked_sidebar_layer.visibilityChanged.connect(self.setVisible)
        self._linked_sidebar_layer.opacityChanged.connect(self.setOpacity)
        self._linked_sidebar_layer.indexChanged.connect(self.__indexChangedSlot)
        self._linked_sidebar_layer.compositionModeChanged.connect(self.__compositionModeChangedSlot)
        self._linked_sidebar_layer.setThumbnail(self.pixmap())
    

    def unlinkBackendLayer(self):
        if self._linked_backend_layer is None:
            return
        
        self.pixmap().fill(Qt.transparent)
        self._linked_backend_layer.maskChanged.disconnect(self.__maskChangedSlot)
        self._linked_backend_layer.pixelsChanged.disconnect(self.__pixelsChangedSlot)
        self._linked_backend_layer.interpolationChanged.disconnect(self.__interpolationChangedSlot)
        toolbar.ToolBar.getInstance().toolChanged.disconnect(self.__toolChangedSlot)
        self._linked_backend_layer = None
    

    def linkBackendLayer(self, layer):
        if layer is None or not isinstance(layer, beLayers.Layer):
            return
        
        self.unlinkBackendLayer()

        self._linked_backend_layer = layer
        toolbar.ToolBar.getInstance().toolChanged.connect(self.__toolChangedSlot)
        self._linked_backend_layer.interpolationChanged.connect(self.__interpolationChangedSlot)
        self._linked_backend_layer.pixelsChanged.connect(self.__pixelsChangedSlot)
        self._linked_backend_layer.maskChanged.connect(self.__maskChangedSlot)
        self.updatePixmap()
    

    def renderMode(self):
        return self._render_mode

    def setRenderMode(self, mode):
        self._render_mode = mode


    def updatePixmap(self):
        if self._linked_backend_layer is None:
            self.pixmap().fill(Qt.transparent)
            return
        
        array = None

        if self.renderMode() == RenderMode.Interpolated:
            array = self._linked_backend_layer.fullResolutionInterpolated()

        elif self.renderMode() == RenderMode.Mask:
            array = self._linked_backend_layer.downscaledPixels().astype(np.float32)
            array = cv2.addWeighted(
                cv2.cvtColor(array, cv2.COLOR_RGB2RGBA), 0.5,
                self._linked_backend_layer.downscaledMask(), 0.5,
                0.0
            )
            array = cv2.cvtColor(array, cv2.COLOR_RGBA2RGB)

        else:
            array = self._linked_backend_layer.fullResolutionInterpolated()

        self.setPixmap(
            uLayers.numpyArrayToPixmap(array)
        )

        if self._linked_sidebar_layer is not None:
            self._linked_sidebar_layer.setThumbnail(self.pixmap())
    

    def opacity(self):
        return int(super().opacity() * 100)

    def setOpacity(self, opacity):
        super().setOpacity(opacity / 100)


    def position(self):
        return self._position
    
    def setPosition(self, pos):
        self._position = pos
        self.setPos(self._position + self.translation() - self._scale_offset)


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
        super().setScale(scalar)

        delta = (origin - self.pos()) * (factor - 1)
        self._scale_offset += delta
        self.setPosition(self.position())

    
    def paint(self, painter: QPainter, option, widget = None):
        painter.save()
        painter.setCompositionMode(self._composition_mode)

        if self.renderMode() == RenderMode.Mask:
            painter.scale(
                1 / self._linked_backend_layer.downscaleFactor(),
                1 / self._linked_backend_layer.downscaleFactor(),
            )

        super().paint(painter, option, widget)
        painter.restore()

        if self.isLayerSelected():
            painter.save()
            painter.setPen(PixmapLayer.__SelectionPen)

            offset = PixmapLayer.__SelectionPen.width() / 2
            bounds = self.boundingRect().adjusted(-offset, -offset, offset, offset)
            painter.drawRect(bounds)

            painter.restore()
    
    
    def boundingRect(self):
        super_rect = super().boundingRect()
        super_size = super_rect.size()

        if self.renderMode() == RenderMode.Mask:
            super_size = super_size / self._linked_backend_layer.downscaleFactor()

        return QRectF(
            super_rect.topLeft(),
            super_size
        )
    
    def shape(self):
        path = QPainterPath()
        path.addRect(self.boundingRect())
        return path


    def mousePressEvent(self, qevent: QGraphicsSceneMouseEvent):
        active_tool = toolbar.ToolBar.getInstance().activeTool()

        if (active_tool == toolbar.Tool.PanView
            or not self._linked_sidebar_layer.isLayerSelected()
        ) and qevent.buttons() == Qt.LeftButton:
            sbLayers.LayerList.getInstance().changeSelection(
                self._linked_sidebar_layer, qevent)
        else:
            self.__tryPaintToMask(qevent)


    def mouseMoveEvent(self, qevent: QGraphicsSceneMouseEvent):
        active_tool = toolbar.ToolBar.getInstance().activeTool()

        if active_tool == toolbar.Tool.MoveLayers:
            if (qevent.buttons() != Qt.LeftButton
                or not self._linked_sidebar_layer.isLayerSelected()
            ):
                return
            
            delta = (qevent.pos() - qevent.lastPos()) * self.scale()
            for layer in self.view()._items:
                if not isinstance(layer, PixmapLayer):
                    continue

                if layer._linked_sidebar_layer.isLayerSelected():
                    layer.setPosition(layer.position() + delta)
        else:
            self.__tryPaintToMask(qevent)

    def mouseReleaseEvent(self, qevent: QGraphicsSceneMouseEvent):
        pass
    

    def __tryPaintToMask(self, qevent):
        if (toolbar.ToolBar.getInstance().activeTool() != toolbar.Tool.MaskBrush
            or not self._linked_sidebar_layer.isLayerSelected()
        ):
            return
        
        color = None
        if qevent.buttons() == Qt.LeftButton:
            color = beBrush.MaskBrush.getInstance().colorRed()
        elif qevent.buttons() == Qt.RightButton:
            color = beBrush.MaskBrush.getInstance().colorNone()
        
        radius = beBrush.MaskBrush.getInstance().radius()
        if color is None or radius <= 0:
            return


        self._linked_backend_layer.drawCircleToMask(
            qevent.pos().x(),
            qevent.pos().y(),
            radius,
            color
        )


    def __indexChangedSlot(self, index):
        self.setZValue(- index)

    def __interpolationChangedSlot(self):
        # if self.renderMode() == RenderMode.Interpolated:
        self.updatePixmap()
    
    def __pixelsChangedSlot(self):
        if self.renderMode() == RenderMode.Pixels:
            self.updatePixmap()

    def __maskChangedSlot(self):
        if self.renderMode() == RenderMode.Mask:
            self.updatePixmap()
    
    def __toolChangedSlot(self, tool):
        if self.isLayerSelected():
            if (tool == toolbar.Tool.MaskBrush
                and self.renderMode() != RenderMode.Mask
            ):
                self.setRenderMode(RenderMode.Mask)
                self.updatePixmap()

            if (tool != toolbar.Tool.MaskBrush
                and self.renderMode() == RenderMode.Mask
            ):
                self.setRenderMode(RenderMode.Pixels)
                self.updatePixmap()

    def __compositionModeChangedSlot(self, mode):
        self._composition_mode = mode
        self.update()
